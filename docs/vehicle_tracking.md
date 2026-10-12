# YOLO Vehicle Tracking

This is the runnable ROS 2 / PX4 / Gazebo vehicle-following system. The current
validated configuration uses YOLO11s on Torch CPU, ByteTrack, camera-motion
compensation, bounded ROI detection and an independent original-target lock.

The current evidence is two same-appearance red-car scenarios, each independently
restarted ten times with identical frozen perception/control settings. The
different-color ten-run GUI batch remains a separate historical baseline.
Some early development artifacts were deleted at the user's request; newer
trials, including every failed attempt in this batch, are retained.

## Environment

- ROS 2 Jazzy and the built workspace at `ros2_ws/install/`.
- PX4 SITL and Gazebo Harmonic with the X500 camera resources.
- Micro XRCE-DDS Agent, `px4_msgs`, `ros_gz_image` and `ros_gz_bridge`.
- `.venv-yolo`, local `yolo11s.pt`, and the dependencies recorded in the batch.
- A graphical desktop/WSLg session for the GUI validation command.

Keep the source, unit tests, model weights, dependency environments and required
build/install artifacts. Cleaning experiment outputs does not remove runtime
dependencies.

## Architecture

Gazebo RGB images enter `/camera/image_raw`. The perception node performs YOLO
detection, optional ROI merging, ByteTrack updates and original-target
association. YOLO and ByteTrack exchange boxes, classes and confidence scores
in memory inside that node. Camera-motion compensation is applied to both
tracker and target prediction. The latest-frame buffer can skip queued images;
not every input camera frame is processed.

`/perception/vehicles` exposes candidate vehicles. `/perception/target` reports
a confirmed original target. ByteTrack IDs are temporary association labels,
not proof of semantic identity. The target lock combines appearance, geometry,
motion, confidence and temporal confirmation; it may restore the original
vehicle under a new tracker ID. Candidate rejection reasons are recorded.

The controller sends bounded Offboard setpoints through PX4 DDS interfaces.
Vehicle ground truth is used only by the independent evaluator, never as
perception or flight-control input.

## Current Configuration

| Item | Value |
| --- | --- |
| Detector / backend | YOLO11s / Torch CPU |
| ByteTrack, GMC, ROI | Enabled |
| Truncated vertical geometry protection | Enabled |
| Box-scale velocity prediction | Enabled |
| Per-candidate overlap recovery / bounded scale / confirmation continuity | Enabled |
| Recovery competition | Disabled |
| Experimental recovery setpoint smoothing | Disabled |
| Target speed | 0.8 m/s |
| Occlusion | Starts at 15 simulation seconds; lasts 4 simulation seconds |
| Scene | Red target and distractor; fixed left-lane or lane-change overtaking |
| Parked car lateral position | -4.4 m |
| Loss debounce | 0.5 seconds |
| Blind-motion time / distance | 10 wall seconds / 4 m |
| Recovery prediction speed limit | 0.8 m/s |

The blind-motion limit does not permanently disable visual reassociation.
Predictions cannot refresh the last genuine target observation or count as
confirmed tracking. Truncated boxes do not directly update full-body vertical
center/height or their velocities.

## Run One Fresh GUI Validation

Use a new output directory; never overwrite final evidence. This command starts
a new flight and requires the local ROS/PX4/Gazebo environment:

```bash
.venv-yolo/bin/python scripts/run_vehicle_tracking_validation.py \
  --output results/vehicle_tracking_validation/new_gui_validation \
  --gui --gui-config scripts/vehicle_tracking_gui.config \
  --overtaking --distractor-color red --parked-y -4.4 --vehicle-speed 0.8 \
  --occlusion-start 15 --occlusion-duration 4 \
  --model-path yolo11s.pt --detector-backend torch
```

The default-disabled competition and smoothing options are intentionally not
enabled. Do not use ground-truth positions for the flight controller.

