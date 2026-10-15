# MISO 步骤一：空间信道数据与契约验算（2026-10-15）

## 实现范围

新增 `satellite_2port_ground_omni`：两个独立全向阵元、半波长间距、固定 ENU 朝向，地面一个阵元。下行保留 `[Rx=1, Tx=2, Path=11, Snapshot=362]`；上行在对应载频重新生成，再转置 Rx/Tx 轴为 `[2,1,11,362]`，不取共轭。不调用单波束合成函数。原 16x16 单波束/SISO 数据保持不变。

新增显式归一化标记 `unit_snapshot_mean_link_power`，每个快照使用整个空间矩阵共享的功率、时延和相位参考：

- 所有 Rx/Tx 链路的路径功率总和 / (Rx × Tx) = 1；不是分别把每个链路归一化。
- 所有链路共同减去最早激活路径时延，保留阵元间时延差。
- 所有系数乘同一个公共相位旋转，保留空间相位差。
- residual_gain_db 仍为零；STK 继续提供绝对增益。

C reader、Python validator、审计器和 schema 接受新标记，同时保留旧 `unit_snapshot_link_power` 语义。旧版本 reader 会拒绝新标记，必须重新构建。

## 已执行验证

Windows MATLAB R2023b，仓库内 QuaDRiGa 2.8.1-0：

```text
matlab -batch "addpath('quadriga/matlab'); export_example_miso"
matlab -batch "addpath('quadriga/tests'); test_spatial_normalization"
```

两者退出码均为 0。空间参考测试验证 2i 的阵元复系数比、2 ns 阵元时延差、共同相位去除、平均链路功率及上行轴转置。上下行均输出到独立 `examples/fdd-miso`，没有覆盖已有示例。

WSL Ubuntu-22.04，项目既有系统 Python 3.10.12：

```bash
python3 -m quadriga.tools.audit_link_budget examples/fdd-miso/downlink examples/fdd-pass/trace.csv
python3 -m quadriga.tools.audit_link_budget examples/fdd-miso/uplink examples/fdd-pass/trace.csv
```

| 验算项 | 下行 | 上行 |
|---|---:|---:|
| Tx × Rx | 2 × 1 | 1 × 2 |
| 快照 / 路径 | 362 / 11 | 362 / 11 |
| 归一化平均链路功率最大误差 | 5.831e-8 | 5.791e-8 |
| 时间轴误差 | 0 s | 0 s |
| 最早激活路径超额时延 | 0 s | 0 s |
| 公共参考相位最大误差 | 1.598e-8 rad | 3.532e-8 rad |
| residual_gain_db 最大绝对值 | 0 dB | 0 dB |
| STK 与组合信道 FSPL 斜率 | 均为 1.16978110066 | 均为 1.16978110066 |

上述功率误差符合 complex64 落盘精度；不是物理预算误差。STK SHA256 为 `3d63d47a050f68bf670e4d298cc579c7f0f09b0550b58c849fdc0a12b2dbda18`。

## 物理解释与限制

这次从 16x16 等效波束切换到双阵元多端口是实验模型变更，不能把两者指标变化直接归因于 MISO 算法。继承的 STK 绝对增益尚未重新标定为双阵元的单阵元参考；因此目前可验证空间信道与数字链路，不宣称已完成绝对 EIRP/阵列增益预算标定。该限制写入 antenna.json。

1 秒时间网格仍触发 QuaDRiGa 采样定理警告。空间维度正确不意味着高速多径衰落的时间精度已经充分。feeder link 仍由 STK 表达，未增加逐阵元 feeder/transponder 模型。
