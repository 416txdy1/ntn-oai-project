# QuaDRiGa 与伪卫星切换 NTN 平台整合设计

本次整合以 zky 的全部已提交内容为基底，接入旧 NTN 平台已有的星座轨迹选择、伪切换日程和验证工具。新增实验使用独立分支、源码、构建、核心网和运行目录；原平台继续使用原分支和原 OAI 二进制。只有整合验证和原平台复验均通过后，才推送新分支。

## 用户要求与范围

用户要求保留 zky 的改动和新增内容，结合包含卫星切换的既有平台完成整合、测试并推送新分支，同时确保旧平台仍可正常运行。

支持的切换语义沿用旧平台：一个地面 gNB、一个 UE、一个小区，在离线轨迹中选择服务卫星并混合切换段。日程提供卫星身份和切换阶段，RFsim 回放合成轨迹。此次整合没有 Xn 或 RRC 小区切换，也不将合成轨迹解释成两颗独立物理卫星的相干联合发射。

QuaDRiGa 提供服务链的残余多径，STK 继续提供绝对传播时延、载波多普勒、链路功率、可见性和噪声。feeder link 仍归 STK。当前 RFsim 支持 SISO；MATLAB 仅用于离线导出，不参与运行时回放。

## 源码与运行基线

| 对象 | 固定基线 |
| --- | --- |
| 原平台仓库分支 | codex/ntn-oai-20260929 |
| 原平台仓库提交 | f30bc90a626214d227a7991d7429cf7723233f96 |
| zky 基底 | 70a38b5492b615498cea2332bd077c0d4f958d25 |
| 新分支 | codex/ntn-quadriga-handover |
| 原外部 OAI 提交 | c4125d1c740181ab1f7da0e7dd1d04ed07c37670 |
| 原外部 5GC 提交 | 212f92fc6a2fb82b5df1e8f4ef20075e75acefb3 |
| zky vendor OAI 提交 | 1e0c78bfbb80424f275e73a3103f582e0f903413 |
| QuaDRiGa | zky vendor 中的 2.8.1-0 |
| MATLAB | D:\Program Files\MATLAB\R2022b，9.13.0.2049777 |

新 Windows 工作树为 C:\Users\WSZ\.codex\worktrees\ntn-quadriga-handover\OAI调研。Linux 测试副本使用 /home/kayoko/ntn-workspaces/ntn-quadriga-handover，源码与产物放在该副本的 .runtime 下，避免在原 /home/kayoko/OAI/openairinterface5g 中部署或编译。同步只包含新分支源码和已审计输入，排除 .git、.private、.runtime；运行清单记录同步源码的提交及文件哈希。

原 OAI 和 5GC 均有既有本地改动。保持其内容不变，不执行 reset、clean 或整树补丁覆盖。原部署模块与仓库副本匹配，但实际 RFsim CMakeLists.txt 与 staged 副本不一致；staged 不作为新部署入口。新部署的唯一入口是 zky 的 oai_patch/current 与 quadriga/oai。

原核心网容器在准备阶段全部停止，无 modem 和 UE namespace；已有 demo-oai-public-net=192.168.70.128/26 保持不变。Ubuntu-22.04 已启动以完成核查，准备阶段没有启动或停止容器、modem或更改网络。

原构建目录为 /home/kayoko/OAI/openairinterface5g/cmake_targets/ran_build/build。保护指纹如下，实施结束复核 SHA256 与 mtime：

| 文件 | SHA256 | mtime UTC |
| --- | --- | --- |
| nr-softmodem | 51fa1f0bcd644e927e29e95ee3b129f44007ca7f9f0f15fff5d184a98c0240f3 | 2026-09-23 11:36:38 |
| nr-uesoftmodem | 89e68dc725212a074b2f270f4e7dedf60b4ddd9d46e0baafaeb8b305e72cb08d | 2026-09-23 11:34:59 |
| librfsimulator.so | 2573784de2a44cfae6a58c5425945773d6e414301ddd8910b041c7e3243841e8 | 2026-09-28 01:31:57 |

## 整合方式

采用 zky 基底加兼容 profile。其优点是保留信道读取器、QD adapter、长 IQ 历史、构建归档与自包含实验工具，只在有冲突的接口上接入旧平台能力。

