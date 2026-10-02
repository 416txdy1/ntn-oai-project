# 当前单仓库入口

QuaDRiGa 源码由 vendor/quadriga-source.tar.gz 提供；运行 python3 scripts/prepare_sources.py 后可用 quadriga/matlab/export_example_fdd.m 重新生成示例。主调试入口见 ../local_ntn/MANUAL_RUN.md。以下为模块说明及历史记录。

# QuaDRiGa 离线信道接口（QDCHANNEL1）

本目录定义 STK、QuaDRiGa 与 OAI RFsim 之间的离线数据边界，并提供 MATLAB/Octave 离线导出器。QDCHANNEL1 已在外部 OAI 源码的 RFsim IQ 路径中完成 SISO 稀疏多径接入，详见 [集成说明](docs/step04_rfsim_integration.md) 和 [2026-09-28 复核报告](docs/recheck_20260928.md)。完整 gNB/UE/5GC 联调尚未完成。

## 为什么单独定义接口

现有 `STKTRACE2` 由 RFsim IQ 样本时钟驱动，负责卫星绝对几何、可见性、公共传播时延、主体 Doppler、链路功率和 C/N。QuaDRiGa 的 `qd_channel` 则提供随快照演化的复信道系数和路径时延，原生张量顺序为 `[Rx antenna, Tx antenna, path, snapshot]`。

直接叠加两套模型会重复应用路径损耗、传播时延和 Doppler。QDCHANNEL1 因此使用以下职责划分：

| 来源 | 负责内容 |
|---|---|
| STKTRACE2 | 可见性、绝对几何、公共时延、卫星主体 Doppler、绝对链路幅度和噪声基准 |
| QDCHANNEL1 | 归一化复多径系数、相对超额时延、零均值残余大尺度增益 |

对某个快照、接收天线、发射天线和路径，后续 RFsim 应按下式组合：

```text
h_final[path] = stk_absolute_amplitude
              * 10^(quadriga_residual_gain_db / 20)
              * quadriga_normalized_coefficient[path]

delay_final[path] = stk_bulk_delay + quadriga_excess_delay[path]
```

主体 Doppler 仍由 STK 的径向速度产生。QDCHANNEL1 复系数只携带去除主体 Doppler 后的残余相位演化，防止频移重复计数。

## Bundle 结构

每个 bundle 是一个目录：

```text
bundle/
├── manifest.json
├── times.f64
├── delays.f64
├── coefficients.cf32
└── residual_gain_db.f32
```

数组统一使用小端字节序，磁盘轴顺序统一为 `[snapshot, rx, tx, path]`：

| 文件 | 类型 | 元素数量 | 单位/含义 |
|---|---|---:|---|
| `times.f64` | float64 | `S` | STK trace 相对秒，严格递增 |
| `delays.f64` | float64 | `S*R*T*P` | 相对超额时延，秒，非负 |
| `coefficients.cf32` | complex64，实虚交错 | `S*R*T*P` 个复数 | 归一化复电压系数 |
| `residual_gain_db.f32` | float32 | `S*R*T` | 相对 STK 绝对增益的残余大尺度增益，dB |

`coefficients.cf32` 的每个复数保存为连续两个 float32：`real, imag`。每个 `(snapshot, rx, tx)` 的所有路径满足：

```text
sum(abs(h[path])**2) = 1
```

未激活路径以零系数表示。每个链路快照至少一个激活路径，且激活路径的最小相对时延必须为 0（允许 `1e-12 s` 数值误差）。

## 时间与插值

- `times.f64` 使用与 STKTRACE2 相同的 trace 秒坐标。
- RFsim 查询时刻仍为 `trace_epoch + IQ_timestamp / sample_rate * rate`。
- v1 规定复系数和时延在相邻快照间线性插值；路径出生/消亡通过系数平滑到零表示。
- 导出器必须先让 QuaDRiGa 在目标轨迹位置完成插值，再写入固定路径维度；不要在 OAI 运行时调用 MATLAB/Octave。
- 扫描越界或 STK 不可见时沿用现有策略：信号静音，不循环、不冻结最后状态。

## 可复现性

`manifest.json` 必须记录：

- QuaDRiGa 版本、场景名和随机种子；
- 输入 STKTRACE2 文件 SHA256；
- 中心频率、`downlink`/`uplink` 方向和四个维度；
- 每个二进制文件的 dtype、逻辑元素数、字节数和 SHA256。

