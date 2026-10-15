#include "nr_ntn_tx_predictor.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
static double fs=7680000,dl=2488400000,ul=1614900000;
static double delay(double t,double v,double acc){return fs*(.022+v*t+acc*t*t);}
static double actual(double nominal,uint64_t base,double offset,double v,double acc)
{
 double a=nominal+fs*.022;
 for(int j=0;j<12;j++){double t=(a-(double)base)/fs;double derivative=1-v-2*acc*t;a-=(a-offset-delay(t,v,acc)-nominal)/derivative;}
 return a;
}
static int checks;
static void smooth(uint64_t base,double velocity,double curvature,int noisy)
{
 ntn_tx_clock c={0};double offset=1234.25,fo0=-37350,rate=13250;
 double worst=0;
 for(int i=0;i<40;i++){
  double t=i*.02;uint64_t a=base+(uint64_t)llround(t*fs);double measured_q=(double)a-offset-delay(t,velocity,curvature);
  int noise=noisy?((i*37+19)%5-2):0;uint64_t q=(uint64_t)llround(measured_q)+noise;
  assert(ntn_tx_observe(&c,0,a,q,fo0+rate*t,fs));
  if(!c.anchored && c.n==NTN_TX_HISTORY){uint64_t epoch=q+(uint64_t)llround(.083*fs);double epoch_t=((double)epoch+offset-(double)base)/fs;assert(ntn_tx_anchor(&c,epoch,delay(epoch_t,velocity,curvature),fs));}
  if(!c.anchored)continue;
  uint64_t qrx=q+(uint64_t)llround(fs*.006),qtx=qrx+(uint64_t)llround(fs*.083);
  double arx=actual(qrx,base,offset,velocity,curvature);ntn_tx_prediction result={0};
  assert(ntn_tx_predict(&c,0,(uint64_t)llround(arx),qrx,qtx,fs,.020,.100,100,0,dl,ul,rate,&result));
  double expected_arrival=(double)qtx+offset-100;
  double t_arrival=(expected_arrival-(double)base)/fs;
  double desired_ta=delay((arx-(double)base)/fs,velocity,curvature)+delay(t_arrival,velocity,curvature);
  double error=fabs(result.ta_samples-desired_ta);if(error>worst)worst=error;
  assert(error<20);assert(fabs(result.arrival_sample-expected_arrival)<16);
  double true_dl=fo0+rate*t_arrival,true_ul=ul*true_dl/(dl+true_dl);
  assert(fabs(result.total_ul_fo-true_ul)<.05);
  ++checks;
 }
 assert(c.anchored);printf("smooth base=%llu v=%.6f curve=%.6f noisy=%d max_ta_error_samples=%.6f\n",(unsigned long long)base,velocity,curvature,noisy,worst);
 ntn_tx_clock before=c;ntn_tx_observation last=c.h[c.n-1];
 assert(!ntn_tx_observe(&c,0,last.a,last.q,0,fs));assert(!memcmp(&before,&c,sizeof(c)));
 assert(!ntn_tx_observe(&c,0,last.a+7680,last.q+7680,NAN,fs));assert(!memcmp(&before,&c,sizeof(c)));
 ntn_tx_prediction sentinel={123,456,789,10,true},out=sentinel;
 assert(!ntn_tx_predict(&c,0,last.a,last.q+fs*.021,last.q+fs*.1,fs,.020,.100,100,0,dl,ul,rate,&out));assert(!memcmp(&out,&sentinel,sizeof(out)));
 assert(!ntn_tx_predict(&c,1,last.a,last.q,last.q+fs*.083,fs,.020,.100,100,0,dl,ul,rate,&out));assert(!memcmp(&out,&sentinel,sizeof(out)));
 assert(!ntn_tx_predict(&c,0,last.a,last.q,last.q+fs*.2,fs,.020,.100,100,0,dl,ul,rate,&out));
 assert(!ntn_tx_anchor(&c,last.q,10,fs));assert(!memcmp(&before,&c,sizeof(c)));
 /* Abrupt measured change resets only fit history and retains serving anchor. */
 assert(ntn_tx_observe(&c,0,last.a+153600,last.q+153600+1000,1,fs));assert(c.n==1&&c.anchored);
 assert(ntn_tx_observe(&c,0,last.a+307200,last.q+307200+2000,2,fs));assert(c.n==2&&c.anchored);
 assert(ntn_tx_observe(&c,1,last.a+460800,last.q+460800+3000,3,fs));assert(c.n==1&&!c.anchored&&c.pci==1);
 checks+=10;
}
int main(void)
{
 uint64_t bases[]={76800000ULL,2147483644ULL,4294967292ULL,1099511627772ULL};
 for(unsigned i=0;i<sizeof(bases)/sizeof(bases[0]);i++)
  for(int noise=0;noise<=1;noise++){
   smooth(bases[i],.00003,0,noise);
   smooth(bases[i],-.002725,.002,noise);
  }
 puts("TX_CANDIDATE_MATH_PASS");printf("asserted_samples_and_controls=%d\n",checks);return 0;
}
