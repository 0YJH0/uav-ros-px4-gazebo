# OpenVINO 两场景各十次闭环补充验证

## 实验门槛与边界

先完成 FP32 离线数值一致性检查，再完成一次独立后方变道回中闭环。单次严格联合验收和安全门槛均通过后，才启动本批 20 次；单次不计入批量分母。

- 离线检查：54 张原图、108 组全图/裁剪对照，175 个匹配框，未匹配框为 0；最大框坐标差 0.0001221 px，最大置信度差 0.000007391。
- 单次：确认覆盖率 91.33%，回中后 162 帧独立原车证据，981 条场景请求全部成功，严格通过并安全落地。
- 使用相同 YOLO11s 原始权重，OpenVINO CPU FP32，无量化；全图 544×960、ROI 640×640，实际 8 推理线程。ByteTrack、目标锁、控制器、场景参数和验收阈值不变。
- 两种同外观红车场景交替、无 GUI、独立重启各十次；车速 0.8 m/s，计划遮挡 4 仿真秒，保留 10 墙钟秒盲跟限制。未替换失败试次。
- 导出模型、解释器、软件版本、源代码、安装文件和评测脚本已冻结；本报告只读取结果，不调整验收规则。

运行环境：Python 3.12.3，OpenVINO 2026.4.1，Ultralytics 8.4.174。批次从 2026-10-11 跨午夜运行至 2026-10-12，目录日期表示启动日。

## 本批结果

| 指标 | 左侧超车 | 后方变道超车再回中 |
| --- | ---: | ---: |
| 任务通过 | 10/10 | 9/10 |
| 独立身份通过 | 10/10 | 10/10 |
| 严格联合通过 | 7/10 | 3/10 |
| 确认覆盖率 (%) | 94.191 ± 0.250；最差 93.697；n=10 | 92.622 ± 1.994；最差 88.646；n=10 |
| 全图检测耗时 (ms) | 112.514 ± 3.389；最差 121.824；n=10 | 111.919 ± 1.082；最差 113.645；n=10 |
| 完整感知处理耗时 (ms) | 128.011 ± 3.798；最差 138.336；n=10 | 127.261 ± 1.411；最差 129.473；n=10 |
| 发布帧龄 (ms) | 159.113 ± 4.902；最差 171.599；n=10 | 157.456 ± 2.849；最差 163.787；n=10 |
| 逐试次发布帧龄 P95 (ms) | 249.818 ± 13.963；最差 285.745；n=10 | 249.289 ± 10.193；最差 264.097；n=10 |
| 横向像素误差 (px) | 13.172 ± 3.058；最差 17.127；n=10 | 14.283 ± 1.165；最差 15.950；n=10 |
| 非计划丢失次数 | 0.200 ± 0.422；最差 1.000；n=10 | 1.300 ± 2.003；最差 5.000；n=10 |
| 非计划最长恢复 (s) | 0.200 ± 0.000；最差 0.200；n=2 | 0.740 ± 0.942；最差 2.400；n=5 |
| 计划遮挡最长恢复 (s) | 1.139 ± 0.242；最差 1.612；n=10 | 1.100 ± 0.144；最差 1.320；n=10 |

数值为跨试次均值 ± 样本标准差；最差覆盖率取最小值，其余取最大值。没有非计划丢失的试次恢复耗时为 N/A，不以 0 秒填充。覆盖率不是检测 mAP，也不是独立身份准确率。

计划遮挡恢复耗时描述所有记录到的遮挡事件，包括入口前提不满足的事件；耗时可测不等于该事件验收通过。各试次完整统计及恢复删失计数以严格报告为准。

已核对 24393 条关联记录，全部实际使用 OpenVINO、8 推理线程，没有 Torch 回退记录。

共记录 20714 条原生场景请求，确认失败 7 条，缺失回执 8 条。两者分开统计。

可评分错车观测 0，可评分身份切换 0，记录到的安全事件观测 0，监督干预 0。未观察到不等于所有帧身份可评分或实机安全保证。

## 逐次结果及失败原因

