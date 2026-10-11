# 环境准备与仓库资源

本文说明下载仓库之后必须准备的资源，不改变已归档实验或飞行算法。原实验环境为 Linux/WSL、ROS 2 Jazzy、Gazebo Harmonic 和 PX4 SITL；重新编译与新机器运行不等于逐位重现实验环境。

## 1. 子模块

```bash
git submodule update --init --recursive
```

主仓库固定以下提交，不使用子模块最新分支替代：

| 组件 | 提交 |
| --- | --- |
| PX4-Autopilot | `d6f12ad1c4f70ad3230afd7d86e971421e02fef4` |
| px4_msgs | `86d8239e962f6939e05c3737784f60c02fa884db` |
| Micro-XRCE-DDS-Agent | `73622810d984349b80bbac0ef55fc0b694d62222` |

PX4 内部 Gazebo 模型子模块的原实验提交为 `b6127f4ec20de867e215fb5f78ae88b80f371909`。不要在已经开始的固定版本批次中升级子模块。

## 2. 系统依赖

先准备 ROS 2 Jazzy、Gazebo Harmonic、PX4 SITL 构建依赖，以及 ROS 的 `ros_gz_image`、`ros_gz_bridge`、`cv_bridge`、消息包和 colcon。Gazebo 原生请求需要可导入的 `gz.transport13` 与 `gz.msgs10` Python 绑定。

各组件的系统安装步骤以其自带说明为准。本仓库没有将系统安装、自动校准或全部环境状态封装成容器，不能仅复制 Python 虚拟环境替代系统依赖。

## 3. 自定义相机模型

原工作区中的 `uav_rgb_camera` 与 `x500_perception` 位于 PX4 的嵌套 Gazebo 模型子模块中，但不属于上游提交。因此，发布时将相同文件保存到主仓库 `config/gazebo_models/`，下载后需要恢复：

```bash
cp -a config/gazebo_models/uav_rgb_camera \
  PX4-Autopilot/Tools/simulation/gz/models/
cp -a config/gazebo_models/x500_perception \
  PX4-Autopilot/Tools/simulation/gz/models/
```

在已有自定义改动的工作区操作前先比较文件，不覆盖自己的修改。主项目中的车辆模型已位于 `ros2_ws/src/uav_learning/config/models/`，无需从个人 Gazebo 缓存获取。

## 4. 构建

在单独终端准备 PX4 构建环境，避免 ROS vendor 或 Windows Conda 路径干扰：

```bash
source scripts/px4_env.sh
make -C PX4-Autopilot px4_sitl_default
```

在 ROS 构建终端执行：

```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
cd ..
```

确认 `PX4-Autopilot/build/px4_sitl_default/bin/px4`、`MicroXRCEAgent` 和 ROS 包入口可用。监督器会检查仿真残留进程、感知导入和启动状态；不要绕过失败检查直接起飞。

## 5. Python 感知环境

ROS Python 包需要能被虚拟环境访问：

```bash
python3 -m venv --system-site-packages .venv-yolo
.venv-yolo/bin/python -m pip install \
  -r ros2_ws/src/uav_learning/requirements-yolo.txt
.venv-yolo/bin/python -m pip install scipy matplotlib pyulog pytest
```

`requirements-yolo.txt` 固定 Ultralytics 版本，但不是完整传递依赖锁文件。最终批次的 `freeze_manifest.json` 与每次 `implementation_snapshot.json` 记录实际版本，重新安装需核对；只安装这些依赖不能证明复现了原实验软件栈。

仓库上传选定的 `yolo11s.pt`，模型运行时不在线下载。核对根目录权重与最终批次 `frozen_files/yolo11s.pt` 的 SHA-256；其他轻量基线权重和 OpenVINO 导出产物未作为当前运行必需品上传。

## 6. 验证与结果

GUI 验证需要可用的本地图形会话或 WSLg。按照 [运行说明](vehicle_tracking.md) 启动新实验，输出使用新目录。此处准备步骤没有在干净新机器上执行完整闭环验证。

最终实验中的原始 JSON、CSV、图像、ULog、请求日志及冻结数据保留。普通 `ros2_ws/build/` 和 `install/` 不进入当前发布树；结果目录内部的冻结二进制与安装快照属于证据，不能因名称相同一并删除。

冻结协议里的原机器路径保持原样，用于解释当时执行环境。在新路径上运行新的批量实验时，应建立新参考与新冻结版本，不修改旧参数或快照来让哈希检查“通过”。
