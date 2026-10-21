# 合并版输出格式与旧分支兼容性（2026-10-21）

## 核查范围与结论

比较原 handover `65bc517`、原 zky-miso `9a65bc7` 与合并版 `045627f` 加本次 UPF 修复。实际样本分别是 `review-full-20261018`、`fullpass-1792294964392103430`、`miso-full-20261021-qfi-fixed`。字段证据见 [output-format-comparison.json](validation/upf-qfi-fix-20261021/output-format-comparison.json)。原始业务日志和身份数据不随文档发布。

相对 handover，主要业务输出保持兼容，有少量附加诊断字段；相对 zky-miso 的旧 full_pass 流程，报告路径、层级及指标口径均有变化。相同的 `passed=true` 不能用于证明两个实验配置相同。本次 UPF 修复本身没有修改业务输出器、统计起点、包序号或验收门限。

## 与原 handover 的比较

|产物|核查结果|读取注意事项|
|---|---|---|
|`run.json`|顶层新增 `qd_workers_requested`、`spatial_mode_requested`；schema 仍为 1|两项是请求配置字符串，不能单凭它们证明实际生效；同时核对运行日志与空间审计|
|`acceptance/report.json`|成功运行顶层字段一致；递归差异仅来自 `network_inodes` 的运行时 PID 键|这些字典键每次运行变化，不是固定 schema 字段|
|失败报告|新增可选 `modem_identity_failure`|包含 expected_start、expected_executable、observed、phase；只在调制解调器存活检查失败时出现|
|`ping-matched.json`、双向 `*-matched.json`|本次实际样本字段路径完全一致|空数组、null 和包数是运行结果，不应硬编码|
|`ping.jsonl`、双向 sender/receiver JSONL|实际样本的每类字段集合一致；相关输出器源码与原 handover 相同|逐行读取 JSON；同一文件包含不同事件，按 event 分派，不按行号推断包号|
|`timeline.csv`|两次实际运行的列名及顺序完全一致|数值、行数和覆盖范围可能随运行变化|
|`timeline.png/.svg`、`switch-comparison.json`|生成器源码相同|图形内容取决于数据，不保证文件字节相同|
|`spatial-audit.json`|合并版额外运行空间审计后生成|补充产物，不是 report.json 原字段的替代|
|信道与覆盖清单|增加 antenna.json 文件记录及部分 overlay 哈希项|清单采用文件名为键，允许集合扩展|
|程序文本日志|增加 MISO、计算线程等诊断输出|不保证整份日志逐字兼容，勿以固定行号或整行数作为业务数据接口|

`handover_metrics.py`、`continuous_ping.py`、`continuous_udp.py`、`handover_plot.py` 与原 handover 的 Git 内容逐字相同。上述实测成功样本不覆盖所有错误事件，失败路径另通过源码核对。

## 与原 zky-miso 的比较

旧 full_pass 实际输出在 `.runtime/reports/fullpass-<标识>.json` 及同名目录，包含 `ping.json`、`ue-iq-udp.json`、`dn-iq-udp.json`、`iq-clock.json`、`iq-observations.jsonl`。当前主验收输出在 `.runtime/runs/<profile>/<run_id>/acceptance/`，含 report、逐包 JSONL、匹配结果、时间线和切换窗口比较。旧 full_pass 入口仍保留；这里比较的是旧实验与当前主验收，不表示旧入口被删除。

|旧输出或含义|当前主验收|适配方式|
|---|---|---|
|报告顶层 `uplink`、`downlink`|`report["udp"]["uplink"]`、`report["udp"]["downlink"]`|调整访问路径，不能直接复用旧提取代码|
|UDP 状态 JSON 与汇总|发送端、接收端独立事件 JSONL，再按 sequence 匹配|区分 sent、唯一 received、duplicate、最终缺失和超期；不能把所有事件行数当包数|
|`target_bits_per_iq_second`、`sent_bits_per_iq_second`、`received_bits_per_iq_second`|墙钟业务负载与 measured_wall_bits_per_second；时间线另保留 observed_iq_bits_per_second|不能仅改字段名，分母的时间轴不同|
|Ping `rtt_ms` 等旧汇总|事件 wall_rtt_ms、报告 wall_latency_ms_* 等|按实际字段与总体统计定义取值，区分 Ping 往返与 UDP 单向|
|旧最终丢包统计|最终交付、5 秒期限、边界不确定性、窗口覆盖与业务退化统计|最终收到的超期包仍可算期限失败；不能仅看 lost_packets 判断通过|
|旧 IQ 观测记录|timeline.csv、切换前/中/后比较与数值审计|新的 CSV 是派生指标，不是旧观测 JSONL 的直接改扩展名|

