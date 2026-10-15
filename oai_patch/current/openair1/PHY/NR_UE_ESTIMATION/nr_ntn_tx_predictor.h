/* SPDX-License-Identifier: LicenseRef-CSSL-1.0 */
/* Receiver-derived NTN transmit-time prediction; no simulator truth input. */
#ifndef NTN_TX_PREDICTION_CANDIDATE_H
#define NTN_TX_PREDICTION_CANDIDATE_H
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include <limits.h>
#define NTN_TX_HISTORY 7
typedef struct {
  uint64_t a,q;
  double fo;
} ntn_tx_observation;
typedef struct {
  bool anchored;
  int pci,n;
  double clock_offset;
  ntn_tx_observation h[NTN_TX_HISTORY];
} ntn_tx_clock;
typedef struct {
  double ta_samples,total_ul_fo,arrival_sample,delay_samples;
  bool quadratic;
} ntn_tx_prediction;
static inline bool ntn_tx_diff(uint64_t a,uint64_t b,double *result)
{
  uint64_t d=a>=b?a-b:b-a;
  if(d>INT64_MAX)return false;
  *result=a>=b?(double)d:-(double)d;
  return true;
}
/* Delay derivatives in samples/second and samples/second^2 (half acceleration).
 * Relative integer clocks retain precision across 32-bit clock boundaries. */
static inline bool ntn_tx_fit(const ntn_tx_clock *c,double fs,double *slope,double *curve)
{
  *slope=*curve=0;
  if(!c || c->n<2 || !isfinite(fs) || fs<=0)return false;
  const ntn_tx_observation *last=&c->h[c->n-1],*prev=&c->h[c->n-2];
  double da,dq;
  if(!ntn_tx_diff(last->a,prev->a,&da)||!ntn_tx_diff(last->q,prev->q,&dq)||da<=0||dq<=0)return false;
  *slope=(da-dq)*fs/da;
  if(c->n<NTN_TX_HISTORY)return false;
  double s2=0,s3=0,s4=0,y1=0,y2=0;
  for(int i=0;i<c->n-1;i++){
    double xa,xq;
    if(!ntn_tx_diff(c->h[i].a,last->a,&xa)||!ntn_tx_diff(c->h[i].q,last->q,&xq))return false;
    double t=xa/fs,y=xa-xq;
    s2+=t*t;s3+=t*t*t;s4+=t*t*t*t;y1+=t*y;y2+=t*t*y;
  }
  double det=s2*s4-s3*s3;
  if(!isfinite(det)||det<=DBL_EPSILON*s2*s4)return false;
  double v=(y1*s4-y2*s3)/det,k=(y2*s2-y1*s3)/det;
  if(!isfinite(v)||!isfinite(k))return false;
  *slope=v;*curve=k;return true;
}
static inline bool ntn_tx_observe(ntn_tx_clock *c,int pci,uint64_t a,uint64_t q,double fo,double fs)
{
  if(!c||pci<0||pci>1007||!isfinite(fo)||!isfinite(fs)||fs<=0)return false;
  if(c->n && c->pci==pci){
    const ntn_tx_observation *last=&c->h[c->n-1];double da,dq;
    if(!ntn_tx_diff(a,last->a,&da)||!ntn_tx_diff(q,last->q,&dq)||da<=0||dq<=0)return false;
    double slope,curve;ntn_tx_fit(c,fs,&slope,&curve);double dt=da/fs;
    /* A measured change clears the local fit; it never rejects that observation.
     * Four four-sample search cells cover quantization and measurement jitter. */
    if(c->n==NTN_TX_HISTORY && fabs((da-dq)-(slope*dt+curve*dt*dt))>16)c->n=0;
  }else if(c->n || c->pci!=pci){memset(c,0,sizeof(*c));}
  c->pci=pci;
  if(c->n==NTN_TX_HISTORY){memmove(c->h,c->h+1,sizeof(c->h[0])*(NTN_TX_HISTORY-1));--c->n;}
  c->h[c->n++]=(ntn_tx_observation){a,q,fo};return true;
}
/* Capture only the initial decoded serving SIB TA at its actual TX subframe
 * epoch. Later SIB updates do not replace a valid receiver clock anchor. */
static inline bool ntn_tx_anchor(ntn_tx_clock *c,uint64_t q_epoch,double half_ta,double fs)
{
  if(!c||c->anchored||c->n<2||!isfinite(half_ta)||half_ta<=0||!isfinite(fs)||fs<=0)return false;
  const ntn_tx_observation *last=&c->h[c->n-1];double aq,qa;
  if(!ntn_tx_diff(last->a,last->q,&aq)||!ntn_tx_diff(q_epoch,last->a,&qa))return false;
  double slope,curve;ntn_tx_fit(c,fs,&slope,&curve);
  double offset=aq-half_ta;
  for(int i=0;i<8;i++){
    double dt=(qa+offset)/fs;
    double derivative=-1+(slope+2*curve*dt)/fs;
    if(!isfinite(dt)||fabs(dt)>.25||!isfinite(derivative)||fabs(derivative)<.5)return false;
    offset-=(aq-offset+slope*dt+curve*dt*dt-half_ta)/derivative;
  }
  if(!isfinite(offset))return false;
  c->clock_offset=offset;c->anchored=true;return true;
}
/* Main-thread prediction only. raw_rx_slot is the actual RF sample at the
 * current slot's raw start, not a corrected FFT timestamp. The caller passes
 * actual frame-parameter slot clocks and a configured RX-to-TX bound. */
