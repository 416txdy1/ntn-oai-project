/* 对实际输入做 A/B：只允许合成过渡的载波速度改变，位置和功率必须逐点相同。 */
#include "stk_trace.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv) {
  assert(argc==2);char error[256];stk_trace old={0},fixed={0};
  setenv("OAI_STK_TRACE_INTERPOLATION","hermite",1);
  assert(stk_trace_load(argv[1],&old,error,sizeof(error)));
  setenv("OAI_STK_TRACE_INTERPOLATION","blend-aware",1);
  assert(stk_trace_load(argv[1],&fixed,error,sizeof(error)));
  size_t blend_points=0;double max_old_speed=0,max_new_speed=0,max_old_doppler=0,max_new_doppler=0;
  for(size_t k=0;k+1<old.count;k++)for(int j=0;j<1000;j++) {
    double time=old.rows[k].time+(old.rows[k+1].time-old.rows[k].time)*j/1000.;
    stk_trace_row a,b;assert(stk_trace_at(&old,time,&a));assert(stk_trace_at(&fixed,time,&b));
    double va=0,vb=0,ra=0,pa=0,pb=0;
    for(int i=0;i<3;i++) {
      assert(a.pos[i]==b.pos[i]);assert(a.path_velocity[i]==b.path_velocity[i]);
      if(!b.synthetic_blend)assert(a.vel[i]==b.vel[i]);
      va+=a.vel[i]*a.vel[i];vb+=b.vel[i]*b.vel[i];
      double d=a.pos[i]-a.ue[i];ra+=d*d;pa+=d*a.vel[i];pb+=d*b.vel[i];
    }
    assert(a.dl_power==b.dl_power && a.ul_power==b.ul_power && a.dl_cn==b.dl_cn && a.ul_cn==b.ul_cn);
    assert(a.dl_valid==b.dl_valid && a.ul_valid==b.ul_valid);
    if(b.synthetic_blend)blend_points++;
    max_old_speed=fmax(max_old_speed,sqrt(va));max_new_speed=fmax(max_new_speed,sqrt(vb));
    double v1=pa/sqrt(ra),v2=pb/sqrt(ra);
    max_old_doppler=fmax(max_old_doppler,fabs(-v1/(299792458.+v1)*2488400000.));
    max_new_doppler=fmax(max_new_doppler,fabs(-v2/(299792458.+v2)*2488400000.));
  }
  assert(blend_points==4000);assert(max_old_speed>1000000);assert(max_new_speed<20000);
  printf("PASS blend A/B: points=%zu old_speed=%.3f new_speed=%.3f m/s old_DL=%.3f new_DL=%.3f Hz; positions/powers/flags unchanged\n",blend_points,max_old_speed,max_new_speed,max_old_doppler,max_new_doppler);
  free(old.rows);free(fixed.rows);
}