旧字段完整列表保存在对比 JSON。旧程序的状态文件与当前事件文件是不同结构，不建议通过通用递归“寻找同名字段”混用。

## 时间单位与数值解释

- `monotonic_ns`、`send_ns`、`receive_ns`、`deadline_ns` 为单调墙钟纳秒，不是 Unix 日期，也不是 IQ 样本数。差值除以 1e6 得毫秒。
- `*_iq_s` 是 IQ 秒，`*_stk_s` 是场景秒，`wall_seconds` 是实际运行墙钟秒。时间线按 IQ 区间组织，不代表其中的延迟指标也以 IQ 秒计。
- 当前双向各 100000 bit/墙钟秒、1000 字节载荷，理论发送间隔 0.08 墙钟秒；期限 5e9 纳秒。旧 100000 bit/IQ秒在实时因子 R=IQ秒/墙钟秒时，约等于 100000×R bit/墙钟秒。因此 R=0.5 时旧负载约 50 Kbit/墙钟秒，当前仍是 100 Kbit/墙钟秒。
- 时间线的 observed_iq_bits_per_second 与 measured_wall_bits_per_second 可以同时存在，但含义不同。不能用整个实验的平均实时因子代替每个切换窗口的真实墙钟分母。
- 无观测/无有效样本的 null 或 CSV 空格项不可当作零丢包、零延迟；边界不确定的包要保留原统计上下界。

## 信道二进制布局：版本不变，维度与归一化需核对

三者均为 QDCHANNEL1、schema_version=1、小端序，轴顺序 `[snapshot, rx, tx, path]`。times/delays 为 float64，coefficients 为实虚交错 complex64，residual_gain_db 为 float32。不得按16×16直接 reshape 端口数据：物理阵列为16×16，当前等效模型是四个8×8子阵端口。

|全程 bundle|DL 维度 snapshot×Rx×Tx×path|UL 维度|每方向 coefficients 字节数|
|---|---|---|---:|
|handover SISO|621×1×1×11|621×1×1×11|54648|
|zky-miso 四子阵|362×1×4×11|362×4×1×11|127424|
|合并版四子阵|621×1×4×11|621×4×1×11|218592|

合并版每方向复系数621×4×11=27324个，每个8字节；delays同样218592字节；times为621×8=4968字节；residual_gain_db为621×4×4=9936字节。短切换 bundle 的维度另从它自己的 manifest 读取。

原 handover 的 composition.quadriga_coefficients 是 `unit_snapshot_link_power`；两版 MISO 是 `unit_snapshot_mean_link_power`。这是空间信道归一化语义差异，不能忽略 composition 后再对每条链路任意归一化，否则会改变端口间相对增益。空间审计与独立卷积已经按当前模型验证。

合并版 trace 与切换 CSV 采用原 handover 更新版，相关文件相对65bc517无差异。新信道 manifest 的 stk_trace_sha256 与 handover 相同，为 b73fa3db…c8db366；旧 zky-miso 为3d63d47a…b2dbda18。快照数、哈希和场景覆盖改变属于数据来源变化；不能把旧362点数据拼接到新621点轨迹。STKTRACE2与QDCHANNEL1格式名称本身未改。

## 使用建议与本次验收

沿用 handover 分析脚本时允许附加键，并从 manifest 读取维度、dtype、归一化约定；旧 zky-miso 分析脚本需要显式适配路径、报告层级与墙钟统计。run.json 的 schema=1 尚不能单独区分新增可选字段，应结合字段存在性和源码/产物哈希。

本次620 IQ秒全程 Ping1174/1174、UL15009/15009、DL15006/15006，均无缺失和超期；该结果使用原 handover 的墙钟负载和期限。短测另有2个UL缺失，详见 [完整验收与限制](UPF_QFI_FIX_VALIDATION_20261021.md)。格式核查只新增文档和脱敏结构证据，没有改写运行原始数据或验收输出器。
