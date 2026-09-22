#include "stk_trace.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv) {
  assert(argc==3);stk_trace t={0};char error[256];
  bool ok=stk_trace_load(argv[1],&t,error,sizeof(error));
  if(ok!=(atoi(argv[2])!=0)){fprintf(stderr,"Unexpected parse result: %s accepted=%d\n",argv[1],ok);return 1;}
  free(t.rows);return 0;
}
