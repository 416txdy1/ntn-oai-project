#!/usr/bin/env bash
set -euo pipefail
# Ubuntu 22.04；只安装发行版构建包，不克隆额外源码仓库。
sudo apt-get update
sudo apt-get install -y build-essential cmake ninja-build autoconf automake libtool pkg-config \
  flex bison python3 python3-yaml libssl-dev libsctp-dev libconfig-dev libfftw3-dev \
  libblas-dev liblapack-dev liblapacke-dev libgnutls28-dev libgcrypt20-dev zlib1g-dev \
  libelf-dev libdw-dev libunwind-dev libyaml-cpp-dev libboost-all-dev libreadline-dev \
  iproute2 iputils-ping
# Docker Engine 和 Compose v2 由管理员预先安装；本脚本不修改 Docker 配置。