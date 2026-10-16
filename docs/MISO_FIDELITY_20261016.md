# 4×1 信道时间精度修复记录（2026-10-16）

用户确认：4.5 MHz 占用带宽内频响 NRMSE 门限为 1%。本记录区分运行时修复、离线时间采样与子阵宽带近似；业务接通不等于通过频响精度验收。

## 已完成：RFsim 块内逐采样更新

原适配器在 update_channel_model_from_quadriga 中只查询 IQ 块起点，随后整块复用同一组系数和时延。离线加密快照不能消除这种零阶保持误差。现在卷积以 timestamp + sample 查询同一个 STK IQ 时钟，逐采样更新所有 Tx 到当前 Rx 的系数、相对时延和残余增益。每个 Rx 从同一块时间起点计算；块内进入/离开有效时间范围时逐采样静音。接口、bundle v1 格式、STK 绝对时延/多普勒/功率来源不变。

代价是逐采样查询增加计算量；当前验收证明功能与数值一致性，不宣称达到实时吞吐。旧 1 秒 bundle 保持原样，不将其重新标记为 1% 精度合格。

## 可复现验证

源码目录 `/mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project`，运行目录 `/home/duyaya/OAI/self-contained-test`，均在 Ubuntu-22.04 中。命令使用已有 root 实验环境。

```bash
bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/scripts/wsl_lab.sh build /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project /home/duyaya/OAI/self-contained-test
cd /home/duyaya/OAI/self-contained-test
OAI_SPATIAL_MODE=miso4-subarray bash scripts/test.sh > .runtime/fidelity-regression.log 2>&1
source scripts/env_subarray4.sh
python3 scripts/validate_spatial.py --ports 4 > .runtime/fidelity-business.log 2>&1
```

- 构建成功，scripts/test.sh 退出码 0：包括 trace parser、真实 IQ、reader、ASan/UBSan adapter 回归。
- 独立 Lagrange IQ 参考按逐采样信道计算，覆盖 362 个快照及 361 个中点、速率 0/0.5/1/1000000；极高速率用于跨节点和范围边界测试。
- 下行 4×1 最大绝对 IQ 误差 1.10644806e-11；上行 1×4 为 4.4147982e-12。
- 静态 smoke-0-1792054572731347034：PDU 成功、ping 10/10、UL UDP 0/130 丢包、DL UDP 0/137、PBCH 失败 0。
- 动态 smoke-1-1792054686472845170：PDU 成功、ping 10/10、UL UDP 0/130、DL UDP 0/131、PBCH 失败 0。
- 两次空间/物理公式审计 passed=true；时钟、Hermite 几何、时延、多普勒、增益和 C/N 均按独立公式验算。测试仅启停自己管理的服务，结束已停止。
- 此处业务测试使用原有完整过境 bundle，用于检查运行时改动的兼容性；不是新密集信道的端到端精度认证。

## 离线精度检测仍在进行

首 2 秒真实 QD 参考中，1 秒线性插值全局误差约 5.59%、最差约 51%；均匀 2 ms 插值相对于 1 ms 参考最差仍约 2.69%。不能简单指定一个较小间隔就宣布合格。

首 2 秒自适应下行结果：1242 个输出节点、12411 个真实参考点，最差时间 NRMSE 0.490963%，全局 0.109593%；子阵连续频带保守上界 0.012278%，组合界 0.503301%。这些数字只对应同一次生成的有限时间参考点，尚不能推广到完整过境或独立生成网格；正在进一步交叉验证。

直接逐阵元宽带计算显示原子阵平均时延在首 2 秒的误差约 0.00064%。新带宽保护用泰勒余项和频响导数给出连续频带保守界；无法证明或超门限时拒绝认证，不通过放宽门限或隐藏失败来生成数据。
## 后续精度工具与当前验收状态

用户追加最终要求：完整 361 秒业务，仅允许保留既有 IQ 约 357–361 秒的末尾连接失败；末段由其他协作者处理。本次不修改 STK trace、末段几何、切换/同步补偿、原始 bundle 或原 full_pass.py 的判定规则。

新工具：

