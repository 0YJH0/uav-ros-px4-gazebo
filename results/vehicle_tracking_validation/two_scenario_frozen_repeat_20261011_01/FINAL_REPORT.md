# Two-Scenario Frozen Repeat Report

## Protocol

Independent simulator restart for every attempted trial; no failed run is replaced. Frozen YOLO11s/PyTorch parameters and 10-second blind-motion limit are unchanged. Both scenarios use red distractors and a curbside parked car.

Coverage is time-weighted onboard target confirmation, not mAP or independently verified identity accuracy. Identity uses exclusive_projection_v2 with unchanged criteria. Unscorable frames are not counted as correct.

Strict pass requires task, independent identity, completed traffic maneuver, autonomous landing/disarming, complete successful native service receipts, ULog safety evidence and frozen source/parameter integrity.

| Scenario | Planned | Attempted | Completed | Task Pass | Identity Pass | Strict Pass | Unlaunched |
|---|---:|---:|---:|---:|---:|---:|---:|
| left_overtaking | 10 | 10 | 10 | 10/10 | 10/10 | 8/10 | 0 |
| lane_change | 10 | 10 | 10 | 10/10 | 9/10 | 9/10 | 0 |

## left_overtaking

| Metric | Available Trials | Mean | Sample SD | Worst |
|---|---:|---:|---:|---:|
| task_passed | 10 | 1.000 | 0.000 | 1.000 |
| strict_joint_passed | 10 | 0.800 | 0.422 | 0.000 |
| identity_verified | 10 | 1.000 | 0.000 | 1.000 |
| coverage_percent | 10 | 92.427 | 1.100 | 90.464 |
| unplanned_losses | 10 | 0.600 | 0.843 | 2.000 |
| unplanned_recovery_mean_s | 4 | 0.480 | 0.069 | 0.550 |
| unplanned_recovery_max_s | 4 | 0.506 | 0.082 | 0.600 |
| unplanned_recovery_censored_count | 10 | 0.000 | 0.000 | 0.000 |
| recovery_timeout_count | 10 | 0.000 | 0.000 | 0.000 |
| planned_recovery_mean_s | 10 | 1.614 | 0.497 | 2.491 |
| planned_recovery_max_s | 10 | 1.614 | 0.497 | 2.491 |
| track_mean_abs_pixel_error | 10 | 15.621 | 1.641 | 18.212 |
| track_p95_abs_pixel_error | 10 | 37.248 | 1.073 | 38.752 |
| final_home_horizontal_error_m | 10 | 0.676 | 0.029 | 0.720 |
| drone_follow_travel_m | 10 | 55.362 | 6.667 | 45.661 |
| full_frame_yolo_mean_s | 10 | 0.163 | 0.033 | 0.230 |
| full_frame_yolo_p95_s | 10 | 0.209 | 0.060 | 0.295 |
| processing_mean_s | 10 | 0.180 | 0.035 | 0.251 |
| processing_p95_s | 10 | 0.267 | 0.052 | 0.353 |
| target_publish_age_mean_s | 10 | 0.228 | 0.045 | 0.314 |
| target_publish_age_p95_s | 10 | 0.340 | 0.061 | 0.449 |
| queue_wait_mean_s | 10 | 0.049 | 0.010 | 0.065 |
| queue_wait_p95_s | 10 | 0.135 | 0.022 | 0.176 |
| wrong_identity_observations | 10 | 0.000 | 0.000 | 0.000 |
| scorable_identity_switches | 10 | 0.000 | 0.000 | 0.000 |
| identity_scorable_fraction | 10 | 0.945 | 0.009 | 0.930 |
| post_identity_frames | 10 | 208.100 | 68.245 | 105.000 |
| scene_request_failures | 10 | 0.100 | 0.316 | 1.000 |
| safety_event_observations | 10 | 0.000 | 0.000 | 0.000 |
| wall_duration_s | 10 | 195.474 | 11.846 | 221.502 |

Unplanned recovery episodes: 6; recovered: 6; censored: 0; timeout: 0. Recovered-only pooled mean: 0.487 s, sample SD: 0.077 s, worst: 0.600 s. Censor lower bounds: [].

Failure reasons:

- scene_service_requests_failed: 1
- service_receipt_sequence_incomplete:scene: 1

## lane_change

