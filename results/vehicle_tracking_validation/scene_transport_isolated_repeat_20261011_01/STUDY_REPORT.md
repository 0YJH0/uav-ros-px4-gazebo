# Frozen Vehicle Tracking Study

Failed and interrupted attempts are retained. Missing observations are not replaced with successful-run values.

| Group | Attempted / Planned | Success | Safety Event Trials |
| --- | --- | --- | --- |
| selected_overtaking | 10 / 10 | 10 (100.0%) | 0 |

## selected_overtaking

| Metric | N / Missing | Mean | Sample Std | Worst |
| --- | --- | --- | --- | --- |
| visibility | 10 / 0 | 0.9069 | 0.0239 | 0.8605 |
| unplanned_losses | 10 / 0 | 0.7000 | 0.6749 | 2.0000 |
| planned_recovery_s | 10 / 0 | 1.6540 | 0.2221 | 1.8805 |
| unplanned_recovery_mean_s | 6 / 4 | 1.9508 | 2.6235 | 6.7003 |
| mean_pixel_error | 10 / 0 | 16.0739 | 5.8612 | 22.1264 |
| p95_pixel_error | 10 / 0 | 31.3698 | 10.3801 | 40.0120 |
| processing_mean_s | 10 / 0 | 0.1799 | 0.0162 | 0.1957 |
| processing_p95_s | 10 / 0 | 0.2334 | 0.0523 | 0.3194 |
| processing_max_s | 10 / 0 | 0.3486 | 0.0319 | 0.3901 |
| frame_interval_p95_s | 10 / 0 | 0.3293 | 0.0289 | 0.3584 |
| follow_wall_s | 10 / 0 | 100.7454 | 3.0844 | 107.0524 |
| home_error_m | 10 / 0 | 0.6880 | 0.0488 | 0.7532 |
| blind_window_max_s | 10 / 0 | 7.6660 | 0.5337 | 8.2994 |
| blind_command_distance_max_m | 10 / 0 | 2.0139 | 0.2937 | 2.3721 |
| gmc_mean_s | 10 / 0 | 0.0057 | 0.0003 | 0.0060 |
| full_frame_yolo_mean_s | 10 / 0 | 0.1635 | 0.0145 | 0.1772 |
| bytetrack_mean_s | 10 / 0 | 0.0008 | 0.0001 | 0.0008 |
| appearance_mean_s | 10 / 0 | 0.0002 | 0.0000 | 0.0002 |
| identity_association_mean_s | 10 / 0 | 0.0004 | 0.0000 | 0.0005 |
| roi_mean_when_run_s | 10 / 0 | 0.1334 | 0.0119 | 0.1437 |
| frame_age_p95_s | 10 / 0 | 0.3330 | 0.0306 | 0.3635 |
| queue_wait_p95_s | 10 / 0 | 0.1413 | 0.0171 | 0.1554 |
| vertical_error_std | 10 / 0 | 0.1207 | 0.0068 | 0.1317 |
| vertical_bottom_p95 | 10 / 0 | 0.9336 | 0.0108 | 0.9491 |
| vertical_edge_fraction | 10 / 0 | 0.0343 | 0.0095 | 0.0503 |
| outside_panel_losses | 10 / 0 | 0.7000 | 0.6749 | 2.0000 |
| scene_update_errors | 10 / 0 | 0.0000 | 0.0000 | 0.0000 |
| wrong_identity_observations | 10 / 0 | 0.0000 | 0.0000 | 0.0000 |
| scorable_identity_switches | 10 / 0 | 0.0000 | 0.0000 | 0.0000 |
| armed_failsafe_observations | 10 / 0 | 0.0000 | 0.0000 | 0.0000 |
| armed_offboard_lost_observations | 10 / 0 | 0.0000 | 0.0000 | 0.0000 |
| ulog_dropout_events | 10 / 0 | 0.0000 | 0.0000 | 0.0000 |

## Limitations

- No failures are retried or removed. Missing metrics have explicit counts; means include available failed-trial observations, not successes only.
- Std is sample standard deviation; one observation has undefined std.
- Repeated deterministic scenes measure restart/runtime variability, not independent environmental diversity or a general reliability rate.
- TRACK pixel errors are conditional on confirmed observations, not YOLO mAP.
- Blind audits approximate receipt timestamps and sampled setpoints; they supplement, not replace, controller invariant tests.
- Baseline and stress groups are reported separately. Crossing identity needs its own ground-truth evaluation; task pass alone cannot prove ReID.
