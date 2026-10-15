/* SPDX-License-Identifier: LicenseRef-CSSL-1.0 */
#ifndef NR_NTN_RX_TRACKER_H
#define NR_NTN_RX_TRACKER_H
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <limits.h>
#include "PHY/NR_REFSIG/pss_nr.h"
#include "PHY/NR_REFSIG/sss_nr.h"
#include "PHY/NR_REFSIG/nr_refsig.h"
#include "PHY/nr_phy_common/inc/nr_phy_common.h"

#define NR_NTN_RX_ANTS 8
#define NR_NTN_PSS_WINDOW 512
#define NR_NTN_DIAG_PSS_LIMIT 4000U
#define NR_NTN_DIAG_UL_LIMIT 70000U
#define NR_NTN_DIAG_UL_STRIDE 10U
/* Job-owned original IQ. No worker reads mutable receiver tracker state. */
typedef struct nr_ntn_rx_snapshot_s {
  bool active;
  int antennas;
  int length;
  int64_t logical_begin;
  uint64_t native_begin;
  uint64_t nominal_slot;
  uint64_t observed_sample;
  int32_t fft_delta;
  double total_fo;
  c16_t *iq[NR_NTN_RX_ANTS];
} nr_ntn_rx_snapshot;

typedef struct {
  bool valid;
  uint64_t begin, end;
  int antennas, capacity, length;
  c16_t *iq[NR_NTN_RX_ANTS];
} nr_ntn_rx_history;

typedef struct {
  bool valid, has_rate;
  int pci;
  uint64_t a_ref, q_ref, a_last, q_last;
  double e_ref, e_last, rate_samples_s, total_fo, fo_rate_hz_s;
} nr_ntn_rx_tracker;

static inline bool nr_ntn_new_profile(void)
{
  const char *profile = getenv("OAI_NTN_PROFILE");
  return profile && (!strcmp(profile,"integrated-handover") || !strcmp(profile,"legacy-handover"));
}
static inline bool nr_ntn_rx_enabled(void)
{
  const char *flag = getenv("OAI_NTN_RX_TRACKER");
  return nr_ntn_new_profile() && (!flag || !strcmp(flag,"1"));
}
static inline bool nr_ntn_timing_diag_enabled(void)
{
  const char *flag = getenv("OAI_NTN_TIMING_DIAG");
  return nr_ntn_new_profile() && flag && !strcmp(flag,"1");
}
static inline bool nr_ntn_diag_stride(unsigned call, unsigned limit, unsigned stride)
{
  return stride && call && call <= limit && (call - 1) % stride == 0;
}
static inline bool nr_ntn_diag_reserve(bool enabled, unsigned *sequence, unsigned limit)
{
  if (!enabled || !sequence || *sequence >= limit) return false;
  ++*sequence;
  return true;
}
/* Diagnostic window uses the actual RF sample clock, never STK geometry. */
static inline bool nr_ntn_diag_start_value(const char *value, unsigned *start)
{
  if (!start) return false;
  *start = 0;
  if (!value || !*value) return true;
  unsigned count = 0, result = 0;
  for (const char *p = value; *p; ++p) {
    if (*p < '0' || *p > '9' || ++count > 3) return false;
    result = result * 10 + (unsigned)(*p - '0');
  }
  if (result > 620) return false;
  *start = result;
  return true;
}
static inline bool nr_ntn_diag_in_window(uint64_t sample, double fs, unsigned start)
{
  return isfinite(fs) && fs > 0 && start <= 620
      && (long double)sample >= (long double)start * (long double)fs;
}
static inline bool nr_ntn_diag_at(uint64_t sample, double fs)
{
  unsigned start;
  return nr_ntn_diag_start_value(getenv("OAI_NTN_TIMING_DIAG_START_IQ_S"), &start)
      && nr_ntn_diag_in_window(sample, fs, start);
}

