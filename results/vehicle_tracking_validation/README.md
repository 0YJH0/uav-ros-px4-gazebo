# 实验结果索引

当前保留两场景各十次的 Torch 批次，以及新增两场景各十次的 OpenVINO FP32 批次，历史异色十次单独归档。清理时的早期冒烟、开发试跑、失败和已替代实验产物曾按要求删除；清理后的新增验证全部保留，包括未通过的结果，各批次不混计。

## OpenVINO 补充批次

2026-10-11 启动、2026-10-12 完成。先通过 [离线一致性](openvino_equivalence_20261011_01/report.json)，再通过 [单次严格准入](openvino_pilot_20261011_01/PILOT_GATE.json)，然后两场景交替、无 GUI 独立重启各十次，未调参或替换失败。单次不计入这二十次。

[结果、逐次失败原因及 Torch 对照](openvino_two_scenario_repeat_20261011_01/RESULTS.md)；
[完整严格报告](openvino_two_scenario_repeat_20261011_01/FINAL_REPORT.md)；
[逐次 CSV](openvino_two_scenario_repeat_20261011_01/trials.csv)；
[独立复核](openvino_two_scenario_repeat_20261011_01/INDEPENDENT_CHECK.json)。

| 场景 | 任务 / 身份 / 严格通过 | 确认覆盖率均值 ± 样本标准差 | 最差覆盖率 | 感知平均处理耗时 | 非计划丢失总数 / 最长恢复 |
| --- | --- | --- | --- | --- | --- |
| 左侧超车 | 10/10 / 10/10 / 7/10 | 94.19% ± 0.25 个百分点 | 93.70% | 128.01 ms | 2 次 / 0.200 s |
| 后方变道超车再回中 | 9/10 / 10/10 / 3/10 | 92.62% ± 1.99 个百分点 | 88.65% | 127.26 ms | 13 次 / 2.400 s |

二十次均自主落地；可评分错车、身份切换、监督接管和记录到的安全事件为 0。实际 24393 条关联记录均为 OpenVINO、8 推理线程。20714 条原生请求中七条未获成功确认，另有八条回执缺失；独立 778 项核查通过，但不改判十个严格未通过试次。

严格失败：`lane_change_01/03/04/05/07/10` 与 `left_overtaking_02` 首次创建请求未获确认；`left_overtaking_01/05` 各缺最初四条回执；`lane_change_09` 遮挡入口前发生重叠歧义拒绝、尚未完成三帧确认，入口未锁定，之后约 0.995 秒恢复仍不满足计划遮挡验收前提。全部保留，不能只筛选成功试次。

原始目录为 `openvino_two_scenario_repeat_20261011_01/left_overtaking_01..10/` 和 `lane_change_01..10/`，包含图像、关联、服务、身份、参数和 ULog。冻结模型产物在 `runtime_artifacts/yolo11s_openvino_fp32_20261011_01/`，冻结副本与解释器版本见本批协议。两批先后运行，性能差异是观察性结果，不证明唯一因果；10 秒盲跟限制保持不变。

## 当前两场景批次

[完整报告](two_scenario_frozen_repeat_20261011_01/FINAL_REPORT.md)；
[失败与恢复分析](two_scenario_frozen_repeat_20261011_01/FAILURE_ANALYSIS.md)；
[独立复核](two_scenario_frozen_repeat_20261011_01/INDEPENDENT_CHECK.json)；
[指标 JSON](two_scenario_frozen_repeat_20261011_01/SUMMARY.json)；
[逐次 CSV](two_scenario_frozen_repeat_20261011_01/trials.csv)。

| 场景 | 完成试次 | 任务 / 身份 / 严格通过 | 确认覆盖率均值 ± 样本标准差 | 最差覆盖率 | 非计划丢失总数 / 最长恢复 |
| --- | --- | --- | --- | --- | --- |
| 固定左侧车道超车 | 10/10 | 10/10 / 10/10 / 8/10 | 92.43% ± 1.10 个百分点 | 90.46% | 6 次 / 0.60 s |
| 后侧同车道变道至左侧超车再回中 | 10/10 | 10/10 / 9/10 / 9/10 | 90.44% ± 2.05 个百分点 | 87.83% | 20 次 / 4.33 s |

两组使用相同冻结源码、模型、感知与飞控配置，交替无 GUI 运行，不替换失败试次。保留 10 墙钟秒、4 m、0.8 m/s 盲跟限制。可评分错车、身份切换与已记录 ULog 安全事件均为 0，但不代表所有图像都能确认身份或实机安全已获证明。

严格未通过的三个试次均保留：`left_overtaking_01` 首次建路请求未获确认后重试成功；`left_overtaking_04` 缺少最初四条创建请求回执，不能记成四次请求失败；`lane_change_10` 返航前未覆盖完整回中及后续身份窗口。最后一次车流在返航后完成动作，不等于在有效跟踪窗口中完成验证，不能解释为已经回中却认不出原车。详细时间与原因以失败分析为准。

独立复核 778 项检查通过，确认汇总与原始证据一致；它不将三个未通过试次改判为成功。已记录原生请求 17410 条，其中 1 条未获成功确认，另有 4 条回执缺失。

