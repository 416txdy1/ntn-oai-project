# MISO有声直播整合验收（2026-10-22）

本次整合的构建、回归、新平台实际有声演示、短对照、原平台业务及旧直播复验均通过。失败轮次仍保留于本文，不计作PASS。来源分支报告不能替代下列实测。

## 来源与隔离

- 直播：`95207d325f3272b5ba241175aac246c0b6bfa73c`。
- MISO：`fc389626ffd7cfa3fd3b477682c1c45b0bf772da`。
- 双亲合并：`277751819e2d5b8b08b9dae1df939c1efa50fd76`。
- 新分支：`codex/ntn-live-miso-integration-20261021`；两个来源分支保留。
- 新运行副本 `/home/kayoko/ntn-workspaces/ntn-live-miso` 使用独立构建和私密配置。旧运行副本 `/home/kayoko/ntn-workspaces/ntn-quadriga-handover` 没有重新构建或覆盖配置。

## 构建与回归

以下命令在新Linux副本执行，均exit=0。完整日志只保存在该副本私有目录。

```bash
JOBS=6 nice -n 10 bash scripts/build.sh
python3 scripts/build_upf_qfi.py --jobs 6 --network host
sudo python3 scripts/configure_upf_qfi.py
cmake --build .runtime/oai/cmake_targets/ran_build/build --target nr_prachsim nr_pbchsim -j 6
bash local_ntn/run_regressions.sh
bash scripts/test.sh
python3 -B -m unittest discover -s ntn_live_demo -p 'test_*.py'
python3 -B ntn_test_launcher/test_launcher.py
python3 -B ntn_test_launcher/full_test.py --root /home/kayoko/ntn-workspaces/ntn-live-miso --check-only
```

PHY测试构建4.93秒、trace/IQ回归15.13秒、完整脚本回归191.36秒。完整脚本包含实际SISO/MISO上下行数据集的数值与内存检查。测试环境使用独立test-venv（pytest 8.3.5），未修改旧环境或系统Python。32项直播Python测试、9项启动器测试通过；前端13项规则及真实DOM/图表、端口、线程、恢复、失效保护测试通过；三个PowerShell入口语法检查通过。对照实验另重跑trace/IQ回归（12.5秒）、完整脚本回归（178.1秒）、派生预检和上下行实际数据读取测试，全部通过。

实际UPF镜像ID：`sha256:a3361bc70ccb324cecf50b721287a88434ca85e47b2c8bbb46c6d37715495ae6`；二进制SHA256：`4ae4a05013a967eb0d55e02a31f141e40e9bcae8890dd8b9f5f81711370cf5ea`。MISO演示校验容器实际镜像ID与构建清单一致，不只检查标签。

## 真实有声演示

使用用户提供的本地H264/AAC视频，实时循环转码VP8/Opus。视频、音轨、私有路径和原始UE日志不发布。下列PowerShell命令中的`$video`为本地媒体路径，启动器与CMD共用同一实现，已完成回归后使用`-SkipRegressions`避免逐轮重复回归。

|测试|运行编号|结果|
|---|---|---|
|新平台SISO首次切换|live-firsthandover-20261022-094719-3ae9aa|PASS|
|新平台MISO首次切换|live-firsthandover-20261022-095048-9ea9a1|PASS|
|MISO同一连接双切换，615 IQ秒|live-full-20261022-112546-ba667e|PASS|
|MISO四轮独立重放|handover-replay-20261022-103407-59e358|4/4 PASS|
|MISO短三组对照|causal-20261022-104928-5bf488|SUPPORTED，三组演示均PASS|
|原平台实际业务复验|merge-20261022-original|PASS|
|保留的旧直播分支及旧运行目录|live-firsthandover-20261022-111720-f048e4|PASS|

```powershell
.\ntn_live_demo\launch.ps1 -Case firsthandover -SpatialMode siso -SkipRegressions -Source $video
.\ntn_live_demo\launch.ps1 -Case firsthandover -SpatialMode miso4-subarray -QdWorkers 8 -SkipRegressions -Source $video
.\ntn_live_demo\launch.ps1 -Case full -SpatialMode miso4-subarray -QdWorkers 8 -SkipRegressions -Source $video
.\ntn_live_demo\launch_replay.ps1 -SpatialMode miso4-subarray -QdWorkers 8 -Rounds 4 -SkipRegressions -Source $video
.\ntn_live_demo\launch_causal.ps1 -SpatialMode miso4-subarray -QdWorkers 8 -Smoke -Repeats 1 -Source $video
```

