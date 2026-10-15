from pathlib import Path
import subprocess,json,hashlib,sys
import argparse,tempfile
ap=argparse.ArgumentParser(description="Compile actual UE main/prefix scheduling code; numeric fixture, no live resources")
ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
ap.add_argument('--overlay',type=Path)
ap.add_argument('--output',type=Path)
ap.add_argument('--mutant-lifecycle',action='store_true',help='negative control: restore unconditional reset; expected failure')
args=ap.parse_args();r=args.root.resolve();overlay=(args.overlay or r/'oai_patch/current').resolve()
if args.output:
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=False,mode=0o700)
else:
 (r/'.private').mkdir(exist_ok=True);out=Path(tempfile.mkdtemp(prefix='tx-main-contract-',dir=r/'.private'))
src=overlay/'executables/nr-ue.c';s=src.read_text()
block=s[s.index('    const uint64_t tx_q_rx ='):s.index('    if (curMsg.proc.nr_slot_rx == 0)\n      nr_ue_rrc_timer_trigger')]
a=block.index('    // Calculate TX deadline');b=block.index('    // but use current UE->timing_advance')
block=block[:a]+block[b:]
life_source=s
if args.mutant_lifecycle:
 life_source=life_source.replace('                                                      ignore_timestamp, first_symbols, rx_history_capacity)) {\n          rx_tracker = (nr_ntn_rx_tracker){0};\n          tx_clock = (ntn_tx_clock){0}; tx_sib_pending = false;\n        }','                                                      ignore_timestamp, first_symbols, rx_history_capacity))\n          rx_tracker = (nr_ntn_rx_tracker){0};\n          tx_clock = (ntn_tx_clock){0}; tx_sib_pending = false;')
 assert life_source!=s,'negative control did not mutate source'
