# Two-Scenario Frozen Repeat Report

## Protocol

Independent simulator restart for every attempted trial; no failed run is replaced. Frozen YOLO11s/OpenVINO FP32 CPU parameters and 10-second blind-motion limit are unchanged. Both scenarios use red distractors and a curbside parked car.

Coverage is time-weighted onboard target confirmation, not mAP or independently verified identity accuracy. Identity uses exclusive_projection_v2 with unchanged criteria. Unscorable frames are not counted as correct.

Strict pass requires task, independent identity, completed traffic maneuver, autonomous landing/disarming, complete successful native service receipts, ULog safety evidence and frozen source/parameter integrity.

| Scenario | Planned | Attempted | Completed | Task Pass | Identity Pass | Strict Pass | Unlaunched |
|---|---:|---:|---:|---:|---:|---:|---:|
| left_overtaking | 10 | 10 | 10 | 10/10 | 10/10 | 7/10 | 0 |
| lane_change | 10 | 10 | 10 | 9/10 | 10/10 | 3/10 | 0 |

## left_overtaking

| Metric | Available Trials | Mean | Sample SD | Worst |
|---|---:|---:|---:|---:|
| task_passed | 10 | 1.000 | 0.000 | 1.000 |
| strict_joint_passed | 10 | 0.700 | 0.483 | 0.000 |
| identity_verified | 10 | 1.000 | 0.000 | 1.000 |
| coverage_percent | 10 | 94.191 | 0.250 | 93.697 |
| unplanned_losses | 10 | 0.200 | 0.422 | 1.000 |
| unplanned_recovery_mean_s | 2 | 0.200 | 0.000 | 0.200 |
| unplanned_recovery_max_s | 2 | 0.200 | 0.000 | 0.200 |
| unplanned_recovery_censored_count | 10 | 0.000 | 0.000 | 0.000 |
| recovery_timeout_count | 10 | 0.000 | 0.000 | 0.000 |
| planned_recovery_mean_s | 10 | 1.139 | 0.242 | 1.612 |
| planned_recovery_max_s | 10 | 1.139 | 0.242 | 1.612 |
| track_mean_abs_pixel_error | 10 | 13.172 | 3.058 | 17.127 |
| track_p95_abs_pixel_error | 10 | 32.461 | 7.843 | 37.135 |
| final_home_horizontal_error_m | 10 | 0.725 | 0.036 | 0.769 |
| drone_follow_travel_m | 10 | 67.074 | 1.257 | 64.905 |
| full_frame_yolo_mean_s | 10 | 0.113 | 0.003 | 0.122 |
| full_frame_yolo_p95_s | 10 | 0.125 | 0.012 | 0.158 |
| processing_mean_s | 10 | 0.128 | 0.004 | 0.138 |
| processing_p95_s | 10 | 0.210 | 0.003 | 0.215 |
| target_publish_age_mean_s | 10 | 0.159 | 0.005 | 0.172 |
| target_publish_age_p95_s | 10 | 0.250 | 0.014 | 0.286 |
| queue_wait_mean_s | 10 | 0.032 | 0.002 | 0.035 |
| queue_wait_p95_s | 10 | 0.099 | 0.006 | 0.111 |
| wrong_identity_observations | 10 | 0.000 | 0.000 | 0.000 |
| scorable_identity_switches | 10 | 0.000 | 0.000 | 0.000 |
| identity_scorable_fraction | 10 | 0.961 | 0.002 | 0.956 |
| post_identity_frames | 10 | 349.600 | 16.521 | 321.000 |
| scene_request_failures | 10 | 0.100 | 0.316 | 1.000 |
| safety_event_observations | 10 | 0.000 | 0.000 | 0.000 |
| wall_duration_s | 10 | 175.467 | 3.132 | 183.502 |

Unplanned recovery episodes: 2; recovered: 2; censored: 0; timeout: 0. Recovered-only pooled mean: 0.200 s, sample SD: 0.000 s, worst: 0.200 s. Censor lower bounds: [].

Failure reasons:

- service_receipt_sequence_incomplete:scene: 2
- scene_service_requests_failed: 1

## lane_change

| Metric | Available Trials | Mean | Sample SD | Worst |
|---|---:|---:|---:|---:|
| task_passed | 10 | 0.900 | 0.316 | 0.000 |
| strict_joint_passed | 10 | 0.300 | 0.483 | 0.000 |
| identity_verified | 10 | 1.000 | 0.000 | 1.000 |
| coverage_percent | 10 | 92.622 | 1.994 | 88.646 |
| unplanned_losses | 10 | 1.300 | 2.003 | 5.000 |
| unplanned_recovery_mean_s | 5 | 0.352 | 0.206 | 0.700 |
| unplanned_recovery_max_s | 5 | 0.740 | 0.942 | 2.400 |
| unplanned_recovery_censored_count | 10 | 0.000 | 0.000 | 0.000 |
| recovery_timeout_count | 10 | 0.000 | 0.000 | 0.000 |
| planned_recovery_mean_s | 10 | 1.100 | 0.144 | 1.320 |
| planned_recovery_max_s | 10 | 1.100 | 0.144 | 1.320 |
| track_mean_abs_pixel_error | 10 | 14.283 | 1.165 | 15.950 |
| track_p95_abs_pixel_error | 10 | 35.596 | 1.068 | 37.379 |
| final_home_horizontal_error_m | 10 | 0.739 | 0.036 | 0.791 |
| drone_follow_travel_m | 10 | 68.552 | 2.000 | 65.227 |
| full_frame_yolo_mean_s | 10 | 0.112 | 0.001 | 0.114 |
| full_frame_yolo_p95_s | 10 | 0.123 | 0.002 | 0.128 |
| processing_mean_s | 10 | 0.127 | 0.001 | 0.129 |
| processing_p95_s | 10 | 0.210 | 0.005 | 0.215 |
| target_publish_age_mean_s | 10 | 0.157 | 0.003 | 0.164 |
| target_publish_age_p95_s | 10 | 0.249 | 0.010 | 0.264 |
| queue_wait_mean_s | 10 | 0.031 | 0.002 | 0.036 |
| queue_wait_p95_s | 10 | 0.097 | 0.003 | 0.101 |
| wrong_identity_observations | 10 | 0.000 | 0.000 | 0.000 |
| scorable_identity_switches | 10 | 0.000 | 0.000 | 0.000 |
| identity_scorable_fraction | 10 | 0.935 | 0.037 | 0.856 |
| post_identity_frames | 10 | 227.300 | 14.652 | 200.000 |
| scene_request_failures | 10 | 0.600 | 0.516 | 1.000 |
| safety_event_observations | 10 | 0.000 | 0.000 | 0.000 |
| wall_duration_s | 10 | 178.246 | 3.592 | 186.195 |

