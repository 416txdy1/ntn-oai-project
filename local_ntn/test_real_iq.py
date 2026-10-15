"""Build actual repository IQ path with OAI's include flags and minimal test doubles."""
import csv,json,os,re,shlex,subprocess,tempfile
from pathlib import Path
from paths import OAI_REPO
repo=OAI_REPO;base=Path(__file__).resolve().parent
build_repo=Path(os.environ.get('OAI_BUILD_REPO',repo)).resolve()
build=build_repo/'cmake_targets/ran_build/build'
make_flags=build/'radio/rfsimulator/CMakeFiles/rfsimulator.dir/flags.make'
if make_flags.exists():
    flags=make_flags.read_text()
    args=[]
    for key in ('C_DEFINES','C_INCLUDES','C_FLAGS'):
        args+=shlex.split(re.search(r'^'+key+r' = (.*)$',flags,re.M)[1])
else:
    # Ninja exposes the real compile command without assuming a Makefile layout.
    database=json.loads(subprocess.check_output(['ninja','-C',str(build),'-t','compdb'],text=True))
    entry=next(e for e in database if e.get('file','').endswith('/apply_channelmod.c'))
    command=shlex.split(entry['command'])
    compiler=next(i for i,v in enumerate(command) if Path(v).name in ('cc','gcc','clang'))
    args=[];i=compiler+1
    while i<len(command):
        v=command[i]
        if v in ('-o','-MF','-MT','-MQ'):
            i+=2;continue
        if v in ('-c','-MD','-MMD','-MP') or v==entry['file']:
            i+=1;continue
        if v.startswith('-'):
            args.append(v)
        i+=1
# Assertions are the test oracle: release builds must not compile them away.
args=[v for v in args if v not in ('-DT_TRACER','-DNDEBUG')]
args=[v.replace(str(build_repo),str(repo)) for v in args]
args.append('-UNDEBUG')
has_legacy='int stk_visible;' in (repo/'openair1/SIMULATION/TOOLS/sim.h').read_text()
if has_legacy:args.append('-DOAI_HAS_LEGACY_STK')
with tempfile.TemporaryDirectory(prefix='oai-stk-iq-') as d:
    d=Path(d);trace=d/'fixture.csv'
    with trace.open('w',newline='') as f:
        f.write('STKTRACE2\n');w=csv.writer(f)
        for i in range(5):
            w.writerow([i,7000000+i*100,0,0,100,0,0,0,0,0,6377900,0,0,6377900,0,0,
                        -100 if i==0 else -110,-100,20,20,int(i<3),int(i<3)])
    src=repo/'radio/rfsimulator'
    subprocess.run(['cc',*args,str(base/'test_real_iq.c'),str(src/'apply_channelmod.c'),
                    str(src/'stk_trace.c'),str(src/'stk_trace_channel.c'),
                    str(src/'qd_channel_reader.c'),str(src/'qd_channel_adapter.c'),
                    '-lcrypto','-lm','-lpthread','-o',str(d/'test')],check=True,cwd=build)
    subprocess.run([str(d/'test'),str(trace)],check=True)
    if has_legacy:subprocess.run([str(d/'test'),'--legacy'],check=True)

    for direction in ('downlink', 'uplink'):
        bundle=base.parent/'examples/fdd-miso'/direction
        subprocess.run([str(d/'test'),str(base.parent/'examples/fdd-pass/trace.csv'),str(bundle)],check=True)
