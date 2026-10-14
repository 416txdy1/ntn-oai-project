# STK 场景交付与天线基线（2026-10-14）

## 打开与使用

在安装 STK 12 且具备所需通信模块许可的 Windows 机器上，打开仓库内 `STK_LEO_Constellation_20260923_train_v2/OAI_LEO_Constellation.sc`。保留整个场景目录及相对布局；`.sa`、`.plc`、`.r`、`.x`、`.c` 和相应图形/单位配置共同组成场景。不要只复制 `.sc`。

本次按保存文件检查对象依赖并纳入 Git，没有启动 STK 做场景加载或重新导出验证。保存文件记录 WrittenBy STK 12.2.0。STK 自带模型、地球定向和图形资源仍由本机安装提供；历史元数据、禁用的 interval-file 字段和界面设置可能保留原作者绝对路径。若本机 STK 提示资源不存在，应先核对提示；不要把历史路径当成调试目录。

目录内 `constellation_manifest.json` 的 scenario/source_scenario 是历史来源信息，不是可直接执行的本机路径。`LogFiles/`、工作区界面布局 `.wsp/.wsptb` 不属于交付输入。

## 保存的 OAI 天线配置

| 端点 | 天线 | 波束目标 |
|---|---|---|
| 北京 gNB DL Tx / UL Rx | Isotropic | 无阵列方向性 |
| UE UL Tx / DL Rx | Isotropic | 无阵列方向性 |
| 卫星 DL Rx / UL Tx（feeder） | 16×16 Phased Array | Place/Beijing |
| 卫星 DL Tx / UL Rx（service） | 16×16 Phased Array | Place/OAI_UE |

卫星阵列为矩形格点，X/Y 间距均 0.5λ；启用阵元因子，指数 1；后瓣抑制 30 dB；目标跟踪扫描限制方位/俯仰各 ±60°。OAI 八个通信端点均 UsePolarization=false。DL 2.4884 GHz、UL 1.6149 GHz。

根目录 `configure_stk_phased_array.py` 是历史场景副本配置脚本，带原机器路径及场景保护条件，其 gNB 16×16、UE 4×4 设置与当前保存场景不同。`stk_build_oai_ntn_scene.py` 则会配置 Isotropic。不要为查看场景而直接运行这两个会改变天线的脚本。

## 与当前回放数据的关系

QuaDRiGa 导出器 `quadriga/matlab/export_stk_to_qdchannel.m` 当前两端为 `qd_arrayant('omni')`，仅生成卫星—UE 的 1×1 SISO 多径；STK 负责绝对链路项。天线一致性调整尚未实施，本提交只保存调整前基线。

Linux 默认调试入口使用 `examples/fdd-pass/trace.csv` 及其 downlink/uplink bundle，不会自动加载本目录的其他 trace。原始、run、test、blend 轨迹及调度文件保留用于追溯，不能任意替换已绑定的 FDD 输入。改变 STK 天线并重导出 trace 后，必须同时生成匹配的双向 QuaDRiGa bundle，并重新验证哈希、频率和方向。

示例回放无需 STK/MATLAB；生成新轨迹和新信道需要相应软件与许可。完整 361 秒示例末段仍有失步，见 `DEBUG_ZKY.md` 和 `MIGRATION_VALIDATION_20261014.md`。