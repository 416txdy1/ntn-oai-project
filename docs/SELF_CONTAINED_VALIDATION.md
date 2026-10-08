# 单仓库交付与数值验证（2026-10-02）

> 2026-10-02 全程复核更新：当前示例末 4 秒含卫星位置混合跳变，361 秒持续业务验收未通过。短测和公式一致性通过不代表完整过境通过。详见 [全程验收失败报告](FULL_PASS_ACCEPTANCE_20261002.md)。


## 源码与构建

OAI、QuaDRiGa、ASN1C、SIMDe 的源码归档位于 vendor/，版本与校验和见 source-manifest.json、checksums.json。OAI 修改文件维护在 oai_patch/current/，QD C 模块维护在 quadriga/oai/。构建解包到 .runtime/ 后应用这些文件，不需要拉取其他源码仓库。系统依赖、Docker、核心网镜像仍需安装；本次没有在全新 Ubuntu 上重新安装系统软件包。

项目交付内容复制到 /home/duyaya/OAI/self-contained-test 后，从归档源码完成 10831 个 Ninja 步骤的全新构建。修正源码版本标识及 SIMDe 归档后，再次构建成功。以下命令已通过：

```bash
bash scripts/build.sh
bash scripts/test.sh
python3 scripts/check_delivery.py
```

回归包含 trace parser、实际 rxAddInput IQ、历史缓存边界、网络及启动预检查、13 项 QD Python 测试、双向链路预算、C reader、带 ASan/UBSan 的 C adapter。双向各检查 723 个快照/中点，最大归一化卷积误差约 1.82e-12。

最终构建后再次通过：

```bash
source scripts/env.sh
python3 local_ntn/test_trace_validation.py
python3 local_ntn/test_real_iq.py
python3 local_ntn/test_preflight.py
python3 scripts/check_delivery.py
for s in scripts/*.sh; do bash -n "$s"; done
```

## 全新核心网和业务验收

全新随机凭据、独立数据库，9 个核心网容器健康。以下是首次初始化和验收命令（已有 .private 时不要重复 init）：

```bash
python3 scripts/init_lab.py --subnet-octet 78 --prefix ntn-verify
source scripts/env.sh
bash scripts/core.sh up
bash scripts/prepare_iperf.sh
python3 scripts/smoke.py --rate 0
python3 scripts/smoke.py --rate 1
python3 local_ntn/experiment.py stop
bash scripts/core.sh stop
```

| 模式 | PDU | ping | 平均 RTT | UL 接收 | DL 接收 |
|---|---|---|---|---|---|
| rate=0 | 成功 | 10/10 | 471.598 ms | 97.6 Kbit/s，0/130 丢包 | 100 Kbit/s，0/130 丢包 |
| rate=1 | 成功 | 10/10 | 563.773 ms | 98.1 Kbit/s，0/130 丢包 | 100 Kbit/s，0/130 丢包 |

两端均加载 STK/QD 一次，最终两轮 PBCH failure 计数为零。早期遇到 libparams_libconfig 缺失和 SQL 挂载读权限问题，已分别增加构建目标和修正挂载文件权限。一次 ping 墙钟回退导致该次验收失败，上表为补测通过结果，没有改变物理参数掩盖错误。

## 独立数值验算

```bash
python3 local_ntn/audit_runtime_numbers.py --run-dir /home/duyaya/OAI/self-contained-test --labels smoke-0-1790911092711381902 smoke-1-1790911151423613603
```

两轮上下行共 96 条日志验算通过：独立计算几何距离、Hermite 位置/速度、IQ 时间、多普勒、增益、C/N 和 TA。最大时延差 4.976e-7 ms、多普勒差 4.837e-4 Hz，均在日志打印舍入容差内，不代表物理测量精度。362 行完整轨迹总 feeder+service 时延为 14.717409591–21.478296499 ms；初始 TA=3614295，量化误差 0.3512 ns。

## 验证边界和维护

动态业务测试覆盖约 24 秒 IQ 时间，不是完整 361 秒过境业务验收；全轨迹离线数据和卷积已检查。ping 墙钟 RTT 包含计算、调度和排队，不能等同几何传播时延。本次没有重新执行 MATLAB/STK 场景生成，示例回放不需要这两个软件。

本次修改交付路径、构建和初始化方式，没有改变信道实验方法、种子或频率。当前源码应修改 oai_patch/current/ 或 quadriga/oai/，不要只改被忽略的 .runtime/。凭据和原始 UE 日志保留在本地，不进入提交。

手动运行指令见 [MANUAL_RUN.md](../local_ntn/MANUAL_RUN.md)。

## 最终复核

按用户要求再次执行 bash scripts/test.sh，全部通过（退出码 0）。从 Git 暂存树独立导出后，check_delivery.py、prepare_sources.py、init_lab.py 均通过。对本次暂存文件及归档内共 6028 个文件检查，未发现本次两套实验环境的私有凭据或私钥头；运行日志、.private 和 .runtime 未进入本次提交。此检查不是对历史 Git 对象的全面审计。
