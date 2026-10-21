# 直播测试版本发布验收（2026-10-21）

分支：`codex/ntn-live-video-demo-20261021`。基底：`65bc517a0ec5bfb4e9e2f665876ea5d188cac1a5`。测试从本候选工作树加载直播代码，OAI仍使用既有隔离Linux运行平台及其准确二进制。未重新构建或替换旧平台。

## 离线验证

候选工作树Windows路径为 `C:\Users\WSZ\.codex\worktrees\ntn-quadriga-handover\OAI调研`，下文 `$publish` 指该目录，`$source` 是用户本地含音频视频的绝对路径（不发布该配置）。

```powershell
wsl.exe -d Ubuntu-22.04 --exec python3 -B -m unittest discover -s '/mnt/c/Users/WSZ/.codex/worktrees/ntn-quadriga-handover/OAI调研/ntn_live_demo' -p 'test_*.py'
wsl.exe -d Ubuntu-22.04 --exec python3 -B '/mnt/c/Users/WSZ/.codex/worktrees/ntn-quadriga-handover/OAI调研/ntn_test_launcher/test_launcher.py'
```

直播Python测试最终25项通过（含5项WSL启动故障保护）；启动器8项通过。使用实验机捆绑Windows Node分别运行 `ntn_live_demo/test_dashboard.cjs` 与 `test_dashboard_ui.cjs`，13项诊断规则及DOM/图表/失效保护/响应式验证通过。

在 `/home/kayoko/ntn-workspaces/ntn-quadriga-handover` 内执行的准确回归命令：

```bash
bash local_ntn/run_regressions.sh
bash scripts/test.sh
```

多轮测试前分别exit=0，8.0秒、81.1秒；对照测试前再次exit=0，9.0秒、81.9秒。派生信道预检以及下行/上行实际C端读取均exit=0。

## 四轮有声直播重放：PASS 4/4

系列：`handover-replay-20261021-115208-33f291`，每轮65 IQ秒，均确认S06→S05的prepare/blend/complete、音频进度、视频推进和平台保护。实际完成IQ为44.999595–44.999596。

|轮次|私有报告标识|解码帧|冻结次数|冻结总墙钟秒|音频采样推进比|
|---|---|---:|---:|---:|---:|
|1|live-firsthandover-20261021-115209-10d128|1267|6|3.459|0.999964|
|2|live-firsthandover-20261021-115436-37ad23|1249|6|3.816|1.000017|
|3|live-firsthandover-20261021-115653-fdba9a|1105|16|10.680|0.999990|
|4|live-firsthandover-20261021-115916-b3822c|1357|2|0.703|0.999993|

这是4次独立建链的同一切换片段，不是连续跨4颗卫星。未以轮间重连充当切换。

## 三组短对照：SUPPORTED

系列：`causal-20261021-120227-245a27`，每组100 IQ秒，固定/正常/干预各1次；干预仅改变DL输入C/N，在70–82 IQ秒降16 dB。

|组别|干预窗UE入流 kbit/s|干预窗播放 fps|响应窗冻结秒|
|---|---:|---:|---:|
|fixed|331.03|14.80|0.000|
|normal|315.56|15.00|0.000|
|intervention|78.46|3.73|5.221|

物理C/N差异、UE入流下降、播放恶化、推流持续实时、完整覆盖、无计数器重置和原平台保护全部满足严格门限，进程exit=0。该结论证明本次受控IQ信道干预的影响；响应尾窗单独判定为INCONCLUSIVE，保留原判定。未证明每次普通切换卡顿都由切换引起，亦未运行默认6轮长时对照。

私有单轮标识：`live-static-20261021-120359-9f2d87`、`live-firsthandover-20261021-120654-e93552`、`live-firsthandover-20261021-121013-90e084`，三轮Demo均PASS。

## 同一连接内两次切换长测：PASS

报告：`live-full-20261021-121438-a36438`，目标615 IQ秒。首次S06→S05在约45 IQ秒完成，第二次S05→S04在约600 IQ秒完成；两端均记录prepare/blend/complete，之后回到steady继续业务。

- 共13477解码帧；14次冻结、总7.293墙钟秒，非零卡顿承诺。
- 音频测量覆盖901.997墙钟秒，采样推进比0.999959，最终非静音。
- 首次切换分析窗增加161视频帧、671520音频采样；第二次增加208帧、672000采样。两个窗口各15个采样点。
- UE隧道抓包、UE中继入流增长及Windows连接路径全部通过。
- OAI源/二进制摘要、原片摘要保持不变，原平台保护通过，清理无错误。

## 启动环境问题及修复后直接入口

本机WSL存在Windows PE处理器丢失：修复前直接启动在打开Node时出现Exec format error，相关失败报告保留，未算PASS。已完成的四轮/短对照/长测使用同一WSL会话内恢复标准 `:WSLInterop:M::MZ::/init:PF` 注册后运行，脚本参数分别为：

```bash
python3 -B -u ntn_live_demo/replay_handovers.py --rounds 4 --skip-regressions --source "$source_linux"
python3 -B -u ntn_live_demo/causal.py --smoke --repeats 1 --source "$source_linux"
python3 -B -u ntn_live_demo/demo.py --case full --skip-regressions --source "$source_linux"
```

最终代码将这项检查移到核心网部署之前，仅在明确的WSL内核、存在/init、缺失标准处理器且错误确为ENOEXEC时恢复会话内注册，然后再次验证Node。已有处理器不被覆盖，不修改任何持久系统配置；试验中新增的持久配置已撤回。

修复后不使用诊断包装，直接运行CMD调用的PowerShell入口：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$publish\ntn_live_demo\launch.ps1" -Case firsthandover -SkipRegressions -Source $source
```

报告 `live-firsthandover-20261021-124025-6ab667`：PASS，实际完成一次S06→S05切换、音视频与原平台保护门限通过，exit=0。会话内恢复提示可见。后续改动仅涉及启动前检查及文档，信道、媒体和验收逻辑保持此次物理测试版本。

## 边界与证据

音频推进含补偿采样，不代表声学听感测试。C/N为输入载噪比，非UE实测SINR；IQ/STK与墙钟没有改成1:1。视频以墙钟实时循环VP8+Opus转码，输入H264/AAC原片只读。前端显示与实际日志统一时间映射，但画面可能受缓冲延后。

私有原始报告位于隔离平台 `.private/<报告标识>/report.json`，不随Git发布。截图、原片、真实订户配置、原始UE日志、运行目录及本地媒体JSON全部排除。历史失败/未完成报告保留原意，不覆盖成PASS。
## 发布前原平台业务复测：PASS

在隔离Linux工作目录运行：

```bash
sudo python3 scripts/original_platform_check.py short-run --snapshot /home/kayoko/ntn-workspaces/ntn-quadriga-handover/.private/live-firsthandover-20261021-124025-6ab667/original-before.json --tag live-release-20261021
```

exit=0；Ping发送30/接收30，上行UDP丢失0/总130，下行丢失0/总131；保护文件差异列表为空。结束后无运行中的nr-softmodem/nr-uesoftmodem，隔离核心网容器数0，持久互操作配置试验文件不存在。