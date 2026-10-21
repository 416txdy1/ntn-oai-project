# 多轮切换入口验证（2026-10-21）

新增 `run_ntn_more_handovers.cmd`，默认4轮，支持 `-Rounds 1..8`。采用已验证的原firsthandover输入，每轮独立接入、65 IQ秒；不修改轨迹、QD数据或IQ时钟，也不把轮间重连计为切换。

PowerShell启动器解析及播放器内联JS语法检查通过。`python3 -B -m unittest discover -s /mnt/d/实验室学习工作/杂活/雄安/OAI调研/ntn_live_demo -p 'test_*.py'`：20项通过，含5项切换计数检查，拒绝仅steady标签变化、未完成阶段、错误顺序，重复完成日志只计一次。

实际命令：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ntn_live_demo\launch_replay.ps1 -Rounds 2
```

Series：`handover-replay-20261021-105440-fc70cd`，整体exit=0、PASS，2/2轮通过。

启动时在Linux隔离平台 `/home/kayoko/ntn-workspaces/ntn-quadriga-handover` 执行 `bash local_ntn/run_regressions.sh`：exit=0、8.5秒；`bash scripts/test.sh`：exit=0、81.8秒。记录位于 `.private/<series-id>/`。

|轮次|run-id|UE切换完成IQ|解码帧|累计冻结次数/墙钟秒|音频门限|保护/源文件|
|---|---|---:|---:|---|---|---|
|1|live-firsthandover-20261021-105609-1a1347|44.999596|1256|6 / 5.115|通过|全部通过|
|2|live-firsthandover-20261021-105834-d1a5a5|44.999595|1322|10 / 4.616|通过|全部通过|

两轮UE日志均有prepare→blend→complete，卫星从S06变为S05；每轮完成后媒体、调制解调器和核心网均清理，再自动进入下一轮。两次原平台、运行源码/二进制、原片摘要均不变。结束后无调制解调器、网络命名空间或该隔离项目容器残留。

本次实际验证两轮；默认四轮及更多轮数使用同一循环机制，尚未完整执行四轮或八轮。PASS不代表零冻结，也不代替自然双切换或因果对照验收。播放器标题“已观测”是阶段完成观测，摘要中的通过轮数另外要求音视频、路径及保护门限全部通过。

可读摘要：`ntn_live_demo/replay-results/handover-replay-20261021-105440-fc70cd/RESULTS.md`。原始UE日志仍在Linux私有目录，未发布或复制到摘要。