- `resample_stk_geometry.m` 从原 STK 位置/速度做 Hermite 加密，支持非均匀真实 QD 生成时间轴。
- `channel_band_error.m` 用 sinc 核解析积分整个 4.5 MHz 带宽。测试包含一个 129 点频率网格错误给出零误差、连续频带真实 NRMSE 为 sqrt(2) 的反例。
- `certify_subarray_bandwidth.m` 用保留复数相消的一阶项和二阶泰勒余项控制子阵平均时延误差，再以带内能量积分和反三角不等式确定 NRMSE 上界。它是带内 NRMSE 界，不是单个深零陷频点的相对误差。
- `export_fidelity_subarrays.m` 用真实 QD 时间留出点自适应加密，保存实际参考数组和生成条件绑定的检查点，拒绝超门限数据。
- `validate_fidelity_reference.m` 使用另一批真实生成参考，按连续频带积分验收，并用两档频率数值网格交叉检查。
- `export_full_fidelity.m` / `generate_bounded_reference.m` 使用原完整轨迹的同一个初始阵元/路径功率参考分块生成，逐批验证共同点。前 357 秒自适应加密，尾部原始 4 个快照保留，完整时长不截短。最终还有每个输出区间内两个未用于当前选点的独立留出点。
- Python bundle 检查验证 1% 门限、误差合成、实际时间间隔与认证前缀/未认证尾部数量；链路预算审计在密集时间轴上独立计算 Hermite 几何，继续检查原 trace SHA256 和重复大尺度损耗。
- C adapter 已去掉逐采样重复二分搜索，按块定位后随采样时钟移动索引，仍保留逐采样系数/时延更新；优化后完整回归再次通过。

### 已完成的量化验证

| 验证 | 实测 |
|---|---|
| 下行首 2 秒，独立均匀 1 ms 参考 | 全局 NRMSE 0.1605824%，最差 0.5285695%，含子阵界的组合界 0.5315809% |
| 上行首 2 秒，独立均匀 1 ms 参考 | 全局 NRMSE 0.1339812%，最差 0.4889715%，组合界 0.4914282% |
| 原 1 秒下行数据，独立参考负向验收 | 最差约 51.506%，正确拒绝 |
| 新密集下行 C adapter | 2483 个节点/中点、四种速率，ASan/UBSan 通过，最大绝对 IQ 误差 1.18234311e-11 |
| 固定原功率参考的分块证明 | 测试点分布在 IQ 0/100/200/300/357 秒；分块相对整体生成的系数相对误差 2.53816939695e-14，时延差 0 |
| 完整导出器小规模验证 | 1 秒认证前缀加原剩余尾部，2239 个真实参考、640 个总输出节点；组合界 0.4998213%，与原尾部连接检查通过 |
| 数学及格式检查 | MATLAB 解析几何、可见性、连续频带界、危险带宽拒绝、频率混叠反例、冲突参数拒绝通过；Python 14 项格式/审计测试通过 |

独立原始参考位于主仓库 `.runtime/fidelity-dl-1000us.mat` 和 `.runtime/fidelity-ul-1000us.mat`，未加入 Git。短窗口输出与全程缓存也在 `.runtime/`；原始 UE 日志不发布。

### 精确复现入口

MATLAB R2023b、QuaDRiGa 2.8.1-0、seed=20260925，在仓库根目录执行：

```matlab
addpath('quadriga/matlab'); addpath('quadriga/tests');
test_fidelity_helpers;
diagnose_channel_fidelity(0.001);
validate_fidelity_reference('.runtime/fidelity-adaptive-test','.runtime/fidelity-dl-1000us.mat');
validate_fidelity_reference('.runtime/fidelity-adaptive-uplink','.runtime/fidelity-ul-1000us.mat');
t=read_stktrace2('examples/fdd-pass/trace.csv');
export_full_fidelity('downlink','.runtime/fidelity-full/downlink',t.times_s(1)+357);
export_full_fidelity('uplink','.runtime/fidelity-full/uplink',t.times_s(1)+357);
```

完整导出输出目录必须不存在；`.work` 中保存源代码/trace/功率参考签名及 `samples-*.mat`。相同条件中断后可复用缓存，输入改变则拒绝混用。不能任意修改生成器后继续沿用旧签名。内存由逐阵元批次控制，保存的是归一化四端口参考。

已执行的新增命令：

```bash
python3 -m unittest quadriga.tests.test_validate_bundle quadriga.tests.test_audit_link_budget
python3 -m quadriga.tools.audit_link_budget .runtime/fidelity-adaptive-test examples/fdd-pass/trace.csv
python3 quadriga/tests/run_qd_rfsim_adapter_test.py --sanitize --oai-repo /home/duyaya/OAI/self-contained-test/.runtime/oai --build-repo /home/duyaya/OAI/self-contained-test/.runtime/oai --bundle .runtime/fidelity-adaptive-test --trace examples/fdd-pass/trace.csv
```

运行副本完整回归日志：`.runtime/fidelity-final-regression.log` 和 `.runtime/fidelity-optimized-regression.log`，均退出 0。密集下行审计的最大功率归一化误差 2.69e-8、残余增益为零。

### 正在进行，尚不能宣布完成

双向完整前缀生成与独立时间参考验收已启动。随后必须把最终 bundle 接入 `scripts/env_subarray4_fidelity.sh`，运行 `scripts/test_fidelity.sh` 和完整业务，独立验算公式并定位丢包/失步发生区间。此前短窗口通过不能替代这一步。原 `scripts/full_pass.py` 的严格全程判定保持，已知尾部失败与新前缀验收结论分别记录。

