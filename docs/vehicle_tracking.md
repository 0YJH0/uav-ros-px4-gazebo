# YOLO Vehicle Tracking

This is the runnable ROS 2 / PX4 / Gazebo vehicle-following system. The current
validated configuration uses YOLO11s on Torch CPU, ByteTrack, camera-motion
compensation, bounded ROI detection and an independent original-target lock.

The final evidence is the complete ten-run different-color, separate-lane
overtaking batch from 2026-10-11. Earlier smoke, development and failed experiment
artifacts were deleted at the user's request. They are not available for replay;
the final batch contains every attempt, including its lower-coverage runs.

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

## Final Configuration

| Item | Value |
| --- | --- |
| Detector / backend | YOLO11s / Torch CPU |
| ByteTrack, GMC, ROI | Enabled |
| Truncated vertical geometry protection | Enabled |
| Box-scale velocity prediction | Enabled |
| Recovery competition | Disabled |
| Experimental recovery setpoint smoothing | Disabled |
| Target speed | 0.8 m/s |
| Occlusion | Starts at 15 simulation seconds; lasts 4 simulation seconds |
| Scene | Red target, blue distractor, separate-lane overtaking |
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
  --overtaking --vehicle-speed 0.8 \
  --occlusion-start 15 --occlusion-duration 4 \
  --model-path yolo11s.pt --detector-backend torch
```

The default-disabled competition and smoothing options are intentionally not
enabled. Do not use ground-truth positions for the flight controller.

## Repeat a Fixed Configuration

A retained final trial supplies implementation and runtime-parameter evidence,
so rerunning does not require the deleted selection pilot. Use a new batch path:

```bash
.venv-yolo/bin/python scripts/repeat_best_vehicle.py \
  --reference results/vehicle_tracking_validation/scene_transport_isolated_repeat_20261011_01/overtaking_01 \
  --output results/vehicle_tracking_validation/new_fixed_repeat \
  --count 10
```

The tool checks source/model agreement with its reference, freezes inputs and
independently restarts processes. A mismatch must be resolved explicitly, not
bypassed. A new repetition is a new batch; never mix it into the retained
ten-run denominator. PX4 calibration/counters can persist and must be audited.

## Inspect Retained Evidence

Each `overtaking_01/` through `overtaking_10/` contains task and identity
reports, supervisor status, runtime parameters, samples, candidate association
logs, scene/traffic request logs, paired raw images, annotated JPEGs and a
`flight.ulg` copy.

The audit directory contains the final report, metrics, plot, completion check,
service-request audit, latency/safety audit and nonplanned-loss analysis.
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

All ten attempts passed task, independent identity and strict joint acceptance.
Mean confirmed coverage was 90.69%, sample standard deviation 2.39 percentage
points, worst 86.05%. All 8149 scene requests succeeded. There were seven
nonplanned losses, including a 6.70-second recovery; every final attempt and
loss record is retained.

Coverage is time-weighted original-target confirmation during the follow
window, not YOLO mAP or pixel-level visibility. Processing latency is not the
entire exposure-to-actuation delay. Different-color overtaking does not prove
same-appearance crossing ReID, hard realtime, hardware safety or generalization.

See [project overview](../PROJECT_OVERVIEW.md),
[engineering challenges](../PROJECT_CHALLENGES.md),
[retained-result index](../results/vehicle_tracking_validation/README.md) and
[final report](../results/vehicle_tracking_validation/scene_transport_isolated_repeat_audit_20261011_01/FINAL_REPORT.md).
