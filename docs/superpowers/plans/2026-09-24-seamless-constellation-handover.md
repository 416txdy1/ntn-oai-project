# NTN 单小区连续信道切换实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在固定地面 gNB/UE 和单小区 RFsim 架构中，通过 STK 轨迹渐变实现 `S06 → S05 → S04` 期间的 PDU Session 和业务连续。

**Architecture:** STK 导出器在卫星切换前生成保护区和连续有效链路状态；RFsim 继续使用同一个 `STKTRACE2` 链路，只读取渐变后的时延、多普勒、功率和 C/N。调度旁路文件记录旧卫星、新卫星和切换阶段，gNB/UE 保持同一 RNTI、PDU Session 和 `oaitun_ue1`。

**Tech Stack:** Python CSV/JSON、C RFsim channel model、OAI nr-softmodem/nr-uesoftmodem、WSL、STK 导出轨迹。

**Spec:** `docs/superpowers/specs/2026-09-24-seamless-constellation-handover-design.md`

## Global Constraints

- 不修改地面 gNB/UE 位置。
- 不引入 Xn、NGAP 或标准多小区 RRC 切换。
- 保持旧版 22 字段 `STKTRACE2` 轨迹可读。
- 不在 STK 轨迹范围外外推状态；无效区间继续静默 RF。
- 不提交 subscriber secrets、密码、私钥、原始 UE 日志或构建树。
- 不使用宽范围 `pkill -f`。

## Review Focus

- 切换前后的时延和多普勒差值必须有限且不突变：由离线轨迹测试覆盖。
- 5 秒保护区必须产生 `prepare/blend/complete` 状态：由调度测试覆盖。
- 旧轨迹没有渐变字段时行为不改变：由兼容性测试覆盖。
- gNB 和 UE 必须共享相同的渐变轨迹和速率：由启动器和日志检查覆盖。
- PDU Session 和 TUN 接口只能建立一次：由长时业务测试覆盖。

---

### Task 1: 增加切换渐变轨迹生成器

**Files:**
- Modify: `local_ntn/export_constellation_trace.py`
- Create: `local_ntn/handover_blend.py`
- Create: `local_ntn/test_handover_blend.py`

**Interfaces:**
- `handover_blend.interpolate_state(old, new, alpha) -> dict`
- `handover_blend.build_blended_rows(old_rows, new_rows, start_time, duration_s) -> rows`

- [x] **Step 1: 写失败测试**

测试两组含时延、多普勒、功率和 C/N 的状态，在 `alpha=0/0.5/1` 时分别等于旧状态、中间状态和新状态，并断言切换区的相邻差值小于直接切换。

- [x] **Step 2: 运行测试确认失败**

```text
python -m pytest -q local_ntn/test_handover_blend.py
```

预期：由于 `handover_blend.py` 尚不存在而失败。

- [x] **Step 3: 实现最小插值函数**

对连续数值使用线性插值，对位置/速度使用同一 `alpha`，不修改地面站 ECEF 坐标；保留卫星 ID 和阶段字段供调度文件使用。

- [x] **Step 4: 运行测试确认通过**

```text
python -m pytest -q local_ntn/test_handover_blend.py local_ntn/test_satellite_schedule.py
```

- [x] **Step 5: 接入导出器**

增加 `--handover-blend-s` 参数，默认 `5.0`；在旧卫星释放前生成 prepare/blend/complete 行，输出渐变后的 22 字段 `STKTRACE2` 和阶段调度 CSV。

### Task 2: 在 RFsim 中增加阶段日志和兼容校验

**Files:**
- Modify: `local_ntn/stk_schedule.h`
- Modify: `local_ntn/stk_schedule.c`
- Modify: `local_ntn/stk_trace_channel.c`
- Modify: `/home/kayoko/OAI/openairinterface5g/radio/rfsimulator/stk_schedule.h`
- Modify: `/home/kayoko/OAI/openairinterface5g/radio/rfsimulator/stk_schedule.c`
- Modify: `/home/kayoko/OAI/openairinterface5g/radio/rfsimulator/stk_trace_channel.c`

**Interfaces:**
- `stk_schedule_entry` 增加 `handover_phase`、`previous_satellite_id`、`next_satellite_id`。
- 旧 CSV 只有五列时阶段默认为 `steady`，旧行为保持不变。

- [x] **Step 1: 写失败的阶段解析测试**

验证五列旧 CSV 和扩展阶段 CSV 均可读取，并能在切换点返回旧 ID、新 ID和阶段。

- [x] **Step 2: 运行测试确认失败**

```text
python -m pytest -q local_ntn/test_stk_schedule.py
```

- [x] **Step 3: 实现兼容解析和日志**

扩展 C 结构和 bounded parser；日志输出 `handover prepare/blend/complete`，但不改变 RFsim 的 IQ 增益、时延和多普勒计算接口。

- [x] **Step 4: 编译并运行现有 IQ 回归**

```text
wsl.exe -d Ubuntu-22.04 -- cmake --build /home/kayoko/OAI/openairinterface5g/cmake_targets/ran_build/build --target rfsimulator -j 6
wsl.exe -d Ubuntu-22.04 -- python3 /mnt/d/实验室学习工作/杂活/雄安/OAI调研/local_ntn/test_real_iq.py
```

### Task 3: 生成切换专用轨迹并执行长时业务验收

**Files:**
- Create: `local_ntn/test_constellation_seamless.py`
- Modify: `local_ntn/run_constellation_validation.sh`
- Create: `docs/validation-2026-09-24-seamless-handover.md`

- [x] **Step 1: 生成覆盖两次切换的 1 Hz 轨迹**

生成从 STK 7614 s 开始、覆盖 8244 s 和 8799 s 的渐变轨迹，确认 schedule 顺序为 S06、S05、S04。

- [x] **Step 2: 运行离线连续性测试**

检查切换区时延、多普勒、功率、C/N 均有限，并统计最大相邻差值。

- [x] **Step 3: 编译全部 OAI 目标**

```text
wsl.exe -d Ubuntu-22.04 -- cmake --build /home/kayoko/OAI/openairinterface5g/cmake_targets/ran_build/build --target nr-softmodem nr-uesoftmodem rfsimulator -j 6
```

- [ ] **Step 4: 执行跨切换持续业务测试**（需要在 WSL 交互输入 sudo 密码）

保持同一核心网、gNB 和 UE，持续 ping 每秒发送一次，并运行覆盖两个切换点的 UDP iperf；检查 PDU Session 建立次数、TUN 创建次数、RRC 状态和切换日志。

- [x] **Step 5: 记录已完成的离线结果和端到端运行指令**

只记录统计结果和关键切换行，不写入原始 UE 凭据；如果仍有 PBCH 错误或丢包，报告发生时间和具体数量，不宣称无缝成功。
