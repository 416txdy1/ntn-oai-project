# 卫星 16×16 阵列与地面全向信道（2026-10-14）

本次是 **Experimental Method Change**：QuaDRiGa 默认 service link 从两端全向改为卫星 16×16 矩形阵列、地面单阵元全向。OAI/RFsim 仍使用一个波束射频端口，不扩展 MIMO，也不修改 feeder link、STK 保存场景、原 trace、载频、随机种子或验收阈值。

## 具体配置及边界

| 项目 | 当前实现 |
|---|---|
| 卫星阵元 | 16×16，共 256 个，中心对称矩形格点 |
| 阵元间距 | 每个方向的载频对应 0.5λ；DL 2.4884 GHz，UL 1.6149 GHz |
| 地面端 | qd_arrayant('omni')，一个阵元/一个射频端口 |
| 卫星姿态 | 根据 ECEF 位置及速度，加地球自转项估计 geocentric VVLH；机械法线指向星下点 |
| 跟踪波束 | 每个快照的 satellite→UE LOS，等幅、单位总激励功率的电子相位权重 |
| 阵元方向图 | 功率余弦指数 1 的近似；后半球恒定 30 dB 抑制；Fa 为功率平方根 |
| 扫描限制 | 局部方位/俯仰 ±60°；STK 标为可见但越界则拒绝导出；不可见的越界快照由 STK 静音 |
| 时延合并 | 阵元时延均值，与等幅 QuaDRiGa 耦合约定一致，属于窄带波束近似 |
| 绝对增益 | STKTRACE2；阵列多径先相干合成再归一化，residual_gain_db 仍为 0 |

对齐的是阵列规模、间距、地面全向模式和单目标跟踪。保存的 STK 天线还使用 MVDR，且 UsePolarization=false；本实现采用均匀幅度相位跟踪，没有实现 STK 的干扰协方差、自适应零陷或完整 MVDR 约束。QuaDRiGa 的既有极化模型保留，地面 omni 是垂直极化；功率余弦阵元及从轨迹估计的姿态也不宣称逐项复刻 STK 方向图/姿态。

