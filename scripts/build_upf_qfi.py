"""在 Docker 内构建固定 UPF 版本的首包 QFI 修复，不安装宿主依赖。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

REVISION = "451c27daa4b38bd03a5cb5b92412743364ff8ae0"
BASE = "oaisoftwarealliance/oai-upf@sha256:03985036c2477a75755ded9b7fe9508b62f49e4ce9e9f059bbb68af63932e7f7"
IMAGE = "ntn-local/oai-upf:2.2.1-qfi-v1"
BUILDER = "ntn-local/upf-qfi-builder:451c27da"
ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str], cwd: Path | None = None) -> str:
    print("+ " + " ".join(args), flush=True)
    return subprocess.run(args, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE).stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=6)
    parser.add_argument('--network', choices=('default', 'host'), default='default',
                        help='Docker build network; host can recover dependency downloads in WSL')
    args = parser.parse_args()
    if not 1 <= args.jobs <= 32:
        parser.error("jobs must be between 1 and 32")
    work = ROOT / ".runtime/upf-qfi"
    source = work / "source"
    work.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        print(run(["git", "clone", "--depth", "1", "--branch", "v2.2.1",
                   "https://github.com/openairinterface/oai-cn5g-upf.git", str(source)]))
    if run(["git", "rev-parse", "HEAD"], source).strip() != REVISION:
        raise RuntimeError("UPF source revision mismatch; refusing to overwrite")
    print(run(["git", "submodule", "update", "--init", "--depth", "1",
               "build/common-build", "src/common-src"], source))
    patch = ROOT / "upf_patch/0001-control-plane-downlink-qfi.patch"
    reverse = subprocess.run(["git", "apply", "--reverse", "--check", str(patch)],
                             cwd=source, capture_output=True)
    if reverse.returncode:
        print(run(["git", "apply", "--check", str(patch)], source))
        print(run(["git", "apply", str(patch)], source))
    (source / "src/upf_app/simpleswitch/downlink_qfi.hpp").write_bytes(
        (ROOT / "upf_patch/downlink_qfi.hpp").read_bytes())
    dockerfile = (source / "docker/Dockerfile.upf.ubuntu").read_text()
    dockerfile = dockerfile.replace(
        "RUN git config --global https.postBuffer 123289600 && \\\n    git config --global http.sslverify false",
        "RUN git config --global https.postBuffer 123289600")
    if "sslverify false" in dockerfile:
        raise RuntimeError("Unexpected upstream Dockerfile TLS configuration")
    (work / "Dockerfile.builder").write_text(dockerfile)
    print(run(["docker", "build", "--network", args.network, "--target", "oai-upf-base", "--build-arg",
               "BASE_IMAGE=" + BASE, "-f", str(work / "Dockerfile.builder"),
               "-t", BUILDER, str(source)]))
    # 限制编译并行度；不改程序的构建选项、源码版本或运行参数。
    compile_file = work / "Dockerfile.compile"
    compile_file.write_text(
        "FROM " + BUILDER + "\nCOPY . /openair-upf\n"
        "WORKDIR /openair-upf/build/scripts\nARG UPF_BUILD_JOBS=6\n"
        "RUN MAKEFLAGS=-j${UPF_BUILD_JOBS} ./build_upf --clean --Verbose --build-type Release && "
        "test -x /openair-upf/build/upf/build/upf\n")
    compiled = "ntn-local/upf-qfi-compiled:451c27da"
    print(run(["docker", "build", "--network", args.network, "--build-arg", "UPF_BUILD_JOBS=" + str(args.jobs),
               "-f", str(compile_file), "-t", compiled, str(source)]))
    container = run(["docker", "create", "--entrypoint", "/bin/true", compiled]).strip()
    context = work / "image"
    context.mkdir(exist_ok=True)
    try:
        print(run(["docker", "cp", container + ":/openair-upf/build/upf/build/upf",
                   str(context / "oai_upf")]))
    finally:
        print(run(["docker", "rm", container]))
    (context / "Dockerfile").write_bytes((ROOT / "upf_patch/Dockerfile").read_bytes())
    print(run(["docker", "build", "--network", args.network, "-t", IMAGE, str(context)]))
    manifest = {"source": REVISION, "base": BASE, "image": IMAGE,
                "image_id": json.loads(run(["docker", "image", "inspect", IMAGE]))[0]["Id"],
                "binary_sha256": hashlib.sha256((context / "oai_upf").read_bytes()).hexdigest(),
                "patch_sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
                "header_sha256": hashlib.sha256((ROOT / "upf_patch/downlink_qfi.hpp").read_bytes()).hexdigest(),
                "submodules": run(["git", "submodule", "status"], source).splitlines()}
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
