# NTN 一键完整测试

在 Windows 双击上一级的 `run_ntn_full_test.cmd`。窗口会保持打开，可能需要输入 WSL 用户的 sudo 密码。

默认发行版：`Ubuntu-22.04`。独立平台目录：`/home/kayoko/ntn-workspaces/ntn-quadriga-handover`。
这些启动文件位于原 Windows 工作目录中，但所有新平台构建与测试均在独立 Linux 工作副本运行。
不会自动切换、拉取或推送 Git 分支，不修改原平台源码或配置模板。

只检查启动路径，不运行测试：

```cmd
run_ntn_full_test.cmd -CheckOnly
```

自定义已安装的 WSL 发行版和独立平台目录：

```cmd
run_ntn_full_test.cmd -Distribution Ubuntu-22.04 -ProjectRoot /home/kayoko/ntn-workspaces/ntn-quadriga-handover
```

执行顺序：原平台保护快照 → 首次使用时初始化隔离配置 → 构建 → PHY测试目标构建 → trace/IQ回归
→ 脚本回归 → 70 IQ秒首次切换两轮 → 620 IQ秒QD双切换 → 620 IQ秒关闭QD对照
→ 90 IQ秒静态对照 → 原平台实际业务短跑 → 原平台parser/trace/stock IQ回归 → 保护比较。
本入口运行原平台 stock IQ 测试；不把它声称为另行编译的原平台 ASan/UBSan 测试。

每轮使用新 run ID，并重新启动/关闭隔离核心网。失败不重试、不放宽原验收阈值，并停止后续场景。
原平台须事先停止；依赖、Docker、原平台既有容器及配置应已就绪，本入口不安装依赖。
整个过程可能运行数十分钟，取决于编译缓存和仿真速度。每轮业务验收墙钟上限3600秒。
不要并行手动启动原平台或其他实验。

窗口显示：START/END/退出码、每15秒阶段存活提示；业务场景中每5秒显示两端IQ/STK时间、
物理delay/Doppler/CN、累计Ping/UL/DL发送接收数、在途数及超过5秒尚未送达数；
每次卫星身份/phase变化立即显示SAT记录。Ping RTT保留墙钟单位。
实时pending和pending_over_5s不是最终丢包率，最终结论以现有验收器report.json为准。
原始构建、modem及worker日志不会直接打印，防止泄露凭据。

第一次切换：IQ39 prepare → IQ40–43 blend → IQ44 complete（S06→S05）。
第二次切换：IQ594 prepare → IQ595–598 blend → IQ599 complete（S05→S04）。
动态场景STK=8200+IQ；静态场景不推进STK时间。实际日志以采样时钟记录为准。

总报告：独立平台 `.private/suite-日期时间-随机后缀/suite-report.json`。
每阶段原始日志：同目录 `*.private.log`。原始日志只应本机保留。
每场景报告和联合时间轴：`.runtime/runs/<profile>/<run-id>/acceptance/report.json`、`timeline.png`。

使用 Ctrl+C 请求有界中止；让窗口中的清理结束后再关闭。强制关闭窗口或终止WSL不能保证完成清理。
若提示资源归属或清理失败，保留证据检查，不要使用广泛pkill或删除原平台资源。

启动器验证命令（不会启动仿真）：

```bash
python3 -B ntn_test_launcher/test_launcher.py
```
