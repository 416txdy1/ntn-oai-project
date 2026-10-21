发布版的媒体配置和实验机路径要求见 [RELEASE.md](RELEASE.md)。仓库不包含个人媒体路径配置，先复制示例并设置自己的视频，或使用 -Source 参数。

# 隔离低缓冲直播 Demo

用户视频含音频的入口为上一级 `run_ntn_video_audio.cmd`，使用 Windows 原生播放器。见 [有声说明](AUDIO.md) 和 [实测结果](AUDIO_RESULTS.md)。下文介绍原有无声合成画面入口。

播放器现支持 [实时信道指标与卡顿关联提示](LIVE_INDICATORS.md)，长时对照仍使用 `run_ntn_channel_comparison.cmd`。

希望少等steady、多看几次切换，可用 `run_ntn_more_handovers.cmd`，见 [多轮重放说明](MORE_HANDOVERS.md)。每轮重新连接，不代表同一会话的连续多星切换。

Windows双击上一级`run_ntn_live_demo.cmd`。默认开启可见的WSLg浏览器，运行第一次卫星切换场景。
请保持播放器可见；其他测试和原平台必须事先停止。需要时输入WSL用户的sudo密码。

```cmd
run_ntn_live_demo.cmd
run_ntn_live_demo.cmd -Case static
run_ntn_live_demo.cmd -Case full
```

默认每次先运行既有trace/IQ及脚本回归。对同一未改动运行版本进行连续Demo时，可加
`-SkipRegressions`复用已记录的离线检查；不会改变业务判定。自动化无窗口测试可加`-Headless`。

依赖独立安装在`/home/kayoko/ntn-live-demo-tools`，包括MediaMTX v1.21.2、Playwright1.55.0
及其Chromium、imageio-ffmpeg0.6.0携带的FFmpeg。首次普通用户准备使用`-Prepare`。
准备程序只读复用现有测试环境pip引擎，安装到新的user-venv，不运行get-pip，不使用apt安装。
下载HTTPS来源和包/归档SHA256单独记录；不声称已验证发布者签名。
当前入口针对已配置的Ubuntu-22.04、kayoko用户与独立Linux平台目录；不是任意机器的通用安装器。

媒体路径：FFmpeg实时测试画面 → ext-DN网络空间内MediaMTX → UDP/WebRTC → UPF/gNB/RFsim →
UE oaitun_ue1 → UE命名空间内普通用户Chromium。媒体服务与浏览器均降权运行，Chromium启用沙箱。
服务器明确发布192.168.71.135:8189候选地址，不使用外部STUN/TURN。
控制页面与指标服务仅在UE本地127.0.0.1:8765，不能把页面控制连接误认为媒体已经穿过OAI。
实际候选地址、UE路由和隧道抓取的媒体包共同验证路径。

初始编码426×240/15fps/VP8，250kbit/s目标码率、实时编码、每秒关键帧、无音频。
当前Playwright Chromium没有协商出H264支持，首轮失败证据保留；使用其原生支持的VP8。
若浏览器支持则请求200ms接收抖动缓冲目标；实际缓冲由浏览器决定，不保证固定200ms或零卡顿。
播放器展示码率、帧率、接收缓冲、无新显示帧时长和卫星阶段。

static运行到约IQ60，首次切换运行到约IQ65，full运行到约IQ615；这些是Demo观测范围，
不冒充既有70/90/620IQ秒Ping/UDP验收。动态STK=8200+IQ，静态STK不推进。
首切prepare/blend/complete约IQ39/40–43/44，第二次约594/595–598/599。

独立平台`.private/live-场景-时间-随机后缀`保存report.json、视频JSON/CSV时间线、浏览器事件、
原平台前后快照比较、回归记录和私有子进程日志。
`/home/kayoko/ntn-live-demo-tools/runs/<run-id>/player-*.png`保存播放器截图。
画面帧时间使用浏览器/宿主机单调时钟配对映射到IQ/STK，缓冲与冻结仍使用墙钟单位。

Demo通过意味着：实际解码了视频、指定UE媒体路径核验通过、覆盖要求的切换窗口且窗口内仍有解码帧、
原平台保护比较与运行源码/二进制摘要不变。它不意味着零冻结、容量验收或现有Ping/UDP验收通过。
真实失败run保留，不自动重试或修改物理模型掩盖问题。

不修改现有源码、配置模板、入口或Docker镜像；复用隔离平台既定核心网服务，各轮创建并清理本轮容器，不改变网络端点归属。
仅在本次UE命名空间内加入ext-DN专用路由；停止时清理该命名空间及本轮独立核心网。
同一时间只能运行一个OAI实验。Ctrl+C后等待清理完成，不要强行关闭WSL。
