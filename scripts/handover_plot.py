"""Scientific export of physical/business evidence on a shared IQ/STK axis."""
import bisect
import csv
import json
import math
from pathlib import Path
from handover_metrics import cohort_summary


def iq_to_wall(anchors,iq,fs):
    samples=iq*fs
    counters=[a['samples'] for a in anchors]
    if not counters[0]<=samples<=counters[-1]:raise ValueError('bin not physically bracketed')
    index=max(0,min(len(anchors)-2,bisect.bisect_right(counters,samples)-1))
    a,b=anchors[index:index+2]
    return (a['monotonic_ns']+(samples-a['samples'])/(b['samples']-a['samples'])*(b['monotonic_ns']-a['monotonic_ns']))/1e9


def write_timeline(output,observer,probes,business_start,business_end,report):
    output=Path(output);epoch=observer.manifest['epoch'];rate=observer.manifest['rate'];fs=observer.fs
    end=min(a[-1]['samples']/fs for a in observer.anchors.values())
    rows=[]
    for index in range(math.ceil(end)):
        lo=float(index);hi=min(lo+1,end)
        if hi<=lo:continue
        active=hi>business_start and lo<business_end
        row=dict(iq_start_s=lo,iq_end_s=hi,iq_s=(lo+hi)/2,
                 stk_s=epoch+rate*(lo+hi)/2,
                 business_state='partial_startup_measurement' if active and lo<business_start else 'partial_tail_drain' if active and hi>business_end
                                else 'establishing_business' if active and lo<report.get('traffic_ready_iq_s',business_start)
                                else 'continuous' if active else 'startup_unavailable' if lo<business_start else 'intentional_tail_drain',
                 max_event_uncertainty_iq_s=max(report['clock_max_iq_gap_s'].values()))
        wall_spans={}
        for side in ('gnb','ue'):
            anchors=observer.anchors[side]
            if lo<anchors[0]['samples']/fs:
                row[side+'_real_time_factor']=None;wall_spans[side]=None
            else:
                wall_spans[side]=iq_to_wall(anchors,hi,fs)-iq_to_wall(anchors,lo,fs)
                row[side+'_real_time_factor']=(hi-lo)/wall_spans[side]
            physical=[p for p in observer.numbers[side] if lo<=p['samples']/fs<hi]
            if physical:
                for key in ('delay_ms','doppler_hz','cn_db','gain_db'):
                    row[side+'_'+key]=sum(p[key] for p in physical)/len(physical)
                row[side+'_physical_sample_iq_s']=physical[0]['samples']/fs
            else:
                for key in ('delay_ms','doppler_hz','cn_db','gain_db','physical_sample_iq_s'):row[side+'_'+key]=None
            selected=[p for p in observer.schedules[side] if p['samples']/fs<=hi]
            row[side+'_satellite_id']=selected[-1]['satellite_id'] if selected else None
            row[side+'_handover_phase']=selected[-1]['phase'] if selected else None
        for name,side in [('ping','ue'),('uplink','gnb'),('downlink','ue')]:
            if active:
                summary=cohort_summary(probes[name]['packets'],lo,hi,wall_interval_s=wall_spans[side])
                for key in ('sent','received','eventual_missing','deadline_timeouts','late_received',
                            'boundary_ambiguous_sent','boundary_ambiguous_missing','loss_lower_bound','loss_upper_bound'):
                    row[name+'_'+key]=summary[key]
                row[name+'_wall_rtt_ms' if name=='ping' else name+'_one_way_wall_ms']=summary['wall_latency_ms_mean']
                # Arrival throughput uses receive-event estimate; bracketing precision remains in CSV.
                arrivals=[p for p in probes[name]['packets'] if p['received'] and lo<=p['receive']['iq_s']<hi]
                byte_count=sum(p['bytes'] for p in arrivals)
                row[name+'_arrival_bytes']=byte_count
                row[name+'_observed_iq_bits_per_second']=byte_count*8/(hi-lo)
                row[name+'_measured_wall_bits_per_second']=byte_count*8/wall_spans[side] if wall_spans[side] else None
                row[name+'_wall_jitter_ms']=summary['wall_jitter_ms_mean']
            else:
                for key in ('sent','received','eventual_missing','deadline_timeouts','late_received',
                            'boundary_ambiguous_sent','boundary_ambiguous_missing','loss_lower_bound','loss_upper_bound',
                            'arrival_bytes','observed_iq_bits_per_second','measured_wall_bits_per_second','wall_jitter_ms'):
                    row[name+'_'+key]=None
                row[name+'_wall_rtt_ms' if name=='ping' else name+'_one_way_wall_ms']=None
        rows.append(row)
    fields=list(dict.fromkeys(key for row in rows for key in row))
    csv_path=output/'timeline.csv'
    with csv_path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader();writer.writerows(rows)
    comparison=[]
    for completion in __import__('handover_metrics').case_spec(report['case'])['completions']:
        item={'completion_stk_s':completion,'intervals':{}}
        for name,lo,hi in [('before',completion-15,completion-5),('during',completion-5,completion+5),('after',completion+5,completion+15)]:
            item['intervals'][name]={kind:cohort_summary(probes[kind]['packets'],lo,hi,'stk') for kind in ('ping','uplink','downlink')}
        comparison.append(item)
    (output/'switch-comparison.json').write_text(json.dumps(comparison,indent=2))
    draw(rows,output,report,epoch,rate,business_start,business_end)
    return {'csv':str(csv_path),'svg':str(output/'timeline.svg'),'png':str(output/'timeline.png'),
            'comparison':str(output/'switch-comparison.json'),'x_axis':'absolute_stk_s' if rate else 'iq_elapsed_s',
            'throughput_bins':'receive-time estimate, with explicit bracketing precision',
            'latency_units':'wall_clock_ms','source_logs':'private','rows':len(rows)}


