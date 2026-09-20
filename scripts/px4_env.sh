#!/usr/bin/env bash

# ============================================================
# PX4 / Gazebo clean build environment
#
# Usage:
#   source ~/ROS2_manmade/scripts/px4_env.sh
#
# Purpose:
#   Remove ROS 2 Jazzy vendor paths and Windows Anaconda paths
#   from the current shell before compiling PX4 / Gazebo.
# ============================================================


remove_path_prefix()
{
    local original="$1"
    shift

    local result=""
    local item=""
    local prefix=""
    local remove_item=0

    IFS=':' read -ra items <<< "$original"

    for item in "${items[@]}"; do

        if [[ -z "$item" ]]; then
            continue
        fi

        remove_item=0

        for prefix in "$@"; do
            if [[ "$item" == "$prefix"* ]]; then
                remove_item=1
                break
            fi
        done

        if [[ $remove_item -eq 0 ]]; then

            if [[ -z "$result" ]]; then
                result="$item"
            else
                result="$result:$item"
            fi

        fi
    done

    printf '%s' "$result"
}


ROS_PREFIX="/opt/ros/jazzy"
WINDOWS_ANACONDA="/mnt/c/Users/yjh/anaconda3"


# ------------------------------------------------------------
# Clean executable search path
# ------------------------------------------------------------

export PATH="$(
    remove_path_prefix \
        "$PATH" \
        "$ROS_PREFIX" \
        "$WINDOWS_ANACONDA"
)"


# ------------------------------------------------------------
# Clean library / package search paths
# ------------------------------------------------------------

export LD_LIBRARY_PATH="$(
    remove_path_prefix \
        "${LD_LIBRARY_PATH:-}" \
        "$ROS_PREFIX" \
        "$WINDOWS_ANACONDA"
)"

export PYTHONPATH="$(
    remove_path_prefix \
        "${PYTHONPATH:-}" \
        "$ROS_PREFIX" \
        "$WINDOWS_ANACONDA"
)"

export PKG_CONFIG_PATH="$(
    remove_path_prefix \
        "${PKG_CONFIG_PATH:-}" \
        "$ROS_PREFIX" \
        "$WINDOWS_ANACONDA"
)"


# ------------------------------------------------------------
# Remove ROS 2 environment
# ------------------------------------------------------------

unset ROS_DISTRO
unset ROS_VERSION
unset ROS_PYTHON_VERSION
unset ROS_LOCALHOST_ONLY

unset AMENT_PREFIX_PATH
unset COLCON_PREFIX_PATH
unset CMAKE_PREFIX_PATH


# ------------------------------------------------------------
# Remove Conda environment
# ------------------------------------------------------------

unset CONDA_PREFIX
unset CONDA_DEFAULT_ENV
unset CONDA_EXE
unset CONDA_PYTHON_EXE
unset CONDA_SHLVL

unset _CE_CONDA
unset _CE_M


# ------------------------------------------------------------
# Remove CMake package hints that could point to Conda
# ------------------------------------------------------------

unset Protobuf_DIR
unset protobuf_DIR

unset ZeroMQ_DIR
unset absl_DIR
unset utf8_range_DIR
unset yaml_DIR


# Refresh executable lookup cache
hash -r


echo
echo "========================================"
echo " PX4 clean environment loaded"
echo "========================================"
echo

echo "python3 : $(command -v python3)"
echo "cmake   : $(command -v cmake)"
echo "protoc  : $(command -v protoc)"
echo "gz      : $(command -v gz)"

echo
echo "ROS_DISTRO=${ROS_DISTRO:-not_set}"
echo "CMAKE_PREFIX_PATH=${CMAKE_PREFIX_PATH:-not_set}"
echo "AMENT_PREFIX_PATH=${AMENT_PREFIX_PATH:-not_set}"
echo "CONDA_PREFIX=${CONDA_PREFIX:-not_set}"

echo