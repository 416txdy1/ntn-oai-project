"""Compile actual gNB diagnostic header; exercise profile gates and hard bounds."""
from pathlib import Path
import subprocess,tempfile,os
root=Path(__file__).resolve().parents[1]
header=root/'oai_patch/current/openair2/LAYER2/NR_MAC_gNB/ntn_ta_diag.h'
source=r'''#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned calls;static char line[512];
#define NR_MAC 0
#define LOG_I(component,...) ((void)(component),++calls,(void)snprintf(line,sizeof(line),__VA_ARGS__))
#include "ntn_ta_diag.h"
int main(void){
 unsetenv("OAI_NTN_PROFILE");unsetenv("OAI_NTN_TIMING_DIAG");
 nr_ntn_ta_diag(0,0,0,31,31,1,150);assert(calls==0);
 setenv("OAI_NTN_PROFILE","zky",1);setenv("OAI_NTN_TIMING_DIAG","1",1);
 for(int i=0;i<20010;i++)nr_ntn_ta_diag(0,0,0,31,31,1,150);assert(calls==0);
 setenv("OAI_NTN_PROFILE","integrated-handover",1);setenv("OAI_NTN_TIMING_DIAG","0",1);
 nr_ntn_ta_diag(0,0,0,31,31,1,150);assert(calls==0);
 setenv("OAI_NTN_TIMING_DIAG","1",1);
 nr_ntn_ta_diag(0,123,4,17,31,0,145);assert(calls==1);
 assert(strstr(line,"STKGNB_TA_MEAS")&&strstr(line,"command 17 previous 31 crcOk 0 snrX10 145"));
 for(int i=0;i<20010;i++)nr_ntn_ta_diag(0,0,0,31,31,1,150);assert(calls==20000);
 setenv("OAI_NTN_PROFILE","legacy-handover",1);
 for(int i=0;i<2010;i++)nr_ntn_ta_diag(1,0,0,31,-1,-1,-1);assert(calls==22000);
 assert(strstr(line,"STKGNB_TA_SCHEDULE"));puts("PASS bounded gNB TA numeric diagnostics");
}
'''
with tempfile.TemporaryDirectory(prefix='ntn-ta-diag-') as temp:
 path=Path(temp);(path/'test.c').write_text(source)
 subprocess.run(['cc','-std=c11','-D_POSIX_C_SOURCE=200809L','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-UNDEBUG','-I'+str(header.parent),str(path/'test.c'),'-o',str(path/'test')],check=True)
 subprocess.run([str(path/'test')],check=True,env={k:v for k,v in os.environ.items() if not k.startswith('OAI_')})
