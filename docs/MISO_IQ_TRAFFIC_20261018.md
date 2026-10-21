# 4×1 IQ 时钟业务验收

用户于2026-10-18确认实验口径调整：双向分别以IQ仿真秒定义100 Kbit/s，并保留墙钟性能指标。旧报告保留，不与新负载混作同一实验，不将旧失败改判为通过。

## 实现与验算

`scripts/full_pass.py --traffic-clock iq --max-wall-seconds 7200`启动两个标准库UDP探针，分别位于UE与ext-DN网络命名空间。默认wall模式仍使用原iperf3。ping仍每墙钟秒一次，RTT采用monotonic时钟，作为独立性能探针。

共同IQ时钟取gNB/UE实际样本数除以7.68Msps的较小值，禁止用显示的小数IQ值推算进度。双方绑定完成后设共同起点。每个报文1200字节UDP payload（含探针头，不含IP/UDP头），截至时刻t的应发包数为floor((t−start)×100000/9600)。累计负载量化误差小于9600 bit，2.4 IQ秒恰好25包、240000 bit。时钟停住即不增加预算。日志约每IQ秒更新，因此此版本是约1 IQ秒一批的确定性负载，并非连续亚毫秒CBR。

每包记录序号、发包所见IQ时间与墙钟时间；收端记录收包时钟，支持乱序/重复统计。逐秒原子保存JSON；SIGINT停止发包后继续收5墙钟秒。控制器确认末次IQ预算实际发完才停止。逐序号收发集合差计算缺包，包含末尾连续缺包，不能用“内部序号无缺口”代替无损。接收吞吐分别按发送IQ窗口及发送墙钟窗口统计；前者用于实验负载核对，后者用于运行性能观察。

## 验证

源码目录WSL系统Python：`python3 scripts/test_iq_udp.py && python3 scripts/test_full_pass.py && python3 scripts/test_spatial_audit.py && python3 local_ntn/test_feedback_diagnostics.py`通过，分别3/7/2项及C多线程诊断夹具。

真实localhost双向UDP测试验证：1 IQ秒各发收10包，停住1.2墙钟秒无额外发包，推进至2.4 IQ秒各发收25包，结束报告完整且零缺包，验算100000 bit/IQ秒。额外验证非法/倒退时钟及末尾缺包统计。

尚未完成新口径361秒端到端验收。不会以单元测试代替业务验收；仍保留原357–361秒尾部问题，新的早期接入或数据故障不可豁免。精度数据和信道生成不变，百万参考直接复用。

标准运行副本执行 source scripts/env_subarray4.sh && bash scripts/test.sh 退出0；日志.runtime/iq-clock-regression.log。包含trace parser、实际IQ、空间/网络配置、C reader及ASan/UBSan适配器回归，UL723/723点最大误差1.51165024e-11。

## 中断保留与续查

首次IQ口径实验`fullpass-1792253925496608553`在约IQ9秒中断：恢复检查确认PID2615已消失，没有最终报告。检查点已明确标记`interrupted_without_final_report`，而非仍运行或通过。双方各发送52包，DN收到52包、UE收到42包；最后一批是否还在途无法由不完整结果判断。原日志及逐包JSON保留在`.runtime/fidelity-checkpoints/fullpass-1792253925496608553/`。

2026-10-18改用独立会话启动后台包装器（`start_new_session=True`，标准输入关闭，输出写文件）；实际验证启动命令退出后进程仍存活，PID与SID均为1042。这样可脱离交互命令生命周期，但不能抵抗Windows/WSL关机；协议栈不支持从中间IQ恢复。只重跑必须连续的业务，不重做已完成的精度和IQ回归。

新启动记录`.runtime/iq-clock-detached-launch.json`；监督日志`.runtime/iq-clock-detached-supervisor.log`；业务日志`.runtime/fidelity-iq-clock-business-20261018.log`；记录器日志`.runtime/fidelity-iq-clock-checkpoint-20261018.log`。新标签产生后写入`.runtime/fidelity-checkpoints/active.json`，每15秒保存状态及逐包副本。恢复时先核对进程身份和最终报告，不重复启动。成功验收前仍不pull；任何情况下不push。

2026-10-18完整IQ口径实验fullpass-1792285084820144219已经结束：361秒/3444.866墙钟秒，UDP每向3718包，平均99979.832bit/IQ秒（不足一个1200字节报文的量化差）。UL缺52包均从356.999日志时钟起；DL除同样52包外，还丢首批0..9号（4.999秒）。ping3270/3311，连续收到1..3270，最大RTT7.279秒，无原数百秒积压；PBCH仍200次、首次前置356.99955。首批缺包仍超出尾部许可，因此不能验收或pull。
新增有界双向UDP HELLO/ACK，双方实际往返成功后才建立业务IQ起点；绑定socket不是用户面就绪。握手独立记录，业务包不重传，旧失败不改判。首版握手分支误放发送循环导致localhost测试失败，已移到接收循环，3项UDP及7项full_pass测试通过。另保存ping原始发送monotonic时间及IQ观测时间线，用于末尾缺包定位。标准回归执行中。
握手修复标准回归：运行副本source scripts/env_subarray4.sh && bash scripts/test.sh退出0，日志.runtime/iq-handshake-regression.log；新增时间记录后full_pass 7项与monotonic_ping 3项通过。

握手修复提交0abef85；新连续验收fullpass-1792294964392103430，full_pass PID2651，独立监督PID1343，入口active.json，日志.runtime/fidelity-iq-handshake-business.log。已进入业务，正在等待361秒结束；不重复启动。
新增独立audit_iq_business.py，保持strict passed原值，独立生成accepted_with_known_tail。检查双向握手、发包预算、完整IQ覆盖、逐序号早期缺包、ping发送时间映射和PBCH首故障位置。尾段以357秒及gNB日志提前约1ms的观测边界判定，明示记录分辨率，不宣称逐包精确物理IQ。合成夹具覆盖仅尾段可接受、首10包缺失拒绝、提前ping缺失拒绝，测试通过；没有改旧实验结果。

2026-10-18按用户更新指令执行git fetch origin，未pull/merge/rebase/push。origin/zky=70a38b5、origin/main=cb60f03，当前分支已包含其历史；新远端origin/codex/ntn-quadriga-handover=65bc517。只读检查其验收文档、full_pass差异、接收跟踪器与TA反馈代码：新隔离profile启用导频跟踪/TX预测和CRC成功四分之一增益TA反馈；full_pass使用实际观测采样率。远端620秒验收采用100K墙钟负载、1%业务丢包及5秒及时性门限，不能替代本任务100K/IQ秒、仅尾段失败的验收，也不能替代本任务1%信道频响精度认证。双方共同改动13个文件（含simulator.cpp、启动/预检查、full_pass/test.sh等），不建议覆盖式整合；未执行合并或修改远端。
