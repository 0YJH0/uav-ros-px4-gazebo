from threading import Thread

from uav_learning.vehicle_frame_buffer import LatestFrameBuffer


def test_latest_frame_replaces_pending_frame_without_backlog():
    buffer = LatestFrameBuffer()
    for index in range(100):
        buffer.put(index, float(index))
    assert buffer.replaced == 99
    assert buffer.take() == (99, 99.)
    assert buffer.pending is None


def test_close_unblocks_waiting_worker_and_discards_pending_frames():
    buffer = LatestFrameBuffer()
    results = []
    thread = Thread(target=lambda: results.append(buffer.take()))
    thread.start()
    buffer.close()
    thread.join(timeout=1)
    assert not thread.is_alive() and results == [None]
    buffer.put('after shutdown', 1.)
    assert buffer.pending is None and buffer.take() is None