| 试次 | 任务 / 身份 / 严格 | 覆盖率 (%) | 非计划丢失 | 原始失败原因 |
| --- | --- | ---: | ---: | --- |
| [left_overtaking_01](left_overtaking_01/batch_audit.json) | 通过 / 通过 / 未通过 | 94.003 | 0 | service_receipt_sequence_incomplete:scene |
| [lane_change_01](lane_change_01/batch_audit.json) | 通过 / 通过 / 未通过 | 93.630 | 0 | scene_service_requests_failed |
| [left_overtaking_02](left_overtaking_02/batch_audit.json) | 通过 / 通过 / 未通过 | 93.921 | 0 | scene_service_requests_failed |
| [lane_change_02](lane_change_02/batch_audit.json) | 通过 / 通过 / 通过 | 89.297 | 5 | 无 |
| [left_overtaking_03](left_overtaking_03/batch_audit.json) | 通过 / 通过 / 通过 | 94.348 | 0 | 无 |
| [lane_change_03](lane_change_03/batch_audit.json) | 通过 / 通过 / 未通过 | 93.323 | 1 | scene_service_requests_failed |
| [left_overtaking_04](left_overtaking_04/batch_audit.json) | 通过 / 通过 / 通过 | 94.254 | 0 | 无 |
| [lane_change_04](lane_change_04/batch_audit.json) | 通过 / 通过 / 未通过 | 94.192 | 0 | scene_service_requests_failed |
| [left_overtaking_05](left_overtaking_05/batch_audit.json) | 通过 / 通过 / 未通过 | 93.697 | 0 | service_receipt_sequence_incomplete:scene |
| [lane_change_05](lane_change_05/batch_audit.json) | 通过 / 通过 / 未通过 | 88.646 | 5 | scene_service_requests_failed |
| [left_overtaking_06](left_overtaking_06/batch_audit.json) | 通过 / 通过 / 通过 | 94.229 | 0 | 无 |
| [lane_change_06](lane_change_06/batch_audit.json) | 通过 / 通过 / 通过 | 93.956 | 0 | 无 |
| [left_overtaking_07](left_overtaking_07/batch_audit.json) | 通过 / 通过 / 通过 | 94.480 | 0 | 无 |
| [lane_change_07](lane_change_07/batch_audit.json) | 通过 / 通过 / 未通过 | 93.089 | 1 | scene_service_requests_failed |
| [left_overtaking_08](left_overtaking_08/batch_audit.json) | 通过 / 通过 / 通过 | 94.153 | 0 | 无 |
| [lane_change_08](lane_change_08/batch_audit.json) | 通过 / 通过 / 通过 | 93.593 | 0 | 无 |
| [left_overtaking_09](left_overtaking_09/batch_audit.json) | 通过 / 通过 / 通过 | 94.407 | 1 | 无 |
| [lane_change_09](lane_change_09/batch_audit.json) | 未通过 / 通过 / 未通过 | 92.467 | 0 | supervisor_exit_not_zero:1; task_passed_not_confirmed; planned_occlusion_criteria_not_met; supervisor_autonomous_passed_not_confirmed |
| [left_overtaking_10](left_overtaking_10/batch_audit.json) | 通过 / 通过 / 通过 | 94.413 | 1 | 无 |
| [lane_change_10](lane_change_10/batch_audit.json) | 通过 / 通过 / 未通过 | 94.026 | 1 | scene_service_requests_failed |

### 未通过试次的原生请求与身份证据

- `left_overtaking_01`：超车后（变道场景为回中后）原车证据 329 帧；阶段计数 `{"pre": {"unconfirmed": 6, "tracked_vehicle": 297, "panel_occlusion_unscorable": 23}, "during": {"tracked_vehicle": 67}, "post": {"tracked_vehicle": 329}}`。
  缺失回执序号 `{"scene": [1, 2, 3, 4]}`；这里只能确认日志缺失，不能推断这些请求是否成功。
- `lane_change_01`：超车后（变道场景为回中后）原车证据 222 帧；阶段计数 `{"pre": {"unconfirmed": 8, "tracked_vehicle": 213, "panel_occlusion_unscorable": 23}, "during": {"tracked_vehicle": 243, "unconfirmed": 2}, "post": {"tracked_vehicle": 222}}`。
  `scene` 序号 1，`/world/default/create`，模型 `(未记录)`；预算 500 ms，实际 501.324 ms，binding=False，response=False，原因 `request_not_confirmed`。
- `left_overtaking_02`：超车后（变道场景为回中后）原车证据 335 帧；阶段计数 `{"pre": {"unconfirmed": 9, "tracked_vehicle": 282, "panel_occlusion_unscorable": 22}, "during": {"tracked_vehicle": 64}, "post": {"tracked_vehicle": 335}}`。
  `scene` 序号 1，`/world/default/create`，模型 `(未记录)`；预算 500 ms，实际 501.674 ms，binding=False，response=False，原因 `request_not_confirmed`。