MISO实测要求DL4Tx×1Rx、UL1Tx×4Rx、两端8个计算线程，gNB端口0–3均在至少两个观测窗发送非零IQ。演示通过同时要求数值审计、UE隧道捕获、中继入流和音视频推进；仅播放出画面不算通过。四轮重放每轮65 IQ秒，均核对prepare→blend→complete，每轮重新建立会话；轮间重连不计作切换。

最终长测从7.119至615.116 IQ秒记录1147个连接样本；音频观测1140.995墙钟秒、采样推进比0.999970。两次实际完成位于约45.000及599.999 IQ秒（STK约8245及8800秒）；统计窗口以切换表8244及8799秒为中心，按原实现覆盖事件前后。第一次窗口视频增加244帧、音频增加864000样本，第二次增加269帧、864000样本；两窗口采样到的最大无新显示帧间隔约649.8及813.7ms。存在间歇冻结，不能称零卡顿。

## 短对照的证据与范围

同一编码、随机种子及原四端口系数；干预只在70–82 IQ秒预先设置下行C/N衰减16dB。正常组和干预组随轨迹运行，固定组冻结整个轨迹时钟。派生包的trace/manifest/antenna/完成记录哈希通过预检，原tap载荷字节不变。

|深衰减观测窗口指标|固定组|正常组|干预组|
|---|---:|---:|---:|
|输入下行C/N中位数，dB|16.75|19.89|3.88|
|UE中继入流，kbit/s|340.96|215.60|0.00|
|解码帧率，fps|15.00|16.01|0.00|
|扩展响应窗口冻结，墙钟秒|1.72|0.00|3.22|

三组输入覆盖、保护及物理审计通过；发送器保持实时推进、进程存活，UE入流计数未重置，原配对门限判定SUPPORTED。这只证明本次受控物理信道干预影响UE入流及直播，不能把正常切换中的每次冻结都归因于卫星，也不是多次统计重复或完整双切换的长对照。默认6轮长对照本次未执行。

## 原平台保护

旧集成运行副本44个保护文件摘要全部一致，包括源码覆盖、无线二进制及私有配置；不发布这些私有文件。原OAI及核心网源码快照无变化。初始整合快照中的原工作区差异只涉及本任务三份未跟踪工作草稿，运行时不再改写这些草稿。

使用新鲜停机快照执行原平台业务复验：

```bash
sudo python3 scripts/original_platform_check.py snapshot --snapshot .private/final-original-before-20261022.json
sudo python3 scripts/original_platform_check.py short-run --snapshot .private/final-original-before-20261022.json --tag merge-20261022-original
```

均exit=0：ping 30/30，上行丢失0/130、下行丢失0/130，复验前后快照差异为空。旧实验曾因WSL重启留下停止的容器，已按所属run正常清理；未重新创建或覆盖原核心网、原模板。

另外从保留的 `codex/ntn-live-video-demo-20261021` 工作树执行其原始 `ntn_live_demo/launch.ps1 -Case firsthandover -SkipRegressions -Source $video`，使用旧Linux运行目录完成S06→S05、有声播放及保护门禁，exit=0。未修改旧分支代码。

## 已保留的失败与限制

- 初期宿主C盘耗尽导致WSL只读与构建I/O错误。恢复空间及可写环境后，将本任务失败的生成目录单独保留，从已验证归档重新构建，无线与UPF最终构建通过。未删除视频或改建旧平台。
- Docker默认构建网络获取libbpf时TLS连接失败，改用明确的`--network host`构建；TLS验证仍启用。只停止本任务已核实身份的编译进程后改用6个编译线程，未使用全局清理。
- `live-full-20261022-095423-1d97d8`在Msg3随机接入阶段发生PDU就绪超时，未进入直播，失败保留。没有放宽就绪或业务门限。
- `live-full-20261022-100257-145b21`完成同一连接的两次切换、音视频及物理审计，但整体FAIL：测试期间更新了原工作区一份未跟踪说明草稿，保护比较正确报告`sources`变化。差异只涉及`.planning/live-miso-integration/edit/MISO_LIVE_INTEGRATION.md`，原OAI/核心网源码、二进制和配置无变化；该轮不改记为整体PASS。
- IQ与墙钟不是1:1，来源模型是四子阵LOS相位加权、单层PDSCH，不是完整STK MVDR。C/N是信道输入，不是实测SINR。音频采样推进包括可能的丢包补偿，不能据此承诺声学无损或零卡顿。

最终长测后再次核对旧运行副本44个文件，差异为空；未遗留modem或新核心网容器。运行测试对应功能代码`4cfb7c6242f57d99f75f1f77d89b245633bc1569`，随后的提交仅整理验收与使用文档。相对两个来源真正新增的文件已检查私密路径、媒体、原始日志及凭据模式；运行证据保留私有，发布内容为代码和脱敏说明。