直接将 zky 合并到原工作目录会把新 OAI 基底、运行入口与已有私有配置混合，不符合原平台保护要求。将两个平台保持完全独立并仅复制 trace 则不能恢复切换日程、原插值语义和统一验收，因此不作为完成方案。

### 内容保留

zky 的 vendor 归档、quadriga 全部模块、oai_patch/current、configs、examples、scripts、既有回归和文档保留。涉及整合的现有文件允许作兼容扩展；删除或替换 zky 子系统不属于此设计。

从 f30bc90 恢复缺失的星座生成、星座轨迹导出、handover_blend、satellite_schedule、slice_trace、切换验证和相应测试、schedule C 模块及示例切换 trace。旧脚本中的外部源码路径、核心网自动启动和固定网络名必须改为新 profile 配置后才能执行。

交付时提供文件级保留清单，区分 zky 未变内容、兼容扩展、旧平台恢复内容和新增文件。git 合并基础与两个源提交固定，原分支和 zky 分支均不改写。

### Profile 与资源隔离

统一配置模块负责解析 profile、输入、运行目录和网络资源，Python 与 shell 入口读取同一份配置。支持以下模式：

| Profile | 信道与插值 | 用途 |
| --- | --- | --- |
| zky | 维持现有默认 Hermite、可选 blend-aware 和双向 QD | 验证 zky 原有能力未被移除 |
| legacy-handover | 显式 legacy-linear、切换日程，关闭 QD 和 timing assist | 在新 OAI 构建上验证旧伪切换数值 |
| integrated-handover | 显式 legacy-linear、切换日程、DL 与 UL QD，timing assist 默认关闭 | 本次整合的交付入口 |

未选择新 profile 时保持 zky 的现有语义；原平台使用原工作目录，其入口不改动。新 legacy 与 integrated profile 均采用隔离资源，不复用原平台命名。legacy-handover 明确允许无 QD，integrated-handover 必须同时提供两方向 bundle，缺一即启动失败。

新 profile 的资源如下：

| 资源 | 新实验配置 |
| --- | --- |
| Docker project 和容器前缀 | ntn-qd-integrated |
| 5GC subnet | 192.168.71.128/26 |
| gNB N2 N3 地址 | 192.168.71.129 |
| AMF 地址 | 192.168.71.132 |
| UE PDU subnet | 12.2.1.0/24 |
| UE namespace | ntn-qd-ue |
| veth 名 | ntn-qd-host 与 ntn-qd-peer |
| RFsim subnet | 10.202.0.0/30 |
| RFsim host 和 UE 地址 | 10.202.0.1 与 10.202.0.2 |
| RFsim TCP 端口 | 4044 |
| 私有配置 | .private/profiles/integrated-handover 下 |
| 运行配置与日志 | .runtime/runs/<profile>/<run-id> 下 |
| PID 状态 | 该运行目录中的 processes.json |
| namespace 所有权记录 | /run/ntn-qd-ue.owner.json，包含 profile 和 run 身份 |

资源创建前检查路由、端口、容器、namespace、veth 与目录所有权。发现资源冲突或旧平台资源时拒绝启动，不能删除已有资源抢占名字。该固定配置不支持并行启动两个 integrated run；每次运行获得资源锁，结束时只清理自身创建且身份匹配的资源。

准备配置只写入新 run 目录，不能改原模板。新 subscriber、数据库凭据独立生成，权限受限且不提交；不复用或发布原凭据。新核心网用 zky 已有私有实验初始化工具生成，配置及 compose 只属于新 profile。旧核心网仅在原平台前后验收时按其已有入口启停。

停止过程校验记录的 PID、启动时间与程序身份，只终止本次 run。核心网停止使用明确的新 compose project，网络清理验证所有权。禁止 broad pkill、wsl shutdown 或停止无关容器。

### Trace 与 QuaDRiGa 数据契约

以旧 seamless trace 作为两次伪切换输入：8200–8820 s，共 621 行、一秒间隔。第一处混合段完成于 8244 s，第二处完成于 8799 s。firsthandover 的 8200–8270 s、71 行作为较短调试输入。trace 与 schedule 的范围、切换事件和哈希在导出前验证。

