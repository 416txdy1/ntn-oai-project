# zky 本地交付检查（2026-10-14）

本次沿用自包含源码归档 + 当前覆盖文件 + 固定示例的交付方式，补齐 STK 保存场景、迁移入口和复现文档。提交前基线为 `70a38b5`，本次只在本地 zky 提交，不推送。合作者须在之后发布后获取对应提交。

## 交付范围

- vendor/：固定版本 OAI、QuaDRiGa 2.8.1-0、ASN1C、SIMDe 源码、校验和与许可证，归档未改。
- oai_patch/current/ 与 quadriga/oai/：实际构建覆盖代码，未改变信号处理逻辑。
- examples/fdd-pass/：原 361 秒 trace 及匹配的双向 bundle，未改频率、种子或数据。
- STK_LEO_Constellation_20260923_train_v2/：场景、根对象、通信对象、单位配置及来源轨迹，保留原始字节。
- scripts/wsl_lab.ps1、scripts/wsl_lab.sh：已初始化的 WSL 项目的运行入口；本机路径在被忽略的 .runtime/wsl-target.json。
- scripts/install_deps.sh：声明同步所需的 rsync；本次未安装依赖。
- README.md、STK_SCENE.md、WINDOWS_WSL_RUN.md、MIGRATION_VALIDATION_20261014.md、PROJECT_PROGRESS_REPORT_20261012.md：启动流程、对齐前天线基线和历史实验结果。

.runtime/、.private/、本次 .planning/ 工作记录、原始 modem 日志及 STK 工作区布局不进入提交；既有历史中已跟踪的旧规划材料保留。没有对其他仓库执行同步、构建、提交或清理。

## 接收者使用

按 DEBUG_ZKY.md 克隆 zky，在 WSL2 Ubuntu 22.04 的 Linux 文件系统安装系统依赖，执行 scripts/build.sh、scripts/check_delivery.py、scripts/test.sh，首次执行 scripts/init_lab.py 生成本机随机凭据，再启动核心网和 preflight。系统软件包与 Docker 镜像仍需获取。

示例回放无需 MATLAB/STK；打开场景、重新生成 trace/QD 需要对应软件及许可。当前只保存天线对齐前基线：STK 卫星 16×16 阵列、地面端 Isotropic；QD 两端 omni。后续对齐继续在 zky，变更天线并重导出后须成对更新 trace 与 DL/UL bundle，核对方向、频率及 SHA256，避免重复叠加绝对天线增益。

## 本次验证

从 Git 暂存树 `81c350c1f1ae37df6abd0822e7cffa59de2bea45` 用 git archive 导出独立快照，放在本仓库被忽略的 `.runtime/zky-delivery-audit/snapshot-checked/`。本次使用 Ubuntu-22.04 的 `/usr/bin/python3` 及已有系统依赖，没有安装新依赖。完整命令/输出保留在本机 `.planning/2026-10-14-zky-delivery-audit/terminal.log`。

| 命令/检查 | 结果 |
|---|---|
| `python3 scripts/check_delivery.py`（独立快照） | 0；4 份源码归档 SHA256、DL/UL 示例及路径检查通过 |
| STK 保存对象的递归 SubObjects 文件检查 | 22 个唯一对象定义完整，所需图形副本存在；保存对象字节一致，历史 CSV 换行规范化后文本一致 |
| 只读 Linux 运行树与交付源码核对 | 2366 个归档 C/C++ 文件、19 个覆盖文件一致；覆盖文件允许历史 LF/CRLF 差异 |
| `bash scripts/test.sh`（独立快照，环境覆盖见下文） | 0；全部回归通过，包括 `python3 local_ntn/test_trace_validation.py`、`python3 local_ntn/test_real_iq.py` |
| 双向 C reader 与 ASan/UBSan adapter | 各 723 个快照/中点通过，最大卷积误差约 1.82e-12 |
| `python3 scripts/prepare_sources.py`（独立快照） | 0；用交付归档完整解包并应用覆盖文件 |
| `python3 scripts/init_lab.py --subnet-octet 79 --prefix ntn-audit`（独立快照） | 0；首次本机配置生成成功，无密钥输出，没有启动核心网 |
| `bash -n scripts/*.sh` 对应逐文件检查及 `bash -n local_ntn/local_network.sh` | 0 |
| PowerShell Parser 对 wsl_lab.ps1 / debug_console.ps1 的语法检查 | 无错误 |
| 新增文件凭据/私钥模式检查、暂存路径审查、`git diff --cached --check` | 通过；没有新增私有凭据或运行日志 |

完整回归的精确外层命令为：

```powershell
wsl.exe -d Ubuntu-22.04 -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/2026-10-14-zky-delivery-audit/run_snapshot_tests.sh
```

该本机审计脚本在独立快照执行 `bash scripts/test.sh`，在 `source scripts/env.sh` 后把 OAI_REPO、OAI_BUILD_REPO 和 OAI_BUILD_DIR 覆盖为已逐文件核对的 `/home/duyaya/OAI/self-contained-test/.runtime/oai` 及其构建目录，仅只读复用真实编译参数和生成头文件；测试重新编译实际 IQ/QD 路径，所有临时编译输出写入本仓库 `.runtime/zky-delivery-audit/tmp/`，Python 禁止生成缓存。首次审计专用前缀超过 16 字符而被初始化参数校验拒绝，改用合法 `ntn-audit` 后独立重跑初始化成功；回归无需重复。

完成后仅补充交付报告、协作指南和进展报告的文档格式，最终暂存树与被测树的差异只涉及这三份文档。未在全新系统重装依赖或重新全量构建 OAI；没有调用会同步/改写外部项目的 wsl_lab sync/build。历史构建与业务结果见 MIGRATION_VALIDATION_20261014.md。本次没有启动 STK GUI 加载场景或重导出，没有重跑完整业务，既有末段失步仍是已知问题。
