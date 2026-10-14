#!/usr/bin/env python3
"""Real PBCH IQ generator/decoder regression; all artifacts are private, no live resources."""
import argparse, hashlib, json, os, re, shlex, subprocess, tempfile
from pathlib import Path

SOURCE_SHA='20eff66e9223caacbf08cd480881b278c244d559bebe419bdae7b5d9a5adab83'
DRIVER_CHANGES=[(96, 96, '', '#include "PHY/NR_UE_ESTIMATION/nr_ntn_rx_tracker.h"\nstatic uint64_t rxfix_hash(c16_t **raw,int ants,int length){uint64_t h=1469598103934665603ULL;for(int a=0;a<ants;a++)for(int j=0;j<length;j++){h=(h^(uint16_t)raw[a][j].r)*1099511628211ULL;h=(h^(uint16_t)raw[a][j].i)*1099511628211ULL;}return h;}\n\ntypedef struct {const NR_DL_FRAME_PARMS *fp;const nr_ntn_rx_snapshot *snapshot;c16_t *output;int result;} fixture_fft_job;\nstatic void *fixture_fft_worker(void *arg){fixture_fft_job *j=arg;j->result=nr_slot_fep_tracked(j->fp,0,2,(c16_t (*)[j->fp->samples_per_slot_wCP])j->output,link_type_dl,j->snapshot);return NULL;}\nstatic void fixture_lifecycle(const NR_DL_FRAME_PARMS *fp,c16_t **raw,int length){\n nr_ntn_rx_history h={0};const uint64_t base=4294967292ULL;\n AssertFatal(nr_ntn_history_append(&h,raw,fp->nb_antennas_rx,base,length,length*2),"history initial append");\n nr_ntn_rx_snapshot *a=nr_ntn_snapshot_copy(&h,base,0,base,get_samples_per_slot(0,fp));\n nr_ntn_rx_snapshot *b=nr_ntn_snapshot_copy(&h,base,0,base,get_samples_per_slot(0,fp));\n AssertFatal(a&&b,"owned snapshots");a->active=b->active=true;a->total_fo=0;b->total_fo=-37350;b->fft_delta=-4;\n const c16_t saved=a->iq[0][0];h.iq[0][0].r^=1;\n AssertFatal(a->iq[0][0].r==saved.r,"job aliases mutable history");\n const size_t bytes=sizeof(c16_t)*fp->nb_antennas_rx*fp->samples_per_slot_wCP;\n c16_t *baselineA=NULL,*baselineB=NULL,*outA=NULL,*outB=NULL;AssertFatal(!posix_memalign((void**)&baselineA,32,bytes)&&!posix_memalign((void**)&baselineB,32,bytes)&&!posix_memalign((void**)&outA,32,bytes)&&!posix_memalign((void**)&outB,32,bytes),"aligned output allocation");memset(baselineA,0,bytes);memset(baselineB,0,bytes);memset(outA,0,bytes);memset(outB,0,bytes);\n AssertFatal(baselineA&&baselineB&&outA&&outB,"output allocation");\n fixture_fft_job j0={fp,a,baselineA,-1},j1={fp,b,baselineB,-1},j2={fp,a,outA,-1},j3={fp,b,outB,-1};fixture_fft_worker(&j0);fixture_fft_worker(&j1);\n pthread_t ta,tb;AssertFatal(!pthread_create(&ta,NULL,fixture_fft_worker,&j2)&&!pthread_create(&tb,NULL,fixture_fft_worker,&j3),"worker create");pthread_join(ta,NULL);pthread_join(tb,NULL);\n AssertFatal(j0.result==0&&j1.result==0&&j2.result==0&&j3.result==0&&!memcmp(baselineA,outA,bytes)&&!memcmp(baselineB,outB,bytes),"immutable parallel FFT result");\n AssertFatal(!nr_ntn_history_append(&h,raw,fp->nb_antennas_rx,base+length+5,32,length*2),"discontinuity accepted");\n nr_ntn_rx_snapshot *short_span=nr_ntn_snapshot_copy(&h,base+length+5,0,base,7680);int index;\n AssertFatal(short_span&&!nr_ntn_span_index(short_span,0,fp->ofdm_symbol_size,&index),"clipped span is not valid FFT");\n for(int sign=-1;sign<=1;sign+=2){\n  nr_ntn_rx_tracker t={0};uint64_t q=base+1000;uint64_t observed=(uint64_t)((int64_t)q+sign*183);\n  AssertFatal(nr_ntn_tracker_observe(&t,0,observed,q,0,sign*183,100,7680000)&&t.e_ref==sign*183,"first measured offset lost");\n  AssertFatal(nr_ntn_tracker_observe(&t,0,observed+153600-184,q+153600,0,sign*183-184,365,7680000)&&t.rate_samples_s==-9200,"rate units");\n  double e,f;AssertFatal(nr_ntn_tracker_predict(&t,0,q+307200,153600,7680000,&e,&f)&&e==sign*183-368,"wide forecast");\n  nr_ntn_rx_tracker old=t;AssertFatal(!nr_ntn_tracker_observe(&t,0,observed,q,0,NAN,100,7680000)&&!memcmp(&old,&t,sizeof(t)),"invalid observation changed state");\n  AssertFatal(!nr_ntn_tracker_predict(&t,0,q+307201,153600,7680000,&e,&f),"unbounded hold");\n }\n nr_ntn_snapshot_free(short_span);nr_ntn_snapshot_free(a);nr_ntn_snapshot_free(b);nr_ntn_history_destroy(&h);free(baselineA);free(baselineB);free(outA);free(outB);\n printf("RXFIX_OWNER parallel=1 independent=1 shortReject=1 discontinuity=1 firstOffset=1 rateUnits=1 boundedHold=1\\n");\n}\n\nstatic int rxfix_pilot(PHY_VARS_NR_UE *ue,NR_DL_FRAME_PARMS *fp,c16_t **raw,int len,int pci,uint64_t epoch,double prior,int *ok,int *decoded,double *total){\n nr_ntn_rx_snapshot snap={.antennas=fp->nb_antennas_rx,.length=len,.native_begin=epoch};for(int a=0;a<snap.antennas;a++)snap.iq[a]=raw[a];\n nr_ntn_pilot result=nr_ntn_measure_pilot(fp,&snap,nr_get_ssb_start_symbol(fp,fp->ssb_index),pci,prior);\n *ok=result.accepted;*decoded=result.accepted?pci:-1;*total=result.accepted?result.total_fo:prior;\n return result.accepted?result.delta:0;\n}\n\n\n'), (408, 408, '', '  frame_parms->frame_type = FDD;\n  frame_parms->ssb_type = nr_ssb_type_A;\n'), (486, 486, '', '  printf("RXFIX_CONFIG Fs=%d FFT=%d CP=%d FDD=%d PCI=%d\\n", UE->frame_parms.samples_per_subframe*1000,UE->frame_parms.ofdm_symbol_size,UE->frame_parms.nb_prefix_samples,UE->frame_parms.frame_type==FDD,UE->frame_parms.Nid_cell);\n'), (601, 601, '', '  InitSinLUT(); // Stock simulator does not initialize the FO lookup table.\n  nr_ntn_rx_tracker fixture_tracker = {0};\n  const int fixture_shift = getenv("RXFIX_SHIFT") ? atoi(getenv("RXFIX_SHIFT")) : 0;\n  const double fixture_fo=getenv("RXFIX_FO")?atof(getenv("RXFIX_FO")):0;\n  const double fixture_chirp=getenv("RXFIX_CHIRP")?atof(getenv("RXFIX_CHIRP")):0;\n  const double fixture_native=getenv("RXFIX_NATIVE_S")?atof(getenv("RXFIX_NATIVE_S")):0;\n  double receiver_current_t=getenv("RXFIX_CURRENT_T")?atof(getenv("RXFIX_CURRENT_T")):0;\n  const double fixture_delay_rate=getenv("RXFIX_DELAY_RATE_US_S")?atof(getenv("RXFIX_DELAY_RATE_US_S")):0;\n  const uint64_t fixture_clock_base=getenv("RXFIX_CLOCK_BASE")?strtoull(getenv("RXFIX_CLOCK_BASE"),NULL,10):0;\n  uint64_t receiver_last_observed=0;\n  long receiver_read_shift=0;\n  bool receiver_history=false;\n  double receiver_last_nominal=0,receiver_last_arrival_error=0,receiver_last_t=0;\n  const int fixture_mode=getenv("RXFIX_MODE")?atoi(getenv("RXFIX_MODE")):0;\n  int fixture_symbol = nr_get_ssb_start_symbol(frame_parms, 0);\n  int fixture_fft_start = fixture_symbol * frame_parms->ofdm_symbol_size;\n  for (int sym=0; sym<=fixture_symbol; sym++)\n    fixture_fft_start += sym % (7 << frame_parms->numerology_index) ? frame_parms->nb_prefix_samples : frame_parms->nb_prefix_samples0;\n  double fixture_energy = 0;\n  for (int j=0; j<frame_parms->ofdm_symbol_size; j++) {\n    c16_t v=txdata[0][fixture_fft_start+j];\n    fixture_energy += (double)v.r*v.r + (double)v.i*v.i;\n  }\n  fixture_energy /= frame_parms->ofdm_symbol_size;\n  printf("RXFIX_INPUT shift=%d nominalPss=%d energy=%.9f\\n",fixture_shift,fixture_fft_start,fixture_energy);\n'), (608, 608, '', '      const double nominal_epoch=fixture_native+trial*.020;\n      const double capture_epoch=nominal_epoch+(double)receiver_read_shift/(frame_parms->samples_per_subframe*1000.0);\n      const uint64_t capture_origin=fixture_clock_base+(uint64_t)llround(capture_epoch*frame_parms->samples_per_subframe*1000.0);\n      const long applied_read_shift=receiver_read_shift;\n'), (610, 612, '          r_re[aa][i] = (double)txdata[aa][i].r;\n          r_im[aa][i] = (double)txdata[aa][i].i;\n', '          double physical_time=capture_epoch+(double)i/(frame_parms->samples_per_subframe*1000.0);\n          // RFsim updates channel_offset once per read. SSB2..5 lies in this read block.\n          const double read_epoch=capture_epoch+(frame_parms->ofdm_symbol_size+frame_parms->nb_prefix_samples0)/(frame_parms->samples_per_subframe*1000.0);\n          double delay_epoch=getenv("RXFIX_SAMPLE_WARP")?physical_time:read_epoch;\n          long injected_delay=llround(fixture_shift+fixture_delay_rate*1e-6*(frame_parms->samples_per_subframe*1000.0)*delay_epoch);\n          long src=(long)i+applied_read_shift-injected_delay;\n          r_re[aa][i] = src>=0 && src<frame_length_complex_samples ? (double)txdata[aa][src].r : 0;\n          r_im[aa][i] = src>=0 && src<frame_length_complex_samples ? (double)txdata[aa][src].i : 0;\n          double t=capture_epoch+(double)i/(frame_parms->samples_per_subframe*1000.0);\n          double phase=2*M_PI*(fixture_fo*t+.5*fixture_chirp*t*t);\n          double real=r_re[aa][i],imag=r_im[aa][i];\n          r_re[aa][i]=fixture_mode?0:real*cos(phase)-imag*sin(phase);\n          r_im[aa][i]=fixture_mode?0:real*sin(phase)+imag*cos(phase);\n'), (619, 621, '      sigma2_dB = 20*log10((double)AMP/4)-SNR;\n      sigma2 = pow(10,sigma2_dB/10);\n', '      sigma2_dB = 10*log10(fixture_energy)-SNR;\n      sigma2 = fixture_mode==2?0:pow(10,sigma2_dB/10);\n'), (650, 650, '', '      c16_t *immutable[frame_parms->nb_antennas_rx];c16_t *decode_work[frame_parms->nb_antennas_rx];\n      for(int a=0;a<frame_parms->nb_antennas_rx;a++){immutable[a]=UE->common_vars.rxdata[a];decode_work[a]=NULL;}\n      if (trial==0) fixture_lifecycle(frame_parms,immutable,frame_length_complex_samples);\n      uint64_t raw_before=rxfix_hash(immutable,frame_parms->nb_antennas_rx,frame_length_complex_samples);\n      int pilot_accepted=0,pilot_pci=-1;double measured_total=receiver_current_t;int pilot_delta=0;\n      const char *profile=getenv("OAI_NTN_PROFILE");\n      bool pilot_gate=nr_ntn_rx_enabled() && getenv("RXFIX_TRACK") && !strcmp(getenv("RXFIX_TRACK"),"1");\n      PHY_VARS_NR_UE *pilot_context=UE;\n      if(pilot_gate){\n        int known=getenv("RXFIX_KNOWNPCI")?atoi(getenv("RXFIX_KNOWNPCI")):0;\n        int available=getenv("RXFIX_AVAILABLE")?atoi(getenv("RXFIX_AVAILABLE")):frame_length_complex_samples;\n        if(available>frame_length_complex_samples)available=frame_length_complex_samples;\n        pilot_delta=rxfix_pilot(UE,frame_parms,immutable,available,known,capture_origin,receiver_current_t,&pilot_accepted,&pilot_pci,&measured_total);\n      }\n      printf("RXFIX_TRACK gate=%d accepted=%d measuredDelta=%d decodedPCI=%d measuredT=%.9f\\n",pilot_gate,pilot_accepted,pilot_delta,pilot_pci,measured_total);\n'), (678, 678, '', '          if (pilot_accepted) {\n            nr_ntn_rx_snapshot snap={.active=true,.antennas=frame_parms->nb_antennas_rx,.length=frame_length_complex_samples,.native_begin=capture_origin,.fft_delta=pilot_delta,.total_fo=measured_total};\n            for(int a=0;a<snap.antennas;a++)snap.iq[a]=immutable[a];\n            AssertFatal(nr_slot_fep_tracked(frame_parms,ssb_slot,i%frame_parms->symbols_per_slot,rxdataF,link_type_dl,&snap)==0,"tracked FEP bounds");\n          } else {\n'), (686, 686, '', '          }\n'), (745, 745, '', '        printf("RXFIX_RAW immutable=%d\\n",raw_before==rxfix_hash(immutable,frame_parms->nb_antennas_rx,frame_length_complex_samples));\n        for(int a=0;a<frame_parms->nb_antennas_rx;a++){UE->common_vars.rxdata[a]=immutable[a];free(decode_work[a]);}\n        if(pilot_context!=UE)free(pilot_context);\n        const double arrival_error=(double)applied_read_shift+pilot_delta;\n        double observed_rate=0,observed_fo_rate=0;\n        if(pilot_gate&&pilot_accepted){\n          const double fs=frame_parms->samples_per_subframe*1000.0;\n          const uint64_t q=fixture_clock_base+(uint64_t)llround(nominal_epoch*fs)+fixture_fft_start;\n          AssertFatal(nr_ntn_tracker_observe(&fixture_tracker,0,capture_origin+fixture_fft_start+pilot_delta,\n                                            q,applied_read_shift,pilot_delta,measured_total,fs),"actual controller rejected legal observation");\n          double prediction, next_t;\n          AssertFatal(nr_ntn_tracker_predict(&fixture_tracker,0,q+(uint64_t)llround(.020*fs),\n                                             (uint64_t)llround(.020*fs),fs,&prediction,&next_t),"actual controller prediction failed");\n          observed_rate=fixture_tracker.rate_samples_s;observed_fo_rate=fixture_tracker.fo_rate_hz_s;\n          receiver_read_shift=llround(prediction);receiver_current_t=next_t;\n        }\n        printf("RXFIX_SEQUENCE trial=%d nativeOrigin=%llu observedPss=%llu appliedRead=%ld fftDelta=%d arrivalError=%.9f rateSamplesS=%.9f foRateHzS=%.9f nextRead=%ld nextT=%.9f accepted=%d\\n",trial,(unsigned long long)capture_origin,(unsigned long long)capture_origin+fixture_fft_start+pilot_delta,applied_read_shift,pilot_delta,arrival_error,observed_rate,observed_fo_rate,receiver_read_shift,receiver_current_t,pilot_accepted);\n        printf("RXFIX_RESULT crc=%d payload_errors=%d\\n",ret,n_errors_payload);\n')]

