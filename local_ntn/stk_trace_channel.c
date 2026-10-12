/* SPDX-License-Identifier: LicenseRef-CSSL-1.0
 * Deterministic, sample-timestamp-driven STK channel. Legacy UDP is independent.
 */
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include <limits.h>
#include <common/utils/LOG/log.h>
#include <openair1/SIMULATION/TOOLS/sim.h>
#include "openair2/LAYER2/NR_MAC_gNB/mac_config.h"
#include "rfsimulator.h"
#include "stk_trace.h"
#include "stk_schedule.h"

static pthread_once_t once=PTHREAD_ONCE_INIT;
static pthread_mutex_t lock=PTHREAD_MUTEX_INITIALIZER;
static stk_trace trace;
static stk_schedule schedule;
static bool schedule_enabled;
static bool enabled;
static double rate=1., epoch, dl_reference, ul_reference, bandwidth=2000000.;
static double extra_loss, cn_offset;
static bool noise_enabled=true, dynamic_delay=true, dynamic_doppler=true;
static openair0_ntn_sync_state_t last_sync;
static bool have_sync;
static bool observed_dl;
typedef struct {channel_desc_t *channel;double gain, noise_ratio;bool valid;} iq_state;
static iq_state iq[16];

static double number(const char *name,double fallback,double lo,double hi)
{
  const char *s=getenv(name); if(!s || !*s) return fallback;
  char *end;double v=strtod(s,&end);
  AssertFatal(end!=s && !*end && isfinite(v) && v>=lo && v<=hi,"Invalid %s\n",name);
  return v;
}
static void init(void)
{
  const char *path=getenv("OAI_STK_TRACE"); if(!path || !*path)return;
  enabled=true;char error[256];
  AssertFatal(stk_trace_load(path,&trace,error,sizeof(error)),"STK trace: %s\n",error);
  const char *schedule_path=getenv("OAI_STK_SCHEDULE");
  if(schedule_path && *schedule_path) {
    AssertFatal(stk_schedule_load(schedule_path,&schedule,error,sizeof(error)),"STK schedule: %s\n",error);
    schedule_enabled=true;
  }
  rate=number("OAI_STK_TRACE_RATE",1,0,1);
  epoch=number("OAI_STK_TRACE_EPOCH",trace.rows[0].time,trace.rows[0].time,trace.rows[trace.count-1].time);
  bandwidth=number("OAI_STK_TRACE_BW_HZ",2000000,1,100000000);
  extra_loss=number("OAI_STK_TRACE_EXTRA_LOSS_DB",0,0,200);
  cn_offset=number("OAI_STK_TRACE_CN_OFFSET_DB",0,-200,100);
  noise_enabled=number("OAI_STK_TRACE_NOISE",1,0,1)!=0;
  dynamic_delay=number("OAI_STK_DYNAMIC_DELAY",1,0,1)!=0;
  dynamic_doppler=number("OAI_STK_DYNAMIC_DOPPLER",1,0,1)!=0;
  LOG_I(HW,"STKTRACE2 interpolation=%s\n",trace.legacy_linear?"legacy-linear":trace.blend_aware?"blend-aware":"hermite");
  bool dl=false,ul=false;
  for(size_t i=0;i<trace.count;i++) {
    if(!dl && trace.rows[i].dl_valid){dl_reference=trace.rows[i].dl_power;dl=true;}
    if(!ul && trace.rows[i].ul_valid){ul_reference=trace.rows[i].ul_power;ul=true;}
  }
  AssertFatal(dl && ul,"STK trace has no valid DL/UL power reference\n");
  LOG_I(HW,"STKTRACE2 loaded %zu states [%.3f, %.3f], epoch %.3f, rate %.3f STK-s/IQ-s; noise %d\n",
        trace.count,trace.rows[0].time,trace.rows[trace.count-1].time,epoch,rate,noise_enabled);
}
static void ranges(const stk_trace_row *s,const double site[3],double *r,double *v,double *a)
{
  double rr=0,rv=0,vv=0,ra=0;
  for(int i=0;i<3;i++){double x=s->pos[i]-site[i];rr+=x*x;rv+=x*s->vel[i];vv+=s->vel[i]*s->vel[i];ra+=x*s->acc[i];}
  *r=sqrt(rr);AssertFatal(isfinite(*r) && *r>1 && isfinite(rv) && isfinite(vv) && isfinite(ra),"Invalid STK range\n");
  *v=rv / *r * rate;*a=(vv+ra-(rv / *r)*(rv / *r)) / *r * rate*rate;
  AssertFatal(isfinite(*v) && isfinite(*a),"Invalid STK range derivatives\n");
}
static double path_rate(const stk_trace_row *s,const double site[3],double distance)
{
  double value=0;
  for(int i=0;i<3;i++)value+=(s->pos[i]-site[i])*s->path_velocity[i];
  return value/distance*rate;
}
static double clamp(double v,double lo,double hi){return fmin(hi,fmax(lo,v));}
static bool at(uint64_t ts,double fs,stk_trace_row *s)
{return stk_trace_at(&trace,stk_trace_epoch(epoch,ts,fs,rate),s);}

