# QuaDRiGa Handover Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 保留完整 zky 能力，接入原伪卫星切换流程，在独立环境通过验收并推送 codex/ntn-quadriga-handover，证明旧平台仍可运行。

**Architecture:** 以 zky current OAI overlay 和 QD C 模块为唯一新部署来源。统一 RuntimeConfig 向启动器、网络、核心网和验收提供 profile/run 配置；新增显式 legacy-linear 和 schedule 日志，继续使用原 QD IQ 接收链。原平台只做有界的前后复验。

**Tech Stack:** Python 3、Bash、PowerShell、C/C++、CMake/Ninja、WSL Ubuntu-22.04、Docker Compose、MATLAB R2022b、QuaDRiGa 2.8.1-0、OAI RFsim。

**Spec:** ../specs/2026-10-09-ntn-quadriga-handover-design.md，设计提交 4834787，用户已于 2026-10-09 批准。

## Global Constraints

- 新 Windows 工作树：C:\Users\WSZ\.codex\worktrees\ntn-quadriga-handover\OAI调研；所有任务的仓库相对路径以此为根。
- 新 Linux 测试副本：/home/kayoko/ntn-workspaces/ntn-quadriga-handover；新 OAI 与 build 仅使用其 .runtime/oai。
- 基底 origin/zky=70a38b5492b615498cea2332bd077c0d4f958d25；旧能力来源 f30bc90a626214d227a7991d7429cf7723233f96。最终分支 codex/ntn-quadriga-handover，不移动原分支或 zky。
- zky 默认 Hermite、blend-aware、timing assist、QDCHANNEL1、vendor、示例、回归和文档均保留。当前部署入口为 oai_patch/current 与 quadriga/oai。
- 新 profile 使用 ntn-qd-integrated、192.168.71.128/26、12.2.1.0/24、ntn-qd-ue、ntn-qd-host/peer、10.202.0.0/30、TCP 4044；原平台资源拒绝复用。
- integrated-handover 必须具有同 trace 的 DL 2488400000 Hz 与 UL 1614900000 Hz QD bundle；legacy-handover 明确关闭 QD。新 profile 均为 legacy-linear，timing assist 默认关闭。
- 回放共用 trace、rate、插值模式与 IQ epoch；schedule 是伪切换身份日志，不是 Xn/RRC handover。
- 不改写原配置模板、原外部 OAI/5GC、原二进制；不提交私有配置、订阅密钥、数据库密码、build 或原始 UE 日志。
- 不 broad pkill、不 wsl shutdown、不清理无关进程、网络和容器；新旧 modem 串行运行。
- 每项功能先写有意义的失败测试，再实现、验证和提交。只读基线与环境准备不编写镜像实现的测试。

## Review Focus

1. 继承旧平台环境变量或输入路径时，新 profile 必须拒绝原源码/build、state、网络和私有目录，而非悄悄复用；由任务 1 的 contamination 测试覆盖。
2. 部分网络创建失败、旧 marker、PID 被复用时，回滚只清理本次创建且身份匹配的资源；由任务 2、3 的 failure/reused identity 测试覆盖。
3. MATLAB 导出失败留下一个方向或 bundle 与 slice 不匹配时，整合入口必须拒绝启动；由任务 6 的 partial export/hash 测试覆盖。
4. 切换段位置跳变、零多普勒、长历史及 trace/bundle 尾端不能导致越界或静默误算；由任务 5 的真实 IQ 边界测试覆盖。
5. PDU/业务建立晚于 IQ 8239 s、缺少任一切换窗口或接收计数时，验收必须失败；由任务 7 的 window coverage 测试覆盖。

## 文件与接口分工