static inline bool nr_ntn_sample_diff(uint64_t a,uint64_t b,int64_t *out)
{
  uint64_t magnitude=a>=b?a-b:b-a;
  if(magnitude>(uint64_t)INT64_MAX) return false;
  *out=a>=b?(int64_t)magnitude:-(int64_t)magnitude;
  return true;
}

static inline void nr_ntn_history_clear(nr_ntn_rx_history *h)
{
  h->valid=false;h->length=0;h->begin=h->end=0;
}
static inline void nr_ntn_history_destroy(nr_ntn_rx_history *h)
{
  for(int a=0;a<NR_NTN_RX_ANTS;a++)free(h->iq[a]);
  memset(h,0,sizeof(*h));
}
static inline bool nr_ntn_history_append(nr_ntn_rx_history *h,c16_t **input,
                                        int antennas,uint64_t timestamp,int count,int capacity)
{
  if(!input || antennas<1 || antennas>NR_NTN_RX_ANTS || count<1 || count>capacity
      || capacity<1 || timestamp>UINT64_MAX-(uint64_t)count) return false;
  for(int a=0;a<antennas;a++)if(!input[a])return false;
  if(h->capacity!=capacity || h->antennas!=antennas){
    nr_ntn_history_destroy(h);h->capacity=capacity;h->antennas=antennas;
    for(int a=0;a<antennas;a++){
      h->iq[a]=malloc16_clear(sizeof(c16_t)*(size_t)capacity);
      if(!h->iq[a]){nr_ntn_history_destroy(h);return false;}
    }
  }
  bool contiguous=!h->valid || timestamp==h->end;
  if(!contiguous)nr_ntn_history_clear(h);
  if(!h->valid){h->begin=timestamp;h->length=0;h->valid=true;}
  int drop=h->length+count>capacity?h->length+count-capacity:0;
  for(int a=0;a<antennas;a++){
    if(drop)memmove(h->iq[a],h->iq[a]+drop,sizeof(c16_t)*(size_t)(h->length-drop));
    memcpy(h->iq[a]+h->length-drop,input[a],sizeof(c16_t)*(size_t)count);
  }
  h->length=h->length-drop+count;h->begin+=drop;h->end=timestamp+count;
  return contiguous;
}
static inline void nr_ntn_snapshot_free(const nr_ntn_rx_snapshot *s)
{
  if(!s)return;
  for(int a=0;a<s->antennas;a++)free(s->iq[a]);
  free((void*)s);
}
static inline nr_ntn_rx_snapshot *nr_ntn_snapshot_copy(const nr_ntn_rx_history *h,
                                                       uint64_t slot_native,int slot_logical,
                                                       uint64_t nominal_slot,int slot_samples)
{
  if(!h->valid || slot_native<h->begin || slot_native>=h->end || slot_samples<1) return NULL;
  uint64_t lo=slot_native>(uint64_t)NR_NTN_PSS_WINDOW?slot_native-NR_NTN_PSS_WINDOW:0;
  if(lo<h->begin)lo=h->begin;
  uint64_t extra=(uint64_t)slot_samples+NR_NTN_PSS_WINDOW;
  if(slot_native>UINT64_MAX-extra)return NULL;
  uint64_t hi=slot_native+extra;if(hi>h->end)hi=h->end;
  if(hi<=lo || hi-lo>INT_MAX)return NULL;
  int64_t delta;if(!nr_ntn_sample_diff(lo,slot_native,&delta))return NULL;
  nr_ntn_rx_snapshot *s=calloc(1,sizeof(*s));if(!s)return NULL;
  s->antennas=h->antennas;s->length=(int)(hi-lo);s->logical_begin=(int64_t)slot_logical+delta;
  s->native_begin=lo;s->nominal_slot=nominal_slot;
  for(int a=0;a<s->antennas;a++){
    s->iq[a]=malloc16_clear(sizeof(c16_t)*(size_t)s->length);
    if(!s->iq[a]){nr_ntn_snapshot_free(s);return NULL;}
    memcpy(s->iq[a],h->iq[a]+(size_t)(lo-h->begin),sizeof(c16_t)*(size_t)s->length);
  }
  return s;
}

