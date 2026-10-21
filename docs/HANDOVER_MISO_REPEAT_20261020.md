# MISO 完整复测、数值验算与启动丢包定位（2026-10-20）

## 结论与范围

相同二进制、覆盖源码、STK trace/切换表、信道包、随机种子及运行参数下，再次完成620 IQ秒，验收passed=true。未修改生产代码、实验负载、信道或门限；仅新增诊断脚本与验证记录。没有提交或推送。

本轮运行miso-full-20261020-repeat-a，1249.983271097墙钟秒，numeric与spatial通过，PBCH/RRC IDLE/reaccess均0，stop_exit=0，专属核心网已关闭。

|业务|收到/发出|5秒期限失败|已收包最大延迟|
|---|---|---|---|
|Ping|1190/1190|0%|RTT 3.462230秒|
|UL UDP|15220/15220|0%|1.966142秒|
|DL UDP|15213/15218|0.032855829%|1.724886秒|

两个切换窗口三种业务期限失败均0。DL缺失5包计入失败，已收到的包没有超期。上下行实际发包速率分别99762.969和99758.388 bit/墙钟秒，与100000配置偏差小于0.25%，在原5%测量容限内。

## 丢包时间与重复性

上次全程miso-full-20261020-batch-rx缺失的全部是下行序号1–5，本次也为1–5；seq6起到结束无最终丢包。原SISO全程review-full-20261018缺失seq1–4（IQ6.470346–6.595814）；此前MISO短测缺失seq1–4（IQ7.110927–7.240799）。证据支持业务启动阶段的重复模式，不能说固定STK时刻必然丢5包。

|序号|上次距首发墙钟秒|上次IQ秒估计|上次STK秒估计|本次IQ秒估计|
|---|---|---|---|---|
| 1 | 0.000000 | 7.230965 | 8207.230965 | 7.124861 |
| 2 | 0.080138 | 7.268670 | 8207.268670 | 7.163915 |
| 3 | 0.160883 | 7.303560 | 8207.303560 | 7.203001 |
| 4 | 0.240968 | 7.338165 | 8207.338165 | 7.241906 |
| 5 | 0.321125 | 7.374470 | 8207.374470 | 7.280448 |

本次首批丢包相对首发墙钟秒为0、0.080164、0.160312、0.240467、0.320601。上次切换窗口为IQ39–49与594–604，丢包与这两个窗口没有重合。时间小数来自相邻STKCLOCK锚点的线性插值；原始上下界宽约0.1 IQ秒，不能将显示的小数位当成直接测量精度。证据JSON保留上下界与插值值。

两次DL接收器分别在首发前88.894761ms和75.555763ms报告ready，代码在bind成功后才写ready，驱动等ready后才启动sender。因此不能归因于接收器尚未bind。未记录逐层抓包，尚不能把丢包精确定位到UPF/GTP-U、无线承载或其他转发阶段；也不能仅凭启动集中就断言某一层已找到根因。本轮没有预热、延迟首发或剔除启动包。

独立脚本从原始sender/receiver事件重建序号集合，检查未知/重复包、负时延、送达期限、总数、发包速率，并从原始锚点样本重算缺失包的IQ/STK映射，均与正式报告一致。

## 数值验算

- 16×16阵列256阵元，端口映射四组各64阵元，每组8×8；物理间距0.06023799590098055m。参考频率2.4884GHz，因此DL为0.5波长，UL1.6149GHz为0.32448561324545894波长。二者使用同一物理几何。
- 四组full/short与DL/UL文件哈希、布局、有限值、时间轴检查通过；full621快照，short71快照，间距1秒，11路径。
- 快照平均链路功率最大归一化误差6.45009015e-8。线性复系数插值的中点平均功率最低DL0.964993789、UL0.971569550；不能要求复数插值后功率恒为1，未增加重新归一化改变模型。
- gNB和UE运行各620行数值记录对照STK插值通过：时延最大误差<0.5ns，多普勒<0.0005Hz，增益/CN<0.0005dB，均在原日志舍入容限内。初始TA量化误差1.695627631ns。
- 四组独立卷积对照：full DL1241/1241、UL1241/1241；short DL141/141、UL141/141。最大误差分别2.54801219e-11、1.46296729e-11、2.42683456e-11、1.38828341e-11，ASan/UBSan通过。
- 实际IQ相位/四端口旋转缓存参考误差0；10dB损耗的能量比例0.100000000或浮点近似0.099999994；噪声、不可见/耗尽、历史缓冲和端口回归通过。
- 大超额时延弱径核对：MISO最大DL730.593us、UL495.838us，原SISO也存在同量级长径。MISO超过10us路径的合计功率比例最高0.00864344%，功率加权RMS时延最大约DL4.266us、UL3.934us。不能把最大单径时延当作所有信号共同延迟，也不据此宣称模型获得完整物理保真认证。

结论限定为本机、记录配置与已执行检查；仍是四个8×8子阵的LOS相位对齐等效模型，不是完整MVDR实现。保留1秒快照的既有建模限制，本轮未新增高密度信道保真认证。TSan未在本轮重跑，不声称通过。

## 精确执行命令与结果

工作目录 /home/duyaya/OAI/handover-miso-integration。业务运行沿用以下环境：

```bash
export OAI_SPATIAL_MODE=miso4-subarray OAI_QD_WORKERS=8 OAI_QD_PROFILE=1
export OAI_NTN_TIMING_DIAG=1 OAI_NTN_TIMING_DIAG_START_IQ_S=0
export OAI_NTN_PUSCH_FAILURE_THRES=100 OAI_NTN_PDCP_REORDERING_MS=500
export OAI_NTN_CELL_KOFFSET_MS=80 OAI_RNGSEED=20260925
python3 scripts/handover_acceptance.py --case full --profile integrated-handover   --run-id miso-full-20261020-repeat-a --max-wall-seconds 10800
```

外层启动脚本（包含core up、空间审计和trap core down）：

```bash
bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/run_miso_repeat_a.sh
```

返回0。业务完成、core关闭后串行执行：

```bash
bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/check_repeat_a.sh
```

返回0。脚本设置OAI_NTN_PROFILE=zky、OAI_SPATIAL_MODE=siso为通用测试环境，OAI_QD_WORKERS=8，并执行bash local_ntn/run_regressions.sh及check_generated_miso.sh；后者对四组MISO显式传入实际bundle/trace，分别执行audit_link_budget、run_qd_channel_reader_tests.py、run_qd_rfsim_adapter_test.py --sanitize --sample-rate 7680000。通用测试环境不会修改刚结束的业务运行配置。

本轮未修改生产实现，因此未重复构建或完整scripts/test.sh；执行了与本次要求直接相关的trace、实际IQ、多端口数值和sanitizer检查。

安全证据见 [验证目录](validation/handover-miso-repeat-20261020)。原始UE日志和私有网络信息未复制到文档。
