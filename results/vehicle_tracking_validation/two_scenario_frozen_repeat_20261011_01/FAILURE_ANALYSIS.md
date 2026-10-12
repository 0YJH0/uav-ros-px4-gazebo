# 批量实验失败与恢复问题分析

已分析 20 次结束的实验。本报告是事后诊断，不更改预先冻结的验收标准、原始日志或成功率分母。

## 结论边界

任务成功、独立身份证据通过和严格联合验收不是同一个指标。启动阶段的一次场景请求超时，即使重试成功且完成正常跟踪，也会使“所有原生请求成功”的严格条件失败。这类失败须保留，但不能等同为跟踪算法失败。

计划遮挡的“总丢失时长”从任务发出 TRACK_TARGET_LOST 开始；“遮挡结束后恢复时长”从挡板移开开始。两者均为墙钟秒，与设定的 4 秒仿真遮挡时长不同，不能混用。

## 场景请求可靠性

以下区分启动创建请求和运动阶段 set_pose 请求。后续相同载荷重试成功，不会抹除首次失败。native binding/response 未获确认只说明客户端未收到成功回执，不能证明服务端从未执行该请求。

| 实验 | 客户端 / 序号 | 请求 | 耗时/秒 | 后续相同载荷成功序号 |
|---|---|---|---:|---|
| left_overtaking_01 | scene / 1 | /world/default/create | 0.5037 | 2 |

### 回执完整性与真实请求失败分开统计

| 实验 | 客户端 | 实际记录数 | 首/末序号 | 缺失序号 | 重复序号 |
|---|---|---:|---|---|---|
| left_overtaking_04 | scene | 490 | 5 / 494 | [1, 2, 3, 4] | [] |

缺失回执的原始成功/失败状态未知。不能把它们计为已知失败请求，也不能把记录到的零失败扩展为所有请求成功。

## 每次任务丢失与恢复

| 实验 | 计划遮挡内丢失 | 丢失墙钟时刻/秒 | 丢失至确认/秒 | 遮挡结束至确认/秒 | 未恢复 | 正确候选拒绝原因 |
|---|---|---:|---:|---:|---|---|
| left_overtaking_01 | False | 77.600 | 0.499 | 不适用 | False | 无独立可评分的拒绝 |
| left_overtaking_01 | True | 99.699 | 7.500 | 2.423 | False | pending_confirmation: 3, overlap_ambiguous_geometry: 2, overlap_recovery_requires_strong: 3, weak_idless_anchor_expired: 3, center_gate: 3, scale_gate: 3 |
| left_overtaking_01 | False | 116.699 | 0.600 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_01 | False | 80.142 | 4.327 | 不适用 | False | center_gate: 11, mahalanobis_gate: 3, pending_confirmation: 2 |
| lane_change_01 | True | 102.169 | 6.900 | 1.737 | False | pending_confirmation: 2 |
| left_overtaking_02 | True | 106.418 | 7.591 | 2.491 | False | pending_confirmation: 2 |
| lane_change_02 | True | 98.600 | 6.949 | 1.670 | False | pending_confirmation: 2 |
| lane_change_02 | False | 124.248 | 0.100 | 不适用 | False | 无独立可评分的拒绝 |
| left_overtaking_03 | True | 99.971 | 6.840 | 1.346 | False | pending_confirmation: 2 |
| lane_change_03 | False | 87.985 | 0.500 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_03 | True | 101.085 | 7.100 | 1.841 | False | pending_confirmation: 2 |
| lane_change_03 | False | 172.171 | 1.000 | 不适用 | False | pending_confirmation: 2 |
| left_overtaking_04 | True | 87.537 | 5.500 | 1.228 | False | pending_confirmation: 2 |
| left_overtaking_04 | False | 114.248 | 0.523 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_04 | False | 69.788 | 0.400 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_04 | True | 88.388 | 5.000 | 1.035 | False | pending_confirmation: 2 |
| lane_change_04 | False | 145.109 | 0.200 | 不适用 | False | 无独立可评分的拒绝 |
| left_overtaking_05 | True | 84.721 | 5.400 | 1.200 | False | pending_confirmation: 2 |
| lane_change_05 | True | 85.049 | 5.601 | 1.217 | False | pending_confirmation: 2 |
| lane_change_05 | False | 139.910 | 0.500 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_05 | False | 149.810 | 0.800 | 不适用 | False | pending_confirmation: 1 |
| lane_change_05 | False | 151.510 | 1.508 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_05 | False | 158.710 | 1.960 | 不适用 | False | pending_confirmation: 6 |
| left_overtaking_06 | True | 84.397 | 5.400 | 1.034 | False | pending_confirmation: 2 |
| left_overtaking_06 | False | 103.930 | 0.400 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_06 | True | 95.160 | 6.589 | 1.423 | False | pending_confirmation: 2 |
| lane_change_06 | False | 165.344 | 0.501 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_06 | False | 169.245 | 2.400 | 不适用 | False | pending_confirmation: 3 |
| left_overtaking_07 | True | 104.640 | 6.901 | 1.566 | False | pending_confirmation: 2 |
| lane_change_07 | True | 101.438 | 6.974 | 1.744 | False | pending_confirmation: 2 |
| lane_change_07 | False | 172.253 | 0.500 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_07 | False | 174.553 | 1.700 | 不适用 | False | pending_confirmation: 2 |
| lane_change_07 | False | 180.253 | 0.599 | 不适用 | False | 无独立可评分的拒绝 |
| left_overtaking_08 | True | 87.910 | 6.100 | 1.536 | False | pending_confirmation: 2, weak_idless_anchor_expired: 1, center_gate: 1, scale_gate: 1 |
| lane_change_08 | True | 90.275 | 6.599 | 1.354 | False | pending_confirmation: 2 |
| lane_change_08 | False | 149.389 | 1.001 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_08 | False | 159.589 | 0.700 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_08 | False | 160.990 | 0.999 | 不适用 | False | pending_confirmation: 1 |
| lane_change_08 | False | 166.389 | 0.600 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_08 | False | 168.289 | 1.900 | 不适用 | False | pending_confirmation: 3 |
| left_overtaking_09 | True | 97.086 | 5.900 | 1.486 | False | pending_confirmation: 2 |
| lane_change_09 | True | 87.366 | 5.400 | 1.087 | False | pending_confirmation: 2 |
| left_overtaking_10 | False | 96.400 | 0.500 | 不适用 | False | 无独立可评分的拒绝 |
| left_overtaking_10 | True | 123.482 | 8.099 | 1.826 | False | pending_confirmation: 2 |
| left_overtaking_10 | False | 164.184 | 0.398 | 不适用 | False | 无独立可评分的拒绝 |
| lane_change_10 | True | 121.971 | 7.901 | 1.595 | False | pending_confirmation: 2 |