bool stk_trace_time_at_timestamp(uint64_t timestamp,double sampling_rate,double *trace_time_s)
{
  pthread_once(&once,init);
  if(!enabled || trace_time_s==NULL || !isfinite(sampling_rate) || sampling_rate<=0)
    return false;
  *trace_time_s=stk_trace_epoch(epoch,timestamp,sampling_rate,rate);
  return isfinite(*trace_time_s);
}

bool update_channel_model_from_stk_trace(channel_desc_t *ch,int n,uint64_t ts)
{
  pthread_once(&once,init);
  if(!enabled)return false;
  AssertFatal(ch->modelid==SAT_LEO_TRANS,"STKTRACE2 currently requires SAT_LEO_TRANS\n");
  stk_trace_row s;bool inrange=at(ts,ch->sampling_rate,&s);
  bool valid=inrange && (ch->is_uplink?s.ul_valid:s.dl_valid);
  double gain=0,cn=-100;
  if(inrange) {
    gain=stk_trace_amplitude(ch->is_uplink?s.ul_power:s.dl_power,
                            (ch->is_uplink?ul_reference:dl_reference)+extra_loss,valid);
    /* Numeric IQ reference must not silently saturate. */
    AssertFatal(gain<=16,"STK gain >24 dB above reference; choose a calibrated reference interval\n");
    cn=(ch->is_uplink?s.ul_cn:s.dl_cn)+cn_offset-extra_loss;
  }
  pthread_mutex_lock(&lock);
  int k=0;for(;k<16;k++)if(!iq[k].channel || iq[k].channel==ch)break;
  AssertFatal(k<16,"Too many STK trace channels\n");
  iq[k]=(iq_state){.channel=ch,.gain=gain,.valid=valid,
      .noise_ratio=noise_enabled?pow(10,-clamp(cn,-60,150)/10)*ch->sampling_rate/bandwidth:0};
  pthread_mutex_unlock(&lock);
  if(!inrange) {
    if(!ch->is_uplink){pthread_mutex_lock(&lock);observed_dl=true;have_sync=false;pthread_mutex_unlock(&lock);}
    if(ts/(uint64_t)ch->sampling_rate!=(ts+n)/(uint64_t)ch->sampling_rate)
      LOG_W(HW,"STKTRACE2 exhausted at IQ %.3f s; signal muted (no looping or stale freeze)\n",ts/ch->sampling_rate);
    return true;
  }
  double rs,vs,as,rf,vf,af; ranges(&s,s.ue,&rs,&vs,&as);ranges(&s,s.gnb,&rf,&vf,&af);
  double delay=(rs+rf)/SPEED_OF_LIGHT;
  double doppler=ch->is_uplink?-vs/SPEED_OF_LIGHT*ch->center_freq:-vs/(SPEED_OF_LIGHT+vs)*ch->center_freq;
  double delay_samples=delay*ch->sampling_rate;
  AssertFatal(isfinite(delay_samples) && delay_samples>=0 && delay_samples<(double)LLONG_MAX,
              "STK delay does not fit sample offset\n");
  if(ch->enable_dynamic_delay && dynamic_delay)ch->channel_offset=llround(delay_samples);
  if(ch->enable_dynamic_Doppler && dynamic_doppler)ch->Doppler_phase_inc=2*M_PI*doppler/ch->sampling_rate;
  if(!ch->is_uplink) {
    pthread_mutex_lock(&lock);
    last_sync=(openair0_ntn_sync_state_t){.stk_time_s=s.time,.propagation_delay_ms=delay*1000,.synthetic_blend=s.synthetic_blend,
      .dl_doppler_hz=ch->enable_dynamic_Doppler && dynamic_doppler?doppler:0,
      .dl_time_drift_us_s=(path_rate(&s,s.ue,rs)+path_rate(&s,s.gnb,rf))/SPEED_OF_LIGHT*1e6};
    have_sync=valid;observed_dl=true;pthread_mutex_unlock(&lock);
  }
  if(ts/(uint64_t)ch->sampling_rate!=(ts+n)/(uint64_t)ch->sampling_rate)
    LOG_I(HW,"STKTRACE2 %s IQ=%.6f STK=%.6f delay=%.6fms Doppler=%.3fHz gain=%.3fdB C/N=%.3fdB valid=%d samples=%" PRIu64 "\n",
      ch->is_uplink?"UL":"DL",ts/ch->sampling_rate,s.time,delay*1000,doppler,
      gain>0?20*log10(gain):-300,cn,valid,ts);
  if(schedule_enabled && ts/(uint64_t)ch->sampling_rate!=(ts+n)/(uint64_t)ch->sampling_rate) {
    stk_schedule_entry selected={0};
    if(stk_schedule_at(&schedule,s.time,&selected))
      LOG_I(HW,"STKSCHEDULE %s IQ=%.6f STK=%.6f satellite_id=%s elevation_deg=%.3f visible=%d switched=%d phase=%s previous=%s next=%s samples=%" PRIu64 "\n",
            ch->is_uplink?"UL":"DL",ts/ch->sampling_rate,s.time,selected.satellite_id,
            selected.elevation_deg,selected.visible,selected.switched,selected.handover_phase,
            selected.previous_satellite_id,selected.next_satellite_id,ts);
  }
  /* Publish the state AT the announced next-frame epoch, not the current frame. */
  uint64_t spms=llround(ch->sampling_rate/1000),subframe=ts/spms;
  if(ch->is_uplink && subframe%10==0 && at((subframe/10+1)*10*spms,ch->sampling_rate,&s)) {
    ranges(&s,s.gnb,&rf,&vf,&af);
    gnb_sat_position_update_t u={.sfn=(subframe/10+1)%1024,.subframe=0,
      .delay=llround(clamp(2*rf/(SPEED_OF_LIGHT*4.072e-9),0,66485757)),
      .drift=llround(clamp(2*vf/(SPEED_OF_LIGHT*.2e-9),-257303,257303)),
      .accel=llround(clamp(af/(SPEED_OF_LIGHT*.2e-10),0,28949)),
      .position.X=llround(clamp(s.pos[0]/1.3,-33554432,33554431)),
      .position.Y=llround(clamp(s.pos[1]/1.3,-33554432,33554431)),
      .position.Z=llround(clamp(s.pos[2]/1.3,-33554432,33554431)),
      .velocity.X=llround(clamp(s.vel[0]*rate/.06,-131072,131071)),
      .velocity.Y=llround(clamp(s.vel[1]*rate/.06,-131072,131071)),
      .velocity.Z=llround(clamp(s.vel[2]*rate/.06,-131072,131071))};
    nr_update_sib19(&u);
  }
  return true;
}

