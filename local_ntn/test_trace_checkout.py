"""Verify actual Git checkouts retain generated trace bytes required by bundles."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class TraceCheckoutTest(unittest.TestCase):
    def test_linux_checkout_matches_existing_bundle_provenance(self):
        root = Path(__file__).resolve().parents[1]
        relative = Path('examples/fdd-pass/trace.csv')
        with tempfile.TemporaryDirectory(prefix='ntn-trace-checkout-') as directory:
            repo = Path(directory) / 'repo'
            checkout = Path(directory) / 'checkout'
            repo.mkdir()
            checkout.mkdir()
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            subprocess.run(['git', '-C', str(repo), 'config', 'core.autocrlf', 'false'], check=True)
            (repo / relative).parent.mkdir(parents=True)
            shutil.copy2(root / relative, repo / relative)
            attrs = root / '.gitattributes'
            if attrs.is_file():
                shutil.copy2(attrs, repo / '.gitattributes')
            subprocess.run(['git', '-C', str(repo), 'add', '--all'], check=True)
            subprocess.run(['git', '-C', str(repo), 'checkout-index', '--all', '--prefix=' + str(checkout) + '/'], check=True)
            actual = hashlib.sha256((checkout / relative).read_bytes()).hexdigest()
            for direction in ('downlink', 'uplink'):
                manifest = json.loads((root / 'examples/fdd-pass' / direction / 'manifest.json').read_text())
                self.assertEqual(actual, manifest['provenance']['stk_trace_sha256'], direction)


if __name__ == '__main__':
    unittest.main()
