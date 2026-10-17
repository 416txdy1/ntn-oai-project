# 内嵌源码与当前覆盖文件

这里保存的是源码归档，不是编译二进制，也不是 Git LFS 指针或子模块。SHA256 在 checksums.json；prepare_sources.py 在解包前校验。

- oai-source.tar.gz：来自 source-manifest.json 所列 commit 的工作树，包含已验证的 simulator.cpp 历史修复。保留构建 RFsim 所需源码、许可证和 ASN.1 定义。排除部署凭据示例、SQL/抓包、未使用 E2 子模块等，完整列表见 manifest。
- quadriga-source.tar.gz：QuaDRiGa 2.8.1-0 的 quadriga_src、tutorials 和完整许可证；没有改动上游源码，集成逻辑在 quadriga/matlab/。
- asn1c-source.tar.gz：固定 commit 940dd5fa9f3917913fd487b13dfddfacd0ded06e，包含构建工具源码和许可证。
- simde-source.tar.gz：已验证 SIMD 头文件源码；逐文件保留 MIT 等版权声明，不包含嵌套 .git。

当前实验需要的覆盖文件在 oai_patch/current/（含构建版本标识适配、可选 blend 时延前馈及多接收端口 PUCCH 调度）与 quadriga/oai/（3 个文件），解包器只将它们同步到本仓库 .runtime/oai，不会覆盖外部源码。新增的 openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_uci.c 沿用本归档版本，仅在 NO_BEAM_MODE 下使 PUCCH 使用与 PUSCH 相同的接收端口集合；不修改公开函数签名或有波束模式。

源码之外的操作系统依赖用发行版包安装；5GC 通过容器镜像运行。不会为了构建启用 E2/FlexRIC 或自动下载 ASN1C。

`common/utils/ntn_feedback_diagnostics.h`、`openair2/NR_UE_PHY_INTERFACE/NR_IF_Module.c`及上述PUCCH调度overlay还提供默认关闭的反馈诊断。设置`OAI_NTN_FEEDBACK_DIAGNOSTICS=1`后，每256个事件输出一次UE CRC和gNB反馈累计计数；不修改译码、HARQ和功率控制判定，不输出UE身份或凭据。