static inline int64_t nr_ntn_fft_begin(const NR_DL_FRAME_PARMS *fp,int slot,int symbol,bool synchronized)
{
  int64_t p=get_samples_slot_timestamp(fp,slot)+(int64_t)symbol*fp->ofdm_symbol_size;
  for(int j=slot*fp->symbols_per_slot;j<=slot*fp->symbols_per_slot+symbol;j++)
    p+=(j%(7<<fp->numerology_index) || !synchronized)?fp->nb_prefix_samples:fp->nb_prefix_samples0;
  return p-fp->nb_prefix_samples/fp->ofdm_offset_divisor;
}
static inline bool nr_ntn_span_index(const nr_ntn_rx_snapshot *s,int64_t begin,int size,int *index)
{
  if(!s || size<1 || begin<s->logical_begin)return false;
  uint64_t offset=(uint64_t)(begin-s->logical_begin);
  if(offset>(uint64_t)s->length || (uint64_t)size>(uint64_t)s->length-offset)return false;
  *index=(int)offset;return true;
}

/* Errors retain the first measured offset; timestamps remain wide and unreset. */
static inline bool nr_ntn_tracker_observe(nr_ntn_rx_tracker *t,int pci,uint64_t a,uint64_t q,
                                         double consumed,double delta,double measured_t,double fs)
{
  if(!isfinite(consumed)||!isfinite(delta)||!isfinite(measured_t)||!isfinite(fs)||fs<=0)return false;
  if(!t->valid || t->pci!=pci){
    *t=(nr_ntn_rx_tracker){.valid=true,.pci=pci,.a_ref=a,.q_ref=q,.a_last=a,.q_last=q,
      .e_ref=consumed+delta,.e_last=consumed+delta,.total_fo=measured_t};
    return true;
  }
  int64_t da,dq,da_last,dq_last;
  if(!nr_ntn_sample_diff(a,t->a_ref,&da)||!nr_ntn_sample_diff(q,t->q_ref,&dq)
      ||!nr_ntn_sample_diff(a,t->a_last,&da_last)||!nr_ntn_sample_diff(q,t->q_last,&dq_last)
      || da_last<=0 || dq_last<=0)return false;
  double e=t->e_ref+(double)da-(double)dq;
  double v=(e-t->e_last)*fs/(double)dq_last;
  double f=(measured_t-t->total_fo)*fs/(double)da_last;
  if(!isfinite(e)||!isfinite(v)||!isfinite(f))return false;
  t->e_last=e;t->rate_samples_s=v;t->fo_rate_hz_s=f;t->total_fo=measured_t;
  t->a_last=a;t->q_last=q;t->has_rate=true;
  return true;
}
static inline bool nr_ntn_tracker_predict(const nr_ntn_rx_tracker *t,int pci,uint64_t q,
                                         uint64_t max_hold,double fs,double *error,double *fo)
{
  if(!t->valid || t->pci!=pci || !isfinite(fs)||fs<=0)return false;
  int64_t dq;if(!nr_ntn_sample_diff(q,t->q_last,&dq)||dq<0||(uint64_t)dq>max_hold)return false;
  double dt=(double)dq/fs;
  *error=t->e_last+t->rate_samples_s*dt;*fo=t->total_fo+t->fo_rate_hz_s*dt;
  return isfinite(*error)&&isfinite(*fo);
}
/* Production FFT primitive, also used by the unchanged legacy FEP. */
void nr_symbol_fep(const NR_DL_FRAME_PARMS *fp, int slot, unsigned char symbol,
                   int linktype, c16_t *in[fp->nb_antennas_rx],
                   c16_t *out[fp->nb_antennas_rx], time_stats_t *stats);

