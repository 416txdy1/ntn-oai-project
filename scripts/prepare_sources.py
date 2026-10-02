"""校验并解包仓库内源码；无需 git clone，已有目录拒绝覆盖。"""
import hashlib,json,shutil,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
work=ROOT/'.runtime'
work.mkdir(exist_ok=True)
checks=json.loads((ROOT/'vendor/checksums.json').read_text(encoding='utf-8-sig'))
for name,target in [('oai-source.tar.gz','oai'),('quadriga-source.tar.gz','quadriga'),('asn1c-source.tar.gz','asn1c'),('simde-source.tar.gz','simde')]:
    archive=ROOT/'vendor'/name
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==checks[name],f'checksum mismatch: {name}'
    dest=work/target
    stamp=dest/'.archive-sha256'
    if dest.exists():
        if not stamp.is_file() or stamp.read_text()!=checks[name]:
            raise SystemExit(f'已有源码目录不同，拒绝覆盖：{dest}')
        continue
    dest.mkdir()
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            path=Path(member.name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('unsafe archive path')
            if member.issym() or member.islnk():
                # 本交付源包仅依赖普通文件，拒绝未经审计的链接。
                raise ValueError(f'archive link: {member.name}')
        tar.extractall(dest)
    stamp.write_text(checks[name])
# 当前 OAI 修改文件只有这里和 quadriga/oai 两个来源；每次执行同步到生成树。
for path in (ROOT/'oai_patch/current').rglob('*'):
    if path.is_file():
        dest=work/'oai'/path.relative_to(ROOT/'oai_patch/current')
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
for name in ('qd_channel_reader.c','qd_channel_reader.h','qd_channel_adapter.c'):
    shutil.copyfile(ROOT/'quadriga/oai'/name,work/'oai/radio/rfsimulator'/name)
print('Prepared sources:',work)