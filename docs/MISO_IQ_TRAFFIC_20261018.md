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
`n标准运行副本执行 source scripts/env_subarray4.sh && bash scripts/test.sh 退出0；日志.runtime/iq-clock-regression.log。包含trace parser、实际IQ、空间/网络配置、C reader及ASan/UBSan适配器回归，UL723/723点最大误差1.51165024e-11。