The explicit `--distractor-color red` changes both moving and parked distractors
to the existing red target model. Omitting it preserves the historical `auto`
default: blue overtaking distractors and red crossing distractors. Color is
recorded in the snapshot, scene parameters and independent identity report.
Keep these trials separate from the archived different-color baseline.

Add `--parked-y -4.4` to place the parked car beside the right curb on the
12 m-wide overtaking road. Its body remains inside the road, about 0.53 m from
the curb and more than 0.20 m clear of the roadside barriers. The historical
default is `-12.0`; position is recorded in the snapshot and scene parameters.
Changing both color and parking position is a two-factor scene variation, not
a color-only comparison.

## Same-Lane Approach, Left Pass and Merge Back

Use the new traffic mode without changing perception or control thresholds:

```bash
.venv-yolo/bin/python scripts/run_vehicle_tracking_validation.py \
  --output results/vehicle_tracking_validation/new_lane_change_gui \
  --gui --gui-config scripts/vehicle_tracking_gui.config \
  --lane-change-overtaking --distractor-color red --parked-y -4.4 \
  --vehicle-speed 0.8 --occlusion-start 15 --occlusion-duration 4 \
  --model-path yolo11s.pt --detector-backend torch
```

The red distractor starts 28 m behind the target in the center lane, behind the
drone's initial position. After target motion starts, it approaches to 10 m
behind over 0-25 simulation seconds, changes to the left lane (`y=3.8 m`) over
25-35 s, passes to 10 m ahead over 35-47 s, and returns to the center lane over
47-57 s. It then maintains that longitudinal offset. Quintic transitions keep
position, velocity and yaw continuous. The target keeps its original route;
the 10 wall-second blind-motion limit remains unchanged.

Trajectory and geometry verification live in `scripts/vehicle_lane_change.py`.
The evaluator checks Gazebo poses matched to association images for all five
stages and a minimum horizontal body separation of 0.5 m; this is not a full
pose-stream collision audit. Lateral separation alone is not a valid
criterion after the car merges into the same lane. Original-target identity
still uses independent projection matching; ambiguous overlapping images are
unscorable, not assumed correct. Task success, complete maneuver execution and
verified identity are separate results. This mode is not wired into the old
fixed-baseline batch runner.

## Versioned Identity Evaluation

`exclusive_projection_v2` replaces the blanket rejection of frames whose
ground-truth vehicle projections overlap by more than IoU 0.1. The overlap
event is still recorded independently of the identity label. No flight-control,
detector, association, coverage or blind-motion threshold changes are involved.

The evaluator still requires accepted-box IoU >= 0.4 and a lead of >= 0.2 over
the next vehicle. It additionally requires more than half of the winning
vehicle's projected box to be exclusive of all other vehicles, and more than
half of that exclusive region to be covered by the accepted box. A box covering
at least half of another vehicle's exclusive region remains ambiguous. Fully
contained competitors without distinguishable support are also unscorable.
Areas subtract the union of competing boxes, without counting intersections
twice. An absent accepted box is `unconfirmed`, even during projection overlap.
The majority-support requirement also rejects a small single-vehicle accepted
box covering only 40-50% of its projected vehicle, even if it met the old IoU
minimum. This is an explicit additional evidence requirement, not a claim that
all previously scorable frames remain scorable.

These are independent geometric projection checks, not pixel-level instance
masks. An unchanged tracker ID or similar car color is not identity evidence.
Confirmed identity still needs at least ten pre- and post-maneuver observations,
valid scenario evidence, matched truth, no scored wrong car and no scenario
request error. Merged and otherwise ambiguous boxes never count as correct.

Reassess archived accepted boxes without rerunning detection or flight:

```bash
.venv-yolo/bin/python scripts/reassess_vehicle_identity.py \
  results/vehicle_tracking_validation/red_lane_change_gui_20261011_01 \
  --output results/vehicle_tracking_validation/red_lane_change_identity_v2_review
```

