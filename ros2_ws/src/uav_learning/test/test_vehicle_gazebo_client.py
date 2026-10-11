from types import SimpleNamespace

import pytest

from uav_learning.vehicle_gazebo_client import GazeboSceneClient, IsolatedGazeboSceneClient


POSE = 'name: "tracked_vehicle", position: {x: 16, y: 0, z: 0.05}, orientation: {w: 1}'


@pytest.mark.parametrize('result,reply,success,reason', [
    (True, True, True, 'accepted'), (True, False, False, 'response_false'),
    (False, False, False, 'request_not_confirmed'), (False, True, False, 'request_not_confirmed')])
def test_native_result_and_reply_are_both_required(result, reply, success, reason):
    calls, records = [], []
    def request(*args):
        calls.append(args)
        return result, SimpleNamespace(data=reply)
    client = GazeboSceneClient(node=SimpleNamespace(request=request), record=records.append)
    assert client.request('set_pose', 'gz.msgs.Pose', POSE) is success
    assert len(calls) == len(records) == 1
    assert calls[0][0] == '/world/default/set_pose' and calls[0][-1] == 500
    assert records[0]['reason'] == reason
    assert records[0]['model_name'] == 'tracked_vehicle'
    assert records[0]['requested_position'] == [16., 0., .05]


def test_reuses_native_node_without_retries_or_command_processes():
    calls, records = [], []
    node = SimpleNamespace(request=lambda *args: (calls.append(args) or (True, SimpleNamespace(data=True))))
    client = GazeboSceneClient(node=node, record=records.append)
    for _ in range(3):
        assert client.request('set_pose', 'gz.msgs.Pose', POSE)
    assert client.node is node and len(calls) == 3
    assert [row['sequence'] for row in records] == [1, 2, 3]


def test_exception_is_diagnosed_and_never_successful():
    records = []
    def request(*args):
        raise RuntimeError('connection unavailable')
    client = GazeboSceneClient(node=SimpleNamespace(request=request), record=records.append)
    assert not client.request('set_pose', 'gz.msgs.Pose', POSE)
    assert records[0]['reason'] == 'exception'
    assert records[0]['error_type'] == 'RuntimeError'


def test_malformed_payload_is_rejected_before_transport():
    records = []
    def request(*args):
        pytest.fail('Invalid protobuf must not reach transport')
    client = GazeboSceneClient(node=SimpleNamespace(request=request), record=records.append)
    assert not client.request('set_pose', 'gz.msgs.Pose', 'invalid_field: 2')
    assert records[0]['reason'] == 'exception'


def test_create_message_is_parsed_without_a_cli():
    calls = []
    node = SimpleNamespace(request=lambda *args: (calls.append(args) or (True, SimpleNamespace(data=True))))
    client = GazeboSceneClient('custom', node=node)
    assert client.request('create', 'gz.msgs.EntityFactory', 'sdf: "<sdf/>"')
    assert calls[0][0] == '/world/custom/create' and calls[0][1].sdf == '<sdf/>'


def test_worker_reply_stays_a_failure_and_uses_the_existing_ipc_bound():
    calls, records = [], []
    client = IsolatedGazeboSceneClient.__new__(IsolatedGazeboSceneClient)
    client.world, client.client, client.failed = 'default', 'traffic', False
    client.record = records.append
    client.process = SimpleNamespace(is_alive=lambda: True, pid=42)
    client.connection = SimpleNamespace(send=calls.append, poll=lambda timeout: calls.append(timeout) or True,
                                        recv=lambda: {'success': False, 'reason': 'response_false'})
    assert not client.request('set_pose', 'gz.msgs.Pose', POSE)
    assert calls == [('set_pose', 'gz.msgs.Pose', POSE), 2.]
    assert records[0]['worker_pid'] == 42 and records[0]['transport_backend'] == 'isolated_native'


def test_ipc_timeout_latches_failure_and_closes_worker_without_retry():
    records, sends, closes = [], [], []
    client = IsolatedGazeboSceneClient.__new__(IsolatedGazeboSceneClient)
    client.world, client.client, client.failed = 'default', 'traffic', False
    client.record = records.append
    client.process = SimpleNamespace(is_alive=lambda: True, pid=42)
    client.connection = SimpleNamespace(send=sends.append, poll=lambda timeout: False)
    client.close = lambda: closes.append(True)
    assert not client.request('set_pose', 'gz.msgs.Pose', POSE)
    assert not client.request('set_pose', 'gz.msgs.Pose', POSE)
    assert len(sends) == 1 and client.failed and len(closes) == 2
    assert all(not row['success'] and row['reason'] == 'worker_failure' for row in records)