| Metric | Available Trials | Mean | Sample SD | Worst |
|---|---:|---:|---:|---:|
| task_passed | 10 | 1.000 | 0.000 | 1.000 |
| strict_joint_passed | 10 | 0.900 | 0.316 | 0.000 |
| identity_verified | 10 | 0.900 | 0.316 | 0.000 |
| coverage_percent | 10 | 90.436 | 2.053 | 87.831 |
| unplanned_losses | 10 | 2.000 | 1.633 | 5.000 |
| unplanned_recovery_mean_s | 8 | 1.262 | 1.316 | 4.327 |
| unplanned_recovery_max_s | 8 | 1.723 | 1.322 | 4.327 |
| unplanned_recovery_censored_count | 10 | 0.000 | 0.000 | 0.000 |
| recovery_timeout_count | 10 | 0.000 | 0.000 | 0.000 |
| planned_recovery_mean_s | 10 | 1.470 | 0.290 | 1.841 |
| planned_recovery_max_s | 10 | 1.470 | 0.290 | 1.841 |
| track_mean_abs_pixel_error | 10 | 15.296 | 3.574 | 18.908 |
| track_p95_abs_pixel_error | 10 | 34.842 | 6.771 | 39.508 |
| final_home_horizontal_error_m | 10 | 0.702 | 0.036 | 0.757 |
| drone_follow_travel_m | 10 | 54.530 | 6.033 | 44.897 |
| full_frame_yolo_mean_s | 10 | 0.165 | 0.028 | 0.221 |
| full_frame_yolo_p95_s | 10 | 0.227 | 0.056 | 0.297 |
| processing_mean_s | 10 | 0.184 | 0.029 | 0.242 |
| processing_p95_s | 10 | 0.284 | 0.032 | 0.327 |
| target_publish_age_mean_s | 10 | 0.233 | 0.037 | 0.307 |
| target_publish_age_p95_s | 10 | 0.360 | 0.046 | 0.450 |
| queue_wait_mean_s | 10 | 0.051 | 0.009 | 0.067 |
| queue_wait_p95_s | 10 | 0.138 | 0.016 | 0.167 |
| wrong_identity_observations | 10 | 0.000 | 0.000 | 0.000 |
| scorable_identity_switches | 10 | 0.000 | 0.000 | 0.000 |
| identity_scorable_fraction | 10 | 0.899 | 0.061 | 0.760 |
| post_identity_frames | 9 | 89.000 | 49.674 | 34.000 |
| scene_request_failures | 10 | 0.000 | 0.000 | 0.000 |
| safety_event_observations | 10 | 0.000 | 0.000 | 0.000 |
| wall_duration_s | 10 | 198.268 | 9.503 | 217.326 |

Unplanned recovery episodes: 20; recovered: 20; censored: 0; timeout: 0. Recovered-only pooled mean: 1.110 s, sample SD: 0.988 s, worst: 4.327 s. Censor lower bounds: [].

Failure reasons:

- scenario_maneuver_not_verified: 1
- independent_identity_not_verified: 1
- post_identity_evidence_insufficient: 1

## Every Planned Trial

| Trial | State | Task | Identity | Strict | Coverage % | Unplanned Losses | Mean Error px | Post Identity Frames |
|---|---|---|---|---|---:|---:|---:|---:|
| [left_overtaking_01](left_overtaking_01/) | completed | True | True | False | 90.556 | 2 | 14.752 | 181 |
| [lane_change_01](lane_change_01/) | completed | True | True | True | 88.532 | 1 | 15.083 | 121 |
| [left_overtaking_02](left_overtaking_02/) | completed | True | True | True | 92.438 | 0 | 14.606 | 164 |
| [lane_change_02](lane_change_02/) | completed | True | True | True | 91.747 | 1 | 17.766 | 69 |
| [left_overtaking_03](left_overtaking_03/) | completed | True | True | True | 92.296 | 0 | 17.439 | 162 |
| [lane_change_03](lane_change_03/) | completed | True | True | True | 90.034 | 2 | 18.908 | 78 |
| [left_overtaking_04](left_overtaking_04/) | completed | True | True | False | 93.068 | 1 | 15.151 | 295 |
| [lane_change_04](lane_change_04/) | completed | True | True | True | 93.237 | 2 | 10.484 | 179 |
| [left_overtaking_05](left_overtaking_05/) | completed | True | True | True | 93.794 | 0 | 15.983 | 295 |
| [lane_change_05](lane_change_05/) | completed | True | True | True | 88.257 | 4 | 7.417 | 83 |
| [left_overtaking_06](left_overtaking_06/) | completed | True | True | True | 93.045 | 1 | 13.880 | 277 |
| [lane_change_06](lane_change_06/) | completed | True | True | True | 90.242 | 2 | 16.240 | 46 |
| [left_overtaking_07](left_overtaking_07/) | completed | True | True | True | 92.446 | 0 | 17.007 | 154 |
| [lane_change_07](lane_change_07/) | completed | True | True | True | 89.353 | 3 | 17.205 | 45 |
| [left_overtaking_08](left_overtaking_08/) | completed | True | True | True | 93.111 | 0 | 16.171 | 264 |
| [lane_change_08](lane_change_08/) | completed | True | True | True | 87.831 | 5 | 17.179 | 34 |
| [left_overtaking_09](left_overtaking_09/) | completed | True | True | True | 93.055 | 0 | 18.212 | 184 |
| [lane_change_09](lane_change_09/) | completed | True | True | True | 93.739 | 0 | 15.982 | 146 |
| [left_overtaking_10](left_overtaking_10/) | completed | True | True | True | 90.464 | 2 | 13.007 | 105 |
| [lane_change_10](lane_change_10/) | completed | True | False | False | 91.392 | 0 | 16.693 | None |

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