The output must be a new directory outside the input trial. Original reports,
images, safety/service evidence and source snapshots are not overwritten. The
new report records the evaluator version and input/source hashes. A changed
identity verdict cannot override failed task coverage, incomplete service logs
or safety evidence. This is a scoring-method revision, not a new flight or an
improvement in tracking performance; historical results retain their original
evaluation version.

## Overlap Recovery and Bounded Scale Prediction

Two perception parameters default to `true`: `overlap_candidate_recovery` and
`bounded_scale_prediction`. They can be disabled independently for ablation.
They change online association, not the independent identity evaluator.

Overlap recovery evaluates each detection instead of rejecting the entire
candidate batch. A partially overlapping box needs more than half its area
outside the union of its competing detections, the existing strong appearance
and geometry checks, and three consistent frames. Missing observations, ID
changes and confirmation gaps over 0.5 s reset that evidence. Continuous
confirmed overlap does not restart a three-frame wait after every acceptance.
Merged boxes and indistinguishable competitors remain rejected; detection-box
geometry is evidence for association, not proof of original-vehicle identity.

The scale model retains its previous constant-velocity behavior through 0.5 s
without confirmation. Longer gaps exponentially damp log-width/log-height
velocity and bound predicted dimensions to `[0.8, 1.25]` times the last confirmed
camera-compensated dimensions. Center prediction is unchanged. Normal complete
observations can still correct either an oversized or undersized anchor; the
existing truncated-box protection is retained. Recently overlapping rivals also
prevent accepting a vertically merged box as a full-body height observation.
Predictions and rejected detections never refresh the confirmation timestamp.
The 10-second blind-motion limit is unchanged and does not expire visual
reassociation.

Candidate diagnostics include `candidate_exclusive_fraction`,
`predicted_size_px`, `scale_prediction_clamped` and `overlap_continuation`.
The frozen five-arm offline comparison is in
[the offline report](../results/vehicle_tracking_validation/overlap_scale_offline_20261011_02/RESULTS.md).
Its confirmation-time proxy is not a closed-loop coverage measurement: changed
control would change later camera images. Ambiguous multi-vehicle confirmations
are reported separately, never counted as independently verified targets.

The independently restarted [closed-loop trial](../results/vehicle_tracking_validation/overlap_scale_gui_20261011_01/RESULTS.md)
measured 86.24% confirmed coverage, but did not pass independent post-merge
identity acceptance. Seven nonplanned recoveries remained, with a 2.60 s worst
duration. This is one trial, not a replacement for the retained final batch.
The legacy `analyze_vehicle_recovery_prediction.py` CV reconstruction rejects
the bounded model and unsupported masked corrections; use the frozen replay
or recorded prediction diagnostics for this version.

### Confirmation Continuity

`overlap_confirmation_continuity=true` preserves a candidate's confirmation
count across `partial_overlap` and `overlap_recovery` labels. Crossing between
these labels requires the same assigned ID, an observation interval in
`[0, 0.5]` s, normalized center change below 0.05 and log-size change below 0.2.
These are the existing confirmation constraints, not widened association
thresholds. Three real qualifying observations are still required to mature
the chain. Subsequent strong, same-ID, gate-passing observations keep mature
evidence current even when the rival is briefly absent.

Missing or rejected candidates, unresolved competition, changed IDs, unknown-ID
bridges and temporal or geometric discontinuities cannot carry mature evidence
into a new overlap. Neither stored counts nor predictions refresh the blind
motion timestamp. The parameter is passed through airborne identity reset and
the launch file. The supervisor accepts `--no-overlap-confirmation-continuity`
for a fresh, separately saved ablation; omitting it enables the fix.

The [frozen continuity comparison](../results/vehicle_tracking_validation/continuity_offline_20261011_01/RESULTS.md)
replays two historical trials. Disabling this flag exactly preserves the
previous association decisions; enabling it does not claim to separate merged
YOLO detections. Those remain independently unscorable, even when the task
continues to output a confirmed target.