- `lane_change_03`：超车后（变道场景为回中后）原车证据 234 帧；阶段计数 `{"pre": {"tracked_vehicle": 251, "unconfirmed": 6, "panel_occlusion_unscorable": 23}, "during": {"tracked_vehicle": 291, "unconfirmed": 6}, "post": {"tracked_vehicle": 234}}`。
  `scene` 序号 1，`/world/default/create`，模型 `(未记录)`；预算 500 ms，实际 502.049 ms，binding=False，response=False，原因 `request_not_confirmed`。
- `lane_change_04`：超车后（变道场景为回中后）原车证据 238 帧；阶段计数 `{"pre": {"unconfirmed": 6, "tracked_vehicle": 223, "panel_occlusion_unscorable": 24}, "during": {"tracked_vehicle": 249, "unconfirmed": 2}, "post": {"tracked_vehicle": 238}}`。
  `scene` 序号 1，`/world/default/create`，模型 `(未记录)`；预算 500 ms，实际 501.535 ms，binding=False，response=False，原因 `request_not_confirmed`。
- `left_overtaking_05`：超车后（变道场景为回中后）原车证据 356 帧；阶段计数 `{"pre": {"unconfirmed": 9, "tracked_vehicle": 288, "panel_occlusion_unscorable": 22}, "during": {"tracked_vehicle": 61}, "post": {"tracked_vehicle": 356}}`。
  缺失回执序号 `{"scene": [1, 2, 3, 4]}`；这里只能确认日志缺失，不能推断这些请求是否成功。
- `lane_change_05`：超车后（变道场景为回中后）原车证据 200 帧；阶段计数 `{"pre": {"unconfirmed": 7, "tracked_vehicle": 230, "panel_occlusion_unscorable": 22}, "during": {"tracked_vehicle": 257, "unconfirmed": 3}, "post": {"tracked_vehicle": 200, "unconfirmed": 40, "overlap_unscorable": 44}}`。
  `scene` 序号 1，`/world/default/create`，模型 `(未记录)`；预算 500 ms，实际 501.191 ms，binding=False，response=False，原因 `request_not_confirmed`。
- `lane_change_07`：超车后（变道场景为回中后）原车证据 243 帧；阶段计数 `{"pre": {"unconfirmed": 9, "tracked_vehicle": 214, "panel_occlusion_unscorable": 21}, "during": {"tracked_vehicle": 270, "unconfirmed": 3}, "post": {"tracked_vehicle": 243, "unconfirmed": 7}}`。
  `scene` 序号 1，`/world/default/create`，模型 `(未记录)`；预算 500 ms，实际 601.630 ms，binding=False，response=False，原因 `request_not_confirmed`。
- `lane_change_09`：超车后（变道场景为回中后）原车证据 231 帧；阶段计数 `{"pre": {"unconfirmed": 11, "tracked_vehicle": 234, "panel_occlusion_unscorable": 23}, "during": {"tracked_vehicle": 263, "unconfirmed": 2}, "post": {"tracked_vehicle": 231, "unconfirmed": 9}}`。
  计划遮挡在记录器 78.083 s 开始，但入口 `entry_locked=false`，未满足当时目标可见且连续三帧确认的前提；结束后确认恢复 0.995 s。恢复快不能补足入口前提，保留任务失败结论。
  入口附近关联时间线：77.357s confirmed; 77.471s confirmed; 77.598s confirmed; 77.718s all_candidates_rejected; 77.910s pending_confirmation; 78.015s pending_confirmation; 78.137s confirmed; 78.260s confirmed；每个候选的拒绝原因见 `OPENVINO_COMPARISON.json`。
- `lane_change_10`：超车后（变道场景为回中后）原车证据 239 帧；阶段计数 `{"pre": {"unconfirmed": 7, "tracked_vehicle": 222, "panel_occlusion_unscorable": 24}, "during": {"tracked_vehicle": 263, "unconfirmed": 2}, "post": {"tracked_vehicle": 239, "unconfirmed": 3}}`。
  `scene` 序号 1，`/world/default/create`，模型 `(未记录)`；预算 500 ms，实际 501.448 ms，binding=False，response=False，原因 `request_not_confirmed`。

