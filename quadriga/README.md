# QuaDRiGa 离线信道接口（QDCHANNEL1）

本目录定义 STK、QuaDRiGa 与 OAI RFsim 之间的离线数据边界。本阶段只固定接口和校验规则，尚未把 QDCHANNEL1 接入 OAI。

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
- 中心频率和四个维度；
- 每个二进制文件的 dtype、逻辑元素数、字节数和 SHA256。

JSON Schema 位于 `schema/channel_bundle_v1.schema.json`。标准库校验器除检查 manifest 外，还会流式检查文件大小、哈希、时间单调性、有限值、非负时延、零参考时延和路径功率归一化。

## 当前阶段命令

```powershell
python -m quadriga.tools.create_example_bundle quadriga/examples/siso_two_path
python -m quadriga.tools.validate_bundle quadriga/examples/siso_two_path
python -m unittest quadriga.tests.test_validate_bundle
```

后续步骤才会实现 MATLAB/Octave 导出器和 OAI C/C++ 读取器。

## 官方依据

- QuaDRiGa 官方仓库：<https://github.com/fraunhoferhhi/QuaDRiGa>
- QuaDRiGa v2.8.1 文档：<https://quadriga-channel-model.de/download/534245>
- `qd_channel` 合并实现展示的系数/时延维度：<https://github.com/fraunhoferhhi/QuaDRiGa/blob/main/quadriga_src/%40qd_channel/combine_tx_rx.m>
