# 节点三：16×16 阵列映射为 4 个子阵端口（2026-10-15）

## 链路与物理映射

本节点使用 256 个物理阵元、4 个独立 RF 通道、1 个 UE 接收通道和 1 个数据层。下行数据流为 OAI 四路 IQ → 四个子阵有效信道 → UE 一路 IQ；上行反向为 1×4。没有把四路 RF IQ 再离线压成单路。

`combine_satellite_subarrays.m` 按阵元局部 y/z 坐标划分四个互不重叠的 8×8 子阵，每组 64 阵元。端口 1～4 依次对应 (-y,-z)、(+y,-z)、(-y,+z)、(+y,+z)。MATLAB 阵元索引按 ndgrid 的 y 优先顺序；不能直接把连续 64 个索引当作 8×8 象限。

每快照原全阵 LOS 相位权重模为 1/16。子阵内乘 2 后模为 1/8，各端口权重范数为 1。若 W 是 256×4 映射矩阵，则 WᴴW=I，任意四路输入 x 都满足 ||Wx||²=||x||²。有效路径系数 H_port=H_element W，普通转置运算不重复取共轭。UL 使用对应载频重新生成传播系数，然后转置空间轴，不对传播系数取共轭。

四个子阵都使用 VVLH 近似姿态和 LOS 跟踪；相干合成仅在每个子阵内部，四端口之间保留相对幅度、相位、时延，由 OAI 原生预编码处理。OAI 的 N1=2、N2=1、XP=2 是逻辑码本布局，不把这四个同极化子阵宣称为物理双极化阵列。

## FDD 几何与时延近似

新 profile `satellite_16x16_4port_ground_omni` 增加显式参考频率：DL/UL 都使用 2.4884 GHz 定义的半波长物理间距 0.06023799590098055 m，阵列外侧阵元中心跨度约 0.90357 m。实际 DL 为 0.5λ，UL 1.6149 GHz 为 0.32448561324545894λ。载频改变电气间距和相位，不改变实际阵列尺寸。旧 profile 及旧示例数据不重生成。

同一路径的子阵内时延取均值，四个 RF 端口之间不平均。最大子阵内时延差 DL 1.693305522 ns、UL 1.693573322 ns；相对 7.68 Msps 的 130.208 ns 采样周期约为 1.30%。按占用带宽 4.5 MHz 给出的保守相位跨度 2πBΔτ 小于 0.048 rad。它支持当前窄带近似，但不是逐阵元宽带时延仿真的替代品。

`antenna.json` 保存完整元素→端口表、子阵大小、单位权重功率、实际间距、载频电气间距、最大时延差。校验器拒绝错误映射、功率、几何、负时延跨度；预检查同时拒绝模式/profile 不符和 FDD 双向几何不一致。

## 复现与数值测试

MATLAB R2023b、QuaDRiGa 2.8.1-0、seed 20260925。执行：

```matlab
addpath('quadriga/tests'); test_satellite_subarrays;
addpath('quadriga/matlab'); export_example_subarray4;
```

退出 0。解析测试验证每组 64 元素、单子阵相干功率 64、WᴴW=I、任意输入功率守恒、四端口按 1/2 权重组合等于原全阵合成、相对相位与时延保留、重排元素后结果不变；错误权重必须被拒绝。64 是合成前归一化约定下的解析相干功率，不是运行链路的绝对阵列增益测量。

在 Linux 副本 /home/duyaya/OAI/self-contained-test 执行：

```bash
OAI_SPATIAL_MODE=miso4-subarray bash scripts/test.sh
```

退出 0。覆盖 trace parser、真实 IQ 的全部三种空间场景、接收队列历史、Python 校验、C reader、ASan/UBSan 双向卷积。固定孔径后的每方向数据均为 362 快照、11 路径。

| 方向 | Tx×Rx | 平均链路功率最大误差 | 参考相位误差 rad | 723 点卷积最大误差 |
|---|---|---|---|---|
| DL | 4×1 | 4.4128e-8 | 6.5356e-9 | 1.1065e-11 |
| UL | 1×4 | 4.7570e-8 | 4.9146e-8 | 4.4148e-12 |

全部新旧 MISO bundle 直接通过 Git 暂存区字节读取，核验 manifest 与四个数组的 SHA256；六组双向数据均通过。仅提交源码、示例和去敏文档，不提交 .runtime、私有配置、原始 UE 日志。

## 运行入口与边界

已配置实验副本的 root shell：

```bash
source scripts/env_subarray4.sh
python3 scripts/validate_spatial.py --ports 4
```

默认 env.sh 仍为 SISO；旧 Windows smoke 包装入口会载入默认环境，多端口请在同步后的 WSL 副本使用上述入口。

绝对 STK 功率沿用现有参考，尚未重新标定为每个子阵的端口参考；空间平均链路功率归一化保留相对结构，原 STK 全阵增益与数字合成增益不能未经校准直接叠加做物理 EIRP/容量结论。侧文件显式标记 not_calibrated_STK_reference。1 秒轨迹快照仍触发 QuaDRiGa 采样密度警告，不支持完整快速残余 Doppler 频谱研究。当前测试是有界静态/动态业务，不覆盖完整 361 秒过境。

## 端到端业务结果

source scripts/env_subarray4.sh; python3 scripts/validate_spatial.py --ports 4 退出 0，自动清理成功。

| 模式/label | ping | UL UDP | DL UDP | PBCH 失败 |
|---|---|---|---|---|
| static / smoke-0-1792052243958331347 | 10/10 | 96.3 Kbit/s，0/130 丢包 | 100 Kbit/s，0/130 丢包 | 0 |
| dynamic / smoke-1-1792052331628445386 | 10/10 | 91.7 Kbit/s，0/130 丢包 | 100 Kbit/s，0/130 丢包 | 0 |

PDU 与双向信道均正常加载。动态四个 Tx 端口非零窗数 13/10/10/10，峰值 18463.803/13673.518/13673.595/13673.541。运行独立验算最大误差：delay 4.974e-7 ms、Doppler 4.790e-4 Hz、gain 4.396e-4 dB、C/N 4.387e-4 dB，均在输出舍入精度内。RTT 平均 static 1138.561 ms、dynamic 1226.658 ms 是墙钟仿真开销，不作为几何传播时间。

最后用临时副本执行负向 preflight 验证（.runtime/check_subarray_preflight.py，已加载 env_subarray4.sh）：正确场景通过，替换为普通四阵元 DL 数据被拒绝；UL 参考频率乘 1.01 并一致更新物理/电气间距后，单份 sidecar 内部合法，但双向孔径不一致仍被拒绝。脚本退出 0，未修改原 bundle 或凭据。
