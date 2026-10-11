import json
from pathlib import Path
import shutil
import sys

ROOT = Path('/home/yjh/ROS2_manmade')
sys.path.insert(0, str(ROOT / 'scripts'))
from vehicle_experiment_study import digest, load_json, metric_summary, write_json

study = ROOT / 'results/vehicle_tracking_validation/scene_transport_isolated_repeat_20261011_01'
audit = ROOT / 'results/vehicle_tracking_validation/scene_transport_isolated_repeat_audit_20261011_01'
summary = load_json(study / 'study_summary.json')
completion = load_json(audit / 'completion_check.json')
services = load_json(audit / 'scene_service_summary.json')
losses = load_json(audit / 'loss_windows/nonplanned_loss_audit.json')
parameters = load_json(study / 'px4_parameter_audit.json')
episodes = [{'name': trial['name']+f'_loss_{index+1:02d}', 'recovery_s': loss['duration_wall_s']}
            for trial in losses['trials'] for index, loss in enumerate(trial.get('nonplanned_losses', []))]
assert completion['evidence_complete'] and not services['log_integrity_errors']
assert completion['attempted'] == completion['planned'] == 10
workers = [pid for row in services['trials'] for log in row['logs'].values() for pid in log['worker_pids']]
assert len(workers) == len(set(workers)) == 10
inputs = [study / name for name in ('study_summary.json', 'study_status.json', 'px4_parameter_audit.json')]
inputs += [audit / name for name in ('completion_check.json', 'scene_service_summary.json',
                                   'loss_windows/nonplanned_loss_audit.json')]
result = {
    'batch': str(study), 'planned': 10, 'attempted': 10,
    'task_passes': completion['task_passes'], 'identity_passes': completion['identity_passes'],
    'strict_passes': completion['strict_passes'],
    'summary': summary['groups']['selected_overtaking'],
    'total_scene_requests': services['total_requests'], 'failed_scene_requests': services['failed_requests'],
    'creation_requests': sum(log['services'].get('/world/default/create', {}).get('requests', 0)
                             for row in services['trials'] for log in row['logs'].values()),
    'motion_metrics': services['motion_metrics'],
    'nonplanned_loss_episodes': len(episodes),
    'episode_recovery_metrics': metric_summary(episodes, 'recovery_s', 'max'),
    'unique_service_workers': len(set(workers)), 'worker_pids': workers,
    'calibration_differences': {row['name']: row['calibration_differences'] for row in parameters['trials']
                               if row.get('calibration_differences')},
    'other_recorded_px4_parameter_differences': {row['name']: row['other_parameter_differences']
        for row in parameters['trials'] if row.get('other_parameter_differences')},
    'safety_totals': {key: sum(row[key] for row in summary['trials']) for key in (
        'armed_failsafe_observations', 'armed_offboard_lost_observations', 'ulog_dropout_events', 'interventions')},
    'input_sha256': {str(path): digest(path) for path in inputs},
    'analysis_script_sha256': digest(Path(__file__)),
    'limitations': ['Event-level recovery N=7 differs from per-trial conditional recovery N=6.',
                    'Four trials had no nonplanned loss; their recovery is not imputed as zero.',
                    'Freeze enforces code, weights and ROS configuration, not all persistent PX4 calibration.',
                    'No flight evidence or verdicts were rewritten.'],
}
write_json(audit / 'final_metrics.json', result)
shutil.copy2(Path(__file__), audit / Path(__file__).name)
print(json.dumps({key: value for key, value in result.items() if key not in (
    'summary', 'input_sha256', 'calibration_differences', 'motion_metrics')}, indent=2))
