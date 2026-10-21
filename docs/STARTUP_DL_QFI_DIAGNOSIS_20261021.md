# 启动下行丢包根因：UPF初始QFI与已配置流不一致

日期：2026-10-21。手动指南及此前复测证据已按用户要求提交045627f，标题“完成分支合并，加入手动配置指南”。本文保留修复前诊断证据；当时尚未实施修复。后续补丁与原标准全程验收见[修复报告](UPF_QFI_FIX_VALIDATION_20261021.md)。

## 结论

当前UPF simple-switch把PFCP会话QFI初始化为5，在处理首个匹配的IPv4上行包后从PDR更新会话QFI；本实验配置的QFI为1。首批下行于是携带QFI5，经gNB和无线链路到达UE SDAP后因没有该映射而被丢弃。后续QFI变成1，数据正常交付。

这是当前项目使用的UPF实现问题与配置组合产生的确定性启动缺陷，不是MISO数值误差，不是卫星切换丢包，也不是UDP接收器启动晚。UE拒绝未映射流有明确代码依据，不能通过删掉该检查来掩盖UPF错误标记。

## 三组互相验证的证据

### 1. 本地实际版本和源码

本地镜像oaisoftwarealliance/oai-upf:v2.2.1，image ID/repo digest为sha256:03985036c2477a75755ded9b7fe9508b62f49e4ce9e9f059bbb68af63932e7f7，镜像revision标签commit:451c27da。实际私有配置enable_bpf_datapath=no，使用simple-switch而非BPF数据面。

诊断阶段从官方仓库精确revision取得源码，当时未安装或替换镜像。对应调用链：

- [pfcp_session.hpp L39–40](https://github.com/openairinterface/oai-cn5g-upf/blob/451c27da/src/upf_app/simpleswitch/pfcp_session.hpp#L39)：会话qfi初值0x05。
- [pfcp_switch.cpp L1279–1282](https://github.com/openairinterface/oai-cn5g-upf/blob/451c27da/src/upf_app/simpleswitch/pfcp_switch.cpp#L1279)：处理上行IPv4时，从匹配PDR的PDI取QFI写入会话。不是从任意上行包直接复制未经校验字段。
- [pfcp_switch.cpp L1355–1357](https://github.com/openairinterface/oai-cn5g-upf/blob/451c27da/src/upf_app/simpleswitch/pfcp_switch.cpp#L1355)：下行使用会话qfi传给转发规则。
- [pfcp_far.cpp L35–40](https://github.com/openairinterface/oai-cn5g-upf/blob/451c27da/src/upf_app/simpleswitch/pfcp_far.cpp#L35)：GTP-U封装沿用此QFI。

最初GitHub API查询遇到403限流，按v2.2.1旧目录猜测文件遇到404；随后以本地镜像revision和官方归档真实目录定位成功。源码SHA256单独记录，不将第三方完整源码加入项目提交。

### 2. 真实逐段抓包

运行miso-first-20261020-startup-capture，原代码、原配置、70IQ秒，开启限时只读tcpdump。捕获ext-DN、UPF、gNB主机N3及UE namespace的实验业务，仅保留在本机.runtime/startup-capture目录，不公开原始pcap。

- 首批DL seq1–4在ext-DN原始UDP、UPF入/出、gNB GTP-U入口均存在。
- seq1–4的GTP PDU Session Container实际QFI为5；不是把IPv4首字节0x45误当SDAP头的假象。
- UE隧道首个出现的DL业务包是seq5，seq1–4缺失。
- seq5起GTP扩展头QFI为1。
- 四个捕获点均报告内核丢包0。捕获结束时间稍有不同，尾部总包数不可直接相减；判断只使用已完整覆盖的前20包。

同一pcap墙钟，以下时间以gNB入口首个DL业务包为0：

|事件|相对墙钟秒|QFI|
|---|---|---|
|DL seq1|0|5|
|DL seq2|0.080301|5|
|DL seq3|0.160236|5|
|DL seq4|0.240372|5|
|首个UL IPv4业务seq1|0.309702|1|
|DL seq5|0.320757|1|

在此之前还捕获到两个时段的UL IPv6包（-5.153、-1.242秒），虽然QFI也是1，但不会经过上述IPv4学习路径，不能误称这是整次运行的第一个上行包。

### 3. UE SDAP丢弃记录与应用事件

UE当前源码openair2/SDAP/nr_sdap/nr_sdap_entity.c接收路径在QFI没有映射时返回；日志文字写作“UL”，但该判断位于is_gnb分支之前，同样会拒绝UE下行。

|运行|DL缺失序号|UE未映射QFI5丢弃次数|
|---|---|---|
|原SISO review-full-20261018|1–4|4|
|MISO miso-full-20261020-batch-rx|1–5|5|
|MISO miso-full-20261020-repeat-a|1–5|5|
|本次抓包短测|1–4|4|

这四组均无TUN未attach丢弃、TUN写失败或SDAP entity缺失记录；此前检查UDP接收器rejected/error均0。原SISO也出现完全相同QFI5拒绝原因，因此不是MISO合并新增。原SISO旧运行没有本次逐段pcap，关于其丢弃位置的证据来自保存的事件与SDAP日志。

1000字节/100000bit每墙钟秒对应约80ms发包间隔。在首个有效UL IPv4业务到达UPF前，下行窗口约0.3秒，本次恰好发送4包；执行调度和无线处理稍慢时为5包。因此不是固定序号硬编码丢弃，也不是固定IQ/STK时刻故障。

## 本次诊断运行结果

145.329577465墙钟秒，业务及空间审计通过，numeric_audit_ok=true，PBCH/RRC_IDLE/reaccess=0，stop_exit=0，专属核心网和捕获进程均已退出。Ping115/115、UL1464/1464、DL1459/1463，DL4包计入失败0.2734108%，切换窗口三业务期限失败0。

此处“通过”仍按既有1%门限，不代表启动缺陷已修复。没有预热、推迟首发或排除首包，没有改核心网、UE过滤、信道或物理参数。

本次执行入口：

```bash
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/run_capture_startup.sh
```

脚本调用capture_startup.py，限定项目容器及网络命名空间；同一原acceptance驱动执行短测，最后按run ID清理。parse_startup_capture.py、inspect_gtp_qfi.py及gtp_qfi_timeline.py提取序号/QFI/时间；compact_report.py与audit_loss_timing.py重算正式业务。源码及镜像仅只读检查；未更改生产代码，因此未为诊断重复编译或全套回归。

## 正确修复方向（尚未实施）

优先在UPF数据面从控制面已配置的规则正确选择下行QFI，不依赖首个上行IPv4包学习。需进一步检查匹配DL PDR与QER/PDI提供的QFI，避免硬编码为1、避免把会话单个QFI当作多QoS流通用方案。修复后的专属镜像应固定来源/摘要，保持原镜像可回退。

修复验收至少包括：下行先发且无预热时首包QFI正确、双向原负载、原SISO/MISO对照、70IQ短测、620IQ全程及两个窗口；新增首包QFI/交付回归，不放宽5秒期限与1%门限。只改变启动顺序让上行先完成会掩盖问题，不作为根因修复；修改UE允许未知QFI也不作为默认方案。

安全聚合证据见[验证目录](validation/startup-qfi-20261021)。
