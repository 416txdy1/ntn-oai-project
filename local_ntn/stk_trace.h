/* SPDX-License-Identifier: LicenseRef-CSSL-1.0 */
#ifndef OAI_STK_TRACE_H
#define OAI_STK_TRACE_H
#include <math.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
typedef struct {
  double time, pos[3], vel[3], acc[3], gnb[3], ue[3];
  double dl_power, ul_power, dl_cn, ul_cn;
  int dl_valid, ul_valid;
} stk_trace_row;
typedef struct { stk_trace_row *rows; size_t count; } stk_trace;
static inline double stk_trace_epoch(double epoch, uint64_t timestamp, double fs, double rate)
{ return epoch + (double)timestamp / fs * rate; }
static inline double stk_trace_amplitude(double power, double reference, int valid)
{ return valid ? pow(10.0, (power-reference)/20.0) : 0.0; }
/* Cubic Hermite: velocity is exactly the derivative of interpolated position. */
static inline bool stk_trace_interpolate(const stk_trace_row *a, const stk_trace_row *b,
                                        double time, stk_trace_row *out)
{
  double h=b->time-a->time;
  if (!(h>0) || time<a->time || time>b->time || !isfinite(time)) return false;
  double u=(time-a->time)/h, u2=u*u, u3=u2*u;
  *out=*a; out->time=time;
  for (int i=0;i<3;i++) {
    out->pos[i]=(2*u3-3*u2+1)*a->pos[i]+(u3-2*u2+u)*h*a->vel[i]
                +(-2*u3+3*u2)*b->pos[i]+(u3-u2)*h*b->vel[i];
    out->vel[i]=((6*u2-6*u)*a->pos[i]+(-6*u2+6*u)*b->pos[i])/h
                +(3*u2-4*u+1)*a->vel[i]+(3*u2-2*u)*b->vel[i];
    out->acc[i]=((12*u-6)*a->pos[i]+(-12*u+6)*b->pos[i])/(h*h)
                +((6*u-4)*a->vel[i]+(6*u-2)*b->vel[i])/h;
    out->gnb[i]=a->gnb[i]+u*(b->gnb[i]-a->gnb[i]);
    out->ue[i]=a->ue[i]+u*(b->ue[i]-a->ue[i]);
  }
  out->dl_power=a->dl_power+u*(b->dl_power-a->dl_power);
  out->ul_power=a->ul_power+u*(b->ul_power-a->ul_power);
  out->dl_cn=a->dl_cn+u*(b->dl_cn-a->dl_cn);
  out->ul_cn=a->ul_cn+u*(b->ul_cn-a->ul_cn);
  out->dl_valid=a->dl_valid && b->dl_valid;
  out->ul_valid=a->ul_valid && b->ul_valid;
  return true;
}
bool stk_trace_load(const char *path, stk_trace *trace, char *error, size_t error_size);
bool stk_trace_at(const stk_trace *trace, double time, stk_trace_row *out);
#endif