| 单元 | 文件 | 职责 |
| --- | --- | --- |
| RuntimeConfig | local_ntn/runtime_config.py、paths.py、scripts/env.sh | 统一 profile/run 解析，无系统写入 |
| 隔离网络与核心网 | local_network.sh、verify_network.py、scripts/init_lab.py、core_lab.py | 资源验证、私有配置和只清理自身资源 |
| 启动与停止 | experiment.py、run_local.sh、prepare_local.py、run_state.py | 独立配置、进程身份、run manifest |
| 旧切换工具 | 恢复的 constellation/blend/schedule/slice 工具 | 保留原算法、去除固定原平台入口 |
| RFsim | current stk_trace/stk_schedule/stk_trace_channel/CMake | 插值模式、切换身份与 IQ 接口兼容 |
| QD 导出 | quadriga/matlab/export_handover_fdd.m | 两方向导出与输入溯源 |
| 有界验收 | scripts/handover_acceptance.py、handover_metrics.py | 全 IQ 区间与两处业务窗口验证 |
| 原平台保护 | scripts/original_platform_check.py | 指纹、前后短时业务与初始状态恢复 |

Python 导入延续 local_ntn 的脚本路径模式；可复用函数保持无 argparse 或系统操作的导入副作用。

## Task 1: 统一隔离运行配置

**Files:** Create local_ntn/runtime_config.py、test_runtime_config.py；Modify local_ntn/paths.py、scripts/env.sh；Test 既有 test_local_setup.py。

**Interfaces:**
- Produces `resolve_runtime(root: Path, profile: str, run_id: str, environ: Mapping[str,str]) -> RuntimeConfig` 和 `RuntimeConfig.to_env() -> dict[str,str]`。
- RuntimeConfig 为 frozen dataclass。路径字段 root/oai_repo/build_dir/private_dir/run_dir/state_file/gnb_config/initial_delay_file/ue_config/trace/schedule/dl_bundle/ul_bundle 均为 Path，后三个可为 None。
- 字符串字段 profile/run_id/namespace/host_veth/ue_veth/rf_host_ip/rf_ue_ip/core_project/ext_dn_container/amf_ip/gnb_ip_cidr/ext_dn_ip/ue_pdu_subnet/interpolation；rf_port 为 int，owner_file 为 Path，qd_required/timing_assist 为 bool。
- CLI `python3 local_ntn/runtime_config.py --profile NAME --run-id ID --format json` 输出非秘密配置；env 格式用 shell 安全引用，仅用于可信脚本 source。
- profile 来自显式 CLI 或 OAI_NTN_PROFILE，默认 zky；run_id 来自 CLI 或 OAI_NTN_RUN_ID，默认 default，必须匹配 [A-Za-z0-9][A-Za-z0-9_-]{0,63}。
- integrated 与 legacy 默认输入为恢复的 seamless trace/schedule；QD 默认目录 examples/handover/{downlink,uplink}。新 profile private_dir 为 .private/profiles/integrated-handover，run_dir 为 .runtime/runs/<profile>/<run-id>。

- [ ] 写 test_integrated_defaults、test_zky_legacy_defaults、test_invalid_run_id 和 test_contaminated_environment_rejected。断言 new rf_port==4044、namespace=='ntn-qd-ue'、ue_pdu_subnet=='12.2.1.0/24'；不同 run 的 state/log/config 路径不同；zky 现有 paths/env 默认值不变；原源码/build 与原资源污染抛 ValueError。
- [ ] 运行 `python3 local_ntn/test_runtime_config.py`，确认因缺少 resolve_runtime 失败。
- [ ] 实现 dataclass 和解析，所有新 profile 路径落在独立 root，拒绝 symlink 解析后越界与旧平台资源。新 profile 不能从继承的 OAI_REPO 或私有设置指向原平台。
- [ ] 将 paths/env 改为消费统一配置，保留 zky 的已有变量名和 CLI 查询值；新 profile 设置 OAI_STK_TRACE_INTERPOLATION 和独立网络变量，不输出任何凭据。
- [ ] 运行 test_runtime_config.py、test_local_setup.py 及 `bash -n scripts/env.sh`，要求全部 PASS。
- [ ] 提交：`feat: add isolated NTN runtime profiles`，只暂存本任务文件。

## Task 2: 隔离核心网与网络所有权

**Files:** Modify local_ntn/local_network.sh、verify_network.py、scripts/init_lab.py；Create local_ntn/network_owner.py、test_network_owner.py、scripts/core_lab.py、test_core_lab.py；Extend test_local_setup.py。

