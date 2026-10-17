# 4×1 接收端口修复与361秒复验（2026-10-17）

## 已完成的长程验收结论

`fullpass-1792221840958142385`（6b2167c）已到双端IQ360.999秒，墙钟3381.807秒，但未通过。ping3248发/2750收，未收为末尾2751–3248，最大RTT459005.848ms；UL98596.364bit/s、DL84909.750bit/s。UE PBCH失败200次，首次错误前置IQ356.99955，位置与旧末尾问题一致。**不能仅豁免末尾**：IQ300左右DL MCS降至0，吞吐约0.2Mbps（IQ时钟），业务早已持续排队。

前段IQ0–293 RTT约0.8–1.2秒；后段IQ309/325/341/357分别约100.6/221.4/342/459秒。后段IQ推进速度没有对应骤降，不能继续只归因卷积计算。gNB PUCCH DTX自IQ180的161累计增至IQ300附近1605，MCS由9降至0；这些记录支持调查反馈链路，但不能单独证明所有重传都是反馈错误。

完整记录保存在`.runtime/fidelity-checkpoints/fullpass-1792221840958142385/`，包括最终报告、故障位置和15秒历史。原始UE日志不提交。

## 配置缺口及修复

生成配置只设置RU的`nb_rx=4`，上游`pusch_AntennaPorts`默认仍为1。更进一步，`nr_configure_pucch`固定指定一个空间流，而PUCCH 0/1/2解码器按`numSpatialStreamIndices`遍历接收缓冲区。因此拥有4路RFsim IQ并不等于使用4路上行接收分集。

- `local_ntn/spatial_config.py`显式设置PUSCH接收端口数，与2/4路RU配置一致；UE仍单天线、PDSCH仍单层。
- `oai_patch/current/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_uci.c`在NO_BEAM_MODE下同步PUCCH空间流数量、连续端口索引与FAPI数字波束接口。保持原函数签名和有波束模式。与vendor归档逐行比较仅增加15行逻辑。
- `local_ntn/test_spatial_config.py`覆盖2/4端口配置；`vendor/README.md`记录新overlay。

此修改会影响上行接收分集、反馈可靠性及吞吐，应与旧单端口接收实验区分。没有增加信道系数或改动发射功率、噪声、MCS门限、业务负载、STK及357–361秒尾部。它修复了确定存在的端口配置缺口，是否解决全部长程积压仍需完整业务验证。

## 验证与数据验算

运行副本`/home/duyaya/OAI/self-contained-test`，源码`/mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project`。

1. 标准`bash scripts/wsl_lab.sh build SOURCE RUNTIME`成功。首次构建尚未包含未跟踪overlay；暂存新文件后第二次构建已明确编译`gNB_scheduler_uci.c`并链接两个modem。日志：源目录`.runtime/fidelity-receive-ports-build-final.log`。
2. 运行副本`source scripts/env_subarray4.sh && bash scripts/test.sh`通过，包括trace parser和实际IQ回归；`bash scripts/test_fidelity.sh`通过。完整双向4097时刻，四种时间速率和静音边界，ASan/UBSan，DL最大误差2.57243948e-11、UL1.6512793e-11。日志`.runtime/fidelity-receive-ports-{regression,full-regression}.log`。
3. `cmake --build .runtime/oai/cmake_targets/ran_build/build --target nr_pucchsim -j 4`成功。运行`nr_pucchsim -z RX -P FORMAT -b BITS -q 4 -n 100 -s 10 -S 10.1`，RX=1/2/4，FORMAT=0/1/2，BITS分别2/2/12，九组各100次均零比特错误。这验证原生PHY多路接收能力，不等同于NTN长程通过。初次跨shell变量展开失败；随后格式2的2PRB不满足上游Polar断言，改为明确4PRB后通过，不改生产资源配置。
4. 系统Python/Numpy独立按301个频点积分UL频响，在IQ0/180/270/290/300/320/350，四路各自平均功率约0.989–1.002，端口总功率相对单端口约6.0206dB，符合四路归一化功率相加；不是实测合并SNR增益。
5. 完整信道短业务命令`source scripts/env_subarray4_fidelity.sh && python3 scripts/validate_spatial.py --ports 4`正在执行。静态smoke-0-1792234193445481497已通过，ping10/10，UL0/130、DL0/137，PBCH0，独立物理公式审计通过；运行日志确认pusch_AntennaPorts=4。动态及新361秒复验尚未完成。

百万QD参考、1%精度报告与原尾部数据直接复用，没有重新生成。

补充：动态smoke-1-1792234325858162053及公式审计通过，ping10/10，UL0/130、DL0/131，PBCH0；整体验证进程退出0。动态UL接收83.9Kbit/s（17.95秒统计窗口），DL101Kbit/s，UL低于100K发送目标，不能仅凭内部丢包为0断言没有排队；长程仍须验算。阶段修复将本地提交，随后进行新361秒验收。

2026-10-17 当前续跑：修复提交4854a30已在zky-miso本地完成，未push。标准构建、trace parser/实际IQ回归、完整7.68Msps回归、PUCCH九组测试、静态/动态短业务及公式审计通过。第一次完整启动fullpass-1792234550406584446因网络资源冲突在modem前失败，已保留最终报告。实时只读核对网络和modem均无残留后重试；当前fullpass-1792234702783642530，PID2338，会话87977，记录器同一WSL包装器持续运行，每15秒保存。当前入口.runtime/fidelity-checkpoints/active.json。尚未完成新361秒验收，不要重新生成QD数据，不要重复启动新业务。

## Token余额交接：保留正在运行的测试

实现提交4854a30；完整业务标签`fullpass-1792234702783642530`，WSL会话87977，full_pass PID2338。当前入口`.runtime/fidelity-checkpoints/active.json`，每15秒原子更新latest.json并追加history.jsonl；结束自动收集full_pass_final.json及failure_locations.json。父包装器`.runtime/run_receive_ports_checkpointed.py`持续等待完整业务与记录器结束，不要另起一套测试。

最近检查IQ约23秒，ping1–173连续，最新RTT984.653ms，PBCH0。gNB DL MCS9、goodput1.03Mbps、PUCCH DTX累计10；UL MCS9、goodput1.23Mbps、DTX0。这里是中间结果，尚未到原问题IQ300秒，更不能宣称361秒验收通过。后续以latest.json和原进程实际存活状态为准。

恢复顺序：读取active.json和其checkpoint_path；检查PID启动标识是否匹配；如果仍在运行，只观察既有会话/日志；如果已完成，直接审计最终报告；若无最终报告且进程消失，先诊断中断，保留历史。不要重做百万QD参考、构建或已通过的IQ回归。协议栈没有中途恢复功能，重启不能伪装为无缝续跑。

运行控制日志`.runtime/fidelity-receive-ports-business.log`，记录器日志`.runtime/fidelity-receive-ports-checkpoint.log`；旧启动失败日志另存fidelity-receive-ports-business-start-failed.log，失败标签fullpass-1792234550406584446已有单独检查点。原361秒失败轮次fullpass-1792221840958142385完整保留。没有push，没有停止当前测试。
