"""交付完整性检查：无需解包、编译或网络。"""
from pathlib import Path
import hashlib,json,tarfile,re,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from quadriga.tools.validate_bundle import validate_bundle
checks=json.loads((ROOT/'vendor/checksums.json').read_text(encoding='utf-8-sig'))
for name,digest in checks.items():
    path=ROOT/'vendor'/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            parts=Path(member.name).parts
            assert not Path(member.name).is_absolute() and '..' not in parts and '.git' not in parts,member.name
            assert member.isfile() or member.isdir(),member.name
    print('PASS source archive',name)
for profile in ('fdd-pass','fdd-pass-array'):
    for direction in ('downlink','uplink'):
        bundle=ROOT/'examples'/profile/direction
        manifest=json.loads((bundle/'manifest.json').read_text())
        assert manifest['provenance']['stk_trace_sha256']==hashlib.sha256((ROOT/'examples/fdd-pass/trace.csv').read_bytes()).hexdigest()
        validate_bundle(bundle)
        if profile=='fdd-pass-array':
            antenna=json.loads((bundle/'antenna.json').read_text())
            assert antenna['profile']=='satellite_16x16_ground_omni'
        print('PASS example',profile,direction)
for script in (ROOT/'scripts').iterdir():
    if script.suffix in ('.py','.sh'):
        text=script.read_text()
        assert re.search(r'/home/[a-zA-Z0-9_-]+/OAI/',text) is None,script.name
print('PASS portable script paths')
