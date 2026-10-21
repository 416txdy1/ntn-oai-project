# 直播 Demo 实测结果（2026-10-20）

已在独立Linux平台完成静态视频与首次卫星切换视频两轮实际测试。
现有OAI源文件、六个运行二进制、原平台源码/模板均未被Demo覆盖。
完整第二次卫星切换直播（full入口）尚未实测，不能用本报告替代其验收。

## 实际运行

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ntn_live_demo\launch.ps1 -Case static
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ntn_live_demo\launch.ps1 -Case static -SkipRegressions
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ntn_live_demo\launch.ps1 -Case firsthandover -SkipRegressions
```

第一次static使用H264，MediaMTX收到UE请求但浏览器无法协商该codec，WHEP返回400，
该轮`live-static-20261020-091730-cf8214`明确FAIL，保留完整私有记录。
其trace/IQ回归exit0、10.0秒，scripts/test.sh exit0、85.7秒。
后续仅Demo改为VP8，运行OAI源与六个二进制摘要完全不变，复用这次离线回归记录。

## 真实数值

| 项目 | 静态 | 首次切换 |
| --- | --- | --- |
| run ID | live-static-20261020-092153-f637bc | live-firsthandover-20261020-092639-c02dc7 |
| Demo结果 | PASS | PASS |
| 有解码视频观测IQ区间 | 11.199–59.899 | 10.079–64.777 |
| 已连接的视频统计样本 | 67 | 81 |
| 累计解码帧 | 997 | 1213 |
| 浏览器报告冻结次数/累计时长 | 0 / 0秒 | 0 / 0秒 |
| WebRTC地址对核验 | 通过 | 通过 |
| UE隧道媒体包核验 | 通过 | 通过 |
| OAI覆盖源码及六个二进制摘要 | 未变 | 未变 |
| 原平台快照比较 | passed=true, differences=[] | passed=true, differences=[] |
| 本轮进程/核心网清理 | 通过 | 通过 |

首次切换的STK8239–8249窗口有15个视频统计样本，解码帧数增加209；
窗口最大**采样时刻**显示帧年龄65.4ms，原生冻结计数0。
该采样值不能等同于全帧间隔的最大值；低频采样与原生冻结统计保留各自含义。
实际日志观测到两端prepare→blend→complete→steady、S06→S05。
稳定接收通常约200–220kbit/s，解码约15fps；不是平台容量测量。

媒体显式使用192.168.71.135:8189/UDP，UE路由经oaitun_ue1，
隧道抓包存在12.2.1.x与该媒体端口之间的真实包。
服务器/编码器/浏览器以kayoko普通用户运行，Chromium沙箱验证成功。
浏览器截图已视觉检查；中文字体由独立本地Noto资源提供。

## 原平台实际复验

在所有Demo资源停止后，实际执行独立平台既有检查器：

```bash
sudo python3 scripts/original_platform_check.py short-run \
  --snapshot .private/live-firsthandover-20261020-092639-c02dc7/original-before.json \
  --tag live-demo-final-20261020
sudo python3 scripts/original_platform_check.py compare \
  --snapshot .private/live-firsthandover-20261020-092639-c02dc7/original-before.json
```

业务短跑exit0：Ping30/30，上行UDP130/130，下行UDP131/131，passed=true。
最终compare exit0，passed=true，differences=[]。
原始modem日志与保护快照只在独立平台.private目录，不作为公开附件。

## 范围及依赖准备

未改原平台现有跟踪文件、OAI协议栈、STK轨迹、QuaDRiGa bundle、配置模板或Docker镜像。
新增的Windows入口/脚本为独立文件；运行时与其他OAI实验串行，不保证同时运行互不争用CPU。

初次因系统缺少ensurepip，曾提出以root下载执行get-pip；自动审批拒绝该方式，未执行。
最终使用普通用户复用本地pip引擎，仅安装新user-venv和独立浏览器/媒体文件，不安装系统包。
最后的路径发现改为标准库glob，避免以root导入新下载的媒体Python包；
界面按钮仅补充字体继承。这些不改变已测试OAI运行代码或媒体编码参数。
