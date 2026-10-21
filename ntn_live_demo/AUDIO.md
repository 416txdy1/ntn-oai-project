# 用户视频有声直播

本机双击上一级 `run_ntn_video_audio.cmd`，默认使用 `media-source.local.json` 配置的《爱乐之城》视频，运行首次卫星伪切换场景。控制台显示日志，独立 Windows Edge 窗口播放音视频和展示指标。默认音量15%，请检查自己的输出设备和系统音量。

```cmd
run_ntn_video_audio.cmd
run_ntn_video_audio.cmd -Case static
run_ntn_video_audio.cmd -Case full
run_ntn_live_demo.cmd -Source "D:\视频目录\视频.mp4"
```

`full` 为双切换入口，本次尚未完成有声双切换实测。`-Headless` 仅适用于原有合成画面；有声源始终使用可见 Windows 播放器。首次准备依赖可加 `-Prepare`；本机依赖已准备好。运行前停止其他 OAI 实验，保留控制台与播放器；Ctrl+C 后等待清理完成。

源文件只读，按真实墙钟速度从头循环推送，不保存转码文件。实际输入为 H264 High、1224×480、约23.98fps，AAC LC、48kHz双声道，约4分44秒；文件名中的1080p不是实际分辨率。每次测试前后检查源文件 SHA256。

当前输出为 VP8（宽640、等比例、15fps、目标250kbit/s）和 Opus（48kHz双声道、64kbit/s）。这是实时转码直播，未测试 H264 直接透传。

媒体路径：源视频 → FFmpeg → ext-DN MediaMTX → WebRTC/UPF/gNB/RFsim → UE 的 oaitun_ue1 → UE 内 MediaMTX 中继 → 本机 TCP 桥 → Windows Edge。音视频都先穿过 OAI，再交给 Windows 播放；没有另从本地文件播放音轨。报告同时核验 UE 路由、隧道媒体包和中继入流增长。

本机 WSLg 音频曾出现持续收包但播放时钟停滞，局部音频服务参数和 WebAudio 均未通过完整测试，因此最终使用 Windows 原生输出。未修改系统音频设置，无需重启 WSL；播放器使用临时浏览器配置，不使用个人浏览器资料。

持续记录视频帧、码率、缓冲、冻结和音频样本、能量、补偿及输出样本。音频通过要求轨道存活、样本与字节增长、播放器非静音，并核对48kHz样本进度/墙钟比例在0.8–1.2之间；切换窗口也检查进度。样本可能包含补偿，这些指标不能代替扬声器听感检查。

浏览器事件经宿主机单调时钟映射到 IQ/STK 时间，对齐卫星切换；冻结、缓冲和速率仍按墙钟计量。Windows 统计来自 UE 中继之后，不能直接当作无线链路原始指标；额外中继和 TCP 也会增加时延。请求200ms缓冲只是目标，实测缓冲存在波动。已通过静态和首次切换的路径、持续音频、窗口覆盖检查，但仍有视频冻结，见 `AUDIO_RESULTS.md`。

原 `run_ntn_live_demo.cmd` 无参数时仍运行无声合成画面。新 Demo 使用独立工具目录、互斥锁和本轮核心网，结束后清理；未修改旧平台源码、二进制和配置模板。它与原平台不能同时运行。

报告及私有日志保存在 Linux 独立平台 `.private/<run-id>/`；Windows 截图位于 `C:\Users\WSZ\.codex\visualizations\2026\09\29\01a0ec57-7509-74c2-9656-23dc0cdc5f07\ntn-audio-runs\<run-id>\`。不要公开原始 UE 日志、源视频或含个人路径的 `media-source.local.json`。