**Interfaces:**
- Consumes Task 1 RuntimeConfig。
- Produces `validate_owner(config: RuntimeConfig, topology: dict, marker: dict) -> None`，不符抛 ValueError；`create_owner(config, topology) -> dict` 包含 schema、profile/run_id、ifindex、netns_inode。
- verify_network CLI 新增 --profile/--run-id、保留 --claim；local_network.sh 新增 --action up|down 和同名选择参数，零参数 zky 行为保留。
- init_lab CLI 新增 --profile、--private-dir、--pdu-subnet；原调用默认 .private、subnet-octet70 和 ntn-local 不变。
- core_lab CLI 为 `python3 scripts/core_lab.py preflight|up|down|status --profile NAME --run-id ID`，每个操作只针对 config.core_project 与 config.private_dir/core/compose.yaml。

- [ ] 写 owner 测试：正确 veth/inode/run 身份通过；错误 marker、非 root marker、symlink、旧资源名和部分创建失败拒绝；down 不删除 preexisting 或其他 run 资源。
- [ ] 写 core 测试：新前缀容器名、192.168.71.128/26、oai DNN 12.2.1.0/24、ext-DN 回程路由与健康检查一致；17 字符前缀 ntn-qd-integrated 可用；已存在 private_dir 拒绝覆盖；模板字节不变，stdout 无测试 key/password。
- [ ] 运行 `python3 local_ntn/test_network_owner.py` 和 `python3 scripts/test_core_lab.py`，确认缺少接口/新选项而失败。
- [ ] 将 verify/network shell 的所有固定名字、IP、owner 路径改为 RuntimeConfig。创建过程记录本次资源，异常回滚验证 inode/ifindex；不得按名字单独推断所有权。
- [ ] 将 init_lab 改为 main(argv=None)，保留凭据生成逻辑及权限。渲染新配置时只替换选中 oai DNN 的地址池，并同步 ext-DN 路由与 healthcheck；新 profile 禁用未使用 DNN，避免残留共享 pool，原 zky 渲染不变。
- [ ] 实现 core_lab 的只读冲突检查及精确 compose project 操作，拒绝旧项目和网络；记录新网络 ID。up/down 调用受控 argv，不执行 shell 拼接。core 所有权以独立 project、workspace 和配置哈希校验，实验 run_id 仅关联记录；同一 core 可服务串行的验收 run，不能复用其他 workspace 的容器。
- [ ] 运行上述测试、test_network_config.py、test_local_setup.py 以及两个 shell 的 bash -n，要求全部 PASS。
- [ ] 提交：`feat: isolate NTN core and RFsim network ownership`。

## Task 3: 启动器与 PID 运行状态隔离

**Files:** Modify local_ntn/experiment.py、run_local.sh、prepare_local.py、preflight.py；Create local_ntn/run_state.py、test_run_state.py；Extend test_preflight.py、test_local_setup.py。

**Interfaces:**
- Consumes RuntimeConfig 和 Task 2 owner/network CLI。
- Produces `process_identity(pid: int) -> tuple[str,str] | None`，内容为 starttime/executable；`stop_owned(state_file: Path, run_id: str) -> None`。
- experiment CLI 各 action 接受 --profile/--run-id，保留 --label/--rate/--reverse，恢复 --ping-count/--iperf-seconds。
- `channel_environments(environment, *, qd_required: bool=False) -> dict[str,dict[str,str]]` 保留旧调用；preflight 新增可选 runtime 参数。
- run manifest 位于 config.run_dir/run.json，包含 source_commit、OAI 来源、source/build 绝对路径、二进制 SHA256、trace/schedule/bundle 哈希、epoch/rate/interpolation/timing_assist、网络身份与实际 sample_rate_hz。Fs 必须由实际 modem/RFsim 启动信息确认；缺失时完整验收失败，不能用常量代替。