static inline bool ntn_tx_predict(const ntn_tx_clock *c,int pci,uint64_t raw_rx_slot,
                                  uint64_t q_rx,uint64_t q_tx,double fs,
                                  double max_age,double max_ahead,
                                  double nta_offset,double ordinary_ta,
                                  double dl_carrier,double ul_carrier,
                                  double fo_rate,ntn_tx_prediction *out)
{
  if(!c||!out||!c->anchored||c->n<2||c->pci!=pci||!isfinite(fs)||fs<=0
      ||!isfinite(max_age)||max_age<=0||!isfinite(max_ahead)||max_ahead<=0
      ||!isfinite(nta_offset)||!isfinite(ordinary_ta)||!isfinite(fo_rate)
      ||!isfinite(dl_carrier)||dl_carrier<=0||!isfinite(ul_carrier)||ul_carrier<=0)return false;
  const ntn_tx_observation *last=&c->h[c->n-1];double age,ahead,aq,qr;
  if(!ntn_tx_diff(q_rx,last->q,&age)||!ntn_tx_diff(q_tx,q_rx,&ahead)
      ||!ntn_tx_diff(last->a,last->q,&aq)||!ntn_tx_diff(raw_rx_slot,q_rx,&qr)
      ||age/fs < -.001 || age/fs>max_age || ahead<0 || ahead/fs>max_ahead)return false;
  double tx_a;
  if(!ntn_tx_diff(q_tx,last->a,&tx_a))return false;
  double horizon=(tx_a+c->clock_offset-nta_offset-ordinary_ta)/fs;
  if(horizon<0 || horizon>max_ahead+max_age || !isfinite(horizon))return false;
  double slope,curve;bool quadratic=ntn_tx_fit(c,fs,&slope,&curve);
  double delay=aq-c->clock_offset+slope*horizon+curve*horizon*horizon;
  double current_delay=qr-c->clock_offset;
  double dl=last->fo+fo_rate*horizon;
  double local_velocity=(slope+2*curve*horizon)/fs;
  double ta=current_delay+delay;
  if(!isfinite(delay)||delay<=0||!isfinite(current_delay)||current_delay<=0
      ||!isfinite(ta)||ta<=0||ta>INT_MAX||!isfinite(local_velocity)||fabs(local_velocity)>.1
      ||!isfinite(dl)||fabs(dl)>.01*dl_carrier)return false;
  double ul=ul_carrier*dl/(dl_carrier+dl);
  if(!isfinite(ul))return false;
  *out=(ntn_tx_prediction){ta,ul,(double)q_tx+c->clock_offset-nta_offset-ordinary_ta,delay,quadratic};
  return true;
}
/* Compensation of the CURRENT immutable write, whose timestamp uses the
 * previous TA. Solve the propagation equation at that actual write timestamp;
 * this is separate from the TA which changes the NEXT write's start. */
static inline bool ntn_tx_at_write(const ntn_tx_clock *c,int pci,uint64_t raw_write,
    uint64_t q_rx,double fs,double max_age,double max_ahead,
    double dl_carrier,double ul_carrier,double fo_rate,ntn_tx_prediction *out)
{
  if(!c||!out||!c->anchored||c->n<2||c->pci!=pci||!isfinite(fs)||fs<=0
      ||!isfinite(max_age)||max_age<=0||!isfinite(max_ahead)||max_ahead<=0
      ||!isfinite(dl_carrier)||dl_carrier<=0||!isfinite(ul_carrier)||ul_carrier<=0
      ||!isfinite(fo_rate))return false;
  const ntn_tx_observation *last=&c->h[c->n-1];double age,wa,aq;
  if(!ntn_tx_diff(q_rx,last->q,&age)||age/fs<-.001||age/fs>max_age
      ||!ntn_tx_diff(raw_write,last->a,&wa)||!ntn_tx_diff(last->a,last->q,&aq))return false;
  double slope,curve;bool quadratic=ntn_tx_fit(c,fs,&slope,&curve);
  double delay=aq-c->clock_offset;
  double dt=(wa+delay)/fs;
  for(int i=0;i<8;i++){
    double d=aq-c->clock_offset+slope*dt+curve*dt*dt;
    double derivative=1-(slope+2*curve*dt)/fs;
    if(!isfinite(dt)||dt<0||dt>max_ahead+max_age||!isfinite(d)||d<=0
        ||!isfinite(derivative)||fabs(derivative)<.5)return false;
    dt-=(dt*fs-wa-d)/(fs*derivative);
  }
  delay=aq-c->clock_offset+slope*dt+curve*dt*dt;
  double velocity=(slope+2*curve*dt)/fs;
  double dl=last->fo+fo_rate*dt;
  if(!isfinite(dt)||dt<0||dt>max_ahead+max_age||!isfinite(delay)||delay<=0
      ||!isfinite(velocity)||fabs(velocity)>.1||!isfinite(dl)||fabs(dl)>.01*dl_carrier)return false;
  double ul=ul_carrier*dl/(dl_carrier+dl);
  if(!isfinite(ul))return false;
  *out=(ntn_tx_prediction){0,ul,(double)last->a+dt*fs,delay,quadratic};
  return true;
}
#endif
