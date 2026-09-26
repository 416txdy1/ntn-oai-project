# Step 4：QuaDRiGa 稀疏多径接入 OAI RFsim

## 目标与边界

本步骤只完成卫星UE SISO service link 的 IQ 多径接入。信道量的唯一归属如下：

| 物理量 | 唯一来源 |
| --- | --- |
| 绝对路径增益、可见性、噪声 | STKTRACE2 |
| bulk delay、bulk Doppler | STKTRACE2 |
| 归一化相对多径系数、相对 excess delay | QDCHANNEL1 |

QDCHANNEL1 的生产 bundle 中 `residual_gain_db` 为 0 dB，因此不会再次施加距离相关路径损耗。运行顺序为：

`QuaDRiGa 相对多径卷积 -> STK bulk Doppler -> STK 绝对增益/噪声`

## 为什么不复用 OAI 短 FIR

OAI `channel_desc_t::channel_length` 是 `uint8_t`，最多表达 255 个采样点。真实 bundle 最大相对 excess delay 为 `0.00110293139355125 s`，在 30.72 Msps 下约为 33,882.05 个采样点。直接扩大字段还会破坏现有 ABI 和已经按旧长度分配的 `ch` 缓冲区。

因此本步骤不修改 `channel_desc_t`，而是增加独立的稀疏卷积适配器，并让 RFsim 为每个 block 请求足够的历史 IQ。当前真实 bundle 需要 `ceil(max_delay * sample_rate) + 3 = 33886` 个历史采样点。

## 运行配置

gNB 和 UE 进程必须使用各自方向的 bundle，并使用相同 STK trace 和采样率：

```bash
export OAI_STK_TRACE=/absolute/path/stk_constellation_trace_blend.csv
export OAI_QD_CHANNEL=/absolute/path/qd_bundle
```

适配器会在启动时强制校验：

- STK trace SHA256 与 bundle provenance 一致；
- bundle 为 SISO；
- `radio.link_direction` 与当前 RFsim 上/下行一致；
- bundle 中心频率与 RFsim 载频一致；
- 所需历史长度不超过安全上限。

默认历史长度上限为 1,000,000 个采样点。如经内存评估后确需提高，可显式设置 `OAI_QD_MAX_HISTORY_SAMPLES`。不要仅为绕过错误而提高上限。

## 代码位置

- 项目侧规范实现：`quadriga/oai/qd_channel_adapter.c`
- OAI 运行时实现：`radio/rfsimulator/qd_channel_adapter.c`
- 严格 bundle reader：`radio/rfsimulator/qd_channel_reader.c`
- RFsim 历史输入与卷积接入：`simulator.cpp`、`apply_channelmod.c`
- STK 时间映射和当前 block 噪声标定：`stk_trace_channel.c`

## 验证命令

完整 OAI 隔离构建：

```bash
./cmake_targets/build_oai -d zky_step4 --gNB --nrUE -w SIMU --ninja
cmake --build cmake_targets/zky_step4/build \
  --target nr-softmodem nr-uesoftmodem rfsimulator -j 6
```

真实 bundle 适配器与 sanitizer：

```bash
python3 quadriga/tests/run_qd_rfsim_adapter_test.py --sanitize \
  --oai-repo /home/duyaya/OAI/oai-zky-preserve \
  --build-repo /home/duyaya/OAI/openairinterface5g \
  --bundle .planning/2026-09-24-stk-quadriga-oai-integration-plan/runtime-output/audit-downlink \
  --trace STK_LEO_Constellation_20260923_train_v2/stk_constellation_trace_blend.csv
```

STK parser/IQ 回归和链路预算审计：

```bash
OAI_REPO=/home/duyaya/OAI/oai-zky-preserve \
OAI_BUILD_REPO=/home/duyaya/OAI/openairinterface5g \
bash local_ntn/run_regressions.sh

python3 -m unittest -v quadriga.tests.test_validate_bundle \
  quadriga.tests.test_channel_math quadriga.tests.test_audit_link_budget
python3 -m quadriga.tools.audit_link_budget BUNDLE TRACE.csv
```

## 验算结论

- 完整 OAI 构建成功，两个 QD 源文件均生成于 `rfsimulator` 目标。
- 真实下行适配器测试通过：1,387 快照、11 路径、33,886 历史采样点。
- ASan/UBSan 未发现越界、未定义行为或内存错误。
- 13 个 schema/channel-math/link-budget 测试通过。
- DL/UL 最大 tap 功率误差为 `6.081311076933105e-08`。
- `residual_gain_db` 最大绝对值、FSPL slope、FSPL correlation 均为 0。
- 组合前后 FSPL slope 均为 `1.2038472634976762`，排除重复大尺度路径损耗。
- STK trace parser、物理边界、IQ loss/outage/noise/delay/Doppler 和旧 visibility gate 均通过。

本步骤尚未进行真实 gNB/UE/5GC 空口联调；该工作属于后续运行阶段，不影响本步骤对代码路径、格式和数值所有权的验证。

OAI `zky` 回退点：`1e0c78bfbb80424f275e73a3103f582e0f903413`。