原始试次分别在该批次的 `left_overtaking_01/` 至 `_10/`、`lane_change_01/` 至 `_10/`。`plan.json`、`attempts/`、`batch_protocol.json`、`freeze_manifest.json` 和 `frozen_files/` 保存计划、尝试记录与共享冻结源码；每轮 `executed_sources` 指向该归档。20 份 ULog 和逐轮参数、服务、身份、候选关联及图像记录均保留。

## 后续开发验证

| 路径 | 内容与结论边界 |
| --- | --- |
| [red_distractor_curbside_gui_20261011_01/](red_distractor_curbside_gui_20261011_01/) | 红色干扰车、路边停车的分车道超车可视化验证 |
| [red_lane_change_gui_20261011_01/](red_lane_change_gui_20261011_01/) | 同车道后方变道超车再回中；原试次覆盖率 74.61%，任务未通过 |
| [red_lane_change_identity_v2_20261011_01/](red_lane_change_identity_v2_20261011_01/RESULTS.md) | 对原试次作身份规则 v2 的只读重评，不是新飞行；不能覆盖任务失败 |
| [overlap_scale_offline_20261011_02/](overlap_scale_offline_20261011_02/RESULTS.md) | 重叠候选与尺度修复的最终冻结五臂离线对照；前版 `_01` 也保留用于来源核对 |
| [overlap_scale_gui_20261011_01/](overlap_scale_gui_20261011_01/RESULTS.md) | 修复后独立闭环：覆盖率 86.24%，任务通过，回中后身份证据不足，严格联合未通过 |
| [continuity_offline_20261011_01/](continuity_offline_20261011_01/RESULTS.md) | 确认连续性的双轨迹离线对照，正确确认增加，无新增错车或多车歧义 |
| [continuity_gui_20261011_01/](continuity_gui_20261011_01/RESULTS.md) | 确认连续性单变量闭环：覆盖率 91.75%，非计划丢失 1 次，回中后 53 帧原车证据，严格联合通过；仅一次 |
| [post_merge_detector_offline_20261011_01/](post_merge_detector_offline_20261011_01/RESULTS.md) | 历史合并检测框及 ROI/NMS 问题的只读图像诊断，检测修改未上线 |

以下“最终摘要”仅对应原异色分车道十次批次，不能代替新增同外观变道场景的结论。

## 保留内容

| 路径 | 内容 |
| --- | --- |
| [scene_transport_isolated_repeat_20261011_01/](scene_transport_isolated_repeat_20261011_01/) | 最终十次原始实验、冻结代码/模型/参数、参考证据、逐次日志及图像 |
| [scene_transport_isolated_repeat_audit_20261011_01/](scene_transport_isolated_repeat_audit_20261011_01/) | 完整性、身份、场景服务、安全、时延、构图与丢失审计 |
| [最终报告](scene_transport_isolated_repeat_audit_20261011_01/FINAL_REPORT.md) | 逐次结果、指标、图表、剩余问题和结论边界 |
| [清理清单](CLEANUP_MANIFEST.json) | 删除路径、容量、保留范围和删除前后完整性核对 |

试次 `overtaking_01/` 至 `overtaking_10/` 全部保留，包括覆盖率最低的 09、次低的 06，以及全部非计划丢失记录；没有按成绩筛选、替换或缩小统计分母。`failure_analysis.json` 是最终批次的验收摘要，虽没有失败任务，也属于有效结果，不删除。

## 历史异色批次摘要

- 完整重复 10 次，任务、独立身份、严格联合均通过 10/10；全部自主返航、降落解锁。
- 确认覆盖率均值 90.69%，样本标准差 2.39 个百分点，最差 86.05%。
- 场景请求 8149 次，失败 0 次；可评分错车、身份切换、监督接管和记录到的 armed 安全事件为 0。
- 仍有 7 次非计划丢失，最长恢复 6.70 s；平均感知处理耗时跨试次均值 179.90 ms。

## 图像与原始记录

原始批次每个试次中的 `*.jpg` 为标注图，`*_raw.png` 与 `crossing_*_raw.png` 为原图；图像配对见图像 manifest。关联、样本、身份、场景请求日志和 `flight.ulg` 同目录保留。

[批量指标图](scene_transport_isolated_repeat_audit_20261011_01/batch_metrics.png)；
[完整指标 JSON](scene_transport_isolated_repeat_audit_20261011_01/final_metrics.json)；
[非计划丢失分析](scene_transport_isolated_repeat_audit_20261011_01/loss_windows/nonplanned_loss_audit.json)。

## 清理范围与证据边界

删除 101 个旧实验目录和 9 个旧审计文件，按删除前 `du` 的分配容量合计约 7.76 GiB。删除操作结束时，保留结果树 1554 个文件/链接和代码、模型 724 个文件/链接的校验均与删除前一致。这些数量描述清理时的状态；后续新增验证另存目录，不改写原批次实验数据。

冻结协议、快照及历史分析脚本中的原始来源路径保留，作为当时执行的溯源信息，不代表该历史目录仍然存在。原选择参考的报告、参数和执行源码已复制在最终批次的 `reference_evidence/` 与 `reference_executed_sources/`。新批量实验可用保留的 `overtaking_01/` 作为配置参考，见[运行说明](../../docs/vehicle_tracking.md)。

当前数据不能重新核验已删除的历史失败，也不能把最终批次 10/10 写成整个开发过程零失败、同外观交叉已解决或实机可靠性证明。

[项目总览](../../PROJECT_OVERVIEW.md)；
[主要困难与方法](../../PROJECT_CHALLENGES.md)。
