# ROS 2 PX4 Gazebo 无人机车辆跟踪

基于 ROS 2 Jazzy、PX4 SITL、Gazebo Harmonic、YOLO11s 和 ByteTrack 的车辆视觉跟踪仿真项目。实现自主起飞、搜索和确认原目标、持续跟随、遮挡恢复、返航、降落与独立实验评测。

车辆真值仅用于独立评测，不输入感知或飞行控制。当前成果限定于仿真，不包含实机部署、学习型 ReID、SLAM 或新 YOLO 模型训练。

## 当前结果

2026-10-11 在红色目标车、蓝色干扰车的分车道超车与运动遮挡场景，完成十次独立重启：

| 指标 | 结果 |
| --- | --- |
| 任务、独立身份、严格联合通过 | 各 10/10 |
| 原目标确认覆盖率 | 均值 90.69%，样本标准差 2.39 个百分点，最差 86.05% |
| 道路遮挡确认恢复 | 均值 1.654 s，最差 1.881 s |
| 非计划丢失 | 共 7 次，最长恢复 6.70 s |
| 平均感知处理耗时 | 跨试次均值 179.90 ms |
| 无人机跟随行进距离 | 均值 51.73 m |
| 场景请求 | 8149 次，失败 0 次 |
| 可评分错车、身份切换、监督接管 | 各 0 |

十次全部保留，包括覆盖率较低的试次和全部丢失记录。10/10 不是检测 mAP 或所有环境成功率；异色超车不证明同外观交叉 ReID 已解决，零记录安全事件不等于实机安全证明。

![最终批量指标](results/vehicle_tracking_validation/scene_transport_isolated_repeat_audit_20261011_01/batch_metrics.png)

## 文档

- [项目总览](PROJECT_OVERVIEW.md) / [PDF](PROJECT_OVERVIEW.pdf)
- [主要困难与解决方法](PROJECT_CHALLENGES.md) / [PDF](PROJECT_CHALLENGES.pdf)
- [30 分钟介绍讲稿](PROJECT_PRESENTATION_30MIN.md) / [PDF](PROJECT_PRESENTATION_30MIN.pdf)
- [运行与验证说明](docs/vehicle_tracking.md)
- [环境准备与仓库资源](docs/reproduction.md)
- [最终实验报告](results/vehicle_tracking_validation/scene_transport_isolated_repeat_audit_20261011_01/FINAL_REPORT.md)
- [原始结果与清理说明](results/vehicle_tracking_validation/README.md)

`README_ROS2_PX4_UAV.md` 是早期平台规划记录，包含过时的阶段说明和未实现路线，不作为当前能力或配置依据。早期其他实验产物已清理，不能在当前数据上重新计算历史失败率。

## 数据流

```text
Gazebo RGB -> ROS 图像桥接 -> YOLO 检测 -> ByteTrack
  -> VehicleTargetLock 原目标确认 -> 任务状态机
  -> PX4 Offboard -> 无人机运动 -> 新的 RGB 图像

相机运动补偿服务轨迹与身份预测，ROI 提供有界局部检测。
独立评测使用车辆真值；记录器和监督器保存身份、任务与安全证据。
```

YOLO 与 ByteTrack 在同一感知节点内传递检测框、类别和置信度。短期轨迹 ID 与原目标身份分开维护。失去确认时保留 10 墙钟秒、4 m 位移与 0.8 m/s 预测速度的恢复限制；预算耗尽不永久禁止视觉重关联。

## 下载与运行

仓库包含完整最终实验数据，因此下载量较大。PX4、px4_msgs 和 DDS Agent 使用固定提交的 Git 子模块；虚拟环境与普通构建安装文件不上传，需要本机重新准备。

```bash
git clone --recurse-submodules https://github.com/0YJH0/uav-ros-px4-gazebo.git
cd uav-ros-px4-gazebo
```

先按 [环境准备](docs/reproduction.md) 安装依赖、恢复自定义相机模型并构建。准备完成后，在仓库根目录执行一次新的 GUI 闭环验证：

```bash
.venv-yolo/bin/python scripts/run_vehicle_tracking_validation.py \
  --output results/vehicle_tracking_validation/new_gui_validation \
  --gui --gui-config scripts/vehicle_tracking_gui.config \
  --overtaking --vehicle-speed 0.8 \
  --occlusion-start 15 --occlusion-duration 4 \
  --model-path yolo11s.pt --detector-backend torch
```

输出必须使用新路径，不覆盖已归档数据。不在真实飞行器上直接运行仿真参数。

## 仓库内容

- `ros2_ws/src/uav_learning/`：感知、跟踪、目标锁、控制器、场景、测试与车辆模型。
- `ros2_ws/src/uav_interfaces/`：自定义目标与车辆观测消息及任务接口。
- `scripts/`：独立重启监督、批量编排、指标分析及离线工具。
- `config/gazebo_models/`：自定义 RGB 相机与 X500 模型的发布副本。
- `results/vehicle_tracking_validation/`：最终十次实验及独立审计，含原图、日志、ULog 和冻结快照。
- `yolo11s.pt`：选定检测模型；另有冻结副本供证据核验。

## 许可与复现边界

第三方组件保留各自许可证；本仓库不对其重新授权。PX4、DDS Agent、px4_msgs、Ultralytics 和模型权重的使用、修改与分发需遵守对应许可。车辆模型来源与 CC0 声明保存在各模型目录中。

冻结快照中的 PX4 可执行文件是实验溯源证据，不是通用安装包；新机器应从固定子模块源码重新编译。原日志中的绝对路径、参数和校准值保持原样，不能宣称在另一台机器上能够逐位复现。当前批次未强制清空 PX4 持久校准状态。