STK 官方说明中的阵元配置、扫描与波束形成概念见 [Phased Array Antenna](https://help.agi.com/stk/12.9.0/Content/comm/PhasedArrayAntenna.htm)；本次 API 与相位/时延合并依据为仓库固定版 QuaDRiGa 2.8.1-0 的 qd_arrayant.interpolate、qf.calc_ant_rotation 和 qd_builder.get_channels 源码。

## 为什么还是 SISO

数据流为：

```text
卫星阵列信道 [Rx=1, Tx=256, Path=11, Snapshot=362]
        ↓ 每个快照乘以 256×1 的相位权重，沿阵元维度相干求和
单波束信道 [Rx=1, Tx=1, Path=11, Snapshot=362]
        ↓ 去公共相位、改为超额时延、单位路径功率归一化
QDCHANNEL1 → 原有 RFsim SISO adapter
```

阵元数决定天线空间方向性，射频端口数决定 OAI 看到多少路信号。不能把 256 个阵元直接写成 256 个 OAI 发射端口，也不能先把每个阵元单独归一化再合成。权重的定义为抵消 LOS 阵元间相位，因此 MATLAB 使用普通转置 `.'`，误用共轭转置 `'` 会把扫描相位方向反过来。上行在 UL 载频单独生成，以窄带互易的标量有效端口表示卫星接收阵列，不对传播系数取共轭。

理想各向同性阵元沿目标相干叠加的增益为 256（24.082 dB）。这个值只用于阵列数值测试；输出按快照归一化后不会再次把它叠加到 STK 绝对增益。不同路径的相对权重、相位和波束抑制仍保留。

## 当前回放与旧对照

- 新阵列数据：examples/fdd-pass-array/downlink、uplink。scripts/env.sh 默认选择它们。
- 两个版本共同使用未变的 examples/fdd-pass/trace.csv，SHA256 为 3d63d47a050f68bf670e4d298cc579c7f0f09b0550b58c849fdc0a12b2dbda18。
- 原全向数据：examples/fdd-pass/downlink、uplink，保留原字节用于对照；没有覆盖旧实验结果。

初始化环境后，如需复现历史全向基线，显式覆盖：

```bash
source scripts/env.sh
export OAI_QD_DL_CHANNEL="$NTN_ROOT/examples/fdd-pass/downlink"
export OAI_QD_UL_CHANNEL="$NTN_ROOT/examples/fdd-pass/uplink"
```

回放两端仍须使用同一 trace 和 rate。Windows/WSL 入口运行已有 Linux 副本，需按文档重新同步和构建后才能使用本次变化；本次仅修改 D 盘仓库，没有同步、构建或启动其他运行副本。

## 导出和元数据

先运行 `python3 scripts/prepare_sources.py` 解包固定版源码。在 MATLAB 中：

```matlab
addpath('quadriga/matlab');
export_example_fdd(); % 输出 .runtime/generated-fdd-array，拒绝覆盖已有结果
```

通用导出器的 `options.antenna_profile` 默认为 `satellite_16x16_ground_omni`，显式 `omni` 可重新生成全向对照。输入路径、载频及随机种子的原调用方式保持兼容。

每个新 bundle 附带 antenna.json，记录阵元/端口数、间距、跟踪方法、姿态估计、最大阵元间时延跨度、频率、方向和来源 trace。该文件通过 manifest_sha256 绑定原 manifest。QDCHANNEL1 v1 manifest、二进制轴顺序和 C 接口不变；Python validate_bundle 校验可选元数据，旧 bundle 无需补文件。新示例的 JSON 按原字节纳入 Git，避免 Windows 换行转换破坏绑定哈希。

## 验证与研究限制

MATLAB R2023b / QuaDRiGa 2.8.1-0 已完成 256 阵元间距、后瓣、相干增益、非零扫描角零点、VVLH/Euler 姿态、扫描越界拒绝和实际小规模导出测试；完整上下行各 362 快照、11 路径导出成功。

原 trace 的 1 秒快照仍触发 QuaDRiGa 采样定理警告；本次不改变时间网格，也不消除原尾段位置混合问题。没有启动 STK 重导出，无法仅根据原 trace 证明它的绝对增益已包含当前保存场景的全部天线设置。本次新数据只更改 QuaDRiGa 的相对多径/阵列模型。

未重新全量编译 OAI，没有启动 gNB/UE/5GC 或运行 361 秒业务；原完整业务失败的历史结果不能当作新阵列的验收结果，也不能声称阵列已修复失步。
## 实际验证记录

本轮 Python 使用 Ubuntu-22.04 的 /usr/bin/python3 和既有系统依赖，未安装新依赖。日志仅保留本机 .planning/2026-10-14-zky-delivery-audit/terminal.log。

| 命令/检查 | 结果 |
|---|---|
| MATLAB `test_satellite_antennas(quadriga_path, output_dir)` | 0；256 阵元、间距、30 dB 后瓣、24.082 dB 相干增益、扫描零点、移动 LOS、Euler 奇点、真实全轨迹双载频跟踪、可见越界拒绝、真实阵列及 omni 导出通过 |
| MATLAB `export_example_fdd()` | 0；DL/UL 各 362 快照，11 路径，1×1 波束端口，固定 seed=20260925 |
| `python3 -m unittest quadriga.tests.test_validate_bundle quadriga.tests.test_channel_math quadriga.tests.test_audit_link_budget` | 0；16 测试通过，包含 sidecar 哈希与端口一致性 |
| `python3 scripts/check_delivery.py` | 0；4 个源码归档、旧/新双向 bundle 的哈希、数值及来源匹配通过 |
| `bash scripts/test.sh`（见下方只读构建环境覆盖） | 0；完整回归通过，含 `python3 local_ntn/test_trace_validation.py`、`python3 local_ntn/test_real_iq.py` |
| 新双向 C reader 和 ASan/UBSan adapter | 0；每方向 723 快照/中点通过，最大卷积误差约 1.82e-12 |
| `bash -n scripts/env.sh`、`bash -n scripts/test.sh` | 0 |

原始 361 秒 trace 与原全向 bundle 均未改。新 bundle 在二进制落盘后的最大单位路径功率误差：DL 5.97e-8，UL 8.14e-8；residual_gain_db=0，组合 FSPL 斜率与原 STK 的 1.16978110066 一致，没有再计入绝对阵列增益。最大阵元间时延跨度为 DL 3.629 ns / UL 5.592 ns；本示例的平均时延合并仍是窄带近似。

完整外层验证命令：

```powershell
wsl.exe -d Ubuntu-22.04 -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/2026-10-14-zky-delivery-audit/run_antenna_tests.sh
```

本机审计脚本执行仓库的 scripts/test.sh，仅把 OAI_REPO、OAI_BUILD_REPO 和 OAI_BUILD_DIR 覆盖到已核对且本轮未改的 /home/duyaya/OAI/self-contained-test/.runtime/oai 及其构建目录。只读使用生产源码、编译参数和生成头文件，重新编译 IQ/QD 测试；TMPDIR 在本仓库 .runtime/antenna-check/tmp，Python 禁止写缓存。没有对外部运行副本执行同步、构建或 Git 操作。

Git 暂存树独立导出后，上下行 bundle 的所有文件与本机生成结果逐字节一致，antenna.json 与 manifest 的绑定哈希验证通过；.runtime/.private 及本次工作日志未纳入提交。
