/* Observational indicators only: no changes to media, channel or acceptance gates. */
(function(root){
'use strict';
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const median=a=>{const b=a.filter(finite).sort((x,y)=>x-y);return b.length?b[Math.floor(b.length/2)]:null;};
function assess(history,current,context={}){
 const recent=history.filter(p=>current.wall_s-p.wall_s>=5&&current.wall_s-p.wall_s<=30);
 const baselineCn=median(recent.map(p=>p.cn_db)),baselineIngress=median(recent.map(p=>p.ingress_kbps));
 const cnDrop=finite(baselineCn)&&finite(current.cn_db)?baselineCn-current.cn_db:null;
 const ingressRatio=finite(baselineIngress)&&baselineIngress>20&&finite(current.ingress_kbps)?current.ingress_kbps/baselineIngress:null;
 const flags={cn_drop_db:cnDrop,ingress_ratio:ingressRatio,baseline_samples:recent.length,
  switching:['prepare','blend','complete'].includes(current.phase),
  recent_channel_disruption:history.some(p=>['channel_supply','switch_supply'].includes(p.code)&&current.wall_s-p.wall_s>=0&&current.wall_s-p.wall_s<=15),
  playback_slow:finite(current.fps)&&current.fps<5||finite(current.frame_gap_ms)&&current.frame_gap_ms>800};
 function result(code,title,detail,tone='neutral'){return {code,title,detail,tone,...flags};}
 if(context.paused||context.hidden)return result('player_inactive','播放器暂停或页面不可见','显示帧停顿可能来自播放器状态；暂不进行信道归因。');
 if(!current.channel_fresh)return result('stale','物理数据缺失或过期','不能用旧C/N解释当前画面；检查信道日志及采集状态。','warn');
 if(context.no_frames)return result('startup','等待首帧','接入和缓冲建立期间，暂不判断卡顿原因。');
 if(!current.ingress_fresh)return result('missing_ingress','UE入流指标暂不可用','仅凭物理参数和播放器无法定位；本页不把缺失入流当作零。','warn');
 if(context.publisher_alive===false)return result('publisher_stopped','推流源进程已退出','存在发送端异常；不能认定是卫星信道导致。','warn');
 if(recent.length<8)return result('baseline','正在建立对照基线','收集最近5–30秒的C/N和UE入流，尚不作趋势归因。');
 const channelBad=finite(cnDrop)&&cnDrop>=3||current.channel_valid===false;
 const incomingLow=finite(ingressRatio)&&ingressRatio<.5;
 if(channelBad&&incomingLow&&flags.playback_slow)return result('channel_supply','信道劣化伴随媒体供给下降',`C/N相对近期基线下降，UE入流同步降低，播放也变慢。属于同期关联迹象，正式结论以对照报告为准。`,'bad');
 if(flags.switching&&incomingLow&&flags.playback_slow)return result('switch_supply','切换窗口内媒体入流与播放下降','结合时延、多普勒和协议层记录继续定位；切换标记本身不是原因证明。','warn');
 if(flags.playback_slow&&incomingLow)return result('supply_low','媒体到达不足，原因尚未定位','UE入流下降，但缺少同时的C/N劣化证据；仍需排查无线、核心网及发送端。','warn');
 if(flags.playback_slow&&flags.recent_channel_disruption)return result('recovery_tail','信道与入流已改善，播放仍在恢复','近期记录过信道与入流同时恶化；追帧、残余缓冲或显示调度仍可能造成延后停顿，不能只看瞬时C/N。','warn');
 if(flags.playback_slow)return result('downstream','UE入流尚可，播放出现停顿','优先排查UE中继后的缓冲、解码或本机负载；不能仅凭卡顿归因于卫星。','warn');
 if(channelBad)return result('channel_change','信道已变化，播放暂未明显恶化','链路余量或接收缓冲可能吸收扰动；C/N下降不必然导致卡顿。');
 return result('normal','当前未见明显供给异常','持续观察同一采集时间轴上的物理参数、UE入流和播放表现。','good');
}

class Monitor{
 constructor(){this.history=[];this.events=[];this.lastPhase=null;this.lastCode=null;}
 update(state,row,context){
  const dl=state.channels?.dl,ul=state.channels?.ul,now=state.server_monotonic_ns;
  const stateAge=finite(now)&&finite(state.sampled_host_monotonic_ns)?Math.max(0,(now-state.sampled_host_monotonic_ns)/1e6):Infinity;
  const channelAge=dl?dl.age_ms+stateAge:Infinity;
  const ingressAge=finite(now)&&finite(state.ue_ingress_observed_monotonic_ns)?Math.max(0,(now-state.ue_ingress_observed_monotonic_ns)/1e6):Infinity;
  const channelFresh=!!dl&&channelAge<3500&&(dl.lag_iq_s??Infinity)<2.2&&stateAge<3000;
  const ingressFresh=finite(state.ue_ingress_kbps)&&ingressAge<3500&&stateAge<3000;
  const sample={wall_s:finite(now)?now/1e9:performance.now()/1000,iq_s:state.iq_s,
   cn_iq_s:dl?.iq_s,cn_db:channelFresh?dl.cn_db:null,channel_valid:dl?.valid,
   ingress_kbps:ingressFresh?state.ue_ingress_kbps:null,fps:row.decoded_fps,frame_gap_ms:row.frame_gap_ms,
   channel_fresh:channelFresh,ingress_fresh:ingressFresh,phase:state.phase};
  const explanation=assess(this.history,sample,{...context,publisher_alive:state.publisher_alive});
  sample.code=explanation.code;
  this.history.push(sample);this.history=this.history.filter(p=>sample.wall_s-p.wall_s<=300);
  const phaseKey=(state.satellite||'')+'/'+(state.phase||'');
  if(phaseKey!==this.lastPhase&&finite(state.iq_s)){
   if(this.lastPhase!==null)this.events.push({iq_s:state.iq_s,phase:state.phase,satellite:state.satellite});
   this.lastPhase=phaseKey;
  }
  this.events=this.events.filter(e=>state.iq_s-e.iq_s<=180);
  const $=id=>document.getElementById(id),number=(v,d=2)=>finite(v)?v.toFixed(d):'—';
  $('dlCn').textContent=channelFresh?number(dl.cn_db):'—';
  $('ulCn').textContent=ul&&ul.age_ms+stateAge<3500?number(ul.cn_db):'—';
  $('propDelay').textContent=channelFresh?number(dl.delay_ms,3):'—';
  $('doppler').textContent=channelFresh?number(dl.doppler_hz/1000,2):'—';
  $('ueIngress').textContent=ingressFresh?number(state.ue_ingress_kbps,0):'—';
  $('channelAge').textContent=dl?`采样 IQ ${number(dl.iq_s,2)} s · 观测年龄 ${number(channelAge/1000,1)} s${channelFresh?'':' · 已过期'}`:'等待物理日志';
  $('diagnostic').dataset.tone=explanation.tone;$('diagnosticTitle').textContent=explanation.title;
  $('diagnosticDetail').textContent=explanation.detail;
  $('trendNumbers').textContent=`C/N基线差 ${number(explanation.cn_drop_db,1)} dB ｜UE入流/基线 ${finite(explanation.ingress_ratio)?(100*explanation.ingress_ratio).toFixed(0)+'%':'—'} ｜最近基线样本 ${explanation.baseline_samples}`;
  this.draw();
  const snapshot={...explanation,state_iq_s:state.iq_s,physical_iq_s:dl?.iq_s,
   dl_cn_db:sample.cn_db,dl_delay_ms:dl?.delay_ms,dl_doppler_hz:dl?.doppler_hz,
   channel_age_ms:finite(channelAge)?channelAge:null,state_age_ms:finite(stateAge)?stateAge:null,
   ue_ingress_kbps:sample.ingress_kbps,ingress_age_ms:finite(ingressAge)?ingressAge:null,
   timing_scope:'Near-simultaneous collection, not the exact RF conditions of the currently displayed buffered frame'};
  const changed=this.lastCode!==explanation.code;this.lastCode=explanation.code;
  return {snapshot,changed};
 }
 draw(){
  const canvas=document.getElementById('channelChart'),width=Math.max(400,canvas.clientWidth),height=228;
  const ratio=window.devicePixelRatio||1;canvas.width=width*ratio;canvas.height=height*ratio;
  const c=canvas.getContext('2d');c.scale(ratio,ratio);c.clearRect(0,0,width,height);
  const end=this.history.at(-1)?.iq_s;if(!finite(end))return;
  const start=Math.max(0,end-90),left=116,right=width-18,plotWidth=right-left;
  const x=v=>left+(v-start)/(end-start||1)*plotWidth;
  const panels=[['输入DL C/N','dB','cn_db','#ffc977','cn_iq_s'],['UE媒体入流','kbit/s','ingress_kbps','#6fdad1','iq_s'],['解码帧率','fps','fps','#9dbbff','iq_s']];
  panels.forEach(([label,unit,key,color,timeKey],index)=>{
   const top=14+index*68,bottom=top+46;
   const points=this.history.filter(p=>finite(p[timeKey])&&p[timeKey]>=start&&p[timeKey]<=end);
   const values=points.map(p=>p[key]).filter(finite);
   const min=key==='cn_db'&&values.length?Math.floor(Math.min(...values)-2):0;
   const max=Math.max(min+1,key==='fps'?20:key==='ingress_kbps'?100:1,...values.map(v=>v*1.05+1));
   const y=v=>bottom-(v-min)/(max-min)*(bottom-top);
   c.font='10px system-ui';c.fillStyle='#abc0d7';c.fillText(label,0,top+6);c.fillText(unit,0,top+20);
   c.fillText(max.toFixed(0),left-25,top+4);c.fillText(min.toFixed(0),left-25,bottom);
   c.strokeStyle='#2c4056';c.beginPath();c.moveTo(left,bottom);c.lineTo(right,bottom);c.stroke();
   for(const event of this.events.filter(e=>e.iq_s>=start&&e.iq_s<=end)){
    c.strokeStyle='#b88a52';c.setLineDash([3,3]);c.beginPath();c.moveTo(x(event.iq_s),top);c.lineTo(x(event.iq_s),bottom);c.stroke();c.setLineDash([]);
    if(index===0&&['prepare','complete'].includes(event.phase)){c.fillStyle='#d7ae79';c.fillText(({prepare:'准备',complete:'完成'})[event.phase],Math.min(x(event.iq_s)+2,right-26),top-3);}
   }
   c.strokeStyle=color;c.lineWidth=1.8;c.beginPath();let drawing=false;
   for(const p of points){if(!finite(p[key])){drawing=false;continue;}if(drawing)c.lineTo(x(p[timeKey]),y(p[key]));else c.moveTo(x(p[timeKey]),y(p[key]));drawing=true;}c.stroke();
  });
  c.fillStyle='#abc0d7';c.font='10px system-ui';
  for(let i=0;i<=4;i++){const tick=start+(end-start)*i/4;c.fillText(tick.toFixed(0),Math.min(x(tick)-6,right-8),222);}
 }
}
const api={assess,Monitor};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NTNDashboard=api;
})(typeof window!=='undefined'?window:globalThis);
