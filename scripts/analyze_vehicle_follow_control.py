#!/usr/bin/env python3
"""Inspect fresh navigation and commands during following, excluding return."""

import argparse
import json
import math
from pathlib import Path


def wrap(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


def follow_window(samples):
    following, rows = False, []
    for row in samples:
        following = following or row['state'] == 'TRACK'
        if following and row['state'] in ('RETURN', 'LAND', 'DONE'):
            break
        if following:
            rows.append(row)
    return rows


def fresh_navigation(row):
    nav, command = row.get('navigation'), row.get('setpoint')
    return bool(nav and command and nav['xy_valid'] and nav['z_valid'] and
                0 <= row['wall_s'] - nav['wall_s'] <= 0.5 and
                0 <= row['wall_s'] - command['wall_s'] <= 0.5 and
                math.isfinite(nav['heading_rad']) and math.isfinite(command['yaw_rad']))


def summarize(rows):
    valid = [row for row in rows if fresh_navigation(row)]
    leads = sorted(abs(math.degrees(wrap(
        row['setpoint']['yaw_rad'] - row['navigation']['heading_rad']))) for row in valid)
    simultaneous = [row for row in rows if row.get('position_ned') and
                    row.get('vehicle_ground_truth') and
                    0 <= row['wall_s'] - row['vehicle_ground_truth']['wall_s'] <= 0.5]
    gaps = [row['vehicle_ground_truth']['x'] - row['position_ned'][1] for row in simultaneous]
    return {
        'limitation': 'Sample-conditioned diagnostics, not independent target identity proof. '
                      'Navigation/commands older than 0.5 seconds are excluded; RETURN is excluded.',
        'start_wall_s': rows[0]['wall_s'] if rows else None,
        'end_wall_s': rows[-1]['wall_s'] if rows else None,
        'sample_count': len(rows), 'fresh_navigation_command_samples': len(valid),
        'yaw_command_lead_p95_deg': leads[int((len(leads) - 1) * 0.95)] if leads else None,
        'yaw_command_lead_max_deg': max(leads) if leads else None,
        'forward_gap_start_m': gaps[0] if gaps else None,
        'forward_gap_end_m': gaps[-1] if gaps else None,
        'maximum_uav_east_m': max(row['position_ned'][1] for row in simultaneous)
        if simultaneous else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    args = parser.parse_args()
    directory = Path(args.directory)
    outputs = [directory / 'follow_control.json', directory / 'follow_control.png']
    if any(path.exists() for path in outputs):
        raise RuntimeError('Refusing to overwrite existing diagnostic evidence.')
    rows = follow_window([json.loads(line) for line in
                          (directory / 'samples.jsonl').read_text().splitlines() if line.strip()])
    summary = summarize(rows)
    valid = [row for row in rows if fresh_navigation(row)]
    if not valid:
        raise RuntimeError('No fresh heading/setpoint evidence; use a recorder with navigation outputs.')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    times = [row['wall_s'] for row in valid]
    headings = np.unwrap([row['navigation']['heading_rad'] for row in valid])
    leads = np.array([wrap(row['setpoint']['yaw_rad'] - row['navigation']['heading_rad'])
                      for row in valid])
    figure, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(times, np.degrees(headings), label='Actual heading')
    axes[0].plot(times, np.degrees(headings + leads), label='Commanded heading', alpha=0.8)
    axes[0].set_ylabel('Heading (deg)')
    axes[0].legend()
    observed = [row for row in rows if row.get('target') and row['target']['detected']]
    axes[1].plot([row['wall_s'] for row in observed],
                 [row['target']['error_x'] for row in observed], '.', markersize=2)
    axes[1].axhline(0, color='gray', linewidth=0.8)
    axes[1].set_ylabel('Last associated image error')
    axes[1].set_xlabel('Recorded wall time (s), before RETURN')
    for axis in axes:
        axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(outputs[1], dpi=150)
    outputs[0].write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
