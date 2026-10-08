/* SPDX-License-Identifier: LicenseRef-CSSL-1.0 */
#ifndef STK_TIMING_ASSIST_H
#define STK_TIMING_ASSIST_H
#include <math.h>
#include <stdbool.h>
typedef struct {
  bool valid;
  double time_s, delay_ms, remainder;
} stk_timing_tracker;
/* 返回 1 表示应用前馈，0 表示只记录基准，-1 表示超过安全读块边界。
 * 余数累计保证亚采样量化误差不会在长过渡中累积。 */
static inline int stk_timing_step(stk_timing_tracker *s,double time_s,double delay_ms,
                                  bool synthetic,double fs,int max_shift,int *shift)
{
  if(!isfinite(time_s)||!isfinite(delay_ms)||!isfinite(fs)||fs<=0||delay_ms<0)return -1;
  const double dt=time_s-s->time_s;
  const bool active=s->valid && synthetic && dt>0 && dt<.1;
  const double delta=(delay_ms-s->delay_ms)*fs/1000+s->remainder;
  s->valid=true;s->time_s=time_s;s->delay_ms=delay_ms;
  if(!active){s->remainder=0;return 0;}
  if(!isfinite(delta)||fabs(delta)>max_shift)return -1;
  *shift=-(int)llround(delta);
  s->remainder=delta+*shift;
  return 1;
}
#endif
