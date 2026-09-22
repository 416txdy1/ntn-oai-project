/* Real trace interpolation and numeric-channel contract tests. */
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "stk_trace.h"
int main(void) {
  stk_trace_row a={.time=100}, b={.time=102}, out;
  a.pos[0]=7000000; b.pos[0]=7000200;
  a.vel[0]=b.vel[0]=100;
  a.dl_power=-100; b.dl_power=-110;
  a.ul_power=b.ul_power=-100;
  a.dl_cn=b.dl_cn=20; a.ul_cn=b.ul_cn=20;
  a.dl_valid=b.dl_valid=a.ul_valid=b.ul_valid=1;
  assert(stk_trace_interpolate(&a,&b,101,&out));
  assert(fabs(out.pos[0]-7000100)<1e-6);
  assert(fabs(out.vel[0]-100)<1e-8);
  assert(fabs(out.acc[0])<1e-8);
  assert(fabs(out.dl_power+105)<1e-8);
  assert(!stk_trace_interpolate(&a,&b,99,&out));
  /* A 10 dB received-power drop must change squared IQ amplitude by 0.1. */
  double amp=stk_trace_amplitude(-110,-100,1);
  assert(fabs(amp*amp-0.1)<1e-12);
  assert(stk_trace_amplitude(-100,-100,0)==0);
  /* Same sample timestamp, regardless of call order/wall delay. */
  assert(fabs(stk_trace_epoch(100,15360000,15360000,0.1)-100.1)<1e-10);
  assert(stk_trace_epoch(100,99999999,15360000,0)==100);
  b.dl_valid=0;
  assert(stk_trace_interpolate(&a,&b,101,&out) && out.dl_valid==0);
  puts("PASS: sample clock, Hermite derivative, power-to-IQ and outage contracts");
}
