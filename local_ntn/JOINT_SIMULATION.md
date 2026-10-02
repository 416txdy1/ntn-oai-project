# STK + QuaDRiGa 联合仿真当前入口

当前 zky 的交付方式已经改为单仓库源码归档与相对路径构建。请使用 [MANUAL_RUN.md](MANUAL_RUN.md)。旧 `/home/duyaya/OAI/joint-startup-20260928` 仅是历史测试副本，不是接收者必须具有的路径。

```bash
bash scripts/build.sh
python3 scripts/init_lab.py
source scripts/env.sh
bash scripts/core.sh up
bash scripts/prepare_iperf.sh
python3 local_ntn/experiment.py preflight --rate 1
```

目录解析以脚本所在项目为基准：OAI 在 `.runtime/oai`，QuaDRiGa 在 `.runtime/quadriga`，默认 trace 和双向 bundle 在 `examples/fdd-pass`；UE 私有配置和 Docker Compose 配置在 `.private`。网络或 namespace 操作需要 root，完整命令见手册。

历史两轮测试、数值验算和限制见 quadriga/docs/recheck_20260928.md 及项目历史记录；本次交付验证见 docs/SELF_CONTAINED_VALIDATION.md。