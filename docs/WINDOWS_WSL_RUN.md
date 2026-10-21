# Windows 源码与 WSL 实验运行

## 首次使用

合作者先按 `README.md` / `docs/DEBUG_ZKY.md`，在 WSL2 Ubuntu 22.04 的 Linux 文件系统克隆 zky、安装依赖、构建并初始化本机 `.private/`。不要复制其他人的凭据。此 PowerShell 入口用于已经完成初始化的 Linux 项目，不代替首次安装。

在 Windows 主仓库打开 PowerShell 7，设置本机路径；下例 `/home/你的用户名/ntn-oai-project` 必须改为已配置的实际 Linux 项目：

```powershell
$runtimeProject = '/home/你的用户名/ntn-oai-project'
.\scripts\wsl_lab.ps1 -Action build -RuntimeProject $runtimeProject
.\scripts\wsl_lab.ps1 -Action test -RuntimeProject $runtimeProject
.\scripts\wsl_lab.ps1 -Action up -RuntimeProject $runtimeProject
.\scripts\wsl_lab.ps1 -Action preflight -RuntimeProject $runtimeProject
.\scripts\wsl_lab.ps1 -Action smoke-static -RuntimeProject $runtimeProject
.\scripts\wsl_lab.ps1 -Action smoke-dynamic -RuntimeProject $runtimeProject
.\scripts\wsl_lab.ps1 -Action full-pass -RuntimeProject $runtimeProject -MaxWallSeconds 1800
.\scripts\wsl_lab.ps1 -Action stop -RuntimeProject $runtimeProject
```

每一步确认 `$LASTEXITCODE` 为 0，再进行下一步；full-pass 当前已知可能失败，应保留失败结果。默认发行版是 Ubuntu-22.04，可通过 `-Distribution` 指定。入口使用 WSL root 管理网络和本机 `/usr/bin/python3`，不依赖 Windows Conda。

`build` 先同步源码再执行 `JOBS=4 bash scripts/build.sh`；`test` 执行 `bash scripts/test.sh`。其他动作使用最后同步的 Linux 副本，不会自动构建。源码修改后重新 build/test。WSL 侧同步依赖 rsync，`scripts/install_deps.sh` 已声明。

`up` 启动 `.private/settings.json` 对应的核心网并准备 iperf；短测和全程测试自动管理自己启动的 modem。`stop` 还会停止该核心网，不删除数据库卷。`status` 只查询容器和 modem 状态。不要并行运行两轮实验，保持电脑及 WSL 运行。

## 可选本机路径配置

也可在 Windows 仓库 `.runtime/wsl-target.json` 保存以下配置，之后省略 `-RuntimeProject`：

```json
{"runtime_project":"/home/你的用户名/ntn-oai-project"}
```

`.runtime/` 被 Git 忽略。WSL 目标须在 Linux 文件系统，不能是 `/mnt/` 下的 Windows 目录。CMake 缓存带绝对路径，不应直接搬动已构建的 Linux 项目。

## 同步范围与实验基线

`sync`/`build` 从 Git 跟踪列表复制 `scripts`、`local_ntn`、`oai_patch/current`、`quadriga`、`examples`、`configs`、`vendor`、`docs` 和根目录说明文件。新文件须先纳入 Git 才会同步。Windows STK 场景留在 Windows 源码目录，Linux 示例回放使用 examples。

不复制 `.git`、`.private`、`.planning`、生成配置、进程状态和原始日志，不删除目标文件；不同版本源码先备份到目标 `.runtime/source-backups/`。同步/构建及短测遇到已有 modem 均拒绝接管。Git 仅用于列文件，safe.directory 只在单次命令生效。

基线固定为 hermite 插值、关闭 blend timing assist，使用既有 361 秒输入及 rate=1。全程测试仍有末段失步；不能把到达轨迹末端当成业务通过。该入口不自动改变实验输入或验收标准。

## 结果与历史记录

汇总报告位于 WSL 目标 `.runtime/reports/`；原始 modem 日志仅留本机，不分享 `.private/` 或 UE 原始日志。数值验算在目标目录执行：

```bash
source scripts/env.sh
python3 local_ntn/audit_runtime_numbers.py --run-dir "$PWD" --labels 本轮label
```

2026-10-14 原机器迁移、短测和完整实验结果见 `MIGRATION_VALIDATION_20261014.md`。其中的机器路径是历史证据，不是合作者必须使用的路径。