- [ ] 写 test_stop_ignores_reused_pid、test_stop_ignores_other_run、test_launch_failure_cleans_only_started、test_generated_files_stay_in_run。模拟身份与信号发送，断言只匹配 PID 收到 TERM/KILL。
- [ ] 扩展 preflight：integrated 缺任一 bundle 失败、legacy 无 QD 成功、zky 原函数调用不变、gnb 接收 UL/UE 接收 DL。断言两个子进程字典互不修改，日志不泄露私有内容。
- [ ] 运行 test_run_state.py 与 test_preflight.py，确认新配置/选项尚未接入而失败。
- [ ] 接入 RuntimeConfig；gnb.conf、initial_delay、PID 与日志仅写 run_dir。恢复有限非负 --initial-lead-rfsim，默认 0，只预测初始配置，不改 epoch。
- [ ] run_local.sh 同时给 gNB/UE 指定 RFsim serverport4044 和正确 RF 地址，LD_LIBRARY_PATH 与全部动态库来自新 build。保持 zky 默认命令语义。
- [ ] 实现 run_state 并复用 zky TERM 等待、必要时 KILL 的有界流程；失败保留可诊断状态。新 profile 正常 stop 在 modem 退出后调用 owned network down；新 start 拒绝覆盖已有 run.json，zky 的已有日志语义保持不变。已有 modem 冲突仍拒绝启动，TCP 就绪通过日志判断，不创建伪 UE 探测连接。
- [ ] 运行 test_run_state.py、test_preflight.py、test_local_setup.py、bash -n run_local.sh 和 py_compile 受影响 Python，要求全部 PASS。
- [ ] 提交：`feat: scope NTN launch and cleanup to owned runs`。

## Task 4: 恢复旧星座与伪切换工具

**Files:** Restore create_leo_constellation.py、export_constellation_trace.py、handover_blend.py、satellite_schedule.py、slice_trace.py、run_constellation_validation.sh、run_seamless_validation.sh、test_handover_blend.py、test_satellite_schedule.py、test_seamless.py、test_stk_schedule.py，以及三个 schedule CSV、firsthandover/seamless trace CSV；Create local_ntn/test_handover_profiles.py。

**Interfaces:**
- 保留原纯算法 API；新 wrapper 消费 RuntimeConfig 和 core_lab CLI，禁止调用 /home/kayoko/oai-cn5g-fed 或硬编码旧资源。
- test_seamless.py 保留旧参数兼容入口；完整验收转交任务 7，不以旧 ping/iperf 返回码作为整合通过标准。
- schedule 的 STK 时间与 trace 保持共同绝对区间，slice 必须同时裁剪 trace 与 schedule。

- [ ] 用 f30bc90 按文件读取上述内容到新工作树，纯算法与测试原样恢复；先隔离不能运行的旧 shell 启动入口。
- [ ] 新增 test_wrappers_use_selected_profile 和 test_no_original_core_start。断言 dry-run argv 使用 core_lab、config.namespace/run_dir，输入 trace 为 621 行8200–8820，切换完成8244/8799；不得出现旧 core 路径。
- [ ] 运行 test_handover_profiles.py，确认恢复的 shell 固定原平台路径导致失败。
- [ ] wrapper 接入 --profile/--run-id，日志路由到 run_dir；移除交互 sudo 请求与旧 core 自动启动，根权限不足给出明确命令。保留工具功能并在帮助中标明 pseudo handover。
- [ ] 运行 test_handover_blend.py、test_satellite_schedule.py、test_handover_profiles.py；对 slice 验证共同区间和越界拒绝。需要 C schedule 的测试在任务 5 后运行。
- [ ] 提交：`feat: restore constellation and pseudo-handover tools`。

## Task 5: RFsim 插值与 schedule 兼容

**Files:** Modify oai_patch/current/radio/rfsimulator/stk_trace.h、stk_trace.c、stk_trace_channel.c、CMakeLists.txt；Create current stk_schedule.c/h（来自 f30bc90）；同步 local_ntn 测试用 stk_trace.h/c/stk_trace_channel.c；Create test_legacy_interpolation.c/py；Modify test_real_iq.py/c、run_regressions.sh、scripts/test.sh。

