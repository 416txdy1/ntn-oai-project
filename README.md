# NTN OAI：单仓库 STK + QuaDRiGa 回放调试

本仓库 zky 分支保存当前 OAI/STK/QuaDRiGa 集成源码、构建所需源码归档、真实 FDD 示例和无凭据核心网模板。接收者只需获取本仓库，无需再 clone OAI、QuaDRiGa、ASN1C 或 SIMDe 仓库。

系统依赖仍需安装：Ubuntu 22.04/WSL2、C/C++ 工具链、Docker Engine + Compose v2。核心网使用 Docker 镜像（首次启动可能下载）。示例回放不需要 MATLAB/STK；重新生成信道需 MATLAB 和 STK 导出输入。这里不承诺离线安装系统依赖或支持未验证的平台。

## 布局

| 目录 | 用途 |
|---|---|
| `vendor/` | 固定版本源码压缩快照、SHA256、许可证；无构建二进制、无 Git 子模块 |
| `oai_patch/current/` | 当前 OAI 修改文件，按 OAI 原始相对路径保存 |
| `quadriga/oai/` | QD C reader/adapter 的唯一维护入口 |
| `quadriga/matlab/` | STK→QD 转换、归一化及 FDD 导出脚本 |
| `examples/fdd-pass/` | 共用的 362 快照 trace 与历史全向 DL/UL 对照 |
| `examples/fdd-pass-array/` | 当前默认：卫星 16×16 阵列、地面全向的单波束 DL/UL bundle |
| `STK_LEO_Constellation_20260923_train_v2/` | 保存的 STK 场景、通信对象及轨迹来源；见 [场景说明](docs/STK_SCENE.md) |
| `configs/core/` | 无凭据的 5GC、UE 和数据库表结构模板 |
| `scripts/` | 解包、构建、初始化、核心网管理和回归入口 |
| `.runtime/` | 本地解包源码、构建目录、工具；自动生成，不提交 |
| `.private/` | 本地随机凭据和核心网配置；自动生成，不提交 |

旧 `oai_patch/` 根目录、`local_ntn/original/`、`local_ntn/staged/` 作为历史材料保留，不是当前部署源。不要手动用它们覆盖新 OAI。

> **调试版本状态：** 完整 361 秒业务验收仍未通过，末段有失步。其他成员请先阅读 [zky 协作调试指南](docs/DEBUG_ZKY.md)，按其中步骤配置和复现；实验修正默认关闭。

2026-10-14 默认 QuaDRiGa 天线已切换为卫星 16×16 / 地面全向，原全向数据保留。此为实验模型变更；实现、复现及与 STK MVDR 的差异见 [天线对齐说明](docs/ANTENNA_ALIGNMENT_20261014.md)。历史完整业务结果属于旧全向基线。

## 快速开始

Windows 用户先按下面步骤初始化 WSL 项目；之后可从 PowerShell 调用已配置的运行副本，见 [Windows/WSL 运行入口](docs/WINDOWS_WSL_RUN.md)。

将工作目录放在 WSL 的 Linux 文件系统中（例如 `~/ntn-oai-project`），避免在 `/mnt/c`、`/mnt/e` 编译大量 ASN.1 源码。

```bash
bash scripts/install_deps.sh
bash scripts/build.sh
python3 scripts/check_delivery.py
bash scripts/test.sh
python3 scripts/init_lab.py
source scripts/env.sh
bash scripts/core.sh up
bash scripts/prepare_iperf.sh
python3 local_ntn/experiment.py preflight --rate 1
sudo --preserve-env=OAI_REPO,OAI_BUILD_DIR,OAI_STK_TRACE,OAI_UE_CONFIG,OAI_QD_DL_CHANNEL,OAI_QD_UL_CHANNEL,OAI_AMF_IP,OAI_GNB_IP_CIDR,OAI_EXT_DN_IP,OAI_EXT_DN_CONTAINER python3 local_ntn/experiment.py start --rate 1 --label manual-dynamic
```

完整的 PDU 等待、ping、双向流量、停止命令见 [手动运行指南](local_ntn/MANUAL_RUN.md)。使用 Docker 所需权限由本机管理员配置；也可在 root 终端中执行初始化及运行步骤。不要将 `.private/` 提交或分享。

## zky-miso 多端口入口

`source scripts/env.sh` 仍选择原 SISO。多端口实验需显式选择下表环境；下行均为单数据层，UE 保持 1 Tx / 1 Rx，上行对应 1×N SIMO。

| 场景 | 环境入口 | 数据目录 | 验收记录 |
|---|---|---|---|
| 2×1 独立 RF 通道 | `scripts/env_miso.sh` | `examples/fdd-miso/` | [2×1 验收](docs/MISO_2X1_END_TO_END_20261015.md) |
| 4×1 独立 RF 通道 | `scripts/env_miso4.sh` | `examples/fdd-miso4/` | [4×1 验收](docs/MISO_4X1_VALIDATION_20261015.md) |
| 16×16 阵列 → 4 个 8×8 子阵端口 → 4×1 | `scripts/env_subarray4.sh` | `examples/fdd-miso4-subarray/` | [子阵映射与验收](docs/MISO_SUBARRAY4_VALIDATION_20261015.md) |

在已初始化的 Linux 实验副本中，以 root shell 运行：

```bash
source scripts/env_subarray4.sh
python3 scripts/validate_spatial.py --ports 4
```

该入口在同一活动会话内执行静态/动态 PDU、ping、双向 UDP 和独立物理量验算，只管理自己启动的服务。2×1 使用对应环境并传 `--ports 2`。仅做离线回归可运行 `OAI_SPATIAL_MODE=miso4-subarray bash scripts/test.sh`。Windows 源码先通过现有 WSL 同步入口同步；不要用仅支持默认 SISO 的旧 smoke 包装命令来代替上述多端口入口。

四子阵保留四路 IQ，不合成为单 RF 端口；256 个物理阵元不等于 256 个独立 RF 通道。以上有界业务测试不代表完整过境、绝对 EIRP 或容量对比验收。

精度提示：原 1 秒快照不能视为通过 4.5 MHz 带内 1% 频响验收。逐采样运行时修复、自适应真实 QD 生成、独立参考验算及覆盖范围见 [信道精度修复记录](docs/MISO_FIDELITY_20261016.md)。既有示例数据保留供历史对照。

## 源码变更与许可

OAI 来源版本、排除项见 `vendor/source-manifest.json`。修改 OAI 请编辑 `oai_patch/current/`；QD C 模块编辑 `quadriga/oai/`，然后重新运行 `scripts/build.sh`。解包树是生成产物，重建时会同步这些覆盖文件。

QuaDRiGa 随附源码许可证要求非商业使用，完整条款见 `vendor/QuaDRiGa-LICENSE.txt`。OAI 许可证见 `vendor/OAI-LICENSE` 和归档中的 LICENSES/NOTICE；ASN1C、SIMDe 保留各自源码版权声明。不要把整个仓库误认为采用单一许可证。

已知研究限制：1 秒 QD 快照不足以保证快速残余 Doppler 的采样精度；复系数线性插值中点功率不严格为 1；低速 UDP 验证不代表最大容量或完整过境稳定性。