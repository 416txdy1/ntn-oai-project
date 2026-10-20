function report = validate_fidelity_reference(bundle_dir, reference_path)
% 独立生成的参考不能是对待测 bundle 的再次插值。
% 支持 diagnose_channel_fidelity 的逐阵元缓存及 export_fidelity_subarrays 保存的 reference。
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));addpath(fullfile(root,'quadriga','matlab'));
source=load(reference_path);
manifest=jsondecode(fileread(fullfile(bundle_dir,'manifest.json')));
B=4.5e6;
if isfield(source,'reference')
    reference=source.reference;
    space=reference.metadata.antenna.wideband_error_bound;
else
    [h,d]=combine_satellite_subarrays(source.coefficients,source.delays_s,source.beam_weights,source.positions);
    [h,d,g]=normalize_spatial_channel(h,d);
    reference=struct('times_s',source.times_s,'coefficients',h,'delays_s',d,'residual_gain_db',g);
    space=certify_subarray_bandwidth(source.coefficients,source.delays_s,source.beam_weights,source.positions,B);
    assert(source.frequency_hz==manifest.radio.center_frequency_hz,'参考频率不匹配');
end
if isfield(reference,'metadata')
    assert(reference.metadata.center_frequency_hz==manifest.radio.center_frequency_hz && ...
        strcmp(reference.metadata.stk_trace_sha256,manifest.provenance.stk_trace_sha256),'参考来源不匹配');
end
t=read_values(fullfile(bundle_dir,'times.f64'),'double');
x=read_values(fullfile(bundle_dir,'coefficients.cf32'),'single=>double');
x=complex(x(1:2:end),x(2:2:end));
P=manifest.dimensions.paths; links=manifest.dimensions.rx_antennas*manifest.dimensions.tx_antennas;
assert(links==4 && size(reference.coefficients,3)==P,'参考空间维度不匹配');
h=permute(reshape(x,P,links,[]),[2,1,3]);
d=permute(reshape(read_values(fullfile(bundle_dir,'delays.f64'),'double'),P,links,[]),[2,1,3]);
rh=reshape(reference.coefficients,links,P,[]);rd=reshape(reference.delays_s,links,P,[]);
assert(all(reference.times_s>=t(1) & reference.times_s<=t(end)),'参考时间超出 bundle 范围');
assert(any(~ismember(reference.times_s,t)),'参考必须包含非输出节点');
results=zeros(2,2); exact_energy=0;exact_power=0;exact_worst=0;
for resolution=1:2
    f=linspace(-B/2,B/2,128*resolution+1); energy=0;power=0;worst=0;
    for n=1:numel(reference.times_s)
        time=reference.times_s(n);i=min(find(t<=time,1,'last'),numel(t)-1);u=(time-t(i))/(t(i+1)-t(i));
        c=(1-u)*h(:,:,i)+u*h(:,:,i+1);dt=(1-u)*d(:,:,i)+u*d(:,:,i+1);
        if resolution==2
            [exact_ratio,ee,ep]=channel_band_error(c,dt,rh(:,:,n),rd(:,:,n),B);
            exact_energy=exact_energy+ee;exact_power=exact_power+ep;exact_worst=max(exact_worst,exact_ratio);
        end
        e=0;p=0;
        for port=1:links
            predicted=sum(c(port,:).'.*exp(-2j*pi*dt(port,:).'*f),1);
            actual=sum(rh(port,:,n).'.*exp(-2j*pi*rd(port,:,n).'*f),1);
            e=e+sum(abs(predicted-actual).^2);p=p+sum(abs(actual).^2);
        end
        assert(p>0 && isfinite(e),'非法频响');
        worst=max(worst,sqrt(e/p));energy=energy+e;power=power+p;
    end
    results(resolution,:)=[sqrt(energy/power),worst];
end
exact=[sqrt(exact_energy/exact_power),exact_worst];
frequency_change=max([abs(diff(results)),abs(results(2,:)-exact)],[],'all');
combined=exact_worst*(1+space)+space;
report=struct('bandwidth_hz',B,'tolerance',0.01,'reference_snapshots',numel(reference.times_s), ...
    'global_nrmse',exact(1),'worst_nrmse',exact_worst,'spatial_continuous_band_bound',space, ...
    'combined_bound_at_reference_times',combined,'frequency_grid_change',frequency_change, ...
    'passed',combined<=0.01 && frequency_change<1e-4);
disp(jsonencode(report,PrettyPrint=true));
assert(report.passed,'QDCHANNEL1:Fidelity','独立参考未通过 1%% 频响验收');
end
function values=read_values(path,precision)
fid=fopen(path,'r','ieee-le');assert(fid>=0,'无法读取 bundle 文件');cleanup=onCleanup(@()fclose(fid));
values=fread(fid,inf,precision);
end