# 红车后方变道超车并回中：单次可视化闭环测试

日期：2026-10-11。场景已实现并完成一次独立启动的 Gazebo GUI 测试。

**结论：超车动作完成，但本轮跟踪与严格联合验证未通过。** 无人机自主返航、降落并解除武装，未人工接管。本轮失败证据完整保留，不作为成功基线替代历史结果。

## 场景与修改位置

| 内容 | 文件 |
| --- | --- |
| 红车五阶段轨迹、时间、车道位置与几何检查 | `scripts/vehicle_lane_change.py` |
| 动态车辆位姿更新、阶段事件、独立身份评估 | `scripts/vehicle_crossing_validation.py` |
| 道路、静态车辆、目标车运动与遮挡板 | `ros2_ws/src/uav_learning/uav_learning/vehicle_scene.py` |
| 启动参数传递 | `ros2_ws/src/uav_learning/launch/vehicle_tracking.launch.py` |
| 一键验证入口 | `scripts/run_vehicle_tracking_validation.py` |

目标车与干扰车均为红色；目标车速度 0.8 m/s，停放车位置为 `(30, -4.4, 0.05)` m。沿用加宽道路，左侧车道中心为 `y=3.8 m`。后车起点为 `(-12, 0, 0.05)` m，原目标起点为 `(16, 0, 0.05)` m。

以下时间均为首次 TRACK 后的车辆运动仿真时间，不是启动后的墙钟时间：

| 时间 | 动作 |
| --- | --- |
| 0–25 s | 同车道后方接近，纵向相对位置由 -28 m 平滑变为 -10 m |
| 25–35 s | 保持在原车后方，向左侧车道变道 |
| 35–47 s | 左侧超车，相对位置由 -10 m 变为 +10 m |
| 47–57 s | 保持领先，回到中间车道 |
| 57 s 后 | 中间车道前方约 10 m 同向行驶 |

轨迹使用五次平滑插值，车头朝向根据速度方向计算。保留运动第 15–19 仿真秒的计划遮挡，未修改感知、关联或控制门限，保留 10 秒盲跟安全限制。

## 测试结果

| 指标 | 结果 |
| --- | --- |
| 五阶段动作实证 | 全部完成 |
| 机载目标确认覆盖率 | **74.61%**，低于原有 80% 任务通过线 |
| TRACK 丢失 | 4 次：计划遮挡 1 次、非计划 3 次 |
| 计划遮挡解除后的确认恢复 | 1.372 s（墙钟时间） |
| 非计划丢失至机载重新确认 | 14.002 / 2.100 / 12.303 s（墙钟时间） |
| 恢复超时并转 SEARCH | 2 次；不是持续盲跟超过 10 秒 |
| 无人机跟随行程 | 59.838 m |
| TRACK 平均绝对像素误差 | 17.935 px |
| 最终返航水平误差 | 0.729 m |
| 独立身份验证 | **未通过** |
| 可评分帧错车 / ID 切换 | 0 / 0；不覆盖无法评分的帧 |
| PX4 武装期间 failsafe / Offboard 丢失观测 | 0 / 0 |
| ULog 数据丢段事件 | 0 |
| 自动降落、解除武装 | 完成 |

覆盖率是跟随期间机载确认状态的时间加权比例，不是 YOLO mAP，也不是独立验证后的身份正确率。表中的重新确认时间也仅代表机载判断，不能代替真值身份确认。

完整 Gazebo 位姿审计包含 **9531 条有效车对记录**：最小车身水平分离轴净距 **1.276 m**，干扰车至道路护栏内缘最小余量 **0.258 m**。采样几何支持本次两车未发生实体重合，不证明采样间连续时间或完整无人机机体的碰撞安全。

## 为什么未通过

1. **任务覆盖率不足。** 原有任务报告的通过条件包括覆盖率至少 80%；本轮为 74.61%。3 次非计划丢失中有 2 次经过恢复超时、搜索后重新确认，形成较长的确认空档。
2. **回中后的身份证据不足。** 独立评估在超车前、过程中分别确认原车 197、192 帧；回中后 231 帧全部标记为 `overlap_unscorable`，没有可用于严格通过的原车确认帧。两车实体分离不等于相机投影分离。`00155.7_RECOVER.jpg` 可看到同车道前后两辆红车与重叠候选框。现有包围体投影判据不会将这些帧直接算对，也不能据此断言发生了错车。
3. **场景服务记录存在启动缺口。** 已保存的 1055 条服务记录全部返回成功，且返回值一致；但 `scene` 客户端从 sequence=5 才有记录，缺少最初 1–4 条。不能宣称完整请求链无失败。场景发布与记录订阅采用非持久化 ROS 话题，启动发现时序是可能原因，但本轮未额外证明缺失原因。这一审计缺口也不支持严格联合通过。

上述记录说明任务判定与评估失败的直接原因；尚未逐帧证明三个非计划丢失各自的感知根因，不将它们全部归因于投影重叠，也不通过放宽门限或删除无法评分的帧提高结果。

## 证据

- [执行轨迹图](lane_change_trajectory.png)
- [回中后 RECOVER 图像](00155.7_RECOVER.jpg)
- [结果汇总](validation_summary.json)
- [原始任务报告](report.json)、[独立身份报告](identity_report.json)、[监督器报告](supervisor.json)
- [完整位姿几何审计](full_pose_geometry_audit.json)、[几何审计脚本](audit_lane_change_poses.py)
- [参数与文件哈希](implementation_snapshot.json)、[实际 ROS 参数](runtime_parameters.json)
- `identity_poses.jsonl`、`identity_observations.jsonl`、`scene_service.jsonl`、`traffic_service.jsonl`、`mission.log` 保留原始记录。
- `flight.ulg` 为本次完整飞行日志；`executed_sources/` 保存 40 个经哈希核实的执行文件。
- [归档与汇总审计脚本](audit_validation.py)

验证前已通过 `colcon build --packages-select uav_learning`；车辆相关回归测试 **353 passed**，有 3 条既有 protobuf 警告。测试结束后已确认 PX4、Gazebo 与验证进程退出。

## 复现命令

在项目根目录执行，输出目录必须使用新的名称，避免覆盖本轮证据：

```bash
.venv-yolo/bin/python scripts/run_vehicle_tracking_validation.py \
  --output results/vehicle_tracking_validation/red_lane_change_gui_repeat_02 \
  --gui --gui-config scripts/vehicle_tracking_gui.config \
  --lane-change-overtaking --distractor-color red --parked-y -4.4 \
  --vehicle-speed 0.8 --occlusion-start 15 --occlusion-duration 4 \
  --model-path yolo11s.pt --detector-backend torch
```

本轮仅为新增交通场景的一次功能与闭环测试，不是重复实验，不证明算法改善。没有调整已有跟踪算法，也没有制作 demo 录像。
