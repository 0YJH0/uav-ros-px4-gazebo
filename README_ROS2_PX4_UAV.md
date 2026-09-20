# ROS2 / PX4 / Gazebo 无人机自主感知与任务仿真平台

> 项目状态：开发中  
> 当前阶段：**PX4 + Gazebo + ROS2 双向通信、Offboard 自主任务状态机、RGB 相机接入与 ROS2 图像桥接已完成；正在进入感知闭环与 Benchmark 阶段。**

---

## 1. 项目定位

本项目面向无人机自主感知、任务规划与仿真算法岗位，目标是构建一个可扩展的：

**“物理仿真 → 飞控 → ROS2 通信 → 视觉感知 → 任务决策 → Offboard 控制 → 自动评测”**

闭环平台。

项目不是简单运行 PX4 / Gazebo Demo，而是逐步建立自己的 ROS2 节点、任务状态机、相机模型、感知接口、Benchmark 与数据采集模块，最终形成可用于无人机自主任务算法开发与求职展示的完整工程项目。

---

## 2. 当前系统架构

```text
                         ROS2 Mission Layer
                                │
                    px4_offboard_controller
                                │
                     Mission State Machine
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
     OffboardControlMode   TrajectorySetpoint  VehicleCommand
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                           /fmu/in/*
                                │
                         uXRCE-DDS
                                │
                                ▼
                               PX4
                    ┌───────────┴───────────┐
                    │                       │
               State Estimation        Controllers
                  EKF2                   Position
                    │                    Velocity
                    │                    Attitude
                    │                    Rate
                    │                       │
                    └───────────┬───────────┘
                                ▼
                         Gazebo X500
                                │
                ┌───────────────┴───────────────┐
                │                               │
           Vehicle State                    RGB Camera
                │                               │
          PX4 uORB topics                Gazebo Transport
                │                               │
          uXRCE-DDS Agent                 ros_gz_image
                │                               │
          /fmu/out/*                  /camera/image_raw
                │                               │
                └──────────────┬────────────────┘
                               ▼
                         ROS2 Perception
                         （下一阶段）
```

---

## 3. 当前工程目录

```text
ROS2_manmade/
├── PX4-Autopilot/
│   └── Tools/simulation/gz/models/
│       ├── uav_rgb_camera/
│       └── x500_perception/
│
├── ros2_ws/
│   └── src/
│       ├── uav_learning/
│       ├── uav_interfaces/
│       ├── px4_msgs/
│       └── Micro-XRCE-DDS-Agent/
│
├── config/
│   └── perception_test_targets.sdf
│
├── docs/
├── results/
└── scripts/
    ├── px4_env.sh
    └── wsl_proxy.sh
```

---

## 4. 已实现功能

### 4.1 ROS2 基础通信模块

已手动完成 ROS2 Package / Node / Topic / Message / Service / Action / Launch 基础工程。

包含：

- Publisher / Subscriber
- 自定义 `SetMode.srv`
- 自定义 `FlyToAltitude.action`
- ROS2 Launch 多节点启动
- 基础 UAV 状态发布与监控节点

这部分主要用于建立 ROS2 通信机制与软件工程基础。

---

### 4.2 PX4 SITL + Gazebo 仿真环境

已完成：

```text
PX4 v1.17
+
Gazebo Harmonic
+
X500 Quadrotor
+
WSL2 Ubuntu 24.04
```

能够正常启动：

```bash
make px4_sitl gz_x500
```

并通过 PX4 Shell：

```text
pxh>
```

查看飞控内部状态与 uORB 数据。

---

### 4.3 PX4 uORB → ROS2 状态链路

已完成：

```text
PX4 uORB
    ↓
uxrce_dds_client
    ↓
UDP 8888
    ↓
MicroXRCEAgent
    ↓
DDS
    ↓
ROS2 /fmu/out/*
```

已经能够通过 ROS2 获取：

```text
/fmu/out/vehicle_status_v1
/fmu/out/vehicle_local_position_v1
/fmu/out/vehicle_attitude
/fmu/out/vehicle_odometry
/fmu/out/vehicle_global_position
...
```

实现真实 PX4 状态监控节点：

```text
uav_state_monitor.py
```

每秒汇总：

```text
位置
速度
高度
航向
ARM / DISARM
飞行模式
Failsafe
```

---

### 4.4 ROS2 → PX4 Offboard 控制链路

已打通：

```text
ROS2
    ↓
/fmu/in/offboard_control_mode
/fmu/in/trajectory_setpoint
/fmu/in/vehicle_command
    ↓
uXRCE-DDS
    ↓
PX4
    ↓
Gazebo X500
```

