# 整合测试结果（pre-live checkpoint）

候选保护代码 7f40221（最终pre-live补充验证）；Task7审阅通过基点49a353f26e2304dca8acde9e1da1a875860c6a96。
此文档当前只记录真实离线结果，四组live与原最终复验尚未执行，不代表发布完成。

| 测试 | 实际结果 |
| --- | --- |
| Task8缺checker接口，RED5ed95c8 | exit1，模块不存在 |
| 初版保护边界06f5be2 | 17 tests PASS；range diffcheck exit1，EOF空白 |
| 真实staged-only同status内容改动，RED72114cf | 19 collected，1 FAIL；缺dirty内容指纹 |
| staged/unstaged/index修复fdd0f42 | 19 tests PASS、compile/range diffcheck exit0 |
| 原launcher早退state归属，RED76a58ef | 21 collected，2 ERROR；缺claim_state |
| 精确state恢复3f8e96c | 21 tests PASS，含真实SIGTERM私有Python会话清理/无关会话保留 |
| 既有run_state/network_owner/core_lab | 12 /10 /6 tests PASS |
| static / firsthandover / legacy / full | 未运行 |
| 原平台最终parser/IQ与短跑 | 未运行 |
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