typedef struct {
  bool accepted;
  int32_t delta;
  uint64_t observed_sample;
  double total_fo;
  int reason, pss_pos, pss_peak, pss_avg, pss_fo, sss_metric, sss_pci, sss_fo;
} nr_ntn_pilot;

/* Known-cell measurements use only original observed IQ and current receiver T. */
static inline nr_ntn_pilot nr_ntn_measure_pilot(const NR_DL_FRAME_PARMS *fp,
                                               const nr_ntn_rx_snapshot *s,
                                               int ssb_symbol, int pci, double current_t)
{
  nr_ntn_pilot r = {.reason=1,.sss_pci=-1};
  if (!fp || !s || !isfinite(current_t) || fp->ofdm_symbol_size <= 0
      || fp->ofdm_symbol_size > 4096 || fp->samples_per_subframe <= 0
      || fp->ofdm_offset_divisor == 0 || fp->nb_antennas_rx < 1
      || fp->nb_antennas_rx > NR_NTN_RX_ANTS || s->antennas != fp->nb_antennas_rx
      || ssb_symbol < 0 || ssb_symbol + 3 >= fp->symbols_per_slot * fp->slots_per_frame
      || pci < 0 || pci > 1007) return r;
  const int fft = fp->ofdm_symbol_size, ants = fp->nb_antennas_rx;
  const int slot = ssb_symbol / fp->symbols_per_slot;
  const int symbol = ssb_symbol % fp->symbols_per_slot;
  const int64_t nominal = nr_ntn_fft_begin(fp, slot, symbol, true)
                          + fp->nb_prefix_samples / fp->ofdm_offset_divisor;
  /* Align the local PSS search grid; every candidate has a real FFT-length tail. */
  const int64_t start = (nominal - NR_NTN_PSS_WINDOW) & ~(int64_t)3;
  const int span = 2 * NR_NTN_PSS_WINDOW + 1, size = span + fft - 1;
  int begin;
  if (!nr_ntn_span_index(s, start, size, &begin)) { r.reason=2; return r; }
  c16_t pss_time[NUMBER_PSS_SEQUENCE][fft] __attribute__((aligned(32)));
  for (int n = 0; n < NUMBER_PSS_SEQUENCE; ++n)
    generate_pss_nr_time(fft, fp->first_carrier_offset, n, fp->ssb_start_subcarrier, pss_time[n]);
  c16_t *window[ants];
  memset(window, 0, sizeof(window));
  for (int a = 0; a < ants; ++a) {
    if (!s->iq[a] || posix_memalign((void **)&window[a], 32, sizeof(c16_t) * size) != 0) {
      for (int k = 0; k < ants; ++k) free(window[k]);
      return r;
    }
    nr_fo_compensation(current_t, fp->samples_per_subframe, begin,
                       s->iq[a] + begin, window[a], size);
  }
  pss_search_t query = {.rxdata = window, .nb_antennas_rx = ants,
    .rxdata_length = span, .ofdm_symbol_size = fft,
    .subcarrier_spacing = fp->subcarrier_spacing, .fo_flag = true,
    .target_Nid_cell = pci, .pssTime = &pss_time[0][0]};
  pss_detection_result_t pss = pss_search_time_nr(&query);
  r.pss_pos=pss.pos;r.pss_peak=pss.peak;r.pss_avg=pss.avg;r.pss_fo=pss.freq_offset;
  for (int a = 0; a < ants; ++a) free(window[a]);
  if (!pss.success) { r.reason=3; return r; }
  if (pss.pos <= 4 || pss.pos >= span - 5) { r.reason=4; return r; }
  const int64_t delta = start + pss.pos - nominal;
  int offsets[NR_N_SYMBOLS_SSB];
  for (int j = 0; j < NR_N_SYMBOLS_SSB; ++j) {
    int physical = ssb_symbol + j;
    if (!nr_ntn_span_index(s, nr_ntn_fft_begin(fp, physical / fp->symbols_per_slot,
                                              physical % fp->symbols_per_slot, true) + delta,
                           fft, &offsets[j])) { r.reason=5; return r; }
  }
  c16_t rel[NR_N_SYMBOLS_SSB][ants][fft] __attribute__((aligned(32)));
  c16_t work[ants][fft] __attribute__((aligned(32)));
  c16_t *in[ants], *out[ants];
  for (int j = 0; j < NR_N_SYMBOLS_SSB; ++j) {
    for (int a = 0; a < ants; ++a) {
      nr_fo_compensation(current_t + pss.freq_offset, fp->samples_per_subframe,
                         offsets[j], s->iq[a] + offsets[j], work[a], fft);
      in[a] = work[a]; out[a] = rel[j][a];
    }
    const int physical = ssb_symbol + j;
    nr_symbol_fep(fp, physical / fp->symbols_per_slot, physical % fp->symbols_per_slot,
                   link_type_dl, in, out, NULL);
  }
  nr_sss_params_t params = {.nb_antennas_rx = ants,
    .samples_per_slot_wCP = fp->samples_per_slot_wCP, .ofdm_symbol_size = fft,
    .first_carrier_offset = fp->first_carrier_offset,
    .ssb_start_subcarrier = fp->ssb_start_subcarrier, .subcarrier_spacing = fp->subcarrier_spacing};
  sss_detection_result_t sss = rx_sss_nr(&params, &pss, -1, rel);
  r.sss_metric=sss.metric;r.sss_pci=sss.nid_cell;r.sss_fo=sss.freq_offset;
  const double measured = current_t + pss.freq_offset + sss.freq_offset;
  const int64_t observed_index = start + pss.pos - s->logical_begin;
  if (!sss.success) { r.reason=6; return r; }
  if (sss.nid_cell != pci) { r.reason=7; return r; }
  r.reason=8;
  if (!isfinite(measured) || observed_index < 0
      || UINT64_MAX - s->native_begin < (uint64_t)observed_index) return r;
  r.accepted = true; r.reason=0; r.delta = (int32_t)delta; r.total_fo = measured;
  r.observed_sample = s->native_begin + (uint64_t)observed_index;
  return r;
}
/* Half-open union of the four actual SSB FFT input intervals, in RF absolute samples.
 * nrue_ru_read subtracts device.firstTS. Main records that offset without an STK query.
 * A missing span is invalid, never a guessed SFN or wall-time conversion. */