场景回执缺失意味着证据链不完整，不等同于请求执行失败；请求执行超时须以原生客户端日志为准。身份未验证须检查跟踪窗口是否覆盖完整回中阶段，不以 RETURN 后车流完成替代。所有这些情形均保持原始严格结论。

## 与此前 Torch 二十次的观察性对照

两个批次不是同时间交叉随机化后端消融。相同核心源码、权重和场景协议不排除主机负载、仿真速率、PX4 持久校准状态和检测时序差异；下表只能描述本机本协议的结果，不能归因所有变化于 OpenVINO。

| 场景 / 指标 | Torch | OpenVINO | 差值 OpenVINO−Torch |
| --- | ---: | ---: | ---: |
| left_overtaking / 确认覆盖率 (%) | 92.427 | 94.191 | 1.763 |
| left_overtaking / 全图检测耗时 (ms) | 162.658 | 112.514 | -50.144 |
| left_overtaking / 完整感知处理耗时 (ms) | 180.128 | 128.011 | -52.117 |
| left_overtaking / 发布帧龄 (ms) | 228.020 | 159.113 | -68.908 |
| left_overtaking / 逐试次发布帧龄 P95 (ms) | 340.445 | 249.818 | -90.626 |
| left_overtaking / 横向像素误差 (px) | 15.621 | 13.172 | -2.449 |
| left_overtaking / 非计划丢失次数 | 0.600 | 0.200 | -0.400 |
| left_overtaking / 非计划最长恢复 (s) | 0.506 | 0.200 | -0.306 |
| left_overtaking / 计划遮挡最长恢复 (s) | 1.614 | 1.139 | -0.474 |
| left_overtaking / 严格通过 | 8/10 | 7/10 | 不作为耗时差值 |
| lane_change / 确认覆盖率 (%) | 90.436 | 92.622 | 2.186 |
| lane_change / 全图检测耗时 (ms) | 164.779 | 111.919 | -52.860 |
| lane_change / 完整感知处理耗时 (ms) | 183.712 | 127.261 | -56.451 |
| lane_change / 发布帧龄 (ms) | 233.290 | 157.456 | -75.834 |
| lane_change / 逐试次发布帧龄 P95 (ms) | 360.119 | 249.289 | -110.830 |
| lane_change / 横向像素误差 (px) | 15.296 | 14.283 | -1.012 |
| lane_change / 非计划丢失次数 | 2.000 | 1.300 | -0.700 |
| lane_change / 非计划最长恢复 (s) | 1.723 | 0.740 | -0.983 |
| lane_change / 计划遮挡最长恢复 (s) | 1.470 | 1.100 | -0.370 |
| lane_change / 严格通过 | 9/10 | 3/10 | 不作为耗时差值 |

## 证据与复现

PX4 持久状态未逐次强制清空：二十份日志中，8 次与首轮校准不同、19 次有计数参数差异，其他参数差异 0 次。此边界不能从比较中忽略。

独立检查通过 778 项，重新计算试次数、汇总统计、身份阶段、请求序列、原始日志哈希及 ULog 安全计数。检查不覆盖或改写失败结论。

- [严格审计报告](FINAL_REPORT.md)、[逐次数据](trials.csv)、[机器汇总](SUMMARY.json)、[独立核查](INDEPENDENT_CHECK.json)。
- [冻结协议](batch_protocol.json)、[试次计划](plan.json)、[冻结清单](freeze_manifest.json)、各试次 `attempts/`、原图、关联记录、身份观测、场景回执和 `flight.ulg`。
- [单次准入](../openvino_pilot_20261011_01/PILOT_GATE.json)、[单次审计](../openvino_pilot_20261011_01/lane_change_pilot/batch_audit.json)、[离线一致性](../openvino_equivalence_20261011_01/report.json)。
- [此前 Torch 报告](../two_scenario_frozen_repeat_20261011_01/FINAL_REPORT.md)保持原样，不混计两批样本。

在项目根目录只读复核并重新生成补充报告：

```bash
.venv-yolo/bin/python results/vehicle_tracking_validation/openvino_two_scenario_repeat_20261011_01/independent_check.py
.venv-yolo/bin/python results/vehicle_tracking_validation/openvino_two_scenario_repeat_20261011_01/summarize_openvino.py
```

复核复用原 Torch 批次的独立检查脚本，但从本批冻结快照加载身份评测器；检查脚本与调用包装的哈希均记录在输出中。只更新补充分析产物，不覆盖任务日志或冻结验收结论。
