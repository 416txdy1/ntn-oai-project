"""停机状态下切换本实验 UPF 镜像；不覆盖凭据、网络或原始模板。"""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from core_lab import CoreLab
from runtime_config import resolve_runtime
from build_upf_qfi import IMAGE, REVISION, BASE


def replace_image(text: str, image: str) -> str:
    pattern = r"(?m)^(        image: )(?:oaisoftwarealliance/oai-upf:v2\.2\.1|" + re.escape(IMAGE) + "|" + re.escape(BASE) + r")$"
    result, count = re.subn(pattern, lambda m: m[1] + image, text)
    if count != 1:
        raise ValueError("Expected exactly one known UPF image line")
    return result


def configure(lab: CoreLab, rollback: bool = False) -> str:
    inventory = lab.preflight()
    resources = lab.resources(inventory)
    if lab.marker.exists() or resources["containers"] or resources["networks"]:
        raise ValueError("Stop this profile with core_lab.py before switching images")
    image = BASE if rollback else IMAGE
    info = json.loads(lab.run(["docker", "image", "inspect", image]))[0]
    labels = info.get("Config", {}).get("Labels") or {}
    if not rollback and (labels.get("ntn.upf.source") != REVISION or
                         labels.get("ntn.upf.patch") != "control-plane-qfi-v1"):
        raise ValueError("Image is not the pinned local QFI fix")
    old = lab.compose.read_text()
    new = replace_image(old, image)
    if new != old:
        backup = lab.compose.with_name("compose.before-upf-qfi.yaml")
        if not backup.exists():
            fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as stream:
                stream.write(old)
        temp = lab.compose.with_name("compose.upf-qfi.tmp")
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, "w") as stream:
                stream.write(new)
            os.chmod(temp, stat.S_IMODE(lab.compose.stat().st_mode))
            if lab.compose.read_text() != old:
                raise ValueError("Compose changed during image selection")
            temp.replace(lab.compose)
        finally:
            if temp.exists():
                temp.unlink()
    return image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    try:
        root = Path(__file__).resolve().parents[1]
        config = resolve_runtime(root, "integrated-handover", "configure-upf-qfi", os.environ)
        selected = configure(CoreLab(config), args.rollback)
        print("UPF image: " + selected)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        # Compose 文件和 Docker 异常输出可能含私有字段，不回显。
        parser.exit(1, "UPF image selection refused (" + type(error).__name__ + ")\n")


if __name__ == "__main__":
    main()
