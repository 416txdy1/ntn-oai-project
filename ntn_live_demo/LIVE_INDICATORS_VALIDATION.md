# 实时物理指标联调：2026-10-21

只新增日志数值采集、播放器仪表和观察提示；物理输入、媒体路径、编码、接收缓冲目标、原有验收门限不变。

## 自动检查

- `python3 -B -m unittest discover -s /mnt/d/实验室学习工作/杂活/雄安/OAI调研/ntn_live_demo -p 'test_*.py'`：15项通过，包含原有音频/因果判定以及完整日志行、上下行分离、源IQ与过期检查。
- 本机捆绑Node执行 `ntn_live_demo/test_dashboard.cjs`：13项诊断保护检查通过，包括单独切换不解释卡顿、只有C/N下降不等于业务恶化、过期/缺失/暂停/发送源退出不归因、恢复阶段与历史事件过期。
- 本机捆绑Node执行 `ntn_live_demo/test_dashboard_ui.cjs`：真实Edge DOM/canvas检查通过，覆盖显示数值、关联警示、恢复提示、过期置空、窄屏布局。该测试截图 `dashboard-ui-test.png` 明确标注界面测试，不是实时直播。
- Linux隔离平台工作目录 `/home/kayoko/ntn-workspaces/ntn-quadriga-handover` 执行 `bash local_ntn/run_regressions.sh`：exit=0，9.7秒。检查记录 `.private/dashboard-check-20261021-100020/`。

## 真实OAI媒体联调

run-id：`live-firsthandover-20261021-100946-ed726c`。

以用户原片执行当前demo.py，参数 `--case firsthandover --source "$SOURCE" --skip-regressions --experiment /home/kayoko/ntn-workspaces/ntn-quadriga-handover/.private/causal-20261021-092620-854fd7/1-intervention.json`；SOURCE为原片对应完整WSL路径。此配置运行100 IQ秒，覆盖首次伪切换和IQ70–82的16dB下行C/N干预，不代表双切换长测。

结果：DEMO PASS；解码2049帧，累计12次冻结、7.937墙钟秒。音频进度/墙钟比例0.999913，末态非静音。有接收补偿，不能宣称零卡顿或无音频损伤。原平台、运行源码及二进制、原视频摘要不变，清理无错误。

141条播放统计包含新诊断快照，未发现collector_error。14条显示 `channel_supply`：C/N下降、UE入流下降、播放变慢同时出现。首条对应当前采集IQ72.359、源物理IQ71.999054，输入DL C/N=3.821dB，较近期基线下降15.849dB，UE入流121.39kbit/s（基线35.54%），物理日志观测年龄约773ms。

按 `physical_iq_s` 逐条匹配UE的STKTRACE2源日志：140条非空前端C/N均找到对应物理记录，最大数值误差0.0dB；过期置空的一条不参与匹配。对应下一采样IQ73.166时显示C/N=3.834dB、UE入流103.20kbit/s、解码3.93fps。提示使用低帧率或显示帧间隔判定，二者在缓冲/显示调度作用下不必同时变差。

另外记录到正常、仅信道变化、媒体不足、下游停顿及一次物理数据过期等状态，未把所有卡顿都归为信道。恢复后的显示停顿提示后来补充为15秒恢复观察窗口，并通过独立逻辑/DOM检查；没有为这项纯提示修改重复物理实验。

浏览器事件、包含原始诊断快照的JSON时间线及新增CSV列均保存在该run私有目录。Windows播放器截图在既有visualizations的对应run目录；20秒采样截图不保证刚好截中12 IQ秒的干预段，不能用未截中的图代替数值记录。

开始联调前曾被占用保护拒绝：发现另一轮已停止、无报告落盘的隔离实验 `live-firsthandover-20261021-094229-e5866a` 残留。确认两个实验锁均可获取、无调制解调器、所有归属容器已停止后，使用原experiment stop/core down及精确run-id清理，均exit=0；未删除数据卷。没有绕过平台保护或直接批量删除容器。

本次新仪表实际联调已清理，结束后无网络命名空间和运行容器。完整有声双切换与长时因果配对仍以长测报告为准。
