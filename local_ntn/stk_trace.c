/* SPDX-License-Identifier: LicenseRef-CSSL-1.0 */
#include "stk_trace.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
bool stk_trace_load(const char *path, stk_trace *trace, char *error, size_t error_size)
{
  FILE *f=fopen(path,"r");
  if (!f) { snprintf(error,error_size,"open: %s",strerror(errno)); return false; }
  char line[4096]; size_t lineno=1, cap=0;
  *trace=(stk_trace){0};
  if (!fgets(line,sizeof(line),f)) goto bad;
  line[strcspn(line,"\r\n")]=0;
  if(strcmp(line,"STKTRACE2"))goto bad;
  while (fgets(line,sizeof(line),f)) {
    lineno++;
    if (line[0]=='#' || line[0]=='\n' || line[0]=='\r') continue;
    double v[22]; char *p=line, *end;
    for (int i=0;i<22;i++) {
      errno=0; v[i]=strtod(p,&end);
      if (end==p || errno || !isfinite(v[i])) goto bad;
      p=end;
      if (i<21) { if (*p!=',') goto bad; p++; }
    }
    while (*p==' ' || *p=='\r' || *p=='\n' || *p=='\t') p++;
    if (*p || (v[20]!=0 && v[20]!=1) || (v[21]!=0 && v[21]!=1)) goto bad;
    /* Earth-orbit experiment bounds: reject finite values that overflow geometry. */
    if(fabs(v[0])>1e12)goto bad;
    for(int i=1;i<=3;i++)if(fabs(v[i])>1e8)goto bad;
    for(int i=4;i<=6;i++)if(fabs(v[i])>20000)goto bad;
    for(int i=7;i<=9;i++)if(fabs(v[i])>100)goto bad;
    for(int i=10;i<=15;i++)if(fabs(v[i])>1e7)goto bad;
    for(int i=16;i<=19;i++)if(fabs(v[i])>1000)goto bad;
    if(trace->count>=1000000)goto bad;
    stk_trace_row r={.time=v[0],.dl_power=v[16],.ul_power=v[17],
      .dl_cn=v[18],.ul_cn=v[19],.dl_valid=v[20],.ul_valid=v[21]};
    for(int i=0;i<3;i++) {
      r.pos[i]=v[1+i];r.vel[i]=v[4+i];r.acc[i]=v[7+i];r.gnb[i]=v[10+i];r.ue[i]=v[13+i];
    }
    if (trace->count) {
      double dt=r.time-trace->rows[trace->count-1].time;
      if(dt<1e-6 || dt>60)goto bad;
    }
    if (trace->count==cap) {
      cap=cap?cap*2:1024;
      void *q=realloc(trace->rows,cap*sizeof(r));
      if(!q) goto bad;
      trace->rows=q;
    }
    trace->rows[trace->count++]=r;
  }
  if (ferror(f) || trace->count<2) goto bad;
  fclose(f); return true;
bad:
  snprintf(error,error_size,"invalid STKTRACE2 at line %zu",lineno);
  free(trace->rows); *trace=(stk_trace){0}; fclose(f); return false;
}
bool stk_trace_at(const stk_trace *trace, double time, stk_trace_row *out)
{
  if (trace->count<2 || time<trace->rows[0].time || time>trace->rows[trace->count-1].time)
    return false;
  size_t lo=0,hi=trace->count-1;
  while (hi-lo>1) {size_t m=(lo+hi)/2;if(trace->rows[m].time<=time)lo=m;else hi=m;}
  return stk_trace_interpolate(&trace->rows[lo],&trace->rows[hi],time,out);
}