实现自动：

```text
进入 OFFBOARD
→ ARM
→ 起飞
→ 位置控制
→ 悬停
```

PX4 Command ACK 已验证：

```text
VEHICLE_CMD_DO_SET_MODE       ACCEPTED
VEHICLE_CMD_COMPONENT_ARM_DISARM  ACCEPTED
```

---

### 4.5 自主任务状态机 FSM

当前任务状态机：

```text
WAIT_FOR_PX4
     ↓
PRESTREAM
     ↓
REQUEST_OFFBOARD
     ↓
ARMING
     ↓
TAKEOFF
     ↓
HOVER
     ↓
MOVE
     ↓
HOLD
     ↓
RETURN
     ↓
LAND
     ↓
DONE
```

当前默认任务：

```text
原地起飞 5 m
→ 悬停
→ 向北移动 5 m
→ 悬停
→ 返回起飞点上空
→ 自动降落
→ DISARM
```

支持 ROS2 Parameters 配置：

```text
target_height
move_north
move_east
hover_duration
hold_duration
position_tolerance
vertical_tolerance
speed_tolerance
```

这部分已经形成完整的：

**任务层 → Offboard → PX4 控制器 → Gazebo 飞行动力学 → 状态反馈**

闭环。

---

## 5. RGB 相机与视觉链路

### 5.1 X500 Depth 相机验证

已经验证 PX4 官方 `x500_depth` 的前视 IMX214 RGB 相机：

```text
Gazebo Camera
    ↓
gz transport
    ↓
ros_gz_image
    ↓
sensor_msgs/msg/Image
    ↓
ROS2
```

ROS2 标准接口：

```text
/camera/image_raw
/camera/camera_info
```

已经能够使用：

```bash
ros2 topic hz /camera/image_raw
```

持续获得图像数据，并通过：

```bash
ros2 run rqt_image_view rqt_image_view
```

观察无人机运动对应的相机画面变化。

---

### 5.2 简单感知场景验证

已经创建简单高对比度场景：

```text
红色大型墙体
绿色柱体
蓝色柱体
```

用于验证：

```text
相机安装方向
相机 FOV
目标尺度
无人机运动与图像变化
Gazebo → ROS2 图像链路
```

验证结果：RGB 图像能够正确反映无人机运动与场景变化。

---

## 6. 自定义 x500_perception

为降低渲染负载和减少机翼进入前视相机画面的问题，开始构建自定义：

```text
x500_perception
```

结构：

```text
x500_perception
├── PX4 X500
└── uav_rgb_camera
    └── IMX214
```

相机优化：

```text
安装位置：
x = 0.28 m
y = 0.00 m
z = 0.30 m

RGB：
960 × 540
20 Hz

Depth Camera：
暂时关闭
```

优化前：

```text
1920 × 1080 RGB
+
640 × 480 Depth
+
Gazebo GUI

RTF ≈ 40%
```

优化后目前：

```text
960 × 540 RGB
无 Depth Camera

RTF ≈ 90%
```

即：

**Gazebo Real Time Factor 从约 40% 提升到约 90%。**

该结果目前是单次工程测试结果，后续需要固定测试条件并重复测量后才能作为正式 Benchmark 指标。

---

## 7. 当前已形成的能力

截至目前，平台已经具备：

```text
Gazebo 物理仿真
        ↓
PX4 飞控
        ↓
ROS2 双向通信
        ↓
真实飞控状态读取
        ↓
Offboard 位置控制
        ↓
自主任务状态机
        ↓
RGB 相机
        ↓
ROS2 Image
```

也就是说已经实现：

**“能飞、能控制、能获取视觉数据、能执行完整任务流程”**

但尚未完成：

**“看见目标 → 理解目标 → 根据目标自动改变飞行行为”**

这将是下一阶段的核心。

---

# 8. 下一阶段：Perception Node

首先建立：

```text
/camera/image_raw
        ↓
perception_node.py
        ↓
cv_bridge
        ↓
OpenCV ndarray
        ↓
Target Detection
        ↓
/perception/target
```

第一阶段不立即使用复杂神经网络。

先使用简单高对比目标验证：

```text
HSV / Color Threshold
        ↓
Morphology
        ↓
Contour
        ↓
BBox
        ↓
Center (u, v)
```

输出：

```text
target_visible
bbox
center_u
center_v
confidence
```

作用是先验证：

```text
图像
→ 感知
→ ROS2消息
→ Mission FSM
```

