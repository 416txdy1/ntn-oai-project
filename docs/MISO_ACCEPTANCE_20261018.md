# zky-miso 主体修复验收

2026-10-18，用户明确选择“单列为尾界在途不确定项，接受主体修复”。本任务主体完成；原357–361秒尾段连接故障继续交由其他协作者处理。两个尾界ping无法精确归因，不能称为全程零丢包或严格全通过。

数值记录及证据SHA256见[acceptance.json](validation/miso-20261018/acceptance.json)。原始严格`passed=false`及独立审计的两项ping失败保留，用户接受决定独立记录为`user_accepted_main_scope=true`。

## 完整业务与精度

- 运行标签：`fullpass-1792294964392103430`，实际运行代码`0abef85`。完整覆盖361 IQ秒，业务从IQ4.999秒接入后开始，到360.999秒结束；墙钟4529.561秒。未用短测替代完整业务。
- 四个独立RF发射通道、16×16阵列映射四子阵端口；UE单接收天线。上行使用四路接收分集，已补齐PUSCH/PUCCH实际接收端口。
- 双向各发送3708个1200字节UDP payload，计费窗口356 IQ秒，实际99991.011bit/IQ秒。理论35600000bit与实际35596800bit差3200bit，小于一个报文9600bit，符合整数包预算。
- 双向各收到3656包，序号0–3655连续完整；各缺52包，首个缺包的观测IQ为356.999秒（gNB整秒前约1ms日志），属于约定尾段边界。无早期UDP缺包、重复、非法包或额外序号。
- ping收到4323/4376。末53个未回复，其中4324、4325分别在尾段观测边界前1.195秒、0.181秒发出；邻近正常RTT约1.45–2.09秒。两包单列为尾界在途不确定项，由用户接受，不将其推断为确定尾段故障。其余51个在尾段发送。
- UE PBCH故障200次，首次前置日志IQ356.99955秒，与原有尾段一致；gNB为0。停止退出码0，复查无本次modem或核心网运行残留。
- 墙钟性能另列：IQ/墙钟速度0.0799067；双向接收约7.878Kbit/墙钟秒；ping平均2.074秒、最大9.198秒。该负载实验不证明链路最大容量，也不使用远端分支的5秒及时性门限冒充本任务要求。
- 4.5MHz带内、前357秒的独立密集QD参考与运行时误差组合界：DL **0.949024%**，UL **0.944053%**，均满足用户确认的1%。原末尾四个快照未修改，也不纳入该精度认证。

## 修复原因与验证

IQ负载脚本原先把“socket绑定成功”当成“用户面双向可达”，新负载首批下行丢10包。新增有界HELLO/ACK往返，双方确认路径后才设定业务IQ起点；握手单列计数，业务包不重传，旧失败报告保留。完整复验首批及所有尾段前业务包均收到。实验负载从墙钟100K改为IQ秒100K已获用户同意，旧墙钟负载结果不能与新结果混作同一实验。

主要修改文件：`scripts/iq_udp.py`实现IQ预算、握手及逐包记录；`scripts/full_pass.py`协调双向时钟并记录观测时间线；`scripts/monotonic_ping.py`保留发送单调时钟；`scripts/audit_iq_business.py`独立核对覆盖、负载、逐序号丢包和尾段例外。此前轨迹审计与反馈诊断分别保留实际trace/hash、CRC/PUCCH计数，详见[MISO_IQ_TRAFFIC_20261018.md](MISO_IQ_TRAFFIC_20261018.md)。

实际验证命令：

```bash
# 运行副本 /home/duyaya/OAI/self-contained-test
source scripts/env_subarray4.sh && bash scripts/test.sh
# 退出0，包含trace parser、实际IQ、reader和ASan/UBSan适配器；日志.runtime/iq-handshake-regression.log

# 源目录：UDP 3项、full_pass 7项、ping 3项、独立验收1项均通过
python3 scripts/test_iq_udp.py
python3 scripts/test_full_pass.py
python3 scripts/test_monotonic_ping.py
python3 scripts/test_iq_business_audit.py

# 独立会话包装器启动/管理核心网和检查点，实际业务命令：
source scripts/env_subarray4_fidelity.sh
export OAI_NTN_FEEDBACK_DIAGNOSTICS=1
python3 scripts/full_pass.py --max-wall-seconds 7200 --traffic-clock iq
# strict退出1：原尾段及两个边界ping保留，非全程零故障
python3 local_ntn/audit_runtime_numbers.py --run-dir /home/duyaya/OAI/self-contained-test --labels fullpass-1792294964392103430
# 数值审计退出0
```

独立`audit_iq_business.py`审计退出1，原因仅为4324/4325两个ping的发送时刻早于尾段观测边界；用户随后明确接受两项不确定性。没有改门限让该审计变绿。

## Git 与远端

本地分支`zky-miso`已按阶段提交。2026-10-18按用户更新要求完成`git fetch origin`及代码/验收范围检查，**没有合并、rebase或push**。新获取的`origin/codex/ntn-quadriga-handover`为`65bc517`；其隔离profile接收跟踪、TA反馈及墙钟业务验收与当前MISO口径不同。双方13个文件存在共同修改，未来整合需单独处理，当前不覆盖任何版本。

协作者已有的`docs/ANTENNA_ALIGNMENT_20261014.md`、`docs/DEBUG_ZKY.md`及未跟踪`docs/ARRAY_FULL_PASS_VALIDATION_20261014.md`保持原状，未纳入本任务提交。
