#include <assert.h>
#include <stdio.h>
#include "stk_timing_assist.h"
int main(void) {
  stk_timing_tracker s={0};int shift=999,sum=0;double fs=7680000;
  assert(stk_timing_step(&s,0,15,false,fs,2000,&shift)==0);
  for(int i=1;i<=100;i++) {
    assert(stk_timing_step(&s,i*.01,15+i*.25/fs*1000,true,fs,2000,&shift)==1);
    sum+=shift;assert(fabs(s.remainder)<=.50000001);
  }
  assert(sum==-25);
  s=(stk_timing_tracker){0};
  assert(stk_timing_step(&s,0,15,false,fs,2000,&shift)==0);
  assert(stk_timing_step(&s,.01,14.99,true,fs,2000,&shift)==1 && shift==77);
  assert(stk_timing_step(&s,.02,30,true,fs,2000,&shift)==-1);
  assert(stk_timing_step(&s,1,14,true,fs,2000,&shift)==0);
  assert(stk_timing_step(&s,NAN,14,true,fs,2000,&shift)==-1);
  assert(stk_timing_step(&s,1.01,14.1,false,fs,2000,&shift)==0);
  puts("PASS timing feedforward: fractional accumulation, sign, stale reset, inactive baseline and safety bounds");
}
