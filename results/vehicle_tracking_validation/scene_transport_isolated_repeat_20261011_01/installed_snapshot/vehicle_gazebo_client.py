"""Persistent Gazebo service transport with per-request diagnostics."""

import hashlib
import multiprocessing
import os
import time

from google.protobuf import text_format
from gz.msgs10.boolean_pb2 import Boolean
from gz.msgs10.entity_factory_pb2 import EntityFactory
from gz.msgs10.pose_pb2 import Pose


class GazeboSceneClient:
    def __init__(self, world='default', *, node=None, record=None, client='scene',
                 clock=time.monotonic):
        if node is None:
            from gz.transport13 import Node
            node = Node()
        self.node = node
        self.world = world
        self.record = record
        self.client = client
        self.clock = clock
        self.sequence = 0

    def request(self, service, request_type, payload):
        started = self.clock()
        self.sequence += 1
        diagnostic = {'client': self.client, 'sequence': self.sequence,
                      'service': f'/world/{self.world}/{service}',
                      'request_type': request_type, 'timeout_ms': 500,
                      'start_monotonic_s': started, 'success': False,
                      'payload_sha256': hashlib.sha256(payload.encode()).hexdigest(),
                      'binding_result': None, 'response_data': None}
        try:
            kind = {'gz.msgs.Pose': Pose, 'gz.msgs.EntityFactory': EntityFactory}[request_type]
            message = text_format.Parse(payload, kind())
            diagnostic['model_name'] = message.name
            if isinstance(message, Pose):
                diagnostic['requested_position'] = [message.position.x, message.position.y, message.position.z]
                diagnostic['requested_orientation'] = [message.orientation.x, message.orientation.y,
                                                       message.orientation.z, message.orientation.w]
            result, response = self.node.request(diagnostic['service'], message, kind, Boolean, 500)
            diagnostic.update(binding_result=bool(result), response_data=bool(response.data))
            diagnostic['success'] = bool(result and response.data)
            diagnostic['reason'] = ('accepted' if diagnostic['success'] else
                                    'request_not_confirmed' if not result else 'response_false')
        except Exception as error:
            diagnostic.update(reason='exception', error_type=type(error).__name__, error=str(error))
        diagnostic['duration_s'] = max(0., self.clock() - started)
        if self.record is not None:
            self.record(diagnostic)
        return diagnostic['success']


def _service_worker(connection, world, client):
    records = []
    native = GazeboSceneClient(world, record=records.append, client=client)
    # Warm discovery once. This process has no Python transport subscribers.
    services = native.node.service_list()
    connection.send({'ready': True, 'pid': os.getpid(), 'services': services})
    try:
        while True:
            command = connection.recv()
            if command is None:
                break
            native.request(*command)
            connection.send(records.pop())
    except (EOFError, BrokenPipeError):
        pass
    finally:
        connection.close()


class IsolatedGazeboSceneClient:
    """Keep blocking Gazebo bindings away from Python subscription callbacks."""

    def __init__(self, world='default', *, record=None, client='traffic'):
        self.world, self.record, self.client = world, record, client
        self.failed = False
        context = multiprocessing.get_context('spawn')
        self.connection, child = context.Pipe()
        self.process = context.Process(target=_service_worker, args=(child, world, client),
                                       name='gazebo_scene_service', daemon=True)
        self.process.start()
        child.close()
        try:
            if not self.connection.poll(3.):
                raise RuntimeError('Gazebo service worker did not initialize within 3 seconds.')
            ready = self.connection.recv()
            if not ready.get('ready'):
                raise RuntimeError('Gazebo service worker is not ready.')
        except BaseException:
            self.close()
            raise

    def request(self, service, kind, payload):
        started = time.monotonic()
        try:
            if self.failed or not self.process.is_alive():
                raise RuntimeError('Gazebo service worker is unavailable; no request retry.')
            self.connection.send((service, kind, payload))
            # Pipe polling releases the parent GIL so pose callbacks keep running.
            if not self.connection.poll(2.):
                raise TimeoutError('Gazebo service worker IPC exceeded 2 seconds.')
            diagnostic = self.connection.recv()
            diagnostic.update(transport_backend='isolated_native', worker_pid=self.process.pid,
                              ipc_duration_s=time.monotonic()-started)
        except (EOFError, OSError, RuntimeError, TimeoutError) as error:
            self.failed = True
            diagnostic = {'client': self.client, 'service': f'/world/{self.world}/{service}',
                          'request_type': kind, 'timeout_ms': 500, 'success': False,
                          'reason': 'worker_failure', 'error_type': type(error).__name__,
                          'error': str(error), 'duration_s': time.monotonic()-started,
                          'transport_backend': 'isolated_native', 'worker_pid': self.process.pid}
            self.close()
        if self.record is not None:
            self.record(diagnostic)
        return diagnostic['success']

    def close(self):
        if self.process.is_alive():
            try:
                self.connection.send(None)
            except (OSError, EOFError):
                pass
            self.process.join(2.)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(2.)
            if self.process.is_alive():
                self.process.kill()
                self.process.join()
        self.connection.close()
