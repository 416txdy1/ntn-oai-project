/* Integration test compiles the repository's actual apply_channelmod.c.
 * Only logging, RNG (zero-noise measurement) and RRC callback are test doubles.
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <common/utils/LOG/log.h>
#include <openair1/SIMULATION/TOOLS/sim.h>
#include "radio/rfsimulator/rfsimulator.h"
#include "openair2/LAYER2/NR_MAC_gNB/mac_config.h"
static log_t log_state;
log_t *g_log=&log_state;
void logRecord_mt(const char *f,const char *fn,int l,int c,int level,const char *format,...)
{ (void)f; (void)fn; (void)l; (void)c; (void)level; (void)format; }
void exit_function(const char *f,const char *fn,const int line,const char *s,const int kind)
{ (void)f; (void)fn; (void)line; (void)s; (void)kind; abort(); }
double gaussZiggurat(double mean,double variance)
{ (void)mean; (void)variance; return 0; }
int32_t signal_energy(int32_t *s,uint32_t n)
{ (void)s; (void)n; return 0; }
bool nr_update_sib19(const gnb_sat_position_update_t *s)
{ (void)s; return true; }
bool update_channel_model_from_stk(channel_desc_t *c,int n,uint64_t t)
{ (void)c; (void)n; (void)t; return false; }
static double energy(cf_t *s,int n){double e=0;for(int i=0;i<n;i++)e+=s[i].r*s[i].r+s[i].i*s[i].i;return e/n;}
int main(int argc,char **argv)
{
  assert(argc==2);
  bool legacy=strcmp(argv[1],"--legacy")==0;
  if(!legacy){setenv("OAI_STK_TRACE",argv[1],1);setenv("OAI_STK_TRACE_NOISE","1",1);}
  struct complexd tap={.r=1,.i=0};struct complexd *taps[]={&tap};float phase=0;
  channel_desc_t ch={.nb_tx=1,.nb_rx=1,.channel_length=1,.ch=taps,.Doppler_phase_cur=&phase,
    .sampling_rate=7680000,.modelid=SAT_LEO_TRANS,.center_freq=2488400000,
    .enable_dynamic_delay=true,.enable_dynamic_Doppler=true};
  enum {N=1024};c16_t in[N];cf_t out[N];c16_t *inputs[]={in};
  for(int i=0;i<N;i++)in[i]=(c16_t){.r=1000,.i=2000};
  if(legacy) {
#ifdef OAI_HAS_LEGACY_STK
    ch.stk_n=1;ch.stk_visible=0;memset(out,0,sizeof(out));rxAddInput(inputs,out,0,&ch,N);
    assert(energy(out,N)==0);
    ch.stk_visible=1;memset(out,0,sizeof(out));rxAddInput(inputs,out,0,&ch,N);
    assert(fabs(energy(out,N)/5000000.-1)<1e-6);
    printf("PASS preserved legacy SAT_LEO_STK IQ visibility gate\n");return 0;
#else
    fprintf(stderr,"Legacy test requested on a source tree without SAT_LEO_STK\n");return 2;
#endif
  }
  update_channel_model(&ch,N,0);memset(out,0,sizeof(out));rxAddInput(inputs,out,0,&ch,N);
  double e0=energy(out,N);assert(fabs(e0/5000000.-1)<1e-6);
  int delay0=ch.channel_offset;
  update_channel_model(&ch,N,7680000);memset(out,0,sizeof(out));rxAddInput(inputs,out,0,&ch,N);
  double e1=energy(out,N);assert(fabs(e1/e0-.1)<1e-6);
  assert(ch.channel_offset>delay0);assert(ch.Doppler_phase_inc<0);
  double gain=1,sigma=0;stk_trace_iq_parameters(&ch,inputs,0,N,&gain,&sigma);
  double ratio=2*sigma*sigma/(e0*gain*gain);
  assert(fabs(ratio-(pow(10,-20./10)*7680000/2000000))<1e-8);
  update_channel_model(&ch,N,3*7680000);memset(out,0,sizeof(out));rxAddInput(inputs,out,0,&ch,N);
  assert(energy(out,N)==0);
  printf("PASS actual rxAddInput: 10dB loss energy ratio=%.9f; outage=0; noise ratio=%.9f; delay and Doppler changed\n",e1/e0,ratio);
}
