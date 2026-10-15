from pathlib import Path
import tempfile,subprocess,os
r=Path(__file__).resolve().parents[1]
s=(r/'oai_patch/current/openair1/PHY/NR_UE_ESTIMATION/nr_ntn_rx_tracker.h').read_text()
helpers=s[s.index('static inline bool nr_ntn_diag_start_value'):s.index('static inline bool nr_ntn_sample_diff')]
driver=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <stdio.h>
'''
driver+=helpers+r'''
int main(void){
 unsigned v=999;
 assert(nr_ntn_diag_start_value(NULL,&v)&&v==0);
 assert(nr_ntn_diag_start_value("",&v)&&v==0);
 assert(nr_ntn_diag_start_value("580",&v)&&v==580);
 assert(nr_ntn_diag_start_value("620",&v)&&v==620);
 const char *bad[]={"621","-1","580.0","0000","580;echo x"," 580"};
 for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);i++)assert(!nr_ntn_diag_start_value(bad[i],&v));
 assert(!nr_ntn_diag_start_value("580",NULL));
 const uint64_t threshold=580ULL*7680000ULL;
 assert(!nr_ntn_diag_in_window(threshold-1,7680000.,580));
 assert(nr_ntn_diag_in_window(threshold,7680000.,580));
 assert(!nr_ntn_diag_in_window(4294967295ULL,7680000.,580));
 assert(nr_ntn_diag_in_window(600ULL*7680000ULL,7680000.,580));
 assert(!nr_ntn_diag_in_window(threshold,NAN,580));
 assert(!nr_ntn_diag_in_window(threshold,INFINITY,580));
 assert(!nr_ntn_diag_in_window(threshold,0,580));
 assert(!nr_ntn_diag_in_window(threshold,-1,580));
 assert(!nr_ntn_diag_in_window(threshold,7680000.,621));
 assert(nr_ntn_diag_in_window(0,7680000.,0));
 if(getenv("EXPECT_DIAG_REJECT"))assert(!nr_ntn_diag_at(threshold,7680000.));
 else {assert(!nr_ntn_diag_at(threshold-1,7680000.));assert(nr_ntn_diag_at(threshold,7680000.));}
 puts("ACTUAL_DIAGNOSTIC_WINDOW_HELPER_PASS");
}
'''
with tempfile.TemporaryDirectory(prefix='ntn-diag-window-') as temp:
 out=Path(temp);source=out/'window.c';source.write_text(driver)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic',str(source),'-lm','-o',str(out/'window')],check=True)
 for setting,reject in [('580',False),('bad',True)]:
  env=dict(os.environ,OAI_NTN_TIMING_DIAG_START_IQ_S=setting)
  if reject:env['EXPECT_DIAG_REJECT']='1'
  else:env.pop('EXPECT_DIAG_REJECT',None)
  subprocess.run([str(out/'window')],env=env,check=True)
