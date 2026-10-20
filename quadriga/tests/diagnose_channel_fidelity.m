function diagnose_channel_fidelity(interval_s)
if nargin<1, interval_s=0.01; end
% 使用真实密集 QD 信道检验稀疏时间插值与子阵平均时延。
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root,'quadriga','matlab'));
tag=sprintf('fidelity-dl-%gus',interval_s*1e6);
cache=fullfile(root,'.runtime',[tag,'.mat']);
if ~exist(cache,'file')
    trace=read_stktrace2(fullfile(root,'examples','fdd-pass','trace.csv'));
    options=struct('quadriga_path',fullfile(root,'.runtime','quadriga'), ...
        'antenna_profile','satellite_16x16_4port_ground_omni', ...
        'center_frequency_hz',2488400000,'array_reference_frequency_hz',2488400000, ...
        'link_direction','downlink','snapshot_interval_s',interval_s, ...
        'time_window_s',[trace.times_s(1),trace.times_s(1)+2], ...
        'diagnostic_mat_path',cache);
    output=fullfile(root,'.runtime',tag);
    assert(~exist(output,'dir'),'诊断输出已存在，请检查缓存');
    export_stk_to_qdchannel(fullfile(root,'examples','fdd-pass','trace.csv'),output,options);
end
raw=load(cache);
[h,d]=combine_satellite_subarrays(raw.coefficients,raw.delays_s,raw.beam_weights,raw.positions);
[c,tau]=normalize_spatial_channel(h,d);
f=linspace(-2.25e6,2.25e6,101);
reference=response(c,tau,f);
report=struct('reference_interval_s',interval_s,'bandwidth_hz',4.5e6);
for step=unique(round([1,0.1,0.05,0.02,0.01,0.005,0.002]/interval_s))
    if step<2, continue; end
    knots=1:step:numel(raw.times_s);
    predicted=complex(zeros(size(reference)));
    phase_predicted=predicted;
    for n=1:numel(raw.times_s)
        left=max(1,min(numel(knots)-1,find(knots<=n,1,'last')));
        lo=knots(left); hi=knots(left+1); u=(n-lo)/(hi-lo);
        delay=(1-u)*tau(:,:,:,lo)+u*tau(:,:,:,hi);
        value=(1-u)*c(:,:,:,lo)+u*c(:,:,:,hi);
        predicted(:,:,n)=response(value,delay,f);
        phase0=2*pi*raw.frequency_hz*tau(:,:,:,lo);
        phase1=2*pi*raw.frequency_hz*tau(:,:,:,hi);
        envelope=(1-u)*c(:,:,:,lo).*exp(1j*phase0)+u*c(:,:,:,hi).*exp(1j*phase1);
        value=envelope.*exp(-2j*pi*raw.frequency_hz*delay);
        phase_predicted(:,:,n)=response(value,delay,f);
    end
    report.(sprintf('linear_%dms',round(step*interval_s*1000)))=errors(predicted,reference);
    report.(sprintf('delay_phase_%dms',round(step*interval_s*1000)))=errors(phase_predicted,reference);
end
wideband=complex(zeros(size(reference)));
mean_delay=wideband;
map=1+(raw.positions(2,:)>0)+2*(raw.positions(3,:)>0);
for n=1:numel(raw.times_s)
    origin=min(d(:,:,:,n),[],'all');
    for port=1:4
        selected=find(map==port);
        a=reshape(raw.coefficients(1,selected,:,n),64,[]).*(2*raw.beam_weights(selected,n));
        delay=reshape(raw.delays_s(1,selected,:,n),64,[])-origin;
        wideband(port,:,n)=sum(a(:).*exp(-2j*pi*delay(:)*f),1);
        b=reshape(h(1,port,:,n),[],1);
        dt=reshape(d(1,port,:,n),[],1)-origin;
        mean_delay(port,:,n)=sum(b.*exp(-2j*pi*dt*f),1);
    end
end
report.mean_delay=errors(mean_delay,wideband);
% 区分真实快衰落与最早路径切换造成的公共相位跳变。
fixed=c;
anchor=reshape(h(1,1,1,:),[],1);
for n=1:numel(anchor)
    raw_snapshot=h(:,:,:,n);
    fixed(:,:,:,n)=raw_snapshot/sqrt(sum(abs(raw_snapshot).^2,'all')/4) * ...
        (anchor(1)/abs(anchor(1)))/(anchor(n)/abs(anchor(n)));
end
fixed_reference=response(fixed,tau,f);
for step=unique(round([1,0.1,0.05,0.02,0.01,0.005,0.002]/interval_s))
    if step<2, continue; end
    knots=1:step:numel(raw.times_s);
    predicted=complex(zeros(size(fixed_reference)));
    for n=1:numel(raw.times_s)
        left=max(1,min(numel(knots)-1,find(knots<=n,1,'last')));
        lo=knots(left); hi=knots(left+1); u=(n-lo)/(hi-lo);
        value=(1-u)*fixed(:,:,:,lo)+u*fixed(:,:,:,hi);
        delay=(1-u)*tau(:,:,:,lo)+u*tau(:,:,:,hi);
        predicted(:,:,n)=response(value,delay,f);
    end
    report.(sprintf('fixed_los_%dms',round(step*interval_s*1000)))=errors(predicted,fixed_reference);
end
text=jsonencode(report,PrettyPrint=true);
fid=fopen(fullfile(root,'.runtime',[tag,'-diagnostic.json']),'w');fprintf(fid,'%s\n',text);fclose(fid);
fprintf('%s\n',text);
end
function H=response(c,d,f)
H=complex(zeros(size(c,2),numel(f),size(c,4)));
for n=1:size(c,4)
 for port=1:size(c,2)
  a=reshape(c(1,port,:,n),[],1); tau=reshape(d(1,port,:,n),[],1);
  H(port,:,n)=sum(a.*exp(-2j*pi*tau*f),1);
 end
end
end
function result=errors(actual,expected)
e=sum(abs(actual-expected).^2,[1,2]); p=sum(abs(expected).^2,[1,2]);
[peak,index]=max(reshape(e./p,[],1));
result=struct('nrmse',sqrt(sum(e,'all')/sum(p,'all')),'worst_snapshot_nrmse',sqrt(peak),'worst_snapshot_index',index);
end
