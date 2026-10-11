"""Single-slot camera mailbox: inference never builds a frame backlog."""

from threading import Condition


class LatestFrameBuffer:
    def __init__(self):
        self.condition = Condition()
        self.pending = None
        self.closed = False
        self.replaced = 0

    def put(self, message, received_at):
        with self.condition:
            if self.closed:
                return
            if self.pending is not None:
                self.replaced += 1
            self.pending = (message, received_at)
            self.condition.notify()

    def take(self):
        with self.condition:
            self.condition.wait_for(lambda: self.closed or self.pending is not None)
            if self.closed:
                return None
            result, self.pending = self.pending, None
            return result

    def close(self):
        with self.condition:
            self.closed = True
            self.pending = None
            self.condition.notify_all()
