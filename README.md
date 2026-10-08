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
| `examples/fdd-pass/` | 已验算的 362 快照 trace 与 DL/UL bundle |
| `configs/core/` | 无凭据的 5GC、UE 和数据库表结构模板 |
| `scripts/` | 解包、构建、初始化、核心网管理和回归入口 |
| `.runtime/` | 本地解包源码、构建目录、工具；自动生成，不提交 |
| `.private/` | 本地随机凭据和核心网配置；自动生成，不提交 |

旧 `oai_patch/` 根目录、`local_ntn/original/`、`local_ntn/staged/` 作为历史材料保留，不是当前部署源。不要手动用它们覆盖新 OAI。

> **调试版本状态：** 完整 361 秒业务验收仍未通过，末段有失步。其他成员请先阅读 [zky 协作调试指南](docs/DEBUG_ZKY.md)，按其中步骤配置和复现；实验修正默认关闭。

## 快速开始

将工作目录放在 WSL 的 Linux 文件系统中（例如 `~/ntn-oai-project`），避免在 `/mnt/c`、`/mnt/e` 编译大量 ASN.1 源码。

```bash
bash scripts/install_deps.sh
bash scripts/build.sh
python3 scripts/init_lab.py
source scripts/env.sh
bash scripts/core.sh up
bash scripts/prepare_iperf.sh
python3 local_ntn/experiment.py preflight --rate 1
sudo --preserve-env=OAI_REPO,OAI_BUILD_DIR,OAI_STK_TRACE,OAI_UE_CONFIG,OAI_QD_DL_CHANNEL,OAI_QD_UL_CHANNEL,OAI_AMF_IP,OAI_GNB_IP_CIDR,OAI_EXT_DN_IP,OAI_EXT_DN_CONTAINER python3 local_ntn/experiment.py start --rate 1 --label manual-dynamic
```

完整的 PDU 等待、ping、双向流量、停止命令见 [手动运行指南](local_ntn/MANUAL_RUN.md)。使用 Docker 所需权限由本机管理员配置；也可在 root 终端中执行初始化及运行步骤。不要将 `.private/` 提交或分享。

## 源码变更与许可

OAI 来源版本、排除项见 `vendor/source-manifest.json`。修改 OAI 请编辑 `oai_patch/current/`；QD C 模块编辑 `quadriga/oai/`，然后重新运行 `scripts/build.sh`。解包树是生成产物，重建时会同步这些覆盖文件。

QuaDRiGa 随附源码许可证要求非商业使用，完整条款见 `vendor/QuaDRiGa-LICENSE.txt`。OAI 许可证见 `vendor/OAI-LICENSE` 和归档中的 LICENSES/NOTICE；ASN1C、SIMDe 保留各自源码版权声明。不要把整个仓库误认为采用单一许可证。

已知研究限制：1 秒 QD 快照不足以保证快速残余 Doppler 的采样精度；复系数线性插值中点功率不严格为 1；低速 UDP 验证不代表最大容量或完整过境稳定性。