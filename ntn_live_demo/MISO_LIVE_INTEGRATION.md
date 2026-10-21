# 四端口MISO与有声直播整合

本版本合并 `codex/ntn-live-video-demo-20261021` (`95207d3`) 与 `codex/handover-miso-integration` (`fc389626`)，两个来源分支保持不变。最新实测结果统一记录于 `MISO_LIVE_VALIDATION.md`；来源分支的报告保留为历史，不能替代本版本验证。

## 窗口入口

|命令|用途|
|---|---|
|`run_ntn_miso_video_audio.cmd`|四端口MISO有声直播，默认第一次切换|
|`run_ntn_miso_video_audio.cmd -Case full`|同一会话连续两次切换，615 IQ秒|
|`run_ntn_miso_more_handovers.cmd`|默认4轮，每轮重新建链并重放S06→S05|
|`run_ntn_miso_channel_comparison.cmd -Smoke -Repeats 1`|固定/正常/衰减三组短对照，各100 IQ秒|
|`run_ntn_miso_channel_comparison.cmd`|默认6轮长对照，每轮615 IQ秒，耗时取决于主机|
|`run_ntn_video_audio.cmd`及其他原CMD|保留SISO模式，但使用新的独立运行副本|

媒体配置沿用 `ntn_live_demo/media-source.example.json`：复制成被Git忽略的 `media-source.local.json` 后填本地视频路径；也可每次传 `-Source "D:\Media\video-with-audio.mp4"`。视频与音轨不随Git发布。保持播放器打开、可见、非静音，轮间由程序自动重启，不能关闭窗口来推进实验。

所有直播入口支持 `-ProjectRoot`、`-SpatialMode siso|miso4-subarray` 和 `-QdWorkers 1..8`。MISO入口显式选择 `miso4-subarray`，计算线程默认8；SISO固定1计算线程。不得仅凭请求参数认定四路已生效：前端实际端口与线程来自数值日志，最终验收还要求四路均在至少两个观测窗内发送非零IQ。

## 独立运行目录与构建

本机默认运行副本 `/home/kayoko/ntn-workspaces/ntn-live-miso`，与旧副本 `/home/kayoko/ntn-workspaces/ntn-quadriga-handover` 完全分开，包含独立 `.runtime/` 构建和 `.private/` 配置。启动器拒绝把受保护的旧副本当作新版本运行目录，并通过Git祖先关系确认新副本包含两个已发布来源提交。

在新的Linux文件系统副本中完成：

```bash
bash scripts/build.sh
python3 scripts/init_lab.py --profile integrated-handover
python3 scripts/build_upf_qfi.py --jobs 6
bash scripts/test_upf_qfi.sh
sudo python3 scripts/configure_upf_qfi.py
bash local_ntn/run_regressions.sh
bash scripts/test.sh
```

仅在尚未初始化的独立副本执行初始化；拒绝覆盖已有私密配置。UPF选择器仅针对停机后的该副本私有Compose，保留回退；仅合并补丁文件不会自动启用修复镜像。详细模型和镜像步骤见 `../docs/HANDOVER_MISO_MANUAL.md`。

新旧实验仍使用同一组隔离网络资源、端口和Windows播放器端口，必须顺序运行。不要为启动新实验而强行接管正在运行的其他实验，不使用全局pkill或WSL shutdown清理。

## 保留的物理和业务口径

轨迹、切换表、IQ采样时钟不变。MISO采用DL4Tx×1Rx、UL1Tx×4Rx，16×16阵列分四个8×8子阵，PDSCH单层，不等价于完整STK MVDR或256个独立RF端口。视频仍以墙钟实时循环转码成VP8+Opus，经过OAI UE隧道之后才中继到Windows播放器。

衰减对照只修改STK下行C/N，保留原四端口系数、时延和相对增益字节；派生包重新绑定trace、manifest、antenna及完成记录哈希。前端C/N是输入载噪比，不是实测SINR；请求模式与实际端口分开显示，物理数值独立审计后才允许Demo通过。

IQ与墙钟仍不是1:1。MISO计算更重，来源分支UDP验收不代表本机直播一定无卡顿；若对照门限未满足，保留INCONCLUSIVE或INVALID，不制造卡顿或放宽门限。
