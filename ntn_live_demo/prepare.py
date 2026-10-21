"""Install demo-only dependencies without apt installs or OAI source edits."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import urllib.request

BASE = Path('/home/kayoko/ntn-live-demo-tools')


def font():
    if os.geteuid()==0:raise RuntimeError('Download demo assets only as ordinary user')
    target=BASE/'fonts/NotoSansCJKsc-Regular.otf';target.parent.mkdir(exist_ok=True)
    url='https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf'
    if not target.exists():
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url,timeout=120) as response,target.open('xb') as out:
            import shutil
            shutil.copyfileobj(response,out)
    (target.parent/'source.json').write_text(json.dumps({'url':url,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'license':'SIL Open Font License 1.1; see https://github.com/notofonts/noto-cjk/blob/main/Sans/LICENSE'},indent=2))
    print('DEMO FONT READY',target,flush=True)


def main():
    if os.geteuid()==0:
        raise RuntimeError('Run preparation as ordinary user kayoko, never as root')
    BASE.mkdir(exist_ok=True, mode=0o755)
    env = {k:v for k,v in os.environ.items() if not k.lower().endswith('_proxy')}
    env['PLAYWRIGHT_BROWSERS_PATH'] = str(BASE/'browsers')
    python = BASE/'user-venv/bin/python'
    if not python.exists():
        subprocess.run([sys.executable,'-m','venv','--without-pip',str(BASE/'user-venv')],check=True,env=env)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    # Reuse only the existing local pip engine; never modify its environment.
    local_pip=Path('/home/kayoko/ntn-workspaces/ntn-quadriga-handover/.runtime/test-venv/bin/python')
    wheels=BASE/'wheels';wheels.mkdir(exist_ok=True)
    packages=['playwright==1.55.0','imageio-ffmpeg==0.6.0']
    subprocess.run([str(local_pip),'-m','pip','download','--only-binary=:all:','-d',str(wheels),*packages],check=True,env=env)
    digests={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in wheels.glob('*.whl')}
    (BASE/'wheel-sha256.json').write_text(json.dumps(digests,indent=2))
    subprocess.run([str(local_pip),'-m','pip','--python',str(python),'install','--no-index','--find-links',str(wheels),*packages],check=True,env=env)
    subprocess.run([str(python),'-m','playwright','install','chromium'],check=True,env=env)
    version='v1.21.2'
    archive=BASE/f'mediamtx_{version}_linux_amd64.tar.gz'
    url=f'https://github.com/bluenviron/mediamtx/releases/download/{version}/{archive.name}'
    if not archive.exists():
        print('Downloading',url,flush=True)
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url,timeout=120) as response, archive.open('xb') as stream:
            import shutil
            shutil.copyfileobj(response,stream)
    dest=BASE/'mediamtx'
    dest.mkdir(exist_ok=True)
    with tarfile.open(archive) as tar:
        for name in ('mediamtx','mediamtx.yml','LICENSE'):
            member=tar.getmember(name)
            if not member.isfile():raise ValueError('unexpected archive member')
            target=dest/name
            with tar.extractfile(member) as source,target.open('wb') as out:
                out.write(source.read())
            target.chmod(0o755 if name=='mediamtx' else 0o644)
    sha=hashlib.sha256(archive.read_bytes()).hexdigest()
    (BASE/'provenance.json').write_text(json.dumps({'mediamtx_url':url,'download_sha256':sha,
        'python_packages':{'playwright':'1.55.0','imageio-ffmpeg':'0.6.0'},
        'note':'HTTPS download digest recorded; no claim of independent publisher signature verification'},indent=2))
    subprocess.run([str(python),'-c','import imageio_ffmpeg; print("FFMPEG",imageio_ffmpeg.get_ffmpeg_exe())'],env=env,check=True)
    print('READY',BASE,flush=True)
    font()


if __name__=='__main__':
    if sys.argv[1:]==['--font-only']:font()
    else:main()