def draw(rows,output,report,epoch,rate,start,end):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x=[row['stk_s'] if rate else row['iq_s'] for row in rows]
    value=lambda key:[math.nan if row.get(key) is None else row[key] for row in rows]
    fig,axes=plt.subplots(7,1,sharex=True,figsize=(13,16),constrained_layout=True)
    for side in ('gnb','ue'):
        axes[0].plot(x,value(side+'_delay_ms'),label=side)
        axes[1].plot(x,value(side+'_doppler_hz'),label=side)
        axes[2].plot(x,value(side+'_cn_db'),label=side)
    axes[0].set_ylabel('Physical delay (ms)');axes[1].set_ylabel('Doppler (Hz)');axes[2].set_ylabel('C/N (dB)')
    rtt=value('ping_wall_rtt_ms');finite=[i for i,v in enumerate(rtt) if math.isfinite(v)]
    axes[3].errorbar([x[i] for i in finite],[rtt[i] for i in finite],
                     xerr=max(report['clock_max_iq_gap_s'].values())*(rate if rate else 1)/2,
                     linewidth=.7,elinewidth=.4,label='ICMP wall RTT / horizontal anchor precision')
    axes[3].set_ylabel('Wall RTT (ms)')
    prior_id=None
    for row in rows:
        satellite=row.get('ue_satellite_id')
        if satellite and satellite!=prior_id:
            axes[0].annotate(satellite,(row['stk_s'] if rate else row['iq_s'],.95),
                             xycoords=('data','axes fraction'),rotation=15,fontsize=7)
            prior_id=satellite
    for kind in ('ping','uplink','downlink'):
        low=value(kind+'_loss_lower_bound');high=value(kind+'_loss_upper_bound')
        axes[4].plot(x,[a*100 for a in high],label=kind+' upper')
        axes[4].fill_between(x,[a*100 for a in low],[a*100 for a in high],alpha=.15)
    axes[4].set_ylabel('Cohort loss bounds (%)')
    for kind in ('uplink','downlink'):
        axes[5].plot(x,[a/1000 for a in value(kind+'_measured_wall_bits_per_second')],label=kind+' wall')
        axes[5].plot(x,[a/1000 for a in value(kind+'_observed_iq_bits_per_second')],linestyle='--',label=kind+' IQ')
    axes[5].set_ylabel('Arrival throughput (kbit/s)')
    for side in ('gnb','ue'):axes[6].plot(x,value(side+'_real_time_factor'),label=side)
    axes[6].set_ylabel('IQ seconds / wall second')
    completions=__import__('handover_metrics').case_spec(report['case'])['completions']
    schedule_rows=[row for row in rows if row.get('ue_handover_phase')=='blend']
    for axis in axes:
        axis.grid(alpha=.25);axis.legend(loc='upper right',fontsize=8)
        confirmed=report.get('traffic_ready_iq_s',start)
        axis.axvspan(x[0],epoch+rate*confirmed if rate else confirmed,color='gray',alpha=.15)
        axis.axvspan(epoch+rate*end if rate else end,x[-1],color='gray',alpha=.08)
        for complete in completions:
            axis.axvspan(complete-5,complete+5,color='orange',alpha=.1)
            axis.axvline(complete,color='black',linestyle=':',linewidth=.8)
        for row in schedule_rows:
            axis.axvspan(row['stk_s']-.5,row['stk_s']+.5,color='blue',alpha=.04)
    axes[0].set_title(report['case']+': physical channel and continuous business evidence\n'
                      'Gray: startup unavailable / intentional tail drain; orange: required switch windows; blue: blend phase\n'
                      'RTT is wall time; event x-axis is IQ-mapped. Loss bands preserve boundary uncertainty.')
    axes[-1].set_xlabel('Absolute STK seconds' if rate else 'IQ elapsed seconds (static STK epoch)')
    fig.savefig(output/'timeline.svg');fig.savefig(output/'timeline.png',dpi=140)
    plt.close(fig)