One independently restarted [continuity closed-loop trial](../results/vehicle_tracking_validation/continuity_gui_20261011_01/RESULTS.md)
passed strict joint acceptance at 91.75% coverage, with one nonplanned loss
lasting 0.299 s and 53 independently scorable post-merge target observations.
The mean lateral pixel error increased to 19.29 px from the preceding trial's
12.93 px. This is a single-run result, not proof of uniform improvement or
repeatability. The detector and NMS are unchanged; separate
[historical merged-box diagnostics](../results/vehicle_tracking_validation/post_merge_detector_offline_20261011_01/RESULTS.md)
remain relevant even though this flight produced no ambiguous confirmations.

## Repeat Both Current Scenarios

The retained continuity pilot supplies source/model and runtime-parameter
evidence. Use a new output path; prepare freezes twenty alternating attempts:

```bash
.venv-yolo/bin/python scripts/repeat_two_vehicle_scenarios.py \
  --reference results/vehicle_tracking_validation/continuity_gui_20261011_01 \
  --output results/vehicle_tracking_validation/new_two_scenario_repeat \
  --count 10 --prepare-only

.venv-yolo/bin/python scripts/repeat_two_vehicle_scenarios.py \
  --reference results/vehicle_tracking_validation/continuity_gui_20261011_01 \
  --output results/vehicle_tracking_validation/new_two_scenario_repeat \
  --count 10 --resume
```

The tool checks source/model agreement, installed code/assets and per-trial
runtime parameters. It restarts processes independently, retains scoring
failures, and stops if landing, safety or source integrity is not confirmed.
Resume executes only previously unattempted entries; interrupted or failed
attempts are never replayed. Both groups are headless by default; GUI pilots
are not an isolated runtime-load comparison. PX4 calibration/counters persist
and are audited separately. Do not bypass a reference mismatch to reproduce
the old algorithm with the current implementation.

## Inspect Retained Evidence

Each current `left_overtaking_01/` through `_10/` and `lane_change_01/` through
`_10/` contains task and identity
reports, supervisor status, runtime parameters, samples, candidate association
logs, scene/traffic request logs, paired raw images, annotated JPEGs and a
`flight.ulg` copy.

The current batch directory contains `FINAL_REPORT.md`, `SUMMARY.json`,
`trials.csv`, `summary.png`, per-trial `batch_audit.json`, and supplemental
`FAILURE_ANALYSIS.md`. Frozen scripts define acceptance; supplemental diagnosis
does not revise verdicts. The historical audit directory remains separate.
The archived protocol and snapshots intentionally retain original historical
source paths for provenance; those paths are not promises that the deleted
pilot still exists. Its selected configuration evidence is copied inside the
final batch under `reference_evidence/` and `reference_executed_sources/`.

For a read-only scene-service recomputation after all flights have stopped:

```bash
.venv-yolo/bin/python scripts/summarize_vehicle_service_batch.py \
  --study results/vehicle_tracking_validation/scene_transport_isolated_repeat_20261011_01 \
  --output /tmp/vehicle_service_recheck
```

Use a new external output path. The tool refuses to overwrite existing evidence.

## Results and Limits

Current fixed-left overtaking: task 10/10, identity 10/10, strict 8/10;
confirmed coverage 92.43% +/- 1.10 percentage points (sample SD), worst 90.46%.
Lane-change/merge-back: task 10/10, identity 9/10, strict 9/10;
coverage 90.44% +/- 2.05 percentage points, worst 87.83%.
All twenty attempts remain in their respective denominators.

Strict failures are the first road-creation request timing out in
`left_overtaking_01`, four missing startup receipts in `left_overtaking_04`,
and missing completed-maneuver/post-merge identity evidence in `lane_change_10`.
In that last trial the traffic completed merging after RETURN, when identity
collection had already stopped; the active tracking window did not cover the
full maneuver. This is not evidence that a visible, fully merged target was
rejected after the merge.
A later retry does not erase a failed request; a missing receipt is not a
known failed request. Six and twenty nonplanned losses remain in the two groups,
with longest recoveries of 0.60 s and 4.33 s. All recorded ULog safety counts
and scorable wrong-identity counts are zero; unscorable frames remain unknown.

