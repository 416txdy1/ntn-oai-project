/* Integration test compiles the repository's actual apply_channelmod.c.
 * Only logging, RNG (zero-noise measurement) and RRC callback are test doubles.
 */
#include <assert.h>
#include <complex.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <common/utils/LOG/log.h>
#include <openair1/SIMULATION/TOOLS/sim.h>
#include "radio/rfsimulator/rfsimulator.h"
#include "radio/rfsimulator/stk_trace.h"
#include "radio/rfsimulator/qd_channel_reader.h"
#include "openair2/LAYER2/NR_MAC_gNB/mac_config.h"
static log_t log_state;
static bool measured_noise;
static bool sequence_noise;
static uint32_t noise_state;
static size_t noise_calls;
log_t *g_log=&log_state;
void logRecord_mt(const char *f,const char *fn,int l,int c,int level,const char *format,...)
{ (void)f; (void)fn; (void)l; (void)c; (void)level;
  if(strncmp(format,"STKCHANNELSTART ",16)==0 || strncmp(format,"STKCLOCK ",9)==0 || strncmp(format,"STKSCHEDULE ",12)==0 || strncmp(format,"STKTRACE2 ",10)==0) {
    va_list args;va_start(args,format);vprintf(format,args);va_end(args);
  }
}
void exit_function(const char *f,const char *fn,const int line,const char *s,const int kind)
{ (void)f; (void)fn; (void)line; (void)s; (void)kind; abort(); }
double gaussZiggurat(double mean,double variance)
{ (void)mean; (void)variance;
  if(sequence_noise) {noise_calls++;noise_state=noise_state*1664525u+1013904223u;return ((int)(noise_state%2001)-1000)/1000.0;}
  return measured_noise?1:0; }
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
  setenv("OAI_STK_TRACE_NOISE", "1", 1);
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
  cf_t batch_output[bundle.rx_antennas][N];cf_t *batch_ptr[bundle.rx_antennas];
  memset(batch_output,0,sizeof(batch_output));
  for(size_t rx=0;rx<bundle.rx_antennas;rx++) batch_ptr[rx]=batch_output[rx];
  rxAddInputs(inputs,batch_ptr,&ch,N);
  memset(phases,0,sizeof(phases));
  for(size_t rx=0;rx<bundle.rx_antennas;rx++) {
    struct complexd reference[N];cf_t output[N];memset(output,0,sizeof(output));
    assert(qd_channel_convolve(&ch,inputs,rx,N,reference));
    double gain=1,sigma=0;
    stk_trace_iq_parameters(&ch,inputs,history-1,N,&gain,&sigma);
    rxAddInput(inputs,output,rx,&ch,N);
    for(int n=0;n<N;n++) {
      assert(fabs(batch_output[rx][n].r-output[n].r)<1e-4*(1+fabs(output[n].r)));
      assert(fabs(batch_output[rx][n].i-output[n].i)<1e-4*(1+fabs(output[n].i)));
      assert(fabs(output[n].r-reference[n].r*gain)<1e-4*(1+fabs(reference[n].r*gain)));
      assert(fabs(output[n].i-reference[n].i*gain)<1e-4*(1+fabs(reference[n].i*gain)));
    }
  }
  /* 带非零噪声的确定性序列检查：批量化不能重排端口或I/Q随机调用。 */
  cf_t sequential[bundle.rx_antennas][N];memset(sequential,0,sizeof(sequential));
  double gain=1,sigma=0;stk_trace_iq_parameters(&ch,inputs,history-1,N,&gain,&sigma);assert(sigma>0);
  sequence_noise=true;noise_state=12345;noise_calls=0;memset(phases,0,sizeof(phases));
  for(size_t rx=0;rx<bundle.rx_antennas;rx++) rxAddInput(inputs,sequential[rx],rx,&ch,N);
  assert(noise_calls==2*N*bundle.rx_antennas);
  noise_state=12345;noise_calls=0;memset(phases,0,sizeof(phases));memset(batch_output,0,sizeof(batch_output));
  rxAddInputs(inputs,batch_ptr,&ch,N);assert(noise_calls==2*N*bundle.rx_antennas);
  for(size_t rx=0;rx<bundle.rx_antennas;rx++)for(int n=0;n<N;n++) {
    assert(fabs(batch_output[rx][n].r-sequential[rx][n].r)<1e-4*(1+fabs(sequential[rx][n].r)));
    assert(fabs(batch_output[rx][n].i-sequential[rx][n].i)<1e-4*(1+fabs(sequential[rx][n].i)));
  }
  sequence_noise=false;
  printf("PASS actual spatial rxAddInput: %zu Tx x %zu Rx, STK gain + QD convolution\n",bundle.tx_antennas,bundle.rx_antennas);
  for(size_t tx=0;tx<bundle.tx_antennas;tx++) free(inputs[tx]);
  qd_channel_free(&bundle);
  return 0;
}
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
    /* 与原复指数独立对照，覆盖正负频偏、零频偏、大相位和复数输入。 */
    double maximum_error = 0;
    const double starts[] = {-10000, -3.141592653589793, 0, 3.141592653589793, 10000};
    const double increments[] = {-0.6, 0, 0.6};
    c16_t complex_input[67]; cf_t complex_output[67]; c16_t *complex_inputs[]={complex_input};
    for (int j=0;j<67;j++) complex_input[j]=(c16_t){.r=31000-j*711,.i=-27000+j*583};
    for (int a=0;a<5;a++) for (int b=0;b<3;b++) {
      phase=starts[a]; ch.Doppler_phase_inc=increments[b];
      double expected_phase=phase;
      expected_phase-=2*M_PI*round(expected_phase/(2*M_PI));
      memset(complex_output,0,sizeof(complex_output));
      rxAddInput(complex_inputs,complex_output,0,&ch,67);
      for (int j=0;j<67;j++) {
        const double complex expected=((double)complex_input[j].r+(double)complex_input[j].i*I)*cexp(expected_phase*I);
        const double error=hypot(complex_output[j].r-(float)creal(expected),complex_output[j].i-(float)cimag(expected));
        maximum_error=fmax(maximum_error,error);
        assert(error<0.01); /* float32 输出一个LSB量级，远低于int16量化单位。 */
        expected_phase+=ch.Doppler_phase_inc;
      }
      assert(phase==(float)expected_phase);
    }
    /* 覆盖跨端口缓存命中、不同初相/频偏失效以及超过容量的回退。 */
    const int sizes[] = {67, 7680, 16384, 16385};
    struct complexd *four_taps[] = {&tap, &tap, &tap, &tap};
    float four_phases[4]; ch.nb_rx=4; ch.ch=four_taps; ch.Doppler_phase_cur=four_phases;
    for (int ncase=0;ncase<4;ncase++) {
      const int count=sizes[ncase];
      c16_t *data=calloc(count,sizeof(*data)); cf_t *result=calloc(count,sizeof(*result));
      assert(data && result); c16_t *data_ptr[]={data};
      for(int j=0;j<count;j++) data[j]=(c16_t){31000-j%1000,-27000+j%777};
      for(int iteration=0;iteration<3;iteration++) {
        ch.Doppler_phase_inc=iteration==2?-0.17:0.19;
        for(int rx=0;rx<4;rx++) {
          four_phases[rx]=iteration==1 && rx==2 ? -2.1 : 1.3;
          double expected_phase=four_phases[rx];
          expected_phase-=2*M_PI*round(expected_phase/(2*M_PI));
          memset(result,0,count*sizeof(*result));
          rxAddInput(data_ptr,result,rx,&ch,count);
          for(int j=0;j<count;j++) {
            double complex expected=((double)data[j].r+(double)data[j].i*I)*cexp(expected_phase*I);
            double error=hypot(result[j].r-(float)creal(expected),result[j].i-(float)cimag(expected));
            maximum_error=fmax(maximum_error,error); assert(error<0.01);
            expected_phase+=ch.Doppler_phase_inc;
          }
          assert(four_phases[rx]==(float)expected_phase);
        }
      }
      free(data);free(result);
    }
    printf("PASS actual rxAddInput phase and four-port rotation cache, max error %.9g\n",maximum_error);return 0;
  }
  if(argc==3 && !clock_mode && !qd_mode)return spatial_iq(argv[1],argv[2]);
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
    for(int i=0;i<=38;i++) {
      update_channel_model(&ch,537600,10083072+(uint64_t)i*537600);
      update_channel_model(&ul,537600,10129151+(uint64_t)i*537600);
    }
    puts("PASS actual sample clock log fixture");return 0;
  }
  if(qd_mode) {
    ch.is_uplink=getenv("IQ_TEST_UPLINK")!=NULL;
    if(ch.is_uplink)ch.center_freq=1614900000;
    update_channel_model(&ch,N,0);
    const size_t history=qd_channel_history_length(&ch);assert(history>255);
    const size_t lookahead=qd_channel_lookahead_length(&ch);
    c16_t *storage=calloc(history+N-1+lookahead,sizeof(*storage));assert(storage);
    c16_t *qd_input[]={storage};
    for(size_t i=0;i<history+N-1+lookahead;i++)storage[i]=(c16_t){.r=i<history-1?20000:1000,.i=i<history-1?10000:2000};
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
    uint64_t last=llround((parsed.rows[parsed.count-1].time-parsed.rows[0].time)*ch.sampling_rate);
    update_channel_model(&ch,N,last);memset(out,0,sizeof(out));rxAddInput(qd_input,out,0,&ch,N);
    for(int i=0;i<N;i++)assert(isfinite(out[i].r) && isfinite(out[i].i));
    update_channel_model(&ch,N,last+7680000);memset(out,0,sizeof(out));rxAddInput(qd_input,out,0,&ch,N);
    assert(energy(out,N)==0);
    measured_noise=true;memset(out,0,sizeof(out));rxAddInput(qd_input,out,0,&ch,N);assert(energy(out,N)>0);
    printf("PASS actual QD rxAddInput %s: history=%zu current-RMS noise applied once, finite tail, exhausted mute/background\n",ch.is_uplink?"UL":"DL",history);
    free(storage);free(parsed.rows);return 0;
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