原默认 trace 是 7614–9000 s 的 1387 行；其相邻 JSON 仍记录旧单星 271 行，不能作为新输入的可信元数据，也不修改原文件。新导出清单根据实际 CSV 和 schedule 生成。

离线链路为：星座选择与切换混合生成最终 STKTRACE2 和 schedule，再对该最终 trace 分别生成 DL 2.4884 GHz 与 UL 1.6149 GHz QDCHANNEL1。固定种子、场景、工具版本和哈希写入清单。对 slice 或不同 trace 必须重新生成 bundle，禁止修改已有 manifest 的 trace hash 来绕过校验。

现有 MATLAB 导出器把合成轨迹作为一个虚拟发射端，保留该语义。profile 不宣称提供逐卫星独立簇切换。按现有一秒输入间隔导出，因此不能据此宣称精确解析亚秒级快衰落；更高快照速率和真实逐星信道是后续独立工作。

QDCHANNEL1 继续使用 excess delay、归一化多径系数和 0 dB residual gain。数据审计要求延迟非负、所有数值有限、各导出快照多径总功率为 1、residual gain 为 0 dB，路径/时间尺寸一致。保留 zky 的复数线性插值，中点功率允许随相位关系偏离 1，不对中点重新归一化。保留方向、载频、SISO、trace 与数据哈希检查，绝不放宽 preflight。检查复数插值中点与切换段功率，避免仅检查端点而遗漏相消。

生成到新 .runtime 目录且拒绝覆盖已有导出。经审计的小型示例 bundle 可提交到独立 examples/handover 目录，以便无需 MATLAB 即可复现实验；原始日志、运行产物和私有配置不提交。

### RFsim 与切换接口

在 current 的 stk_trace.h/c 增加显式 legacy-linear 模式，逐字段对齐原平台的线性插值；path_velocity 取输入物理速度，synthetic_blend 为 false。默认 Hermite 及现有 blend-aware 行为不变，未知模式报错。双方使用同一 trace、同一模式、同一 rate 和 IQ sample-clock epoch。

将 stk_schedule.c/h 纳入 current CMake。schedule 只提供按 IQ 回放时间记录的卫星与切换阶段，使用独立 STKSCHEDULE 日志行；不改 STKTRACE2 数值日志格式，也不实现运行时 MATLAB 调用或 bundle 热切换。

恢复旧平台的显式动态时延、多普勒开关和 initial-lead 选项，正常整合 profile 开启动态效应，initial-lead 默认零。initial-lead 只影响初始配置的预测时刻，不能改变共同 IQ epoch。保留现有 blend timing assist，默认关闭，不能通过隐式启用改变旧语义。

保留 zky current 的 IQ 参数 input_offset、QD 历史采样与队列保留计算、crypto 链接和 STK 噪声标定。此设计不替换 apply_channelmod 或 QD adapter 的信号执行顺序。接收信号继续由 STK 绝对时延与载波项、QD 残余多径、STK 增益及噪声组合形成。

静态及真实 IQ 测试覆盖：过长 excess delay、启动 timestamp 不足、切换段 bulk offset 变化、队列历史不足、bundle 尾端、可见性关闭和零多普勒区间。实际失败若来自现有接收链，须定位并提出最小修复；不能降低校验或用日志筛选隐藏失败。

## 验收与推送条件

原平台保护通过文件指纹和实际复验共同证明。所有公开结果仅含命令、提交、输入哈希、计数、数值审计及脱敏结论，不包含原始 UE 日志。

### 整合前基线

2026-10-09 已执行：

~~~powershell
wsl.exe -d Ubuntu-22.04 -u kayoko -- python3 '/mnt/d/实验室学习工作/杂活/雄安/OAI调研/local_ntn/test_trace_validation.py'
wsl.exe -d Ubuntu-22.04 -u kayoko -- python3 '/mnt/d/实验室学习工作/杂活/雄安/OAI调研/local_ntn/test_real_iq.py'
~~~

两项退出码均为 0。parser 通过物理边界、有限值、标志和有效输入检查。真实 rxAddInput 回归通过，10 dB 衰减能量比为 0.1，outage 为 0，噪声比为 0.0384，时延与多普勒变化验证通过。测试只在临时目录编译，不写原源码或 build。