static inline bool nr_ntn_pbch_span(const NR_DL_FRAME_PARMS *fp,int slot,int last_symbol,
                                    int64_t logical_begin,uint64_t rf_begin,int length,int delta,
                                    uint64_t *begin,uint64_t *end)
{
  if(!fp || !begin || !end || !fp->ofdm_offset_divisor || fp->ofdm_symbol_size<=0
      || fp->symbols_per_slot<=0 || slot<0 || slot>=fp->slots_per_frame
      || last_symbol<0 || last_symbol>=fp->symbols_per_slot || length<1)return false;
  nr_ntn_rx_snapshot span={.logical_begin=logical_begin,.length=length};
  uint64_t first=UINT64_MAX,finish=0;
  for(int j=0;j<NR_N_SYMBOLS_SSB;j++){
    int physical=slot*fp->symbols_per_slot+last_symbol-3+j;
    if(physical<0)return false;
    int index;
    if(!nr_ntn_span_index(&span,nr_ntn_fft_begin(fp,physical/fp->symbols_per_slot,
                                              physical%fp->symbols_per_slot,true)+delta,
                         fp->ofdm_symbol_size,&index))return false;
    if(rf_begin>UINT64_MAX-(uint64_t)index-(uint64_t)fp->ofdm_symbol_size)return false;
    uint64_t a=rf_begin+(uint64_t)index,b=a+fp->ofdm_symbol_size;
    if (a < first) first = a;
    if (b > finish) finish = b;
  }
  *begin=first;*end=finish;return true;
}
#endif
