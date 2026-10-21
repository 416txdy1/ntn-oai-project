# 有声视频 Demo 实测（2026-10-20）

输入为用户指定的《爱乐之城》MP4，H264 High 1224×480，AAC LC 48kHz 双声道。源文件 SHA256：`f74934c39581826862eea8cae0824168637a3e5623f7cc84cef10be083925150`。转码 VP8+Opus，Windows Edge 播放经过 OAI 和 UE 中继的音视频。

| 项目 | 静态 | 首次伪切换 |
|---|---:|---:|
| run-id | live-static-20261020-181309-1b1bd0 | live-firsthandover-20261020-181830-15f8b1 |
| Demo 判定 | PASS | PASS |
| 解码视频帧 | 997 | 1105 |
| 浏览器累计视频冻结次数 | 6 | 12 |
| 累计视频冻结墙钟秒 | 3.640 | 8.628 |
| 音频接收/输出样本 | 3,127,680 | 3,860,640 |
| 音频补偿样本 | 3,972 | 3,826 |
| 音频进度/墙钟比例 | 1.000013 | 1.000013 |
| 音频统计跨度（墙钟秒） | 63.999 | 78.999 |
| 最后播放器非静音 | 是 | 是 |
| 媒体候选、UE隧道、中继入流核验 | 通过 | 通过 |
| 原平台保护/运行源码二进制/源文件不变 | 全通过 | 全通过 |

首次切换 S06→S05，日志约 IQ40 prepare、IQ41 blend、IQ45 complete、IQ46 steady。报告窗口 STK8239–8249 共14个统计样本，新增188个视频帧、624,000个音频样本和114,196音频字节，音频进度比例0.999616。窗口 `max_native_freeze_count=11` 是累计计数，不是窗口冻结次数。全程12次/8.628秒冻结也不能全部归因于切换。

Windows 可复现命令：`run_ntn_video_audio.cmd -Case static -SkipRegressions` 和 `run_ntn_video_audio.cmd -Case firsthandover -SkipRegressions`。对应 Python 参数为 `--case static --source "$SOURCE" --skip-regressions` 和 `--case firsthandover --source "$SOURCE" --skip-regressions`；以 sudo python3 -u 执行 `/mnt/d/实验室学习工作/杂活/雄安/OAI调研/ntn_live_demo/demo.py`，SOURCE 为原片完整 `/mnt/d/...mp4` 路径，作为一个参数传入。

当日已先在 `/home/kayoko/ntn-workspaces/ntn-quadriga-handover` 执行：

```bash
bash local_ntn/run_regressions.sh
bash scripts/test.sh
```

分别 exit=0（10.0秒）及 exit=0（90.7秒）。音频检查命令 `python3 -B /mnt/d/实验室学习工作/杂活/雄安/OAI调研/ntn_live_demo/test_audio.py`，4项通过。

完整报告位于 Linux 独立平台 `.private/<run-id>/report.json`。两次测试停止调制解调器、关闭本轮核心网、原平台比较均 exit=0，cleanup 无错误。结束后只读核查无网络命名空间、无运行容器、无 nr-softmodem/nr-uesoftmodem。

## 保留的失败与更正

- `live-static-20261020-170813-009af0`：旧门限曾将持续收包误判成功；实测音频时钟停滞且最后静音。保留原 report，新增 `audio-quality-audit.json` 标明更正为音频失败；进度比例0.028750。未重写历史报告。
- `live-static-20261020-174410-399bde`：WSLg 局部音频参数方案完整测试失败；收包增长不能证明播放正常。
- `live-static-20261020-175259-04ab71`：WebAudio 完整测试失败。此后改用 Windows 原生输出，完成上表两次成功测试。

PASS 范围是视频解码、持续音频、媒体经过 UE、覆盖首次切换、隔离保护及清理。未完成有声第二次切换或全片长时运行；不代表原 Ping/UDP 正式验收，不保证固定200ms缓冲或零冻结。音频样本含补偿；未做端到端声学听感或音画同步标定。Windows 播放器位于中继之后，精确无线效果须结合物理日志分析。
