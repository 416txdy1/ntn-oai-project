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
#include "radio/rfsimulator/stk_trace.h"
#include "openair2/LAYER2/NR_MAC_gNB/mac_config.h"
static log_t log_state;
static bool measured_noise;
log_t *g_log=&log_state;
void logRecord_mt(const char *f,const char *fn,int l,int c,int level,const char *format,...)
{ (void)f; (void)fn; (void)l; (void)c; (void)level;
  if(strncmp(format,"STKCLOCK ",9)==0 || strncmp(format,"STKSCHEDULE ",12)==0 || strncmp(format,"STKTRACE2 ",10)==0) {
    va_list args;va_start(args,format);vprintf(format,args);va_end(args);
  }
}
void exit_function(const char *f,const char *fn,const int line,const char *s,const int kind)
{ (void)f; (void)fn; (void)line; (void)s; (void)kind; abort(); }
double gaussZiggurat(double mean,double variance)
{ (void)mean; (void)variance; return measured_noise?1:0; }
int32_t signal_energy(int32_t *s,uint32_t n)
{ (void)s; (void)n; return 0; }
bool nr_update_sib19(const gnb_sat_position_update_t *s)
{ (void)s; return true; }
bool update_channel_model_from_stk(channel_desc_t *c,int n,uint64_t t)
{ (void)c; (void)n; (void)t; return false; }
static double energy(cf_t *s,int n){double e=0;for(int i=0;i<n;i++)e+=s[i].r*s[i].r+s[i].i*s[i].i;return e/n;}
int main(int argc,char **argv)
{
  assert(argc==2 || argc==3);
  log_state.log_component[HW].level=OAILOG_INFO;
  bool clock_mode=argc==3 && strcmp(argv[2],"--clock")==0;
  bool qd_mode=argc==3 && strcmp(argv[2],"--qd")==0;
  if(strcmp(argv[1],"--phase")==0) {
    struct complexd tap={.r=1};struct complexd *taps[]={&tap};float phase=0;
    channel_desc_t ch={.nb_tx=1,.nb_rx=1,.channel_length=1,.ch=taps,.Doppler_phase_cur=&phase,
      .sampling_rate=7680000,.noise_power_dB=-300,.Doppler_phase_inc=.125};
    c16_t input[8];cf_t output[8]={0};c16_t *inputs[]={input};
    for(int i=0;i<8;i++)input[i]=(c16_t){.r=1000};
    rxAddInput(inputs,output,0,&ch,8);
    assert(fabs(phase-1.)<1e-6);
    ch.Doppler_phase_inc=0;memset(output,0,sizeof(output));
    rxAddInput(inputs,output,0,&ch,8);
    for(int i=0;i<8;i++) {
      assert(isfinite(output[i].r) && isfinite(output[i].i));
      assert(fabs(output[i].r-1000*cos(1.))<1e-3);
      assert(fabs(output[i].i-1000*sin(1.))<1e-3);
    }
    assert(fabs(phase-1.)<1e-6);
    puts("PASS actual rxAddInput nonzero-to-zero Doppler phase continuity");return 0;
  }
  bool legacy=strcmp(argv[1],"--legacy")==0;
  if(!legacy){setenv("OAI_STK_TRACE",argv[1],1);setenv("OAI_STK_TRACE_NOISE","1",1);}
  struct complexd tap={.r=1,.i=0};struct complexd *taps[]={&tap};float phase=0;
  channel_desc_t ch={.nb_tx=1,.nb_rx=1,.channel_length=1,.ch=taps,.Doppler_phase_cur=&phase,
    .sampling_rate=7680000,.modelid=SAT_LEO_TRANS,.center_freq=2488400000,
    .enable_dynamic_delay=true,.enable_dynamic_Doppler=true};
  enum {N=1024};c16_t in[N];cf_t out[N];c16_t *inputs[]={in};
  for(int i=0;i<N;i++)in[i]=(c16_t){.r=1000,.i=2000};
  if(clock_mode) {
    float ul_phase=0;channel_desc_t ul=ch;ul.is_uplink=true;ul.center_freq=1614900000;ul.Doppler_phase_cur=&ul_phase;
    for(int i=0;i<=60;i++) {
      update_channel_model(&ch,537600,(uint64_t)i*537600);
      update_channel_model(&ul,537600,(uint64_t)i*537600);
    }
    puts("PASS actual sample clock log fixture");return 0;
  }
  if(qd_mode) {
    ch.is_uplink=getenv("IQ_TEST_UPLINK")!=NULL;
    if(ch.is_uplink)ch.center_freq=1614900000;
    update_channel_model(&ch,N,0);
    const size_t history=qd_channel_history_length(&ch);assert(history>255);
    c16_t *storage=calloc(history+N-1,sizeof(*storage));assert(storage);
    c16_t *qd_input[]={storage};
    for(size_t i=0;i<history+N-1;i++)storage[i]=(c16_t){.r=i<history-1?20000:1000,.i=i<history-1?10000:2000};
    double gain=1,sigma=0;stk_trace_iq_parameters(&ch,qd_input,history-1,N,&gain,&sigma);
    stk_trace parsed={0};char error[256];assert(stk_trace_load(argv[1],&parsed,error,sizeof(error)));
    double cn=ch.is_uplink?parsed.rows[0].ul_cn:parsed.rows[0].dl_cn;
    const double expected_sigma=sqrt(5000000.*gain*gain*pow(10.,-cn/10.)*ch.sampling_rate/2000000./2.);
    assert(fabs(sigma/expected_sigma-1)<1e-8); // poisoned history must not enter current-block RMS
    cf_t clean[N];memset(clean,0,sizeof(clean));phase=0;rxAddInput(qd_input,clean,0,&ch,N);
    measured_noise=true;memset(out,0,sizeof(out));phase=0;rxAddInput(qd_input,out,0,&ch,N);
    for(int i=0;i<N;i++) {
      assert(isfinite(out[i].r) && isfinite(out[i].i));
      assert(fabs((out[i].r-clean[i].r)-sigma)<1e-3*(1+sigma));
      assert(fabs((out[i].i-clean[i].i)-sigma)<1e-3*(1+sigma));
    }
    measured_noise=false;
    uint64_t last=llround(parsed.rows[parsed.count-1].time*ch.sampling_rate);
    update_channel_model(&ch,N,last);memset(out,0,sizeof(out));rxAddInput(qd_input,out,0,&ch,N);
    for(int i=0;i<N;i++)assert(isfinite(out[i].r) && isfinite(out[i].i));
    update_channel_model(&ch,N,last+7680000);memset(out,0,sizeof(out));rxAddInput(qd_input,out,0,&ch,N);
    assert(energy(out,N)==0);
    measured_noise=true;memset(out,0,sizeof(out));rxAddInput(qd_input,out,0,&ch,N);assert(energy(out,N)>0);
    printf("PASS actual QD rxAddInput %s: history=%zu current-RMS noise applied once, finite tail, exhausted mute/background\n",ch.is_uplink?"UL":"DL",history);
    free(storage);stk_trace_free(&parsed);return 0;
  }
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
  if(getenv("OAI_STK_DYNAMIC_DELAY") && strcmp(getenv("OAI_STK_DYNAMIC_DELAY"),"0")==0)
    assert(ch.channel_offset==delay0);
  else assert(ch.channel_offset>delay0);
  if(getenv("OAI_STK_DYNAMIC_DOPPLER") && strcmp(getenv("OAI_STK_DYNAMIC_DOPPLER"),"0")==0)
    assert(ch.Doppler_phase_inc==0);
  else assert(ch.Doppler_phase_inc<0);
  double gain=1,sigma=0;stk_trace_iq_parameters(&ch,inputs,0,N,&gain,&sigma);
  double ratio=2*sigma*sigma/(e0*gain*gain);
  assert(fabs(ratio-(pow(10,-20./10)*7680000/2000000))<1e-8);
  update_channel_model(&ch,N,3*7680000);memset(out,0,sizeof(out));rxAddInput(inputs,out,0,&ch,N);
  assert(energy(out,N)==0);
  measured_noise=true;memset(out,0,sizeof(out));rxAddInput(inputs,out,0,&ch,N);
  assert(energy(out,N)>0);
  for(int i=0;i<N;i++)assert(isfinite(out[i].r) && isfinite(out[i].i));
  measured_noise=false;
  update_channel_model(&ch,N,5*7680000);memset(out,0,sizeof(out));rxAddInput(inputs,out,0,&ch,N);
  assert(energy(out,N)==0);
  measured_noise=true;memset(out,0,sizeof(out));rxAddInput(inputs,out,0,&ch,N);
  assert(energy(out,N)>0);
  for(int i=0;i<N;i++)assert(isfinite(out[i].r) && isfinite(out[i].i));
  puts("PASS actual rxAddInput: invisible and exhausted signal mute preserve finite background noise");
  printf("PASS actual rxAddInput: 10dB loss energy ratio=%.9f; outage=0; noise ratio=%.9f; delay and Doppler changed\n",e1/e0,ratio);
}