The historical different-color GUI batch is unchanged: strict 10/10,
coverage 90.69% +/- 2.39 percentage points, worst 86.05%, seven nonplanned losses,
and 8149 confirmed successful requests. It used an older configuration and
different scene/runtime load, so it is not a single-variable algorithm ablation.

Coverage is time-weighted original-target confirmation during the follow
window, not YOLO mAP or pixel-level visibility. Processing latency is not the
entire exposure-to-actuation delay. Different-color overtaking does not prove
same-appearance crossing ReID, hard realtime, hardware safety or generalization.

See [project overview](../PROJECT_OVERVIEW.md),
[engineering challenges](../PROJECT_CHALLENGES.md),
[retained-result index](../results/vehicle_tracking_validation/README.md) and
[current final report](../results/vehicle_tracking_validation/two_scenario_frozen_repeat_20261011_01/FINAL_REPORT.md).
## OpenVINO 补充闭环验证

已完成的二十次、单次准入与失败分析见 [OpenVINO 补充报告](../results/vehicle_tracking_validation/openvino_two_scenario_repeat_20261011_01/RESULTS.md)。该批与 Torch 二十次分别统计，不替换默认后端。

OpenVINO 使用相同 `yolo11s.pt` 导出的 CPU FP32 模型，不进行量化，也不改变 ByteTrack、目标锁、控制器和 10 秒盲跟限制。感知节点使用带 OpenVINO 的 `.venv-yolo-backends/bin/python`，监督器及其他 ROS 节点仍使用原环境。该解释器需要原感知依赖和 ROS 环境；版本与二进制哈希由实验协议记录。

严格按“离线一致性 → 单次严格通过 → 两场景各十次”执行。下面每个输出路径必须是新目录；导出模型和冻结文件在验证期间不得修改。

```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export PYTHONPATH="$PWD/ros2_ws/src/uav_learning:$PYTHONPATH"

.venv-yolo-backends/bin/python scripts/export_vehicle_openvino.py \
  --model-path yolo11s.pt --output runtime_artifacts/new_openvino_fp32

.venv-yolo-backends/bin/python scripts/check_vehicle_backend_equivalence.py \
  --trial results/vehicle_tracking_validation/continuity_gui_20261011_01 \
  --model-path yolo11s.pt --backend-artifacts runtime_artifacts/new_openvino_fp32 \
  --output results/vehicle_tracking_validation/new_openvino_equivalence

.venv-yolo/bin/python scripts/run_openvino_vehicle_pilot.py \
  --reference results/vehicle_tracking_validation/continuity_gui_20261011_01 \
  --output results/vehicle_tracking_validation/new_openvino_pilot \
  --backend-artifacts runtime_artifacts/new_openvino_fp32 \
  --perception-python .venv-yolo-backends/bin/python \
  --equivalence-report results/vehicle_tracking_validation/new_openvino_equivalence/report.json
```

单次 `PILOT_GATE.json` 的 `passed` 必须为 `true`，随后才能运行：

```bash
.venv-yolo/bin/python scripts/repeat_two_vehicle_scenarios.py \
  --reference results/vehicle_tracking_validation/new_openvino_pilot/lane_change_pilot \
  --output results/vehicle_tracking_validation/new_openvino_repeat \
  --count 10 --detector-backend openvino \
  --backend-artifacts runtime_artifacts/new_openvino_fp32 \
  --perception-python .venv-yolo-backends/bin/python
```

批量工具会再次审核单次的严格结论、模型产物、源码、安装文件与解释器版本。两场景交替独立重启，不替换失败；安全异常或来源漂移会中止后续运行。工具执行完成不代表所有试次严格通过，须读取 `SUMMARY.json`、`trials.csv` 与 `FINAL_REPORT.md`。单次不计入批量分母，Torch 和 OpenVINO 两批分别统计。
