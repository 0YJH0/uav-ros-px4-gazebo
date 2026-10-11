# 最终有效实验结果

当前只保留 2026-10-11 完整十次异色分车道超车批次及其独立审计。早期冒烟、开发试跑、失败和已替代实验产物已按要求删除；代码、单元测试、模型、依赖与必要构建安装文件保留。

## 保留内容

| 路径 | 内容 |
| --- | --- |
| [scene_transport_isolated_repeat_20261011_01/](scene_transport_isolated_repeat_20261011_01/) | 最终十次原始实验、冻结代码/模型/参数、参考证据、逐次日志及图像 |
| [scene_transport_isolated_repeat_audit_20261011_01/](scene_transport_isolated_repeat_audit_20261011_01/) | 完整性、身份、场景服务、安全、时延、构图与丢失审计 |
| [最终报告](scene_transport_isolated_repeat_audit_20261011_01/FINAL_REPORT.md) | 逐次结果、指标、图表、剩余问题和结论边界 |
| [清理清单](CLEANUP_MANIFEST.json) | 删除路径、容量、保留范围和删除前后完整性核对 |

试次 `overtaking_01/` 至 `overtaking_10/` 全部保留，包括覆盖率最低的 09、次低的 06，以及全部非计划丢失记录；没有按成绩筛选、替换或缩小统计分母。`failure_analysis.json` 是最终批次的验收摘要，虽没有失败任务，也属于有效结果，不删除。

## 最终摘要

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

删除 101 个旧实验目录和 9 个旧审计文件，按删除前 `du` 的分配容量合计约 7.76 GiB。删除操作结束时，保留结果树 1554 个文件/链接和代码、模型 724 个文件/链接的校验均与删除前一致。之后仅整理说明文档，未修改实验数据。

冻结协议、快照及历史分析脚本中的原始来源路径保留，作为当时执行的溯源信息，不代表该历史目录仍然存在。原选择参考的报告、参数和执行源码已复制在最终批次的 `reference_evidence/` 与 `reference_executed_sources/`。新批量实验可用保留的 `overtaking_01/` 作为配置参考，见[运行说明](../../docs/vehicle_tracking.md)。

当前数据不能重新核验已删除的历史失败，也不能把最终批次 10/10 写成整个开发过程零失败、同外观交叉已解决或实机可靠性证明。

[项目总览](../../PROJECT_OVERVIEW.md)；
[主要困难与方法](../../PROJECT_CHALLENGES.md)。