QuaDRiGa 原始载波采样定理警告保留；本次采用的是去除公共载波项后的残余基带频响验收，有限真实时间参考不等价于连续时间的数学误差证明。绝对 EIRP 标定也不属于本次已验证结论。

### 2026-10-17：补入 RFsim 分数时延误差预算

仅验证连续时延频响不足以证明实际 IQ 精度。旧三次 FIR 在首 2 秒下行真实信道上的最差频带误差为 2.0952%，超过门限。当前工作区改用对称 12 点 Lagrange 核；前视 5 样本来自现有 STK 传播缓冲，不添加群时延。首 2 秒新核最差误差为 0.12355%，逐路径三角不等式上界为 0.36366%。整数时延直接取样，分数时延权重可按完全相等条件缓存，不进行量化。

`channel_fir_bound` 对每条路径的 FIR 与理想时延进行 sinc 核解析频带积分，再合成保守端口界。`validate_runtime_fidelity` 遍历全部缓存真参考，以相同参考功率计算时间插值与 FIR 的联合上界，再加子阵界。报告绑定当前 manifest SHA256；Python 校验拒绝旧报告、错误采样率、缺少非输出节点、伪造组合预算。最终 `scripts/test_fidelity.sh` 必须通过该校验。

已执行：

```matlab
addpath('quadriga/tests');
test_fractional_band;
validate_runtime_fidelity('.runtime/fidelity-full-driver-test','.runtime/fidelity-full-driver-test.work');
```

结果：解析核测试通过；1 秒前缀 2239 个真实参考（其中1959个不是输出节点），时间插值最差 0.49750%，FIR 最差界 0.19499%，三项联合上界 0.68077%，通过 1% 门限。该结果只对应此小样本，不能外推为完整过境已通过。

```bash
python3 -m quadriga.tools.validate_runtime_fidelity .runtime/fidelity-full-driver-test
python3 -m unittest quadriga.tests.test_validate_bundle quadriga.tests.test_audit_link_budget
```

报告绑定校验和15项测试通过。完整缓存提前抽查约5900点/方向，DL FIR 最差界0.63002%、UL0.46217%；因此完整导出器同时约束时间误差和三项联合预算（选点使用0.95%裕量，最终验收1%），不能仅沿用首2秒的预算。导出后运行：

```matlab
validate_runtime_fidelity('.runtime/fidelity-full/downlink','.runtime/fidelity-full/downlink.work');
validate_runtime_fidelity('.runtime/fidelity-full/uplink','.runtime/fidelity-full/uplink.work');
```

完整双向参考仍在生成。原始12点实现的 `scripts/test.sh` 通过；首次静态业务PDU超时，保留失败记录；复验 `source scripts/env_subarray4.sh; python3 scripts/validate_spatial.py --ports 4` 退出0、静态/动态业务与公式审计通过（日志 `fidelity-symmetric-business-retry.log`）。最新等价运算优化的数值回归通过，但其业务复验再次出现初始同步失败/PDU超时，原因尚未确定，不能视为只有已知尾部失败。完整361秒新信道业务尚未完成，最终验收仍待进行。

#### 对称 FIR 阶段复验

等价优化使用前后缀积替代逐 tap 除法，且仅在分数时延完全相等时复用权重；没有近似查表。`scripts/build.sh` 构建通过，`source scripts/env_subarray4.sh; bash scripts/test.sh` 完整通过（`fidelity-cached-fir-regression.log`）。ASan/UBSan 下 DL/UL 各723节点/中点，四种时钟速率，实际 IQ 与独立 Lagrange 计算最大误差分别2.12129e-11、1.51165e-11；包括块内跨节点与静音边界。

后台生成任务降低调度优先级后，再次执行 `source scripts/env_subarray4.sh; python3 scripts/validate_spatial.py --ports 4` 退出0：静态 `smoke-0-1792167667735970373`、动态 `smoke-1-1792167791992502903` 均PDU成功，ping10/10，双向UDP零报告丢包，PBCH失败0，四端口及STK公式审计通过。日志为 `fidelity-cached-fir-business-retry.log`。先前失败记录保留；不能仅凭本次成功断言资源争用就是唯一根因。

大规模完整 bundle 的 IQ 测试新增可选 `--max-points`，默认仍遍历全部节点与中点；完整精度流程使用4097个确定性分层点，始终覆盖首尾、四种速率和静音边界。17点入口已通过ASan/UBSan，误差1.63961e-11。数学精度仍遍历全部真实 QD 缓存，文件与C reader校验也不减少；分层只避免对相同卷积实现重复数亿组等价运算。

上述业务使用原完整 bundle 验证新 FIR，不能替代尚未完成的新密集 bundle 的361秒业务验收。
