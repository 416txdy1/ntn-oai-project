import csv,subprocess,tempfile
from pathlib import Path
b=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='oai-trace-parse-') as d:
    d=Path(d);exe=d/'test'
    subprocess.run(['cc','-Wall','-Wextra','-Werror','-I',str(b),str(b/'test_trace_validation.c'),
                    str(b/'stk_trace.c'),'-lm','-o',str(exe)],check=True)
    base=[0,7000000,0,0,100,0,0,0,0,0,6377900,0,0,6377900,0,0,-100,-100,20,20,1,1]
    cases=[('valid',None,None,True),('huge-coordinate',1,1e200,False),('nan',4,float('nan'),False),
           ('unphysical-speed',4,1e100,False),('invalid-flag',20,2,False),('huge-time',0,1e200,False)]
    for name,index,value,expected in cases:
        row=base.copy()
        if index is not None:row[index]=value
        nextrow=row.copy();nextrow[0]=row[0]+1
        path=d/(name+'.csv')
        with path.open('w',newline='') as f:
            f.write('STKTRACE2\n');w=csv.writer(f);w.writerow(row);w.writerow(nextrow)
        subprocess.run([str(exe),str(path),str(int(expected))],check=True)
    print('PASS: trace physical bounds, finite fields, flags and valid input')
