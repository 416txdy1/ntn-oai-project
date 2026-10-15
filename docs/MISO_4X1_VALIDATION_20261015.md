# 节点二：4×1 独立 RF 通道验收（2026-10-15）

## 修改与入口

新增 satellite_4port_ground_omni：4 个半波长间距、固定 ENU 朝向的全向阵元，identity coupling，分别保留空间系数与时延；上行转置为空间 1×4。随机种子、轨迹、载频和 QuaDRiGa 版本沿用 2×1 实验。独立 RF 通道指独立 IQ 序列，不意味着 LOS 信道统计不相关。

local_ntn/spatial_config.py、prepare_local.py、preflight.py、run_local.sh 支持 miso4：gNB 4 Tx/4 Rx，UE 1 Tx/1 Rx；N1=2、N2=1、XP=2、单数据层、CSI-RS。XP 是 OAI 码本的逻辑布局，此全向阵元验证场景不模拟双极化。保留 siso 和 miso2 入口，输出仍为独立的 gnb.miso.conf，不覆盖原模板。

```bash
source scripts/env_miso4.sh
python3 scripts/validate_spatial.py --ports 4
```

在已配置 Linux 副本 root shell 中运行；脚本只管理自己启动的核心网和 modem。

## 数值回归

生成数据：MATLAB R2023b 执行 addpath('quadriga/matlab'); export_example_miso4，退出 0。生成 examples/fdd-miso4/{downlink,uplink}，每方向 362 快照、11 路径。保留 QuaDRiGa 对 1 秒采样密度不足的警告，不能据此研究完整残余 Doppler 频谱。

Linux 副本 /home/duyaya/OAI/self-contained-test 执行 OAI_SPATIAL_MODE=miso4 bash scripts/test.sh，退出 0：trace parser、真实 rxAddInput 2×1/1×2/4×1/1×4、长历史队列、配置、Python 工具、C reader 与 ASan/UBSan 均通过。本阶段未修改 C 数据路径，复用节点一已构建的二进制。

| 方向 | 空间维度 Tx×Rx | 平均链路功率最大误差 | 参考相位误差 rad | 723 点卷积最大误差 | 历史样本数（30.72 MHz） |
|---|---|---|---|---|---|
| DL | 4×1 | 4.1894e-8 | 4.1753e-8 | 1.4666e-11 | 1221 |
| UL | 1×4 | 5.0014e-8 | 1.4707e-8 | 4.0674e-12 | 1586 |

每个 Tx 输入不同宽带伪随机 IQ，独立参考实现逐 Rx/Tx/path 计算；不以复制一条输入替代多端口验证。额外检查归一化共享参考、可见区间外静音、双向频率与端口维度一致。

## 实验边界

沿用 STK 绝对功率参考，尚未校准为四阵元的独立物理链路预算；不能将 2×1 与 4×1 的业务结果作为公平的阵列增益/容量对比。下一节点才加入 16×16 到 4 子阵端口映射。原始 UE 日志及 .runtime 不入库。

## 端到端结果

source scripts/env_miso4.sh; python3 scripts/validate_spatial.py --ports 4 退出 0。

| 模式/label | ping | UL UDP | DL UDP | PBCH 失败 |
|---|---|---|---|---|
| static / smoke-0-1792033608156231007 | 10/10 | 96.3 Kbit/s，0/130 丢包 | 100 Kbit/s，0/130 丢包 | 0 |
| dynamic / smoke-1-1792033695735320838 | 10/10 | 92.4 Kbit/s，0/130 丢包 | 100 Kbit/s，0/130 丢包 | 0 |

PDU、双向 bundle 加载、自动停止均成功。动态 port 0/1/2/3 非零窗分别为 13/10/10/10，峰值 17164.969/12406.800/12406.878/12406.825。运行几何验算最大偏差 delay 4.976e-7 ms、Doppler 4.790e-4 Hz、gain 4.396e-4 dB、C/N 4.387e-4 dB，符合日志精度。RTT 平均 static 1259.595 ms、dynamic 1025.404 ms 为墙钟开销，不代表几何距离变化。

额外修复 .gitattributes：fdd-miso* 导出的 JSON 保留原始字节，防止 Git 自动换行转换破坏 manifest SHA256。重新暂存 2×1 的原始 JSON（无模型/系数改变），通过 git show :path 逐一核对 2×1/4×1 双向 manifest 及全部数组的 SHA256；四组均通过。
