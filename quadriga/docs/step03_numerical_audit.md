# Step 3 QDCHANNEL1 C 读取器数值复验

日期：2026-09-26

## 结论

QDCHANNEL1 C 读取器、真实下行/上行 bundle 和既有 STK/RFsim 链路均通过复验。数值结果表明：STK 仍是绝对路径损耗、主体时延和主体 Doppler 的唯一来源；QuaDRiGa bundle 仅提供归一化相对多径、超额时延和零大尺度残余增益，没有发生路径损耗或主体 Doppler 重复计算。

## 输入身份

- STKTRACE2：`stk_constellation_trace_blend.csv`
- SHA256：`680632212ffdbfa95a8e45a537acbfcad3c6dfaccfca1bc50283f0384c6e3e73`
- Downlink：1387 snapshots，SISO，11 paths
- Uplink：1387 snapshots，SISO，11 paths

同名 `.json` 文件不是该 bundle 的生成输入，其 SHA256 不匹配；provenance 校验会正确拒绝它。

## 真实数据指标

| 指标 | Downlink | Uplink | 判定 |
|---|---:|---:|---|
| 最大时间轴误差 | 0 s | 0 s | 通过 |
| 最大 tap 功率归一化误差 | 6.081311076933105e-08 | 6.081311076933105e-08 | 通过 |
| 最大零参考超额时延误差 | 0 s | 0 s | 通过 |
| 最大参考公共相位误差 | 1.8776618900713638e-08 rad | 1.8776618900713638e-08 rad | 通过 |
| 最大 residual gain | 0 dB | 0 dB | 通过 |
| residual/FSPL slope | 0 | 0 | 通过 |
| residual/FSPL correlation | 0 | 0 | 通过 |
| STK FSPL slope | 1.2038472634976762 | 1.2038472634976765 | 基准 |
| 组合后 FSPL slope | 1.2038472634976762 | 1.2038472634976765 | 与 STK 相同 |
| 主体时延范围 | 0.006219355981913133–0.010739148249658407 s | 相同 | STK 提供 |
| 主体 Doppler 范围 | -33766.102758760244–26982.80915488658 Hz | 相同 | STK 提供 |

DL 和 UL 的 times、delays、coefficients、residual_gain_db 四个 payload SHA256 均逐项相同；只有方向元数据不同，符合当前 SISO reciprocity 设计。

## 测试覆盖

- 13 个 Python schema、channel math 和 link-budget 单元测试。
- 截断 payload、等长 SHA 篡改、NaN delay、路径逃逸、非法 JSON 负例。
- 真实 DL/UL 的 C 加载、维度、provenance 和 smoke sampling。
- GCC `-Wall -Wextra -Werror -pedantic` 和 `-fanalyzer`。
- AddressSanitizer、UndefinedBehaviorSanitizer 和 leak detection。
- STK sample clock、物理边界、Hermite 导数、power-to-IQ、outage、真实 `rxAddInput`、噪声、时延和 Doppler 回归。

## 解释

如果 QuaDRiGa residual gain 再包含距离相关损耗，组合后 FSPL slope 会偏离 STK slope。此次 residual slope 为 0，且组合 slope 与 STK slope 完全一致，因此大尺度路径损耗没有重复。参考公共相位误差接近数值零，说明 QuaDRiGa 公共相位已移除，不会与 STK 主体 Doppler 重复。