def command(argv, cwd, log, env=None):
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
    log.write_text(p.stdout+p.stderr)
    return p

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--output',type=Path)
    ap.add_argument('--overlay',type=Path,help='private candidate headers/source, before formal deployment')
    args=ap.parse_args(); root=args.root.resolve();oai=root/'.runtime/oai';build=oai/'cmake_targets/ran_build/build'
    if args.output:
        out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    else:
        (root/'.private').mkdir(exist_ok=True);out=Path(tempfile.mkdtemp(prefix='rx-tracker-iq-',dir=root/'.private'))
    source=oai/'openair1/SIMULATION/NR_PHY/pbchsim.c';original=source.read_text()
    assert hashlib.sha256(original.encode()).hexdigest()==SOURCE_SHA, 'pinned simulator changed'
    lines=original.splitlines(True)
    for i,j,old,new in reversed(DRIVER_CHANGES):
        assert ''.join(lines[i:j])==old
        lines[i:j]=[new]
    driver=out/'driver.c';driver.write_text(''.join(lines))
    headers=args.overlay.resolve() if args.overlay else oai
    database=json.loads(subprocess.check_output(['ninja','-t','compdb'],cwd=build,text=True))
    def compile_argv(relative, input_file, output_file):
        matches=[x for x in database if x['file'].endswith('/'+relative)]
        assert matches,relative
        argv=shlex.split(matches[0]['command'])
        argv[2:2]=['-I'+str(headers/'openair1'),'-I'+str(headers),'-I'+str(headers/'executables'),
                    '-I'+str(oai/'openair1/PHY'),'-I'+str(oai/'openair1/PHY/MODULATION'),'-I'+str(source.parent)]
        for flag,dest in [('-c',input_file),('-o',output_file),('-MT',output_file),('-MF',str(output_file)+'.d')]:
            if flag in argv:argv[argv.index(flag)+1]=str(dest)
        return argv
    proof={'commands':[],'source_sha256':SOURCE_SHA,'receiver_source_sha256':{}}
    for name,relative,input_file in [('driver','openair1/SIMULATION/NR_PHY/pbchsim.c',driver),
            ('fep','openair1/PHY/MODULATION/slot_fep_nr.c',headers/'openair1/PHY/MODULATION/slot_fep_nr.c')]:
        argv=compile_argv(relative,input_file,out/(name+'.o'));proof['commands'].append(argv)
        p=command(argv,build,out/(name+'-compile.log'));assert p.returncode==0,(name,p.returncode,str(out))
    cmds=subprocess.check_output(['ninja','-t','commands','nr_pbchsim'],cwd=build,text=True).splitlines()
    link=shlex.split(cmds[-1].removeprefix(': && ').removesuffix(' && :'))
    driver_obj='CMakeFiles/nr_pbchsim.dir/openair1/SIMULATION/NR_PHY/pbchsim.c.o'
    link[link.index(driver_obj)]=str(out/'driver.o');link[link.index('-o')+1]=str(out/'fixture');link.insert(link.index('-o'),str(out/'fep.o'))
    proof['commands'].append(link);p=command(link,build,out/'link.log');assert p.returncode==0,('link',p.returncode,str(out))
    for relative in ['openair1/PHY/NR_UE_ESTIMATION/nr_ntn_rx_tracker.h','openair1/PHY/MODULATION/slot_fep_nr.c','openair1/PHY/defs_nr_UE.h']:
        proof['receiver_source_sha256'][relative]=hashlib.sha256((headers/relative).read_bytes()).hexdigest()
    proof['linked_sha256']={}
    for part in link:
        path=Path(part) if part.startswith('/') else build/part
        if path.is_file() and path.suffix in ['.o','.a']:
            proof['linked_sha256'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    (out/'commands.json').write_text(json.dumps(proof,indent=2))
    cases=[]
    for shift in [0,-183,185]:
        cases += [(f'green-{shift}',{'RXFIX_SHIFT':str(shift)},1,30,True,True),
                  (f'red-{shift}',{'RXFIX_SHIFT':str(shift),'RXFIX_TRACK':'0'},1,30,False,shift==0)]
    for seed in [7,19,42,71,103]:cases.append((f'noise-{seed}',{'RXFIX_MODE':'1','OAI_RNGSEED':str(seed)},1,30,False,None))
    controls=[('absent',{'RXFIX_MODE':'2'}),('wrongPCI',{'RXFIX_KNOWNPCI':'3'}),('short',{'RXFIX_AVAILABLE':'2200'}),
      ('edgeL',{'RXFIX_SHIFT':'-512'}),('edgeR',{'RXFIX_SHIFT':'512'}),('outFO',{'RXFIX_FO':'16000'}),
      ('zky',{'OAI_NTN_PROFILE':'zky','RXFIX_SHIFT':'-183'}),('foreign',{'OAI_NTN_PROFILE':'foreign','RXFIX_SHIFT':'-183'}),
      ('off',{'OAI_NTN_RX_TRACKER':'0','RXFIX_SHIFT':'-183'})]
    for name,env in controls:cases.append((name,env,1,30,False,None))
    for snr in [30,20,16]:cases.append((f'joint2725-snr{snr}',{'RXFIX_DELAY_RATE_US_S':'-2725','RXFIX_CHIRP':'13250','RXFIX_FO':'-37350','RXFIX_CURRENT_T':'-37350'},6,snr,True,True))
    for base in [0,2147483644,4294967292]:cases.append((f'wide-{base}',{'RXFIX_SHIFT':'-183','RXFIX_FO':'265','RXFIX_CLOCK_BASE':str(base)},1,30,True,True))
    for base in [2147483644,4294967292]:cases.append((f'ramp-wide-{base}',{'RXFIX_DELAY_RATE_US_S':'-2725','RXFIX_CHIRP':'13250','RXFIX_FO':'-37350','RXFIX_CURRENT_T':'-37350','RXFIX_CLOCK_BASE':str(base)},6,30,True,True))
    records=[]
    for name,extra,count,snr,expected,crc in cases:
        env=os.environ.copy()
        for key in list(env):
            if key.startswith('RXFIX_') or key in ['OAI_NTN_PROFILE','OAI_NTN_RX_TRACKER','OAI_RNGSEED']:env.pop(key)
        env.update(OAI_NTN_PROFILE='integrated-handover',RXFIX_TRACK='1',OAI_RNGSEED='42');env.update(extra)
        argv=[str(out/'fixture'),'-R','25','-m','0','-n',str(count),'-s',str(snr),'-S',str(snr+.1)]
        p=command(argv,out,out/(name+'.log'),env)
        markers=[x for x in p.stdout.splitlines() if x.startswith(('RXFIX_','Initializing random number generator, seed '))]
        track=[x for x in markers if x.startswith('RXFIX_TRACK ')];results=[x for x in markers if x.startswith('RXFIX_RESULT ')]
        assert len(track)==len(results)==count,(name,'missing actual observations')
        assert all(('accepted=1 ' in x)==expected for x in track),(name,'quality acceptance')
        assert markers.count('RXFIX_RAW immutable=1')==count,(name,'raw changed')
        assert 'Initializing random number generator, seed '+env['OAI_RNGSEED'] in markers,(name,'seed')
        assert any(x.startswith('RXFIX_OWNER parallel=1 independent=1 shortReject=1 discontinuity=1 firstOffset=1 rateUnits=1 boundedHold=1') for x in markers),(name,'ownership controls')
        assert 'RXFIX_CONFIG Fs=7680000 FFT=512 CP=36 FDD=1 PCI=0' in markers,(name,'real configuration')
        if crc is not None:
            assert all(('crc=0 payload_errors=0' in x)==crc for x in results),(name,'truth CRC')
            assert p.returncode==(0 if crc else 1),(name,'actual exit')
        record={'case':name,'passed':True,'exit':p.returncode,'seed':env['OAI_RNGSEED'],'markers':markers};records.append(record)
        (out/'results.json').write_text(json.dumps(records,indent=2))
        print(name,'PASS',flush=True)
    wide=[next(x for x in records if x['case']==f'wide-{base}') for base in [0,2147483644,4294967292]]
    assert len({tuple(x for x in row['markers'] if x.startswith(('RXFIX_TRACK ','RXFIX_RESULT ','RXFIX_RAW '))) for row in wide})==1,'wide timestamp changed receiver measurement'
    print('REAL_RX_TRACKER_IQ_PASS cases='+str(len(records))+' artifacts='+str(out))
if __name__=='__main__':main()
