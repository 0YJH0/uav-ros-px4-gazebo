# Read-only Post-Merge Diagnosis

Source trial: `results/vehicle_tracking_validation/overlap_scale_gui_20261011_01`.
No production file, evaluation threshold, model, or scene was modified.
Candidate/identity rows are joined by exact image stamp. Their `wall_s` epochs differ by approximately 4.484 s; use image stamp for cross-file comparison.

## Findings

The post phase contains 5 independently correct confirmations, 17 unconfirmed frames, and 77 accepted boxes supporting multiple vehicles. Among the 17 unconfirmed frames, 11 have an independently correct ID 9 candidate and all are pending temporal confirmation. Confirmation continuity could potentially recover some of these 11 without any detector changes. The original 5 plus 11 available candidates is an upper bound, not a replay result.

All 77 ambiguous confirmations skipped ROI with `strong_full_frame_evidence`; 76 of these have only one full-frame candidate, and the other has two. The saved `00176.2_TRACK.jpg` visibly has a single accepted rectangle enclosing the rear target and the leading red car. This is genuine detector compositing, not simply an evaluation count problem.

Current `needs_zoom` treats a confident box within 0.04 normalized center distance and a factor of two size as sufficient. A composite can satisfy this. Current cross-source `merge_boxes` then runs confidence NMS with IoU 0.7, which can delete the correct smaller ROI target in favor of a confident full-frame composite.

## Frozen-Model Image Tests

Used existing `yolo11s.pt`, class car 2, confidence 0.1, CPU 8 threads. No training/download. Full-frame inference is 960; ROI inference is 640. Labels below use existing independent v2 projected-box evaluation after inference only.

At image `crossing_0126.600_raw.png` (sim 126.600):

- Full-frame composite: `[449.21, 312.01, 527.19, 400.88]`, confidence 0.811, multiple vehicle support.
- Existing 320 px crop generates the correct original: `[448.85, 333.92, 526.69, 401.68]`, confidence 0.566, unique original support.
- Cross-source NMS suppresses that correct original; the retained candidates are the composite and a small fragment of the leading car.

For the three late archived images at sim 125.600, 126.600, 127.652, correct strong ROI availability before NMS:

| Crop | Correct candidates |
|---|---:|
| Fixed 320 square, 640 inference | 1 / 3 |
| Fixed 400 square, 640 inference | 2 / 3 |
| Fixed 480 square, 640 inference | 2 / 3 |
| Centered 480 square clipped at image bottom, 640 inference | 3 / 3 |

The last variant's effective heights are 412, 425, and 442, not 480. It is a separate crop policy, not proof that increasing the existing fixed ROI to 480 solves the problem. 960 ROI inference and very tight crops are worse on these examples, often generating no vehicle or only tiny fragments. Three selected hard examples do not establish generalization.

## Minimal Safe Next Step

1. Complete temporal-confirmation continuity first and measure how many of the 11 pending correct post candidates it truly recovers.
2. Keep strong composite detections from silently suppressing a budgeted ROI attempt only when recent image-based similar-rival evidence and abnormal geometry support suspicion. Do not run extra inference every frame unconditionally.
3. Preserve a suppressed nested ROI alternative only when distinct candidate geometry provides additional evidence; do not globally raise NMS IoU or select a smaller box solely because it is smaller.
4. One safer composite test is a full-frame enclosing candidate plus two strong, geometrically distinct ROI candidates, both substantially contained by it, each with exclusive support. Reject/mark only the enclosing composite; leave identity selection and three-frame confirmation unchanged. Must test duplicate ROI variants and partial-car fragments before adoption.
5. Do not crop/synthesize the accepted box from predicted geometry: that would manufacture apparent identity evidence instead of adding detector evidence.

## Artifacts

- `/tmp/post_merge_detection_check.py`, `/tmp/post_merge_detection_check.json`: nine archived frames, current crop and cross-source NMS.
- `/tmp/post_merge_crop_check.json`: broad crop-size/input-size diagnostic results.
- `/tmp/post_merge_crop_check.py`, `/tmp/post_merge_fixed_crop_check.json`: subsequent fixed-square comparison.

No closed-loop claims follow from these image checks. Latencies were measured without simulation load and must not be treated as deployment P95.