的数据闭环。

---

# 9. 后续自主任务 FSM

完成感知节点后，将当前：

```text
TAKEOFF
→ HOVER
→ MOVE
→ HOLD
→ RETURN
→ LAND
```

升级为：

```text
INIT
 ↓
TAKEOFF
 ↓
SEARCH
 ↓
DETECT
 ↓
APPROACH
 ↓
TRACK
 ↓
RETURN
 ↓
LAND
```

其中：

### SEARCH

按照预设航点或搜索轨迹移动。

### DETECT

从：

```text
/perception/target
```

确认目标存在。

### APPROACH

根据目标像素误差 / 目标空间位置调整 UAV 运动。

### TRACK

保持目标位于图像中心附近。

### RETURN

任务完成后回到 Home。

### LAND

PX4 AUTO LAND。

---

# 10. TF2 与坐标系统

后续需要建立完整：

```text
world / map
    ↓
odom
    ↓
base_link
    ↓
camera_link
    ↓
camera_optical_frame
```

用于：

```text
图像像素
    ↓
相机坐标
    ↓
机体坐标
    ↓
世界坐标
```

并明确处理：

```text
PX4 NED
ROS2 ENU
Gazebo ENU
Camera Optical Frame
```

之间的坐标转换。

这是后续真正实现目标空间定位和视觉闭环控制的关键。

---

# 11. Benchmark 系统

项目最终需要建立独立 Benchmark，而不是只看一次 Gazebo Demo 是否成功。

建议建立：

```text
scripts/run_benchmark.py
results/
├── benchmark.csv
├── mission_logs/
├── trajectories/
└── figures/
```

每次实验自动记录：

```text
随机种子
目标位置
任务参数
起飞时间
首次检测时间
目标到达时间
返回时间
降落时间
任务是否成功
位置误差
视觉检测结果
控制状态
Failsafe
```

---

# 12. 最终量化指标

项目真正达到“简历强项目”水平时，应至少能够稳定统计以下四类指标。

## A. 仿真平台性能

### Real Time Factor

```text
RTF = simulation time / wall-clock time
```

当前阶段测试：

```text
原始 x500_depth：约 40%
x500_perception：约 90%
```

正式 Benchmark 时需在：

```text
相同硬件
相同 world
相同 GUI 设置
相同任务
```

下重复测量。

### Camera Throughput

```text
ROS2 image FPS
平均帧间隔
P95 frame latency
```

例如：

```text
Camera configured: 20 Hz
ROS2 measured: xx Hz
```

---

## B. 飞行控制指标

### Hover Altitude RMSE

```text
RMSE_z
```

比较：

```text
target_z
vs
vehicle_local_position.z
```

### Waypoint Position Error

```text
horizontal RMSE
3D RMSE
final waypoint error
```

### Trajectory Tracking Error

```text
ATE / RMSE
```

用于衡量预设轨迹与实际飞行轨迹之间的误差。

---

## C. 感知指标

如果使用简单目标：

```text
Detection Success Rate
Center Pixel Error
Detection Latency
FPS
```

后续替换 YOLO 等模型后：

```text
Precision
Recall
mAP50
mAP50-95
Inference Latency
FPS
```

---

## D. 自主任务指标

这是最重要的一类。

### Mission Success Rate

```text
成功完成：
Takeoff
→ Search
→ Detect
→ Approach
→ Track
→ Return
→ Land
```

的实验比例。

### Mission Completion Time

从任务开始到落地。

### Target Acquisition Time

```text
首次开始搜索
→
首次稳定检测目标
```

### Tracking Performance

例如：

```text
目标中心平均像素误差
P95像素误差
目标丢失率
连续跟踪时间
```

### Landing Error

```text
最终落点
vs
Home
```

---

# 13. 到哪一步可以写进简历？

## 当前阶段

现在已经可以在简历里作为：

**“个人项目 / 在研项目”**

出现。

可以描述：

> 基于 ROS2、PX4 SITL 与 Gazebo 搭建无人机自主任务仿真平台，完成 uXRCE-DDS 双向通信、PX4 状态监测、Offboard 位置控制与 TAKEOFF–MOVE–RETURN–LAND 任务状态机；接入前视 RGB 相机并完成 Gazebo–ROS2 图像桥接，自定义轻量化 X500 感知模型，将仿真实时因子由约 40% 提升至约 90%。

但这一阶段最有价值的量化结果主要仍然是：

```text
RTF
相机吞吐率
基础位置控制误差
```

项目尚不足以强调“自主感知任务”。

---

# 14. 最低简历完整线

