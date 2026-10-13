# 整合测试结果（验收进行中）

候选保护代码 7f40221（最终pre-live补充验证）；Task7审阅通过基点49a353f26e2304dca8acde9e1da1a875860c6a96。
此文档保留初期离线检查点，并追加真实运行结果；最终验收与原平台业务后测尚未完成，不代表发布完成。

| 测试 | 实际结果 |
| --- | --- |
| Task8缺checker接口，RED5ed95c8 | exit1，模块不存在 |
| 初版保护边界06f5be2 | 17 tests PASS；range diffcheck exit1，EOF空白 |
| 真实staged-only同status内容改动，RED72114cf | 19 collected，1 FAIL；缺dirty内容指纹 |
| staged/unstaged/index修复fdd0f42 | 19 tests PASS、compile/range diffcheck exit0 |
| 原launcher早退state归属，RED76a58ef | 21 collected，2 ERROR；缺claim_state |
| 精确state恢复3f8e96c | 21 tests PASS，含真实SIGTERM私有Python会话清理/无关会话保留 |
| 既有run_state/network_owner/core_lab | 12 /10 /6 tests PASS |
| static / firsthandover / legacy / full | 后续实际结果见下；尚未全部通过 |
| 原平台最终parser/IQ与短跑 | parser/IQ 已通过；最终业务短跑待执行 |
| 最终全分支独立审阅/远程push | 未完成 |

实际GREEN命令，在独立Linux克隆中set-e串行执行，aggregate exit0：

~~~bash
python3 scripts/test_original_platform_check.py
python3 local_ntn/test_run_state.py
python3 local_ntn/test_network_owner.py
python3 scripts/test_core_lab.py
python3 -m py_compile scripts/original_platform_check.py
git diff --check 49a353f26e2304dca8acde9e1da1a875860c6a96 HEAD
~~~

## 整合前原短跑与保护证据范围

2026-10-12实际前测：rate1、原1387行7614–9000 trace；ping30/30，
UL/DL UDP各0/130丢失，各命令exit0。七项trace、模板、原binary的真实before/after SHA256与mtime相同。
原ignored gnb.local.conf和initial_delay_ms.txt由既有launcher再生成，其旧字节恢复没有被证明。

纠正原baseline报告：private before.json的Git HEAD/status字段实际包含dubious ownership错误文本。
这些文本相等不能证明完整源码HEAD/dirty集合未变；原始before.json保留不修改。
原sources.lock在2026-09-22提交cb60f035c3968077d0c8a4b505ea9640bf99d279已记录
OAI c4125d1c74和5GC212f92f，当前成功checked Git查询与之相符。
当前32/13个dirty/untracked普通文件mtime均早于前测只能作为辅助证据，
没有可靠Task1前完整dirty集合及内容hash快照。

Task8新的成功快照将明确标时点，覆盖随后live阶段源码status、dirty文件hash、index摘要、
七项文件、容器ID/labels/running和网络身份；它不补造此前缺失证据。
真实四case结果、命令/退出码、time precision/workload/two windows及原最终复验应在执行后追加；
所有失败记录保留，只有验收与保护审阅全部通过才允许新分支push。
最终pre-live checkpoint：7f40221。23项阶段又观察到容器归属RED d23a5b9 exit1：
失败start后同ID被外部启动，旧实现错误调用stop。5b0b09f只在精确start成功ID确认且
StartedAt处于本次命令区间时登记，未知partial保留失败；cleanup还匹配owned StartedAt，
外部同ID重启拒绝停止。7f40221补充成功/区间外启动/外部重启三场景验证。
最终24保护tests、run_state12、network_owner10、core_lab6、compile及全范围diffcheck aggregate exit0。
真实private Python子会话SIGTERM停止与无关会话保留通过；这不是任何modem或业务live测试。

## 2026-10-13 实际运行与当前失败

物理时钟启动修复候选 `96a5aea` 的 static 90 IQ 秒实测通过：ping 104/104，
UL UDP 1323/1323，DL UDP 1318/1322（0.30% 丢失）；业务区间为 IQ
19.6223–85.016 秒，PBCH 错误和重接入为 0，QD 双侧各加载一次，停止与清理成功。
这是该候选的实测结果，不能替代后续接收端修改的重新验收。

PRACH 中心搜索候选 `a438f5c9b2f44dee14772ae0dd93783f18e00eb9`：实际生产
波形生成、提取与解码 200 场景通过，其中 66 项明确正确前导真值检查、24 项正时延
TA 单位检查。测试范围和边界详见 `prach-centered-search.md`；不是任意时延的保证。
五目标实际构建、parser/IQ 回归、完整离线回归及独立范围审查通过。

同一候选运行命令：

~~~bash
python3 scripts/handover_acceptance.py --case firsthandover --profile integrated-handover --run-id task8-first-20261013c --max-wall-seconds 3600
~~~

**实际退出码 1，验收失败，保留记录。** 初始 PDU 已建立，持续业务覆盖 IQ
18.932923–64.425199 秒；物理观测完整覆盖 70 IQ 秒。首次切换 STK
8239–8249 秒窗口完整，但 ping 0/14，UL UDP 5/172，DL UDP 5/173：
窗口丢失率分别为 100%、97.11%、97.13%。全程 ping 50/64，UL 636/806，
DL 633/805；验收观测内 PBCH 错误 314、PHY 重接入 5。双侧 QD 各加载一次，
停止退出码 0、清理无错误。不得把完整覆盖或成功接入解释为切换验收通过。

接收跟踪诊断仍是待验证假说：真实时延在切换阶段每秒下降约 1144–1229 微秒，
每 10 ms 移动约 88–94 个采样，现有定时搜索约 ±36 个采样。首次 PBCH 错误
位于实际时钟括号 IQ [38.93355, 39.03355]，不是精确的错误时间戳。
候选修复必须从接收信号测量，不能通过模型真值补偿、重置时钟或放宽验收阈值通过。

`cacc0eb` 仅修正 RTT 图显示：收到的 ICMP 样本画为独立点，丢包空缺不连接曲线；
原失败数据、统计和验收结果不变。

原平台实际回归从原工作目录执行，所有命令退出码 0；编译产物和日志只存新平台
私有目录，不写原构建树：

~~~bash
cc -Wall -Wextra -Werror -I local_ntn local_ntn/test_trace.c local_ntn/stk_trace.c -lm -o /home/kayoko/ntn-workspaces/ntn-quadriga-handover/.private/task8-20261013/original-parser-iq-current/test_trace
/home/kayoko/ntn-workspaces/ntn-quadriga-handover/.private/task8-20261013/original-parser-iq-current/test_trace
PYTHONDONTWRITEBYTECODE=1 python3 local_ntn/test_trace_validation.py
PYTHONDONTWRITEBYTECODE=1 python3 local_ntn/test_real_iq.py
~~~

最终原平台业务后测、完整保护对比、四组新平台验收和全分支独立审查仍待完成。