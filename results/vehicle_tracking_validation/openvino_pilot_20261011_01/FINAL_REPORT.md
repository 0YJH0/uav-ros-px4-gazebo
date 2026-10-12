# Two-Scenario Frozen Repeat Report

## Protocol

Independent simulator restart for every attempted trial; no failed run is replaced. Frozen YOLO11s/OpenVINO FP32 CPU parameters and 10-second blind-motion limit are unchanged. Both scenarios use red distractors and a curbside parked car.

Coverage is time-weighted onboard target confirmation, not mAP or independently verified identity accuracy. Identity uses exclusive_projection_v2 with unchanged criteria. Unscorable frames are not counted as correct.

Strict pass requires task, independent identity, completed traffic maneuver, autonomous landing/disarming, complete successful native service receipts, ULog safety evidence and frozen source/parameter integrity.

| Scenario | Planned | Attempted | Completed | Task Pass | Identity Pass | Strict Pass | Unlaunched |
|---|---:|---:|---:|---:|---:|---:|---:|
| lane_change | 1 | 1 | 1 | 1/1 | 1/1 | 1/1 | 0 |

## lane_change

| Metric | Available Trials | Mean | Sample SD | Worst |
|---|---:|---:|---:|---:|
| task_passed | 1 | 1.000 | N/A | 1.000 |
| strict_joint_passed | 1 | 1.000 | N/A | 1.000 |
| identity_verified | 1 | 1.000 | N/A | 1.000 |
| coverage_percent | 1 | 91.331 | N/A | 91.331 |
| unplanned_losses | 1 | 2.000 | N/A | 2.000 |
| unplanned_recovery_mean_s | 1 | 0.701 | N/A | 0.701 |
| unplanned_recovery_max_s | 1 | 1.002 | N/A | 1.002 |
| unplanned_recovery_censored_count | 1 | 0.000 | N/A | 0.000 |
| recovery_timeout_count | 1 | 0.000 | N/A | 0.000 |
| planned_recovery_mean_s | 1 | 1.487 | N/A | 1.487 |
| planned_recovery_max_s | 1 | 1.487 | N/A | 1.487 |
| track_mean_abs_pixel_error | 1 | 10.755 | N/A | 10.755 |
| track_p95_abs_pixel_error | 1 | 31.362 | N/A | 31.362 |
| final_home_horizontal_error_m | 1 | 0.705 | N/A | 0.705 |
| drone_follow_travel_m | 1 | 60.254 | N/A | 60.254 |
| full_frame_yolo_mean_s | 1 | 0.132 | N/A | 0.132 |
| full_frame_yolo_p95_s | 1 | 0.170 | N/A | 0.170 |
| processing_mean_s | 1 | 0.150 | N/A | 0.150 |
| processing_p95_s | 1 | 0.242 | N/A | 0.242 |
| target_publish_age_mean_s | 1 | 0.188 | N/A | 0.188 |
| target_publish_age_p95_s | 1 | 0.306 | N/A | 0.306 |
| queue_wait_mean_s | 1 | 0.040 | N/A | 0.040 |
| queue_wait_p95_s | 1 | 0.112 | N/A | 0.112 |
| wrong_identity_observations | 1 | 0.000 | N/A | 0.000 |
| scorable_identity_switches | 1 | 0.000 | N/A | 0.000 |
| identity_scorable_fraction | 1 | 0.918 | N/A | 0.918 |
| post_identity_frames | 1 | 162.000 | N/A | 162.000 |
| scene_request_failures | 1 | 0.000 | N/A | 0.000 |
| safety_event_observations | 1 | 0.000 | N/A | 0.000 |
| wall_duration_s | 1 | 186.448 | N/A | 186.448 |

Unplanned recovery episodes: 2; recovered: 2; censored: 0; timeout: 0. Recovered-only pooled mean: 0.701 s, sample SD: 0.426 s, worst: 1.002 s. Censor lower bounds: [].

Failure reasons:

- None recorded.

## Every Planned Trial

| Trial | State | Task | Identity | Strict | Coverage % | Unplanned Losses | Mean Error px | Post Identity Frames |
|---|---|---|---|---|---:|---:|---:|---:|
| [lane_change_pilot](lane_change_pilot/) | completed | True | True | True | 91.331 | 2 | 10.755 | 162 |

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
