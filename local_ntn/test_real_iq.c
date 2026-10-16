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
#include "radio/rfsimulator/qd_channel_reader.h"
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
/* 用真实 STK + QD + rxAddInput 路径检查多端口结果没有被退回旧单 tap。 */
static int spatial_iq(const char *trace, const char *bundle_path)
{
  setenv("OAI_STK_TRACE", trace, 1);
  setenv("OAI_QD_CHANNEL", bundle_path, 1);
  setenv("OAI_STK_TRACE_NOISE", "0", 1);
  qd_channel_t bundle = {0};
  char error[512];
  assert(qd_channel_load(bundle_path, NULL, &bundle, error, sizeof(error)));
  float phases[bundle.rx_antennas];
  memset(phases, 0, sizeof(phases));
  channel_desc_t ch = {.nb_tx=bundle.tx_antennas, .nb_rx=bundle.rx_antennas,
    .channel_length=1, .Doppler_phase_cur=phases, .sampling_rate=7680000,
    .modelid=SAT_LEO_TRANS, .center_freq=bundle.center_frequency_hz,
    .is_uplink=strcmp(bundle.link_direction,"uplink")==0};
  enum {N=128};
  update_channel_model(&ch,N,0);
  size_t history=qd_channel_history_length(&ch);
  size_t lookahead=qd_channel_lookahead_length(&ch);
  c16_t *inputs[bundle.tx_antennas];
  for(size_t tx=0;tx<bundle.tx_antennas;tx++) {
    inputs[tx]=calloc(history+N-1+lookahead,sizeof(c16_t));assert(inputs[tx]);
    for(size_t n=0;n<history+N-1+lookahead;n++)
      inputs[tx][n]=(c16_t){.r=(int)(n*(17+tx)%2000)-1000,.i=(int)(n*(31+tx)%2000)-1000};
  }
  for(size_t rx=0;rx<bundle.rx_antennas;rx++) {
    struct complexd reference[N];cf_t output[N];memset(output,0,sizeof(output));
    assert(qd_channel_convolve(&ch,inputs,rx,N,reference));
    double gain=1,sigma=0;
    stk_trace_iq_parameters(&ch,inputs,history-1,N,&gain,&sigma);
    rxAddInput(inputs,output,rx,&ch,N);
    for(int n=0;n<N;n++) {
      assert(fabs(output[n].r-reference[n].r*gain)<1e-4*(1+fabs(reference[n].r*gain)));
      assert(fabs(output[n].i-reference[n].i*gain)<1e-4*(1+fabs(reference[n].i*gain)));
    }
  }
  printf("PASS actual spatial rxAddInput: %zu Tx x %zu Rx, STK gain + QD convolution\n",bundle.tx_antennas,bundle.rx_antennas);
  for(size_t tx=0;tx<bundle.tx_antennas;tx++) free(inputs[tx]);
  qd_channel_free(&bundle);
  return 0;
}
int main(int argc,char **argv)
{
  assert(argc==2 || argc==3);
  if(argc==3)return spatial_iq(argv[1],argv[2]);
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
