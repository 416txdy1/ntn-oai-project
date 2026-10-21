"""QFI 镜像切换的配置隔离与回退测试，不启动 Docker。"""
import json
from pathlib import Path
import tempfile
import unittest
from configure_upf_qfi import configure, replace_image
from build_upf_qfi import IMAGE, REVISION, BASE


class FakeLab:
    def __init__(self, folder: Path) -> None:
        self.compose = folder / "compose.yaml"
        self.marker = folder / "owner.json"
        self.compose.write_text("services:\n    oai-upf:\n        image: oaisoftwarealliance/oai-upf:v2.2.1\n        environment: KEEP_ME\n")
        self.labels = {"ntn.upf.source": REVISION, "ntn.upf.patch": "control-plane-qfi-v1"}
        self.active = False

    def preflight(self) -> None:
        return None

    def resources(self, inventory: object) -> dict[str, list[str]]:
        return {"containers": ["owned"] if self.active else [], "networks": []}

    def run(self, args: list[str]) -> str:
        assert args[:3] == ["docker", "image", "inspect"]
        return json.dumps([{"Config": {"Labels": self.labels}}])


class ImageSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.lab = FakeLab(Path(self.temp.name))
        self.original = self.lab.compose.read_text()

    def test_switch_and_rollback_preserve_other_fields(self) -> None:
        self.assertEqual(configure(self.lab), IMAGE)
        self.assertEqual(self.lab.compose.read_text(), self.original.replace("oaisoftwarealliance/oai-upf:v2.2.1", IMAGE))
        backup = self.lab.compose.with_name("compose.before-upf-qfi.yaml")
        self.assertEqual(backup.read_text(), self.original)
        self.assertEqual(configure(self.lab, True), BASE)
        self.assertEqual(backup.read_text(), self.original)
        self.assertIn("KEEP_ME", self.lab.compose.read_text())

    def test_active_resources_refused(self) -> None:
        self.lab.active = True
        with self.assertRaises(ValueError): configure(self.lab)
        self.assertEqual(self.lab.compose.read_text(), self.original)

    def test_owner_marker_refused(self) -> None:
        self.lab.marker.write_text("{}")
        with self.assertRaises(ValueError): configure(self.lab)

    def test_wrong_image_provenance_refused(self) -> None:
        self.lab.labels["ntn.upf.source"] = "other"
        with self.assertRaises(ValueError): configure(self.lab)
        self.assertEqual(self.lab.compose.read_text(), self.original)

    def test_unknown_or_multiple_images_refused(self) -> None:
        for text in ("image: unknown", self.original + self.original):
            with self.assertRaises(ValueError): replace_image(text, IMAGE)

    def test_repeat_is_idempotent(self) -> None:
        configure(self.lab)
        before = self.lab.compose.read_bytes()
        configure(self.lab)
        self.assertEqual(self.lab.compose.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
