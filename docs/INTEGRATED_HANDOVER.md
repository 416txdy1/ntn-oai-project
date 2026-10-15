# 隔离的 NTN / QuaDRiGa / 伪卫星切换平台

整合代码已完成编译、离线回归和多轮真实连续业务测试。当前 e3ed4b9 的首次切换测试通过，完整验收矩阵仍未全部通过；既有失败记录保留，原平台最终业务复验尚待完成，新分支尚未推送。
不得把单次通过或短片段结果当作完整620 IQ秒稳定运行证据。实际结果见 [整合测试记录](INTEGRATION_TEST_RESULTS.md)。

基底是完整 zky。新 profile 为 integrated-handover；legacy-handover 使用同一独立构建、同一STK轨迹并关闭QD。伪切换只改变连续物理信道与卫星身份日志，不是多小区Xn/RRC切换。默认 legacy-linear，timing assist关闭。原平台入口与外部源码不作为新平台部署目标。

## 独立环境

在独立Linux工作副本构建，新OAI位于 .runtime/oai。已有源码归档与示例无需重新下载。
初始化仅在没有现存私有profile时执行，输出捕获到私密文件；不要提交 .private 或 .runtime。

~~~bash
python3 scripts/init_lab.py --profile integrated-handover
sudo python3 scripts/core_lab.py up --profile integrated-handover --run-id integrated-core-001
~~~

独立资源为 ntn-qd-integrated、192.168.71.128/26、12.2.1.0/24，
ntn-qd-ue、ntn-qd-host/peer、10.202.0.0/30、RF TCP4044。
运行前不得沿用已source的zky或其他run环境；明确profile/run，再source或使用无残留OAI变量的环境。

四组验收必须串行且使用fresh run ID：

~~~bash
# 当前诊断/验收使用的显式参数；原始默认值与 zky profile 保持不变。
# sudo env 确保参数实际传递到启动器及其 gNB/UE 子进程。
ntn_acceptance() {
  sudo env OAI_NTN_TIMING_DIAG=1 OAI_NTN_TIMING_DIAG_START_IQ_S=0 \
    OAI_NTN_PUSCH_FAILURE_THRES=100 OAI_NTN_PDCP_REORDERING_MS=500 \
    OAI_NTN_CELL_KOFFSET_MS=80 OAI_RNGSEED=20260925 \
    python3 scripts/handover_acceptance.py "$@"
}
ntn_acceptance --case static --profile integrated-handover --run-id integrated-static-001 --max-wall-seconds 3600
ntn_acceptance --case firsthandover --profile integrated-handover --run-id integrated-first-001 --max-wall-seconds 3600
ntn_acceptance --case legacy --profile legacy-handover --run-id integrated-legacy-001 --max-wall-seconds 3600
ntn_acceptance --case full --profile integrated-handover --run-id integrated-full-001 --max-wall-seconds 3600
~~~

每组应同时核对真实退出码、acceptance/report.json passed/failure_reasons/stop_exit、
双向实际100K±5% wall offered rate、独立数值审计，以及进程和网络确实清理。
static需90 IQ秒并至少30 IQ秒业务；short需70 IQ秒及首个完整窗口；
legacy和full均需620 IQ秒及8239–8249、8794–8804两个完整非空窗口。

持续ping和双向UDP在检测到PDU并完成身份、路径及worker就绪核验后启动，贯穿切换窗口并有界排空。
逐方向报告PDU到首次发送/收取的wall时长及双端IQ/STK边界；只有实际发包区间属于业务观测覆盖。
timeline.csv/svg/png及switch-comparison.json把物理delay/Doppler/CN、身份/phase、
ping RTT/loss及UDP到达吞吐/损失放到同一IQ/STK轴；wall RTT仍保留wall单位。
完整时间映射、观测精度和保守损失边界见 [连续验收](continuous-handover-acceptance.md)。

失败run保留；修复后另用fresh ID重测，不能覆盖证据或放宽阈值。
原始modem和worker日志私密保存，只发布审阅过的数值时间线与汇总。

## 停止与原平台保护

~~~bash
sudo python3 local_ntn/experiment.py stop --profile integrated-handover --run-id integrated-full-001
sudo python3 scripts/core_lab.py down --profile integrated-handover --run-id integrated-core-001
~~~

每次stop仅对本次PID/start/executable和owner/inode/ifindex匹配资源操作；
身份变化时拒绝清理，保留证据供检查。不要使用广泛pkill或WSL shutdown。

Task8在首次真实新实验前采集成功的新保护快照；它不冒充Task1前的完整dirty证据：

~~~bash
sudo python3 scripts/original_platform_check.py snapshot --snapshot .private/integration/pre-live.json
sudo python3 scripts/original_platform_check.py short-run --snapshot .private/integration/pre-live.json --tag integration-after-001
sudo python3 scripts/original_platform_check.py compare --snapshot .private/integration/pre-live.json --early-snapshot .private/integration/early-before.json
~~~

short-run固定使用原项目 /mnt/d/实验室学习工作/杂活/雄安/OAI调研，
原trace/rate1、ping30、UL/DL各15秒，私密捕获原输出。仅启动经过ID/Compose标签验证的既有原容器，
逐项等待health，再在finally只停止本次从stopped转running且身份不变的容器，不重建或删除。
原inactive processes.json仅在本次精确归属/bytes/fd/inode确认后恢复。
原 parser/IQ回归另直接运行原脚本，不覆盖原外部OAI或配置模板。

回退至原平台只需停止新平台并在原工作目录使用原入口；不合并此新分支到原分支。
原平台应与新modem串行运行。

## 重新生成QD

MATLAB R2022b与QuaDRiGa2.8.1-0的实测版本在各provenance中记录。
只向不存在的新目录导出，再审计DL/UL的manifest/data以及实际OAI reader/adapter。
不要覆盖已有示例或修改bundle hash绕过输入检查。

~~~matlab
addpath('.runtime/quadriga/quadriga_src');
addpath('quadriga/matlab');
export_handover_fdd('local_ntn/stk_trace_seamless.csv', ...
 'local_ntn/satellite_schedule_seamless.csv', '.runtime/regenerated-handover');
~~~

长621行和短71行分别具有自己的complete provenance；两频率为DL2488400000、UL1614900000 Hz。
仍存在1秒快照采样警告和伪切换合成位置的研究限制，不能由低速业务验收推断最大容量。
