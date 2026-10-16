"""Compile the production TA block and verify isolation and bounded feedback."""
from pathlib import Path
import os, subprocess, tempfile, sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'local_ntn'))
from runtime_config import ta_feedback_policy
d=root/'oai_patch/current/openair2/LAYER2/NR_MAC_gNB'
text=(d/'gNB_scheduler_ulsch.c').read_text(encoding='utf-8')
start=text.index('      if (timing_advance != 0xffff) {')
end=text.index('\n\n      const NR_sched_pusch_t *',start)
block=text[start:end]
assert 'nr_ntn_ta_feedback_value(timing_advance)' in block
# The separate random-access assignment must retain native semantics.
assert 'UE_scheduling_control->ta_update = timing_advance;' in text[:start]+text[end:]
source=r'''#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#define NR_MAC 0
#define LOG_I(component,...) ((void)(component))
#include "ntn_ta_diag.h"
static int apply(int timing_advance,int previous,int good) {
 struct {int ta_update;} control={previous};
 __typeof__(control) *UE_scheduling_control=&control;
 int frameP=0,slotP=0,pusch_snrx10=100;
 const void *sduP=good?&control:NULL;
 PRODUCTION_BLOCK
 return control.ta_update;
}
int main(void) {
 const char *profiles[]={"zky","integrated-handover","legacy-handover","unknown"};
 unsetenv("OAI_NTN_RX_TRACKER");unsetenv("OAI_NTN_TX_PREDICTOR");
 for(int p=0;p<4;p++) {
  setenv("OAI_NTN_PROFILE",profiles[p],1);
  for(int c=0;c<64;c++) {
   int v=apply(c,42,1);
   if(p==0||p==3) {assert(v==c);assert(apply(c,42,0)==c);}
   else {assert(v>=23&&v<=39);assert(apply(c,42,0)==42);
    assert(abs(4*(v-31)-(c-31))<=2);
    if(c>0)assert(v>=apply(c-1,42,1));
    if(c<=62)assert(v+apply(62-c,42,1)==62);
   }
  }
  assert(apply(0xffff,42,1)==42);
  assert(apply(-1,42,1)==-1);assert(apply(64,42,1)==64);
 }
 setenv("OAI_NTN_PROFILE","integrated-handover",1);
 assert(apply(30,42,1)==31&&apply(31,42,1)==31&&apply(32,42,1)==31);
 for(int initial=-31;initial<=31;initial++) {
  int residual=initial;
  for(int step=0;step<20;step++)residual-=apply(31+residual,31,1)-31;
  assert(abs(residual)<=1);
 }
 const char *keys[]={"OAI_NTN_RX_TRACKER","OAI_NTN_TX_PREDICTOR"};
 for(int k=0;k<2;k++) {
  setenv(keys[k],"0",1);
  for(int c=0;c<64;c++)assert(apply(c,42,0)==c&&apply(c,42,1)==c);
  unsetenv(keys[k]);
 }
 puts("PASS production TA block: CRC gate, quarter gain, native isolation, invalid values, RAR unchanged");
}
'''.replace('PRODUCTION_BLOCK',block)
with tempfile.TemporaryDirectory(prefix='ntn-ta-feedback-') as temp:
 path=Path(temp);(path/'test.c').write_text(source,encoding='utf-8')
 subprocess.run(['cc','-std=gnu11','-D_POSIX_C_SOURCE=200809L','-Wall','-Wextra','-Wno-unused-parameter','-Wno-unused-variable','-Werror','-UNDEBUG','-I'+str(d),str(path/'test.c'),'-o',str(path/'test')],check=True)
 subprocess.run([str(path/'test')],check=True,env={k:v for k,v in os.environ.items() if not k.startswith('OAI_')})
for profile in ('zky','unknown','integrated-handover','legacy-handover'):
 for rx in (None,'1','0',''):
  for tx in (None,'1','0',''):
   env={k:v for k,v in zip(('OAI_NTN_RX_TRACKER','OAI_NTN_TX_PREDICTOR'),(rx,tx)) if v is not None}
   active=profile in ('integrated-handover','legacy-handover') and rx in (None,'1') and tx in (None,'1')
   assert ta_feedback_policy(profile,env)==('crc-good-quarter-gain-v1' if active else 'native')
assert '"'+ta_feedback_policy('integrated-handover',{})+'"' in (d/'ntn_ta_feedback.h').read_text(encoding='utf-8')
print('PASS manifest policy truth table; toy loop checks are not PHY acceptance')