建议至少完成到：

```text
RGB Camera
     ↓
Perception Node
     ↓
目标检测
     ↓
SEARCH
     ↓
DETECT
     ↓
APPROACH
     ↓
RETURN
     ↓
LAND
     ↓
Batch Benchmark
```

并进行：

```text
≥ 30 次自动仿真实验
```

能够给出：

```text
Mission Success Rate
Detection Success Rate
Target Acquisition Time
Position RMSE
Mission Completion Time
RTF
```

到这一步，就已经可以形成一段比较完整、有量化结果的简历项目经历。

---

# 15. 推荐的“强简历版本”完成线

如果时间允许，建议做到：

```text
ROS2 / PX4 / Gazebo
        ↓
自定义无人机感知模型
        ↓
RGB Camera
        ↓
目标检测
        ↓
TF2
        ↓
目标空间定位
        ↓
SEARCH
        ↓
DETECT
        ↓
APPROACH
        ↓
TRACK
        ↓
RETURN
        ↓
LAND
        ↓
rosbag2 自动记录
        ↓
Batch Benchmark
        ↓
Failure Analysis
```

并进行：

```text
50 ~ 100 次
多目标位置 / 多随机种子 / 多初始条件
自动测试
```

至少形成以下最终结果：

```text
Mission Success Rate         xx.x %
Detection Success Rate       xx.x %
Target Acquisition Time      x.xx s
Tracking Pixel Error         xx.x px
Trajectory RMSE              x.xx m
Landing Position Error       x.xx m
Mission Completion Time      xx.x s
Gazebo RTF                   xx %
Camera Throughput            xx FPS
```

如果再加入：

```text
rosbag2
RViz2
Failure Analysis
3DGS RGB + Pose 数据导出
```

则可以进一步强化：

**仿真平台、感知算法、机器人软件工程、数据生成与 Benchmark 能力。**

---

# 16. 推荐简历项目名称

中文：

**基于 ROS2 / PX4 / Gazebo 的无人机自主感知与任务仿真平台**

或：

**面向自主感知任务的 ROS2–PX4 无人机仿真与自动评测平台**

英文：

**ROS2-PX4 UAV Autonomous Perception, Mission Simulation and Benchmarking Platform**

---

# 17. 推荐最终简历结构

### 针对问题

针对无人机感知、飞控与任务算法模块相互独立、缺少可复现实验闭环的问题，构建 ROS2 / PX4 / Gazebo 一体化自主任务仿真与自动评测平台。

### 核心工作

基于 uXRCE-DDS 打通 PX4 uORB 与 ROS2 双向通信，自研 Offboard 控制节点与任务状态机，实现自主起飞、航点飞行、返航及降落；构建前视 RGB 感知链路与自定义轻量化 X500 感知模型，并进一步接入目标检测、TF2 空间定位、感知驱动任务规划及 rosbag2 自动记录。

### 技术成果

最终填写真实 Benchmark 结果，例如：

```text
完成 xx 组随机场景自动测试，
任务成功率 xx.x%，
目标检测成功率 xx.x%，
轨迹 RMSE x.xx m，
平均目标获取时间 x.xx s；
通过相机模型轻量化将 Gazebo RTF
由约 40% 提升至 xx%。
```

这里的所有数字必须由最终自动 Benchmark 实际测得，不提前虚构。

---

# 18. 当前下一步

当前项目最值得继续推进的路径：

```text
① 固定 x500_perception
        ↓
② 测量优化后 Camera FPS / RTF
        ↓
③ perception_node.py
        ↓
④ 红色目标检测
        ↓
⑤ /perception/target
        ↓
⑥ FSM: SEARCH → DETECT → APPROACH
        ↓
⑦ 完整 SEARCH → TRACK → RETURN → LAND
        ↓
⑧ 自动 Batch Benchmark
        ↓
⑨ Failure Analysis
        ↓
⑩ 3DGS 数据生成扩展
```

其中 **第 ⑧ 步完成以后**，项目就能够稳定产生一组可信的量化结果，适合作为简历中的完整工程项目。

---

## 19. 当前阶段结论

当前已经完成：

**“ROS2 能控制 PX4 无人机完成任务，并能够实时获取前视 RGB 图像。”**

下一阶段真正决定这个项目简历价值的是：

**“视觉感知是否真正进入任务闭环，以及是否建立了可重复的自动 Benchmark。”**

因此项目的下一条主线不应继续堆工具，而应该集中在：

```text
Perception
    +
Mission Integration
    +
Benchmark
```

三个部分。
