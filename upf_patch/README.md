# UPF 下行首包 QFI 本地覆盖

本补丁只修改普通（simple-switch）UPF 的 IPv4 下行 QFI 选择。基础镜像是项目原来的 `oaisoftwarealliance/oai-upf:v2.2.1`，固定摘要 `sha256:03985036c2477a75755ded9b7fe9508b62f49e4ce9e9f059bbb68af63932e7f7`；源码固定为 `451c27daa4b38bd03a5cb5b92412743364ff8ae0`。

## 原因和规则

原实现初始会话 QFI=5，直到收到 IPv4 上行包才从匹配 PDR 学到 QFI=1。下行早于该上行包到达时，UE SDAP 拒绝未知 QFI。本实验 PFCP 抓包证实 SMF 建立 ACCESS PDR1（QFI=1），随后建立 CORE PDR2，没有下发 QER；不能只增加 QER 查询就认为问题已解决。

新逻辑优先使用匹配下行 PDR 所关联 QER 的有效 QFI。没有 QER 关联时，仅在当前会话的 ACCESS PDR 都具有有效、相同 QFI 时回退。QFI 必须为 1–63；显式 QER 缺失、非法值或多流歧义均拒绝转发并记录诊断，不使用硬编码 1/5，也不放宽 UE 检查。这个回退只用于无 QER 的单 QFI 会话，多 QFI 会话应由 SMF 正确关联 QER。

没有添加预热流量、重发首包、延迟统计起点或剔除失败包；墙钟负载、5 秒期限、STK/IQ 时钟、MISO 空间模型均保持原配置。BPF 转发和 IPv6 的上游实现不在本修复范围内。

## 构建与使用（Ubuntu 22.04 / WSL2）

```bash
python3 scripts/build_upf_qfi.py --jobs 6
bash scripts/test_upf_qfi.sh
# 确认本实验核心网已通过 core_lab.py down 停止
sudo python3 scripts/configure_upf_qfi.py
# 回退也要求先停机
# sudo python3 scripts/configure_upf_qfi.py --rollback
```

原始 OAI 配置模板不覆盖；选择器仅修改隔离 profile 的私有 Compose image 行并保存备份，拒绝来源标签不符的镜像和运行中切换。原官方镜像保留。新环境初始化后也需要执行选择器。

构建脚本在 `.runtime/upf-qfi/source` 克隆固定版本，沿用其锁定子模块：common-build `bcd6a99284a71f4d47a613ef5d661b10fbf5b033`，common-src `ce8dca5fecd3f4fb8a31a70ec518c03db87fbab2`。依赖编译沿用上游 Dockerfile，保留 TLS 证书验证；依赖只安装在构建镜像中。最终镜像只在原镜像上替换 `/openair-upf/bin/oai_upf`，不把编译环境的系统升级带入运行镜像。

产物 `ntn-local/oai-upf:2.2.1-qfi-v1` 及 `.runtime/upf-qfi/manifest.json` 记录源码、基础镜像、补丁、头文件、程序和镜像哈希。源码版本可复现；上游依赖安装访问在线软件包仓库，因此不宣称跨日期构建逐字节相同。不要提交 `.runtime`、`.private`、原始 UE 日志或抓包。

`downlink_qfi.hpp` 是生产调用的同一选择器；18 项 C++ 测试覆盖规则选择和失败分支，启用 ASan/UBSan。`scripts/test_upf_qfi.py` 的 6 项测试检查配置保存、停机约束、来源校验和回退。这些测试已接入 `scripts/test.sh`；完整 UPF 编译及端到端抓包仍是实际修复验收的必要步骤。