实现前后分别对原平台执行相同短输入的注册、PDU、ping 30 包和双向 UDP 收发。记录输入、运行参数、丢包、时延、PDU 地址和退出状态。测试结束按原入口停止本次测试，恢复准备时的核心网停止、无 modem 和 UE namespace 状态。原配置、源码、原二进制哈希必须不变；运行日志、生成配置和自身状态文件属于已有入口的运行输出，仅私下保留。

旧长时伪切换已有掉线记录，zky 长时实验也已有失败记录。原平台复验承诺是旧入口和已建立的短时能力仍正常运行，不将已有长时失败写成通过。新整合的两次切换仍须独立通过下述验收。

### 新平台数值与隔离验证

1. 执行 zky scripts/test.sh 涵盖的既有 parser、IQ、Hermite、blend-aware、timing、QD reader/adapter/history、link budget 与 preflight 回归。
2. 恢复并执行 schedule、blend、slice、seamless 测试。新增 legacy-linear 与原提交结果的数值对照，验证默认模式未改变。
3. 参数化真实 IQ 测试的 source/build，必须指向新 vendor OAI 与新构建。报告打印真实绝对路径和输入哈希；旧硬编码 OAI 上的 PASS 不能用作新构建通过证据。
4. 验证两方向真实生成 bundle 的 reader、adapter 和功率归属；按实际 Fs 校验时延及 Doppler，不固定写死 7.68 MHz。
5. 验证启动冲突拒绝、目录隔离、namespace ownership、PID 身份校验和 cleanup 边界。新 run 的 stop 不得影响无关进程。
6. 编译并验证独立 nr-softmodem、nr-uesoftmodem、rfsimulator 和配置模块，新二进制路径与原 build 完全分离。

测试期间不并行运行新旧 modem，避免 CPU 争用影响验收；独立资源仍必须完整隔离。保留 zky 的全局 modem 冲突拒绝行为。

### 新平台端到端验证

先在新核心网上执行静态 QD 链路及短 firsthandover 调试，再执行 legacy-handover 的短回放对照，最后在 integrated-handover 上覆盖 8200–8820 s 的完整 IQ 时间区间。启动、业务统计、尾部等待和停止由同一 run 清单关联。

完整区间要求实际 IQ 时间越过两次切换完成点。业务统计使用 IQ 区间内的发包窗口，并等待接收尾部，避免把已停止时新发的包计入损失；真实丢包必须保留。验收要求：

- 注册及 PDU 建立成功，PDU 和双向业务必须在 IQ 8239 s 前就绪，两次切换事件按 schedule 顺序出现。
- 两个切换窗口均有完整、非空的发包和接收记录；业务启动过晚或缺失窗口均判为该轮失败，不能只凭 schedule 日志通过。
- 初次建链后的监测窗口无 PBCH 失锁、RRC IDLE、重新接入或 PDU 地址变化。
- 全程 ping 收到至少 99% 的已发包；双向 UDP 以 100 kbit/s 运行，各方向丢包不超过 1%。
- 两个切换完成点前后各 5 s 的业务窗口均满足上述丢包要求，无业务连续性中断。
- 数值审计确认 QD 实际启用，STK 与 QD 时钟一致，功率、时延和 Doppler 对应所选插值模式，无重复绝对项。
- 无内存越界、IQ 历史缺失、进程异常退出或原平台资源变更。

以上指标是交付条件，不是当前已有实验结果。失败时保留脱敏摘要、继续定位；不能将长时失败改为仅短时成功后宣称整合完成。

### 发布

更新来源锁、保留清单、运行说明及测试报告。记录准确命令、退出码、真实 source/build、各输入与 bundle 哈希、短时原平台前后结果和完整新回放结果。

复核原分支 HEAD、tracked 内容、外部 OAI/5GC 改动集合与原构建指纹。扫描待提交内容，排除私有配置、密钥、订阅数据、build 和原始 UE 日志。仅推送 codex/ntn-quadriga-handover，不强推、不移动原分支和 zky。用户已授权该新分支推送，无需在通过验收后再次请求推送许可。

若原平台基线本身无法完成短时业务，或新平台长时验收未通过，则不能给出原平台正常或整合完成的承诺；先报告实际失败并继续处理，发布范围变化须由用户明确决定。