bool get_stk_trace_sync(double frequency,openair0_ntn_sync_state_t *s,openair0_ntn_sync_status_t *status)
{
  pthread_once(&once,init);if(!enabled)return false;
  pthread_mutex_lock(&lock);bool ready=have_sync,seen=observed_dl;*s=last_sync;pthread_mutex_unlock(&lock);
  if(seen){*status=ready?OPENAIR0_NTN_SYNC_READY:OPENAIR0_NTN_SYNC_NOT_VISIBLE;return true;}
  stk_trace_row r;
  if(!stk_trace_at(&trace,epoch,&r)||!r.dl_valid){*status=OPENAIR0_NTN_SYNC_NOT_VISIBLE;return true;}
  double rs,vs,as,rf,vf,af;ranges(&r,r.ue,&rs,&vs,&as);ranges(&r,r.gnb,&rf,&vf,&af);
  *s=(openair0_ntn_sync_state_t){.stk_time_s=epoch,.propagation_delay_ms=(rs+rf)/SPEED_OF_LIGHT*1000,.synthetic_blend=r.synthetic_blend,
    .dl_doppler_hz=dynamic_doppler?-vs/(SPEED_OF_LIGHT+vs)*frequency:0,.dl_time_drift_us_s=(path_rate(&r,r.ue,rs)+path_rate(&r,r.gnb,rf))/SPEED_OF_LIGHT*1e6};
  *status=OPENAIR0_NTN_SYNC_READY;return true;
}

/* Called from the real rxAddInput path, before per-sample convolution/rotation.
 * Noise is block-RMS calibrated (not an absolute receiver sensitivity model).
 * C/N is referenced to the exported 2 MHz measurement bandwidth by default.
 */
void stk_trace_iq_parameters(channel_desc_t *ch,c16_t **input,int input_offset,int n,double *gain,double *sigma)
{
  pthread_mutex_lock(&lock);iq_state state={0};
  for(int k=0;k<16;k++)if(iq[k].channel==ch){state=iq[k];break;}
  pthread_mutex_unlock(&lock);
  if(!state.channel)return;
  double energy=0;
  for(int ant=0;ant<ch->nb_tx;ant++)for(int i=0;i<n;i++)
    energy+=(double)input[ant][input_offset+i].r*input[ant][input_offset+i].r
      +(double)input[ant][input_offset+i].i*input[ant][input_offset+i].i;
  double original_gain=*gain;
  *gain*=state.gain;
  *sigma=state.valid?sqrt(energy/fmax(n,1)*(*gain)*(*gain)*state.noise_ratio/2):
    sqrt(energy/fmax(n,1)*original_gain*original_gain*1e-8/2);
}
