"""Build actual repository IQ path with OAI's include flags and minimal test doubles."""
import csv,re,shlex,subprocess,tempfile
from pathlib import Path
repo=Path('/home/kayoko/OAI/openairinterface5g');base=Path(__file__).resolve().parent
build=repo/'cmake_targets/ran_build/build'
flags=(build/'radio/rfsimulator/CMakeFiles/rfsimulator.dir/flags.make').read_text()
args=[]
for key in ('C_DEFINES','C_INCLUDES','C_FLAGS'):
    args+=shlex.split(re.search(r'^'+key+r' = (.*)$',flags,re.M)[1])
args=[v for v in args if v!='-DT_TRACER']
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
                    str(src/'stk_schedule.c'),'-lm','-lpthread','-o',str(d/'test')],check=True)
    subprocess.run([str(d/'test'),str(trace)],check=True)