## 关键归因

### 左侧超车第 1 轮：启动建路请求未获确认

唯一原生失败请求为 scene 序号 1 的 create，耗时 503.65 ms，预算 500 ms。后续同载荷序号 2 重试成功。冻结场景代码 pending[0] 为道路，因此这是首次建路阶段的启动可靠性问题，不是车辆运动过程中持续 set_pose 失败。本轮任务与身份证据通过，严格联合验收仍保留失败。

### lane_change_01：80.142 秒开始的非计划恢复

总恢复耗时 4.326779469032772 秒；任务丢失窗口共 16 个关联帧，其中 16 帧存在独立投影支持的原车候选，13 帧的正确候选未被接受。拒绝原因统计：{'center_gate': 11, 'mahalanobis_gate': 3, 'pending_confirmation': 2}。
可评分正确候选主要被中心位置关联条件拒绝，而不是尺度门限。这说明不能把本段恢复概括为 YOLO 一直没有检测到原车，也不能归为修复前的尺度预测发散。
恢复及其前 1.5 秒上下文内，相机运动补偿不可用原因：{'warp_bounds': 1}。这与后续中心预测失配在时间上相关，但日志关联本身不是单变量因果证明。
上下文内被拒的正确候选中心误差范围 0.1356–0.2037（归一化坐标），对数尺度误差范围 0.0045–0.4928；每帧实际门限、预测宽高、GMC 质量和推理延时均保留在 JSON 中。

### 左侧超车第 4 轮：启动回执证据缺口

scene 日志从序号 5 开始，5–494 连续，但最初四个 create 回执未留存。它们对应道路、原车、路边车和挡板初始化；已记录的原生请求没有失败。mission.log 出现 Street and vehicles ready，结合只在 request 返回成功后移除 pending 项的代码，可推断初始化流程完成，但这不能补造四条原始回执或替代严格审计。

场景回执 publisher/subscriber 使用默认 volatile 持久性，且启动未等待该订阅匹配完成，因此现象符合启动期 DDS 匹配前回执未被 recorder 保存。四条消息远少于 depth=100，没有证据支持“队列溢出”或“四次服务实际失败”。当前保留严格完整性失败，不在批次中修改代码。

### lane_change_05：完整感知链路时效波动

