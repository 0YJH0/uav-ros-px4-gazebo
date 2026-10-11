import importlib.util
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[4] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('framing', SCRIPTS / 'analyze_vehicle_framing.py')
framing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(framing)


def test_pose_matching_is_timestamp_bounded_and_handles_ends():
    poses = [{'sim_s': 1.}, {'sim_s': 2.}]
    assert framing.matched_pose(poses, [1., 2.], {'sec': 1, 'nanosec': 100_000_000}) == poses[0]
    assert framing.matched_pose(poses, [1., 2.], {'sec': 2, 'nanosec': 100_000_000}) == poses[1]
    assert framing.matched_pose(poses, [1., 2.], {'sec': 1, 'nanosec': 500_000_000}) is None
    assert framing.matched_pose([], [], {'sec': 1, 'nanosec': 0}) is None


def test_empty_audit_statistics_do_not_invent_observations():
    assert framing.distribution([]) == {'n': 0, 'mean': None, 'p95': None, 'max': None}
