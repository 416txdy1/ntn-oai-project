# 有声直播实验测试分支

基底：`codex/ntn-quadriga-handover` 的 `65bc517a0ec5bfb4e9e2f665876ea5d188cac1a5`。本分支增加独立的直播观测与Windows启动器，不替换原平台OAI源码、构建产物或配置模板。

## 入口

|命令|用途|
|---|---|
|`run_ntn_video_audio.cmd`|有声原片实时转码，默认首次切换|
|`run_ntn_video_audio.cmd -Case full`|同一轮覆盖原轨迹两次切换|
|`run_ntn_more_handovers.cmd`|默认4轮，每轮重新接入，重放已验证的S06→S05|
|`run_ntn_channel_comparison.cmd`|固定/正常/物理载噪比干预，默认两次重复|
|`run_ntn_live_demo.cmd`|保留原无声合成画面入口|
|`run_ntn_full_test.cmd`|既有Ping/UDP全套验收的独立窗口启动器|

多轮重放是多次独立实验，不是同一会话内连续多星切换；固定对照组故意不切换。保持播放器打开、可见且非静音；轮间由程序自动重连。实时显示C/N、时延、多普勒、UE入流、播放帧率、缓冲与观察提示。

## 本地媒体配置

仓库不包含用户视频、音轨或 `media-source.local.json`。复制 `media-source.example.json` 为 `media-source.local.json`，修改为自己的含音频视频绝对路径；该文件被Git忽略。也可直接传入：

```cmd
run_ntn_video_audio.cmd -Source "D:\Media\demo-with-audio.mp4"
run_ntn_more_handovers.cmd -Source "D:\Media\demo-with-audio.mp4" -Rounds 4
run_ntn_channel_comparison.cmd -Source "D:\Media\demo-with-audio.mp4" -Smoke -Repeats 1
```

输入文件只读，FFmpeg实时循环输出VP8+Opus，不是H264码流透传。未在源码中嵌入媒体数据，不下载代替用户原片。

## 环境与边界

这是已配置实验机的测试版本，非通用安装器。Linux独立运行平台位于 `/home/kayoko/ntn-workspaces/ntn-quadriga-handover`，工具位于 `/home/kayoko/ntn-live-demo-tools`，WSL发行版默认Ubuntu-22.04。Windows原生Edge及捆绑Node/Playwright路径在 `windows_player.cjs`、`test_dashboard_ui.cjs` 与 `demo.py` 中按实验机设置；迁移机器需核对这些路径及既有平台准备步骤，不能只下载CMD就运行。第三方媒体工具单独准备，不提交到本分支。启动前会验证WSL能执行Windows Node；若标准Windows处理器缺失，仅在明确的WSL环境中临时恢复该会话注册，并输出提示，不改持久系统配置。其他启动错误会直接报错。

音视频：ext-DN → OAI/卫星RFsim IQ信道 → UE隧道 → UE中继 → Windows播放器。Windows接收统计位于中继之后；上游UE入流单独测量。输入C/N并非UE实测SINR，提示是观测关联，不替代因果配对。IQ与墙钟当前并非严格1:1，速率/冻结仍以墙钟计量。存在视频冻结和音频补偿，不承诺固定200ms或零卡顿。

运行时仍使用隔离Linux平台记录的准确OAI源版本和二进制。直播启动器可从本工作树运行，既有Linux源码不被本发布覆盖；每轮报告记录其准确摘要。不同平台实验不可并行。

## 验证与发布

最新发布验收见 `RELEASE_VALIDATION.md`。其他带日期的RESULTS/VALIDATION文件是历史记录，保留当时失败与未完成范围，不能替代最新验收。因果门限未满足必须为INCONCLUSIVE/INVALID，不以本地播放成功替代无线传输证据。

发布只包括白名单代码、CMD、文档与媒体路径模板。不包含 `.private/`、`.runtime/`、数据库、K/OPc、真实订户配置、原始UE日志、视频/音轨、播放器截图或实验结果目录。原始证据留在实验机，公开摘要仅包含数值与结论。