非计划恢复上下文出现 2 个去重的 stale_inference_result 帧。观测发布时间龄范围 0.557–0.573 秒，处理耗时范围 0.482–0.534 秒。冻结系统保留 0.5 秒图像处理时效限制；过期结果被主动拒绝，随后需要重新积累确认。这是实时性保护与实际计算波动的影响，不能归为 YOLO 完全看不见目标。

### 变道回中第 6 轮：重叠框形态抖动

169.245 秒开始的非计划恢复持续约 2.400 秒。原轨迹 ID 14 没有切换，但候选框宽度约 94 px 时，高度在约 79–111 px 间交替；同一 ID 的三帧确认计数多次重新从 1 累积。冻结连续确认还要求几何一致性，因此保留 ID 本身不保证证据连续。多帧独立投影标签为 overlap_unscorable，符合正常车身框与包含两车投影的大框交替的现象，不能把这些候选全部判定为正确原车。

这与单纯切换重叠模式后无条件清空确认不同；当前修复保留兼容证据，并未消除真实框形态变化带来的安全重确认。后续改进空间在分离重叠实例和提高框稳定性，不能用统一放宽所有关联门限或宣称不可评分大框身份正确来消除统计损失。

### lane_change_06：169.245 秒开始的非计划恢复

总恢复耗时 2.399989994999487 秒；任务丢失窗口共 13 个关联帧，其中 5 帧存在独立投影支持的原车候选，3 帧的正确候选未被接受。拒绝原因统计：{'pending_confirmation': 3}。
上下文内被拒的正确候选中心误差范围 0.0003–0.0051（归一化坐标），对数尺度误差范围 0.0102–0.0437；每帧实际门限、预测宽高、GMC 质量和推理延时均保留在 JSON 中。

### lane_change_08：完整感知链路时效波动

非计划恢复上下文出现 1 个去重的 stale_inference_result 帧。观测发布时间龄范围 0.513–0.513 秒，处理耗时范围 0.377–0.377 秒。冻结系统保留 0.5 秒图像处理时效限制；过期结果被主动拒绝，随后需要重新积累确认。这是实时性保护与实际计算波动的影响，不能归为 YOLO 完全看不见目标。

### 变道回中第 10 轮：任务墙钟窗口早于场景仿真阶段结束

本轮覆盖率 91.39%，任务通过，但身份与严格联合验收不通过。跟随窗口为 99.499 墙钟秒，RETURN 出现在 recorder 墙钟 193.373 秒。最后 TRACK 样本中的车辆运动时长仅 55.4 仿真秒；最后独立身份图像在 sim=120.500 秒、motion=55.2 秒，尚未达到 57 仿真秒的 ahead_follow 阶段。

同一 recorder 时钟下，首次记录 motion=57 的样本在 195.722 秒，状态已经是 RETURN。traffic 节点在返航后继续更新车辆，因此稍后 sim=122.400 秒确实发出了场景完成事件，完整 pose 流也保留了车已回中且在前方的位姿。然而身份 observer 的 association() 明确排除 RETURN 状态，返航后的图像不再进入身份证据窗口。

所以 traffic_completed=True 与 post={} 并不矛盾：场景后来完成，但本次有效跟踪观测窗口没有覆盖回中后的确认。这不是“已经回中后一直认不出原车”，也不是已观察到错车；末帧仍被独立确认为 tracked_vehicle，已记录观测的 truth 匹配比例为 1.0。仿真推进慢于墙钟，使固定墙钟跟踪任务与仿真时间驱动的交通阶段脱节。本批不修改观察窗口，也不把完成事件替代缺失的至少 10 帧 post 原车证据。

注意 crossing_events 与 recorder 的 wall_s 原点不同；上文时间顺序依据同一个 samples.jsonl 及图像 stamp、sim_s 对齐，不直接相减两个节点的墙钟相对值。


## 解释限制

- 身份诊断沿用冻结的 v2 投影体积证据，同图像时间戳匹配；没有向在线控制器输入仿真真值。
- 拒绝原因按候选计数，同一候选可以同时违反多个条件；不是独立漏检帧数量。
- 无候选或无可评分原车候选，不自动等同为 YOLO 漏检：真实遮挡、截断和投影歧义仍可能存在。
- 不可评分帧不能假定跟对；错车为零只适用于可评分观测。
- GMC 和时延变化只说明日志中的时间关联，没有通过新增消融实验证明唯一因果。
- 没有恢复的事件保留为未恢复及已观察时长下界，不填入零秒或当作成功。

完整逐帧候选、补偿矩阵、预测尺度和时延见 [FAILURE_ANALYSIS.json](FAILURE_ANALYSIS.json) 及每轮 `failure_diagnostics.json`。
