#include "stk_trace.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
static void near(double a,double b) { assert(fabs(a-b)<1e-8); }
int main(int argc,char **argv) {
  assert(argc==2);
  stk_trace_row a={.time=0,.pos={100,200,300},.vel={1,2,3},.acc={.2,.3,.4},.gnb={10,20,30},.ue={40,50,60},.dl_power=-120,.ul_power=-117,.dl_cn=20,.ul_cn=14,.dl_valid=1,.ul_valid=1};
  stk_trace_row b={.time=1,.pos={200100,40200,30300},.vel={11,12,13},.acc={.4,.5,.6},.gnb={20,40,60},.ue={80,100,120},.dl_power=-118,.ul_power=-113,.dl_cn=22,.ul_cn=16,.dl_valid=1,.ul_valid=0};
  const double times[]={0,.25,.5,.75,1}, expected_x[]={100,50100,100100,150100,200100}, expected_v[]={1,3.5,6,8.5,11};
  for(int j=0;j<5;j++) {
    double u=times[j];stk_trace_row out;assert(stk_trace_interpolate_linear(&a,&b,u,&out));
    near(out.time,u);near(out.pos[0],expected_x[j]);near(out.vel[0],expected_v[j]);assert(!out.synthetic_blend);
    for(int i=0;i<3;i++) {near(out.acc[i],a.acc[i]+u*.2);near(out.path_velocity[i],out.vel[i]);near(out.gnb[i],a.gnb[i]+u*(b.gnb[i]-a.gnb[i]));near(out.ue[i],a.ue[i]+u*(b.ue[i]-a.ue[i]));}
    near(out.dl_power,-120+2*u);near(out.ul_power,-117+4*u);near(out.dl_cn,20+2*u);near(out.ul_cn,14+2*u);assert(out.dl_valid==1 && out.ul_valid==0);
    stk_trace_row rows[]={a,b}, selected;stk_trace trace={.rows=rows,.count=2,.legacy_linear=true};assert(stk_trace_at(&trace,u,&selected));near(selected.pos[0],expected_x[j]);near(selected.vel[0],expected_v[j]);near(selected.acc[0],out.acc[0]);near(selected.path_velocity[0],expected_v[j]);assert(!selected.synthetic_blend);
  }
  stk_trace_row out;assert(!stk_trace_interpolate_linear(&a,&b,-.1,&out));assert(!stk_trace_interpolate_linear(&a,&b,1.1,&out));assert(!stk_trace_interpolate_linear(&a,&b,NAN,&out));
  stk_trace_row same=b;same.time=0;assert(!stk_trace_interpolate_linear(&a,&same,0,&out));assert(stk_trace_interpolate(&a,&b,.5,&out));assert(fabs(out.vel[0]-6)>10000);
  const char *names[]={"hermite","blend-aware","legacy-linear"};
  for(int mode=0;mode<3;mode++) {assert(setenv("OAI_STK_TRACE_INTERPOLATION",names[mode],1)==0);stk_trace trace;char error[256];assert(stk_trace_load(argv[1],&trace,error,sizeof(error)));assert(trace.blend_aware==(mode==1));assert(trace.legacy_linear==(mode==2));free(trace.rows);}
  assert(setenv("OAI_STK_TRACE_INTERPOLATION","unknown-mode",1)==0);stk_trace trace;char error[256];assert(!stk_trace_load(argv[1],&trace,error,sizeof(error)));assert(!trace.rows && !trace.count);
  puts("PASS legacy independent-field interpolation, mode selection and rejection");return 0;
}
