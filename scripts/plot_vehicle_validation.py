#!/usr/bin/env python3
"""Plot observed forward motion and separation without relying on FSM labels."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    args = parser.parse_args()
    directory = Path(args.directory)
    rows = [json.loads(line) for line in
            (directory / 'samples.jsonl').read_text().splitlines()]
    samples = [row for row in rows if row.get('vehicle_ground_truth')
               and row.get('position_ned')]
    if not samples:
        raise SystemExit('No simultaneous vehicle and UAV telemetry')
    times = [row['wall_s'] for row in samples]
    car_x = [row['vehicle_ground_truth']['x'] for row in samples]
    drone_x = [row['position_ned'][1] for row in samples]
    separation = [a - b for a, b in zip(car_x, drone_x)]
    summary = {
        'vehicle_forward_displacement_m': car_x[-1] - car_x[0],
        'uav_forward_displacement_m': drone_x[-1] - drone_x[0],
        'maximum_uav_forward_position_m': max(drone_x),
        'initial_forward_gap_m': separation[0],
        'final_forward_gap_m': separation[-1],
        'intervention': 'See mission logs; do not interpret displacement as success',
    }
    (directory / 'forward_motion.json').write_text(json.dumps(summary, indent=2))
    figure, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(times, car_x, label='Vehicle world X')
    axes[0].plot(times, drone_x, label='UAV east position')
    axes[0].set_ylabel('Forward position (m)')
    axes[0].legend()
    axes[1].plot(times, separation, color='tab:red')
    axes[1].set_ylabel('Forward separation (m)')
    axes[1].set_xlabel('Recorded wall time (s)')
    report = json.loads((directory / 'report.json').read_text())
    for event in report.get('occlusions', []):
        for axis in axes:
            axis.axvspan(event['start_wall_s'], event['end_wall_s'] or times[-1],
                         alpha=0.2, color='gray')
    for axis in axes:
        axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(directory / 'forward_motion.png', dpi=150)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
