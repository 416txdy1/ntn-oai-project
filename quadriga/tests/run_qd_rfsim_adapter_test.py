"""Compile and run the actual OAI QDCHANNEL1 sparse RFsim adapter."""
from __future__ import annotations
import argparse
import json
import math
import shlex
import subprocess
import tempfile
from pathlib import Path


def compile_flags(build_repo: Path, oai_repo: Path) -> tuple[list[str], Path]:
    build = build_repo / "cmake_targets/ran_build/build"
    database = json.loads(subprocess.check_output(["ninja", "-C", str(build), "-t", "compdb"], text=True))
    entry = next(item for item in database if item.get("file", "").endswith("/apply_channelmod.c"))
    command = shlex.split(entry["command"])
    compiler = next(index for index, value in enumerate(command) if Path(value).name in ("cc", "gcc", "clang"))
    flags: list[str] = []
    index = compiler + 1
    while index < len(command):
        value = command[index]
        if value in ("-o", "-MF", "-MT", "-MQ"):
            index += 2
            continue
        if value in ("-c", "-MD", "-MMD", "-MP") or value == entry["file"]:
            index += 1
            continue
        if value.startswith("-"):
            flags.append(value)
        index += 1
    flags = [value for value in flags if value not in ("-DT_TRACER", "-DNDEBUG")]
    flags = [value.replace(str(build_repo), str(oai_repo)) for value in flags]
    flags.append("-UNDEBUG")
    return flags, build


def run(command: list[str], cwd: Path) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oai-repo", type=Path, required=True)
    parser.add_argument("--build-repo", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    sanitizers = parser.add_mutually_exclusive_group()
    sanitizers.add_argument("--sanitize", action="store_true")
    sanitizers.add_argument("--thread-sanitize", action="store_true",
                            help="检查 OAI_QD_WORKERS 并行卷积的数据竞争")
    parser.add_argument("--sample-rate", type=float, default=30720000,
                        help="IQ 采样率；完整业务使用 7680000 Hz")
    parser.add_argument("--max-points", type=int, default=0,
                        help="大规模 bundle 的确定性分层检查数量；0 表示全部节点及中点")
    args = parser.parse_args()
    if not math.isfinite(args.sample_rate) or args.sample_rate <= 0:
        parser.error('--sample-rate 必须为有限正数')
    if args.max_points < 0 or args.max_points == 1:
        parser.error('--max-points 必须为0或至少2')
    oai_repo = args.oai_repo.resolve()
    flags, build = compile_flags(args.build_repo.resolve(), oai_repo)
    if args.sanitize:
        flags.extend(["-fsanitize=address,undefined", "-fno-omit-frame-pointer"])
    if args.thread_sanitize:
        flags.extend(["-fsanitize=thread", "-fno-omit-frame-pointer", "-fno-pie", "-no-pie"])
    source = Path(__file__).with_name("qd_rfsim_adapter_test.c").resolve()
    rfsim = oai_repo / "radio/rfsimulator"
    with tempfile.TemporaryDirectory(prefix="qd-rfsim-adapter-") as temporary:
        executable = Path(temporary) / "qd_rfsim_adapter_test"
        run(["cc", *flags, str(source), str(rfsim / "qd_channel_reader.c"),
             str(rfsim / "qd_channel_adapter.c"), "-lcrypto", "-lm", "-lpthread",
             "-o", str(executable)], build)
        run([str(executable), str(args.bundle.resolve()), str(args.trace.resolve()), str(args.max_points),
             str(args.sample_rate)], build)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