life=life_source[life_source.index('        if (use_rx_tracker && !nr_ntn_history_append(&rx_history, UE->common_vars.rxdata'):life_source.index('      } else\n        LOG_E(PHY,"can\'t compensate')]
pre=r'''
#include "nr_ntn_tx_predictor.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
typedef int64_t openair0_timestamp_t;
typedef struct {int slots_per_subframe,samples_per_subframe,slots_per_frame,samples_per_frame,Nid_cell;double dl_CarrierFreq,ul_CarrierFreq;} NR_DL_FRAME_PARMS;
typedef struct {int card;} rf_map_t;
typedef struct {rf_map_t rf_map;int N_TA_offset,timing_advance,timing_advance_ntn,next_nta;} ue_t;
typedef struct {bool firstTS_initialized;int64_t firstTS;} openair0_device_t;
typedef struct {double fo_rate_hz_s;} nr_ntn_rx_tracker;
static openair0_device_t openair0_dev[1];
#define IS_SOFTMODEM_RFSIM 1
#define LOG_I(...) ((void)0)
static int determine_N_TA_offset(ue_t *u){return u->next_nta;}
static uint64_t get_samples_per_slot(int slot,const NR_DL_FRAME_PARMS *fp){return fp->samples_per_subframe/fp->slots_per_subframe+(slot%2?-4:4);}
static uint64_t get_samples_slot_timestamp(const NR_DL_FRAME_PARMS *fp,int slot){uint64_t t=0;for(int i=0;i<slot;i++)t+=get_samples_per_slot(i,fp);return t;}
static uint64_t get_samples_slot_duration(const NR_DL_FRAME_PARMS *fp,int slot,int n){uint64_t t=0;for(int i=0;i<n;i++)t+=get_samples_per_slot((slot+i)%fp->slots_per_frame,fp);return t;}
static int nr_ntn_hold_samples(ue_t *u){(void)u;return 153600;}
typedef struct {uint64_t write;int block,used;double arrival,fo;bool valid;} result_t;
static uint64_t payload_start(uint64_t writeTimestamp,int writeBlockSize,int maxWriteBlockSize);
static result_t step(ue_t *UE,NR_DL_FRAME_PARMS *fp,ntn_tx_clock *clock,nr_ntn_rx_tracker rx_tracker,
 int64_t absolute_slot,int duration_rx_to_tx,int64_t rx_timestamp,int firstSymSamp,int iq_shift_to_apply,int *ta){
 bool use_tx_predictor=true,tx_sib_pending=false;
 uint64_t tx_sib_q_epoch=0;double tx_sib_half_ta=0;
 int nb_slot_frame=fp->slots_per_frame,slot_nr=absolute_slot%nb_slot_frame,timing_advance=*ta;
 ntn_tx_clock tx_clock=*clock;
'''
post=r'''
 *ta=timing_advance;*clock=tx_clock;
 (void)tx_next_prediction;
 return (result_t){writeTimestamp,writeBlockSize,tx_used_total_ta,tx_prediction.arrival_sample,tx_prediction.total_ul_fo,tx_prediction_valid};
}
static bool append_ok;
#define nr_ntn_history_append(...) append_ok
static void lifecycle(ntn_tx_clock *clock,bool *pending,nr_ntn_rx_tracker *tracker,bool use_rx_tracker){
 ntn_tx_clock tx_clock=*clock;bool tx_sib_pending=*pending;nr_ntn_rx_tracker rx_tracker=*tracker;
'''
tail=r'''
 *clock=tx_clock;*pending=tx_sib_pending;*tracker=rx_tracker;
}
static const double fs=7680000.,B=1234.,d0=.022*7680000.,fc_dl=2488400000.,fc_ul=1614900000.;
static double velocity,curve,origin;
static double delay(double a){double t=a/fs-origin;return d0+fs*(velocity*t+curve*t*t);}
static double arrival(double w){double a=w+delay(w);for(int j=0;j<16;j++){double t=a/fs-origin;double derivative=1-velocity-2*curve*t;a-=(a-w-delay(a))/derivative;}return a;}
static void fill(ntn_tx_clock *c,uint64_t qrx){
 *c=(ntn_tx_clock){.anchored=true,.pci=0,.clock_offset=B};
 for(int j=6;j>=0;j--){uint64_t q=qrx-(uint64_t)j*153600;double a=arrival((double)q+B);assert(ntn_tx_observe(c,0,llround(a),q,-37350+13250*a/fs,fs));}
 assert(c->n==7&&c->anchored);
}
static void run(int mu,double v,double k,uint64_t base){
 NR_DL_FRAME_PARMS fp={1<<mu,7680,10<<mu,76800,0,2488400000.,1614900000.};
 ue_t u={.N_TA_offset=100,.next_nta=100};
 nr_ntn_rx_tracker tracker={13250};velocity=v;curve=k;origin=base/fs;
 int64_t absolute=base/fp.samples_per_frame*fp.slots_per_frame+fp.slots_per_frame*30;
 uint64_t qrx=(uint64_t)absolute/fp.slots_per_frame*fp.samples_per_frame+get_samples_slot_timestamp(&fp,absolute%fp.slots_per_frame);
 /* The delay time origin remains local while RF clocks cross wide boundaries. */
 double raw=arrival((double)qrx+B);ntn_tx_clock clock;fill(&clock,qrx);
 int duration=83*(1<<mu),ta=llround(raw-qrx-B+delay(qrx+get_samples_slot_duration(&fp,absolute%fp.slots_per_frame,duration)+B-100));
 openair0_dev[0].firstTS=base>4000000000ULL?4294967296ULL:1000000;
 uint64_t device_first=openair0_dev[0].firstTS;
 u.timing_advance_ntn=ta;double previous_end=0,worst=0,worstfo=0,minerr=1e9,maxerr=-1e9;unsigned valid=0;
 for(int i=0;i<300;i++,absolute++){
  int slot=absolute%fp.slots_per_frame;uint64_t rxlen=get_samples_per_slot(slot,&fp);
  qrx=(uint64_t)absolute/fp.slots_per_frame*fp.samples_per_frame+get_samples_slot_timestamp(&fp,slot);
  if(i% (20*(1<<mu))==0)fill(&clock,qrx);
  int shift=slot==fp.slots_per_frame-1?llround(raw+rxlen-arrival(qrx+rxlen+B)):0;
  if(i==120)u.next_nta=104;
  int64_t rawi=llround(raw);int first=slot%2?548:552;
  result_t x=step(&u,&fp,&clock,tracker,absolute,duration,rawi-device_first+first,first,shift,&ta);
  uint64_t qt=qrx+get_samples_slot_duration(&fp,slot,duration);
  if(previous_end)assert(fabs((double)x.write-previous_end)<=1.01);
  int txslot=(absolute+duration)%fp.slots_per_frame;uint64_t txlen=get_samples_per_slot(txslot,&fp);
  double payload=payload_start(x.write,x.block,txlen)+device_first;
  double actual_arrival=arrival(payload),target=(double)qt+B-(i>=121?104:100);
  /* Current slot uses old NTA; next slot uses the new offset. */
  if(i==120)target=(double)qt+B-100;
  double signed_error=actual_arrival-target,error=fabs(signed_error);if(error>worst)worst=error;if(signed_error<minerr)minerr=signed_error;if(signed_error>maxerr)maxerr=signed_error;
  double dl=-37350+13250*actual_arrival/fs,truefo=fc_ul*dl/(fc_dl+dl);
  if(x.valid){valid++;double e=fabs(x.fo-truefo);if(e>worstfo)worstfo=e;assert(e<.1);assert(fabs(x.arrival-actual_arrival)<4);}
  assert(error<12);assert(x.block>0);
  previous_end=x.write+x.block;raw=rawi+rxlen-shift;
 }
 assert(valid>280);printf("main_contract mu=%d v=%.6f curve=%.6g base=%"PRIu64" firstTS=%"PRIu64" valid=%u min_error=%.6f max_error=%.6f max_payload_error_samples=%.6f max_fo_error_hz=%.6f\n",mu,v,k,base,device_first,valid,minerr,maxerr,worst,worstfo);
}
int main(void){
 openair0_dev[0]=(openair0_device_t){true,0};
 ntn_tx_clock c={.anchored=true,.n=7,.pci=0};bool pending=true;nr_ntn_rx_tracker t={123};append_ok=true;
 for(int i=0;i<200;i++){lifecycle(&c,&pending,&t,true);assert(c.anchored&&c.n==7&&pending&&t.fo_rate_hz_s==123);}
 append_ok=false;lifecycle(&c,&pending,&t,true);assert(!c.anchored&&c.n==0&&!pending&&t.fo_rate_hz_s==0);
 c=(ntn_tx_clock){.anchored=true,.n=7};pending=true;lifecycle(&c,&pending,&t,false);assert(c.anchored&&c.n==7&&pending);
 for(int mu=0;mu<=1;mu++){run(mu,-.002725,0,76800000);run(mu,.002725,0,76800000);run(mu,-.002725,.003,76800000);run(mu,.00003,0,2147480000ULL);run(mu,.00003,0,4294960000ULL);}
 puts("ACTUAL_MAIN_AND_PREFIX_CONTRACT_PASS");return 0;
}
'''
# RU_write's original loop is extracted verbatim and compiled independently,
# so test semantics cannot silently drift from real dummy-prefix handling.
ru=s[s.index('  while (writeBlockSize > maxWriteBlockSize) {'):s.index('  // Numeric-only diagnostics:')]
assert 'writeTimestamp += dummyBlockSize' in ru and 'writeBlockSize -= dummyBlockSize' in ru
ru_test='''
#define min(a,b) ((a)<(b)?(a):(b))
#define nrue_ru_write_reorder(...) dummyBlockSize
#define AssertFatal(condition,...) assert(condition)
static uint64_t payload_start(uint64_t writeTimestamp,int writeBlockSize,int maxWriteBlockSize){
'''+ru+'''  return writeTimestamp;
}
'''
(out/'main-contract-extracted.c').write_text(pre+block+post+life+tail+ru_test)
cmd=['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-sign-compare','-pedantic','-O2','-I'+str(overlay/'openair1/PHY/NR_UE_ESTIMATION'),str(out/'main-contract-extracted.c'),'-lm','-o',str(out/'main-contract')]
if args.mutant_lifecycle:cmd.insert(1,'-Wno-misleading-indentation')
proof={'main_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((out/'main-contract-extracted.c').read_bytes()).hexdigest(),'compile_command':cmd}
for name,command in [('compile',cmd),('run',[str(out/'main-contract')])]:
 with (out/('main-contract-'+name+'.log')).open('w') as f:p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
 proof[name+'_exit']=p.returncode;(out/'main-contract-results.json').write_text(json.dumps(proof,indent=2));print(name,p.returncode,flush=True)
 if p.returncode:print((out/('main-contract-'+name+'.log')).read_text()[-5000:]);raise SystemExit(p.returncode)
print((out/'main-contract-run.log').read_text())
math_src=r/'scripts/test_tx_predictor_math.c'
math_cmd=['gcc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O2','-I'+str(overlay/'openair1/PHY/NR_UE_ESTIMATION'),str(math_src),'-lm','-o',str(out/'math')]
for name,command in [('math-compile',math_cmd),('math-run',[str(out/'math')])]:
 with (out/(name+'.log')).open('w') as f:result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
 proof[name]={'command':command,'exit':result.returncode}
 (out/'main-contract-results.json').write_text(json.dumps(proof,indent=2))
 if result.returncode:raise SystemExit(result.returncode)
print('TX_MAIN_AND_MATH_PASS artifacts='+str(out))