**Interfaces:**
- 保留 `stk_trace_at(const stk_trace*, double, stk_trace_row*) -> bool`。
- 新增 inline `stk_trace_interpolate_linear(const stk_trace_row*, const stk_trace_row*, double, stk_trace_row*) -> bool`；trace 新增 legacy_linear 标志，现有 blend_aware 含义不变。
- 继续使用原 stk_schedule_load/at/free；入口 OAI_STK_SCHEDULE，日志独立 STKSCHEDULE，不更改现有 STKTRACE2 numeric 行。
- test_real_iq.py 使用现有 OAI_REPO/OAI_BUILD_REPO，补充 OAI_BUILD_DIR 并打印真实 source/build；编译加入 current stk_schedule.c。保留现有 Ninja/Make 参数来源。

- [ ] 写 C 数值对照：不一致位置/物理速度输入在 t=0.25/0.5/0.75 时，linear pos/vel/acc 与 f30bc90 字段结果一致；path_velocity==vel、synthetic_blend==false；hermite/blend-aware 既有测试结果不变。未知模式必须拒绝。
- [ ] 运行 test_legacy_interpolation.py，确认缺少 linear helper 失败。
- [ ] 实现第三种显式模式，保留原 inline Hermite helper；恢复 schedule source 并追加 CMake，channel 仅增加 schedule 与显式 impairment 开关。
- [ ] 加入真实 IQ 边界 fixture：timestamp 小于需要历史、large excess delay、bulk offset 增减、bundle 尾端、invisible、Doppler 从非零变零。断言有限输出、界内访问、应有静音/背景噪声与相位连续，使用 ASan/UBSan 验证内存边界。
- [ ] 保留 input_offset、QD history 取样与队列清理、crypto、噪声归属。边界测试暴露现有问题时定位最小修复，不改变默认信道模型或放宽测试。
- [ ] 在独立 Linux 副本执行 bash scripts/build.sh，构建四个目标；然后 source scripts/env.sh 运行 bash scripts/test.sh、bash local_ntn/run_regressions.sh 及 test_stk_schedule.py。
- [ ] 对两个 examples/fdd-pass 真实 bundle 执行 QD reader 和 sanitized adapter，要求 PASS。new .runtime/oai 是实际编译来源，原 build 指纹不变。
- [ ] 提交：`feat: add legacy interpolation and IQ-clock handover schedule`；若需要独立边界修复，另作有对应回归的 fix 提交。

## Task 6: 生成与审计伪切换 QD Bundle

**Files:** Create quadriga/matlab/export_handover_fdd.m、quadriga/tests/test_handover_bundle.py；Modify preflight.py、scripts/test.sh；Create examples/handover 下经审计数据和非秘密 provenance.json。

**Interfaces:**
- MATLAB `export_handover_fdd(trace_path, schedule_path, output_dir)`，固定 seed20260925、QuaDRiGa_NTN_Rural_LOS，分别复用 export_stk_to_qdchannel 导出 DL/UL。
- provenance.json 包含原 trace/schedule SHA256、起止时间/621 行、源提交、工具版本/seed/scenario、两个 manifest 和数据哈希。
- Task 3 preflight 复用原 check_bundle，不改变 QDCHANNEL1 schema；额外校验 sidecar 与当前 schedule/trace 一致，任一方向失败保持整合不可启动。

- [ ] 写 test_partial_export_rejected、test_slice_hash_mismatch、test_schedule_hash_mismatch、test_no_overwrite。真实 bundle 断言 directions/frequencies 正确、trace hash 相等、功率审计合格；复数插值中点允许既有相消，不强制单位功率。
- [ ] 运行 test_handover_bundle.py，确认缺少双向 provenance 检查失败。
- [ ] 实现 MATLAB 入口，output_dir 已存在即拒绝；不改归一化、公共相位、excess delay 算法。失败残留目录不能被当成成功 bundle。
- [ ] 核验 vendor checksum 后准备 QuaDRiGa，使用已安装的 D:\Program Files\MATLAB\R2022b\bin\matlab.exe -batch 调用入口，分别对 621 行 seamless 和 71 行 firsthandover 输入生成到新工作树 .runtime/generated-handover 与 .runtime/generated-firsthandover，两个输出保持各自 trace/schedule 哈希。记录命令、版本和退出码，不安装或更新 MATLAB。
- [ ] 对 DL/UL 分别执行 `python3 -m quadriga.tools.audit_link_budget BUNDLE TRACE`、run_qd_channel_reader_tests.py --real-bundle/--real-trace、run_qd_rfsim_adapter_test.py --sanitize --oai-repo "$OAI_REPO" --build-repo "$OAI_REPO" --bundle/--trace。
- [ ] 全部 PASS 后复制小型 bundle 与 provenance 到 examples/handover；原 example FDD 与 vendor 文件哈希不变。新 profile preflight 要求两个方向真实启用。
- [ ] 提交：`feat: add reproducible bidirectional handover channel bundles`。

