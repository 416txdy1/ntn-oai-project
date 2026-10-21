# MISO直播整合验收进度（2026-10-21）

状态：代码整合已完成；真实运行验收未完成，尚未推送，不能称MISO直播已通过。

## 准确来源与隔离

- 直播来源：95207d325f3272b5ba241175aac246c0b6bfa73c。
- MISO来源：fc389626ffd7cfa3fd3b477682c1c45b0bf772da。
- 本地双亲合并提交：277751819e2d5b8b08b9dae1df939c1efa50fd76。
- 新分支：codex/ntn-live-miso-integration-20261021。原两个分支保留。
- 新Linux副本：/home/kayoko/ntn-workspaces/ntn-live-miso，独立解包与私有初始化已完成。
- 旧集成运行副本44个源码/二进制/配置摘要及原平台快照已保存到新副本私有目录，未发布私有文件。

## 已通过

候选适配代码在本工作区 `.planning/live-miso-integration/edit` 验证后同步到新工作树。准确命令：

```powershell
wsl.exe -d Ubuntu-22.04 --exec python3 -B -m unittest discover -s '/mnt/d/实验室学习工作/杂活/雄安/OAI调研/.planning/live-miso-integration/edit/ntn_live_demo' -p 'test_*.py'
wsl.exe -d Ubuntu-22.04 --exec python3 -B '/mnt/d/实验室学习工作/杂活/雄安/OAI调研/.planning/live-miso-integration/edit/ntn_test_launcher/test_launcher.py'
```

32项直播测试、9项启动器测试通过。使用捆绑Windows Node执行test_dashboard.cjs：13项规则通过；test_dashboard_ui.cjs：实际端口/线程/非零端口显示、图表、关联提示、恢复和失效保护通过。受限沙箱Edge首次启动失败，改在正常Windows执行环境复验通过，未改变测试门限。PowerShell启动器语法检查通过。本地视频路径JSON被Git忽略。

## 构建与运行阻塞

- 已在新副本执行低优先级 `JOBS=4 bash scripts/build.sh`，依赖工具及大部分协议源码已编译；尚未成功退出。
- 已执行 `python3 scripts/build_upf_qfi.py --jobs 2`，固定源码与子模块获取成功，Docker依赖构建进行后中断；镜像尚未完成。
- 宿主C盘空间曾只剩约0.03 GiB，随后WSL出现EROFS及系统二进制I/O错误；无线构建exit=1，UPF构建exit=120。不是已定位的源码编译错误，不能算通过。
- 实际MISO派生预检也因创建私有目录时EROFS退出，不能算通过。
- 为释放空间，只将本任务21个已完成截图目录迁移到D盘保留，未移动正在运行的目录、未删除用户视频。宿主C盘随后约0.51 GiB，仍不足以安全完成后续构建。
- 旧实验live-firsthandover-20261021-152710-b5acd5仍有活动gNB/UE和核心网。未接管、停止或重启WSL；已请求允许按所属run正常停止旧实验并恢复WSL环境。

## 待完成门禁

恢复足够宿主磁盘空间和WSL可写环境后，完成独立无线/UPF构建与镜像配置，重跑trace解析/实际IQ及完整脚本回归，验证真实MISO派生信道，然后执行SISO基线、MISO有声首次切换、同一连接双切换、4轮重放及受控衰减配对。每次运行需通过实际四端口非零IQ、数值审计、音视频、路径与清理门禁。最后复验旧平台业务和保护摘要、隐私扫描，才允许推送新分支。

来源分支历史报告不能替代这些新版本测试。当前没有任何新MISO直播物理运行被记作PASS。