JSON Schema 位于 `schema/channel_bundle_v1.schema.json`。标准库校验器除检查 manifest 外，还会流式检查文件大小、哈希、时间单调性、有限值、非负时延、零参考时延和路径功率归一化。

## MATLAB/Octave 导出

导出器位于 `matlab/export_stk_to_qdchannel.m`，数据流为：

```text
STKTRACE2 ECEF 轨迹
  -> 以首个 UE 点为参考的局部 ENU 轨迹
  -> 对齐的 QuaDRiGa Tx/Rx 双移动轨迹
  -> qd_layout.get_channels()
  -> 去公共相位、路径功率归一化、相对时延、零均值残余增益
  -> QDCHANNEL1 bundle
```

“去公共相位”使用每个天线链路的最早激活路径作为参考，消除 QuaDRiGa 输出中的公共传播相位演化，同时保留路径之间的相对相位。这样 OAI 后续使用 STK 径向速度添加主体 Doppler 时不会重复计算。

示例（MATLAB 或兼容的 Octave 8 环境）：

```matlab
addpath('quadriga/matlab');
options.quadriga_path = 'D:\tools\QuaDRiGa';
options.center_frequency_hz = 2.0e9;
options.link_direction = 'downlink';
options.scenario = 'QuaDRiGa_NTN_Rural_LOS';
options.random_seed = 20260925;
export_stk_to_qdchannel('path/to/stk_trace.csv', 'path/to/qd_downlink', options);
```

QuaDRiGa NTN 场景始终以卫星为 Tx、地面 UE 为 Rx 建模。当前 SISO uplink 使用窄带信道互易性复用同一物理多径，并在 manifest 中标记 `link_direction=uplink`；未来扩展 MIMO 时必须显式转置 Rx/Tx 天线维度。

该入口已使用 MATLAB R2023b 与 QuaDRiGa 2.8.1-0 对 1387 个真实 STK 快照完成运行时验证。1 秒 STK 几何网格在 2 GHz 下会触发 QuaDRiGa 的采样定理警告：它可验证离线格式与批量几何演化，但不足以还原毫秒尺度的残余多径 Doppler。主体传播时延、绝对增益和卫星 Doppler 仍由 STK 数据驱动。

当前入口有意限制为一个卫星—UE SISO service link，并为上下行分别生成 bundle。`quadriga_path` 必须显式提供，不会静默下载或安装 QuaDRiGa。STK 不可见区间仍生成时间对齐的快照，但后续由 STKTRACE2 可见性标志静音。

## 校验命令

```powershell
python -m quadriga.tools.create_example_bundle quadriga/examples/siso_two_path
python -m quadriga.tools.validate_bundle quadriga/examples/siso_two_path
python -m unittest quadriga.tests.test_validate_bundle quadriga.tests.test_channel_math quadriga.tests.test_audit_link_budget
```

生产导出器将 `residual_gain_db` 写为 0 dB。原因是 QuaDRiGa 总系数功率包含随卫星距离变化的 path gain，而 STKTRACE2 已提供绝对接收功率；简单减去时间均值仍会重复计算动态路径损耗。归一化多径系数、相对路径功率、K-factor 和超额时延仍由 QuaDRiGa 提供。

真实 bundle 必须额外执行链路预算审计：

```powershell
python -m quadriga.tools.audit_link_budget path/to/qd_bundle path/to/stk_trace.csv
```

审计器会检查 STK provenance、时间对齐、逐快照单位多径功率、零参考超额时延、公共相位稳定、残余增益与 FSPL 的斜率，以及合成前后 STK 路径损耗斜率是否保持不变。

`tools/channel_math.py` 是与 MATLAB 归一化公式一致的 Python 标准库参考实现，用于在没有 MATLAB/Octave 的机器上验证公共相位去除、功率/时延契约与 ENU 坐标方向。它不代替真实 QuaDRiGa 运行。C 读取器和 RFsim 适配器位于 `oai/`，相关测试位于 `tests/`。

## 官方依据

- QuaDRiGa 官方仓库：<https://github.com/fraunhoferhhi/QuaDRiGa>
- QuaDRiGa v2.8.1 文档：<https://quadriga-channel-model.de/download/534245>
- `qd_channel` 合并实现展示的系数/时延维度：<https://github.com/fraunhoferhhi/QuaDRiGa/blob/main/quadriga_src/%40qd_channel/combine_tx_rx.m>