## Task 7: 两次切换的有界业务验收

**Files:** Create scripts/handover_acceptance.py、handover_metrics.py、test_handover_metrics.py；Modify scripts/full_pass.py、local_ntn/audit_runtime_numbers.py、test_seamless.py；保留 test_full_pass.py 和 test_monotonic_ping.py。

**Interfaces:**
- `evaluate_handover(report: dict) -> list[str]` 返回失败原因列表，空列表表示满足全套指标。报告字段为 pdu_ready_stk_s、traffic_ready_stk_s、iq_end_stk_s（gnb/ue）、pdu_address_changes、pbch_errors、rrc_idle、reaccess_count、numeric_audit_ok、ping（sent/received）、udp（uplink/downlink 的 packets/lost_packets）和 windows（complete_stk_s/start_stk_s/end_stk_s/coverage_ok/ping/udp）。缺字段即失败。
- CLI `sudo -E python3 scripts/handover_acceptance.py --profile integrated-handover --run-id ID --max-wall-seconds 3600`。
- audit_runtime_numbers 新增 --manifest RUN_JSON，从 run 路径读实际日志/config、Fs/epoch/rate/interpolation。原 --run-dir/--labels 调用保持兼容；legacy-linear 按独立 Python 线性几何验算。
- 保留 full_pass.py 对 zky 361 s 示例的已有入口和测试；新的通用流程以 trace 实际区间为准。

- [ ] 写 metrics 测试：620 s 覆盖、两处完整窗口、PDU 和双向业务<8239、ping>=99%、每方向UDP loss<=1%、无失锁/重新接入/IP变化均通过；任一缺计数、窗口为空、启动过晚、IQ未越过8799或篡改 Fs 均失败。
- [ ] 运行 test_handover_metrics.py，确认 evaluate_handover 不存在而失败。
- [ ] 实现有界流程：使用 Task 3 experiment 启停；从两侧日志/manifest 跟踪共同 IQ；ping 保留发送和响应时间，UDP 记录接收端逐秒计数并映射到 IQ 窗口。统计必须按完整、非空的匹配发包/收包窗口，不丢弃真实损失。
- [ ] 达到 trace 尾部前停止继续发包并等待尾部响应；验证实际 IQ 覆盖全区间且两次窗口完整。wall timeout、IQ不推进、进程退出立即标记失败并清理自身。
- [ ] 实现 audit 的三模式与实际 Fs 校验，保留旧数值日志正则。报告仅含聚合数据，原始日志权限受限。
- [ ] 运行 test_handover_metrics.py、test_full_pass.py、test_monotonic_ping.py，以及三插值模式的 numeric fixture，要求全部 PASS。
- [ ] 提交：`test: validate complete IQ-time handover business windows`。

## Task 8: 原平台复验、整合实测与发布

**Files:** Create scripts/original_platform_check.py、scripts/test_original_platform_check.py、docs/INTEGRATION_SOURCES.md、docs/INTEGRATION_TEST_RESULTS.md、docs/INTEGRATED_HANDOVER.md；Modify sources.lock、README.md。

