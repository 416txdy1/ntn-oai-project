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