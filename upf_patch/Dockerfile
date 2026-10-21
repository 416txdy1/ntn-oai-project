# UPF v2.2.1 原镜像；只替换完成测试的 UPF 程序。
ARG BASE_IMAGE=oaisoftwarealliance/oai-upf@sha256:03985036c2477a75755ded9b7fe9508b62f49e4ce9e9f059bbb68af63932e7f7
FROM ${BASE_IMAGE}
COPY oai_upf /openair-upf/bin/oai_upf
LABEL ntn.upf.source="451c27daa4b38bd03a5cb5b92412743364ff8ae0" \
      ntn.upf.patch="control-plane-qfi-v1"
RUN ldd /openair-upf/bin/oai_upf && /openair-upf/bin/oai_upf --help