**Interfaces:**
- original_platform_check CLI `snapshot|compare|short-run --snapshot PATH --tag ID`，原项目固定为 /mnt/d/实验室学习工作/杂活/雄安/OAI调研，记录不含秘密内容的文件哈希、既有 dirty 文件集合、二进制指纹、容器状态和网络身份。
- short-run 只在无 modem 时按原入口启动原核心网和实验，ping30、UL/DL UDP各15 s；在 finally 停止自己创建的实验并恢复原容器停止状态。仅清理本次新创建且 owner/inode/ifindex 匹配的 namespace/veth/marker，不改原源码。
- 新发布报告固定包含 spec 中验收指标及全部实际命令/退出码；失败项不能删除或改成预期结果。

- [ ] 在任务1实施前，以既有命令人工记录原平台指纹并做短时前测：原 compose up 后，原 experiment.py start --rate 1 --label integration-before；原 ping --ping-count 30 与 iperf --iperf-seconds 15（另一次 --reverse）。finally 仅 stop 自身进程并验证原网络所有权后清理本次新建 namespace，按原 compose stop 恢复原容器停止状态。前测要求注册/PDU成功、ping30/30、两方向UDP无丢包；原平台不能建立基线时先处理并报告。
- [ ] 写 test_original_platform_check.py，模拟原已有进程、stale owner与SIGTERM中断，断言不启动重叠实验、不终止非自身PID、只回滚本次创建资源且私密输出被阻断；运行并确认缺接口失败。实现 snapshot/compare/short-run 受控 argv，使用任务3身份校验，运行测试至PASS。前测不依赖这个尚未实现的新脚本。
- [ ] 新 Linux 工作副本可建立自己的 Git 元数据，通过本地 fetch/ff-only 同步已提交新代码；不能复制原 .git、私有文件或构建目录。记录部署提交/文件哈希并运行完整回归。
- [ ] 精确检查新 core、RF端口、路由和资源；独立 core_lab up。先静态 QD，再短 firsthandover、新构建 legacy 无 QD 对照，最后完整 integrated 8200–8820 IQ 回放。每次运行均有独立 run_id，finally 停止自身实例。
- [ ] 新整合完整回放必须通过任务7所有条件，包括8239前业务就绪、两处切换窗口、>=99% ping、双向UDP<=1%loss及无PBCH/RRC/PDU变化。失败定位、修复、运行对应回归，再重跑受影响验收。
- [ ] 停止新实验及新 core，复验原 parser/IQ 和同输入 short-run；比较原仓库/外部源码/二进制/模板指纹，保持原已存在 untracked 文件不变。恢复原初始停止状态；WSL保持运行，不shutdown。
- [ ] 生成文件级保留清单：zky未变、兼容扩展、旧内容恢复、新增；锁定来源及bundle哈希。写清运行、停止、重新生成信道和回退至原入口的方法。
- [ ] 执行 `git diff --check`、待提交文件/秘密扫描、完整分支审阅。修复实质问题并做相应验证；仅将脱敏报告提交。
- [ ] 提交最终文档；复核原 HEAD=f30bc90 与 zky=70a38b5，新分支测试证据齐全后执行 `git -c http.proxy= -c https.proxy= push -u origin codex/ntn-quadriga-handover`。
- [ ] 用 ls-remote 核对新分支 SHA 与本地一致，原分支/zky SHA未变。最终返回新分支链接、实际测试结果与原平台复验结论；任何未通过条件均禁止声称完成。

## 执行顺序与审阅

任务1提供公共配置；任务2和3构成隔离运行闭环；任务4和5恢复伪切换语义；任务6产生真实双向信道；任务7提供不遗漏切换窗口的验收；任务8落实实测、原平台保护和推送。任务8的原平台人工前测在任何产品改动前执行，其余步骤在任务1–7完成后执行。

每次提交限定任务文件，运行命令使用绝对新工作树/新Linux路径，避免当前目录错误。已有输入、vendor和原平台不自动升级。实现中若发现需要改变模型、验收指标或切换语义，先提交具体设计修订，不能临时降低目标。

建议使用子代理逐项实现并审阅：公共配置与后续入口高度相关，网络或清理错误会影响原平台，逐项独立审阅有助于提前发现边界问题。也可由主代理直接实现，最后作一次独立全分支审阅；两种方式均保留上述测试与推送条件。
