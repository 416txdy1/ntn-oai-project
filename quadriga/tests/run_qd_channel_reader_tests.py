"""Compile and exercise the standalone QDCHANNEL1 C reader."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


def run(command: list[str], *, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command), flush=True)
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    if (result.returncode == 0) != expect_success:
        raise RuntimeError(f"unexpected exit code {result.returncode}: {' '.join(command)}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real-bundle", type=Path)
    parser.add_argument("--real-trace", type=Path)
    args = parser.parse_args()
    if (args.real_bundle is None) != (args.real_trace is None):
        parser.error("--real-bundle and --real-trace must be provided together")

    project = Path(__file__).resolve().parents[2]
    reader_dir = project / "quadriga" / "oai"
    example = project / "quadriga" / "examples" / "siso_two_path"
    manifest = json.loads((example / "manifest.json").read_text(encoding="utf-8"))
    example_trace_sha256 = manifest["provenance"]["stk_trace_sha256"]

    with tempfile.TemporaryDirectory(prefix="qd-reader-") as temporary:
        temporary_path = Path(temporary)
        executable = temporary_path / "qd_channel_reader_test"
        run(
            [
                "cc",
                "-std=c11",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-pedantic",
                "-O2",
                f"-I{reader_dir}",
                str(reader_dir / "qd_channel_reader.c"),
                str(project / "quadriga" / "tests" / "qd_channel_reader_test.c"),
                "-lcrypto",
                "-lm",
                "-o",
                str(executable),
            ]
        )
        run([str(executable), "--example", str(example), example_trace_sha256])

        truncated = temporary_path / "truncated"
        shutil.copytree(example, truncated)
        coefficient_path = truncated / "coefficients.cf32"
        coefficient_path.write_bytes(coefficient_path.read_bytes()[:-1])
        run([str(executable), "--expect-fail", str(truncated)])

        checksum_mismatch = temporary_path / "checksum-mismatch"
        shutil.copytree(example, checksum_mismatch)
        coefficient_path = checksum_mismatch / "coefficients.cf32"
        coefficient_payload = bytearray(coefficient_path.read_bytes())
        coefficient_payload[0] ^= 0x01
        coefficient_path.write_bytes(coefficient_payload)
        run([str(executable), "--expect-fail", str(checksum_mismatch)])

        nonfinite = temporary_path / "nonfinite"
        shutil.copytree(example, nonfinite)
        delay_path = nonfinite / "delays.f64"
        delay_payload = bytearray(delay_path.read_bytes())
        struct.pack_into("<d", delay_payload, 0, float("nan"))
        delay_path.write_bytes(delay_payload)
        nonfinite_manifest_path = nonfinite / "manifest.json"
        nonfinite_manifest = json.loads(nonfinite_manifest_path.read_text(encoding="utf-8"))
        nonfinite_manifest["files"]["delays"]["sha256"] = hashlib.sha256(delay_payload).hexdigest()
        nonfinite_manifest_path.write_text(
            json.dumps(nonfinite_manifest, indent=2) + "\n", encoding="utf-8"
        )
        run([str(executable), "--expect-fail", str(nonfinite)])

        escaped = temporary_path / "escaped"
        shutil.copytree(example, escaped)
        escaped_manifest_path = escaped / "manifest.json"
        escaped_manifest = json.loads(escaped_manifest_path.read_text(encoding="utf-8"))
        escaped_manifest["files"]["times"]["path"] = "../times.f64"
        escaped_manifest_path.write_text(json.dumps(escaped_manifest, indent=2) + "\n", encoding="utf-8")
        run([str(executable), "--expect-fail", str(escaped)])

        invalid_json = temporary_path / "invalid-json"
        shutil.copytree(example, invalid_json)
        (invalid_json / "manifest.json").write_text('{"format": "QDCHANNEL1",', encoding="utf-8")
        run([str(executable), "--expect-fail", str(invalid_json)])

        if args.real_bundle is not None and args.real_trace is not None:
            trace_sha256 = hashlib.sha256(args.real_trace.read_bytes()).hexdigest()
            run([str(executable), "--smoke", str(args.real_bundle), trace_sha256])

    print("PASS QDCHANNEL1 C reader regression")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