Unplanned recovery episodes: 13; recovered: 13; censored: 0; timeout: 0. Recovered-only pooled mean: 0.461 s, sample SD: 0.596 s, worst: 2.400 s. Censor lower bounds: [].

Failure reasons:

- scene_service_requests_failed: 6
- supervisor_exit_not_zero:1: 1
- task_passed_not_confirmed: 1
- planned_occlusion_criteria_not_met: 1
- supervisor_autonomous_passed_not_confirmed: 1

## Every Planned Trial

| Trial | State | Task | Identity | Strict | Coverage % | Unplanned Losses | Mean Error px | Post Identity Frames |
|---|---|---|---|---|---:|---:|---:|---:|
| [left_overtaking_01](left_overtaking_01/) | completed | True | True | False | 94.003 | 0 | 5.994 | 329 |
| [lane_change_01](lane_change_01/) | completed | True | True | False | 93.630 | 0 | 14.682 | 222 |
| [left_overtaking_02](left_overtaking_02/) | completed | True | True | False | 93.921 | 0 | 15.882 | 335 |
| [lane_change_02](lane_change_02/) | completed | True | True | True | 89.297 | 5 | 15.132 | 204 |
| [left_overtaking_03](left_overtaking_03/) | completed | True | True | True | 94.348 | 0 | 14.764 | 364 |
| [lane_change_03](lane_change_03/) | completed | True | True | False | 93.323 | 1 | 12.390 | 234 |
| [left_overtaking_04](left_overtaking_04/) | completed | True | True | True | 94.254 | 0 | 12.517 | 358 |
| [lane_change_04](lane_change_04/) | completed | True | True | False | 94.192 | 0 | 12.427 | 238 |
| [left_overtaking_05](left_overtaking_05/) | completed | True | True | False | 93.697 | 0 | 12.793 | 356 |
| [lane_change_05](lane_change_05/) | completed | True | True | False | 88.646 | 5 | 15.950 | 200 |
| [left_overtaking_06](left_overtaking_06/) | completed | True | True | True | 94.229 | 0 | 17.127 | 321 |
| [lane_change_06](lane_change_06/) | completed | True | True | True | 93.956 | 0 | 15.036 | 235 |
| [left_overtaking_07](left_overtaking_07/) | completed | True | True | True | 94.480 | 0 | 10.965 | 373 |
| [lane_change_07](lane_change_07/) | completed | True | True | False | 93.089 | 1 | 14.398 | 243 |
| [left_overtaking_08](left_overtaking_08/) | completed | True | True | True | 94.153 | 0 | 14.014 | 348 |
| [lane_change_08](lane_change_08/) | completed | True | True | True | 93.593 | 0 | 13.913 | 227 |
| [left_overtaking_09](left_overtaking_09/) | completed | True | True | True | 94.407 | 1 | 14.066 | 351 |
| [lane_change_09](lane_change_09/) | completed | False | True | False | 92.467 | 0 | 15.065 | 231 |
| [left_overtaking_10](left_overtaking_10/) | completed | True | True | True | 94.413 | 1 | 13.599 | 361 |
| [lane_change_10](lane_change_10/) | completed | True | True | False | 94.026 | 1 | 13.839 | 239 |

## Interpretation And Limits

- All attempted failures remain in success denominators; unlaunched trials are explicitly incomplete, not successes or hidden failures.
- Metric count is the number with available evidence; missing metrics are not imputed as zero. Sample SD uses n-1 and is unavailable for n<2.
- Group timing means summarize per-trial means, not pooled frames. Per-trial timing covers all recorded associations, not only TRACK.
- No-loss trials have no recovery duration, not a zero-second recovery. Unrecovered episodes remain censored and are listed separately.
- Task recovery and inference durations are wall seconds; traffic trajectory phases and identity observer latency are simulation seconds.
- Zero observed wrong identities applies only to scorable projected-volume evidence; ambiguous and missing-truth frames are not proof of correctness.
- Fixed-scene repeats measure runtime repeatability, not random-scene, real-flight or weather generalization.
- ULog safety fields are observation counts, not necessarily distinct incidents; zero counts do not certify absence of every collision.
- The two traffic scenarios have different geometry; their difference is not an isolated algorithm ablation.
- Historical pilot runs are excluded from the repeat denominator.
- Runtime PX4 calibration and flight counters may vary despite frozen launch settings; inspect px4_parameter_audit.json before attributing changes to control tuning.

Machine-readable evidence: [SUMMARY.json](SUMMARY.json), [trials.csv](trials.csv), per-trial `batch_audit.json`, raw logs, identity projections, flight ULogs and frozen source hashes.
