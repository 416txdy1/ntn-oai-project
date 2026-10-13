"""Build actual repository IQ path with OAI's include flags and minimal test doubles."""
import csv,json,os,re,shlex,subprocess,tempfile
from pathlib import Path
from paths import OAI_REPO
repo=OAI_REPO;base=Path(__file__).resolve().parent
canonical=base.parent/'oai_patch/current/radio/rfsimulator'
for name in ('stk_trace.h','stk_trace.c','stk_trace_channel.c','stk_schedule.c','stk_schedule.h'):
    assert (base/name).read_bytes()==(canonical/name).read_bytes(),f'canonical/test mirror drift: {name}'
build_repo=Path(os.environ.get('OAI_BUILD_REPO',repo)).resolve()
build=Path(os.environ.get('OAI_BUILD_DIR',build_repo/'cmake_targets/ran_build/build')).resolve()
print(f'Actual IQ source={repo.resolve()} build={build}',flush=True)
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
if '--sanitize' in __import__('sys').argv:
    args.extend(['-fsanitize=address,undefined','-fno-omit-frame-pointer'])
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
                    str(src/'stk_trace.c'),str(src/'stk_trace_channel.c'),str(src/'stk_schedule.c'),
                    str(src/'qd_channel_reader.c'),str(src/'qd_channel_adapter.c'),
                    '-lcrypto','-lm','-lpthread','-o',str(d/'test')],check=True,cwd=build)
    subprocess.run([str(d/'test'),'--phase'],check=True)
    subprocess.run([str(d/'test'),str(trace)],check=True)
    if has_legacy:subprocess.run([str(d/'test'),'--legacy'],check=True)

    disabled={**os.environ,'OAI_STK_DYNAMIC_DELAY':'0','OAI_STK_DYNAMIC_DOPPLER':'0'}
    subprocess.run([str(d/'test'),str(trace)],check=True,env=disabled)
    schedule=d/'schedule.csv'
    schedule.write_text('time,satellite_id,elevation_deg,visible,switched,handover_phase,previous_satellite_id,next_satellite_id\n'
                        '1,SAT_A,20,1,0,steady,,SAT_A\n'
                        '2,SAT_B,15,1,1,complete,SAT_A,SAT_B\n')
    clock_env={**os.environ,'OAI_STK_TRACE_RATE':'0.5','OAI_STK_TRACE_EPOCH':'1',
               'OAI_STK_SCHEDULE':str(schedule)}
    output=subprocess.check_output([str(d/'test'),str(trace),'--clock'],text=True,env=clock_env)
    clocks=[line.split() for line in output.splitlines() if line.startswith('STKCLOCK ')]
    assert clocks,'actual channel must emit STKCLOCK anchors'
    previous={}
    for words in clocks:
        assert words[1] in ('DL','UL')
        fields=dict(word.split('=',1) for word in words[2:])
        samples=int(fields['samples']);fs=float(fields['sampling_rate']);iq=float(fields['iq_s']);stk=float(fields['stk_s'])
        monotonic=int(fields['monotonic_ns'])
        assert fs==7680000 and abs(iq-samples/fs)<1e-8 and abs(stk-(1+iq*.5))<1e-8
        assert monotonic>0
        if words[1] in previous:
            old=previous[words[1]]
            assert monotonic>=old[0] and 0<iq-old[1]<=.170001
        else:assert samples==({"DL":10083072,"UL":10129151}[words[1]])
        previous[words[1]]=monotonic,iq
    assert set(previous)=={'DL','UL'}
    starts=[line.split() for line in output.splitlines() if line.startswith('STKCHANNELSTART ')]
    assert len(starts)==2,'one actual first-channel observation per direction'
    for words in starts:
        direction=words[1];fields=dict(word.split('=',1) for word in words[2:])
        first=next(line for line in clocks if line[1]==direction)
        assert fields==dict(word.split('=',1) for word in first[2:]),'start must equal first actual CLOCK'
        for prefix in ('STKTRACE2 '+direction+' IQ=', 'STKSCHEDULE '+direction+' IQ='):
            line=next(line for line in output.splitlines() if line.startswith(prefix))
            assert int(re.search(r'samples=(\d+)',line)[1])==int(fields['samples'])
            assert abs(float(re.search(r'IQ=([\d.]+)',line)[1])-float(fields['iq_s']))<=.0000005001
            assert abs(float(re.search(r'STK=([\d.]+)',line)[1])-float(fields['stk_s']))<=.0000005001
    schedules=[line for line in output.splitlines() if line.startswith('STKSCHEDULE ')]
    assert any('satellite_id=SAT_A ' in line and 'phase=steady ' in line for line in schedules)
    assert any('satellite_id=SAT_B ' in line and 'phase=complete ' in line and 'previous=SAT_A ' in line for line in schedules)
    print(f'PASS actual STKCLOCK: {len(clocks)} monotonic/IQ/STK anchors; schedule identity and phase')

    for direction in ('downlink','uplink'):
        bundle=base.parent/'examples/fdd-pass'/direction
        real_trace=base.parent/'examples/fdd-pass/trace.csv'
        qd_env={**os.environ,'OAI_QD_CHANNEL':str(bundle),'OAI_STK_TRACE_RATE':'1',
                'OAI_STK_TRACE_NOISE':'1'}
        qd_env.pop('OAI_STK_SCHEDULE',None)
        qd_env.pop('OAI_STK_TRACE_EPOCH',None)
        if direction=='uplink':qd_env['IQ_TEST_UPLINK']='1'
        else:qd_env.pop('IQ_TEST_UPLINK',None)
        subprocess.run([str(d/'test'),str(real_trace),'--qd'],check=True,env=qd_env)
