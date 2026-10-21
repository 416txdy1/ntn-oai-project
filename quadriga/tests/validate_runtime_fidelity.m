function report=validate_runtime_fidelity(bundle_path, cache_dir)
% 使用全部真实 QD 缓存检验时间插值 + 实际 RFsim FIR + 子阵误差预算。
% 缓存含独立保留点；不修改 bundle，不把保留的原始尾段声明为已认证。
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));addpath(fullfile(root,'quadriga','matlab'));
bundle=read_qdchannel1_arrays(bundle_path);
fidelity=jsondecode(fileread(fullfile(bundle_path,'fidelity_report.json')));
endpoint=fidelity.validated_time_end_s;
count=numel(bundle.times_s);h=reshape(bundle.coefficients,4,[],count);d=reshape(bundle.delays_s,4,[],count);
files=dir(fullfile(cache_dir,'samples-*.mat'));assert(~isempty(files));
worst_temporal=0;worst_fir=0;worst_joint=0;sum_error=0;sum_power=0;checked=0;holdouts=0;
for batch=1:numel(files)
    data=load(fullfile(cache_dir,files(batch).name),'part');part=data.part;
    hr=reshape(part.coefficients,4,[],numel(part.times_s));dr=reshape(part.delays_s,4,[],numel(part.times_s));
    intervals=discretize(part.times_s,bundle.times_s);on_output=ismember(part.times_s,bundle.times_s);
    for n=1:numel(part.times_s)
        t=part.times_s(n);if t>endpoint,continue;end
        left=intervals(n);assert(isfinite(left));
        u=(t-bundle.times_s(left))/(bundle.times_s(left+1)-bundle.times_s(left));
        hp=(1-u)*h(:,:,left)+u*h(:,:,left+1);dp=(1-u)*d(:,:,left)+u*d(:,:,left+1);
        [ratio,e,p]=channel_band_error(hp,dp,hr(:,:,n),dr(:,:,n),4.5e6);
        fir=channel_fir_bound(hp,dp,4.5e6,7680000,p);
        worst_temporal=max(worst_temporal,ratio);worst_fir=max(worst_fir,fir);worst_joint=max(worst_joint,ratio+fir);
        sum_error=sum_error+e;sum_power=sum_power+p;checked=checked+1;
        holdouts=holdouts+~on_output(n);
    end
    fprintf('Runtime fidelity reference batch %d/%d: %d points, joint bound %.9g\n',batch,numel(files),checked,worst_joint);
end
space=fidelity.spatial_continuous_band_bound;
report=struct('bandwidth_hz',4.5e6,'sample_rate_hz',7680000,'tolerance',0.01, ...
    'temporal_global_nrmse',sqrt(sum_error/sum_power),'temporal_worst_nrmse',worst_temporal, ...
    'fir_worst_bound',worst_fir,'joint_temporal_fir_bound',worst_joint, ...
    'spatial_continuous_band_bound',space,'combined_bound',(1+space)*worst_joint+space, ...
    'checked_reference_snapshots',checked,'non_output_reference_snapshots',holdouts, ...
    'validated_time_start_s',bundle.times_s(1),'validated_time_end_s',endpoint, ...
    'bundle_manifest_sha256',sha256_file(fullfile(bundle_path,'manifest.json')), ...
    'scope','prefix_before_unchanged_legacy_tail');
report.passed=holdouts>0 && report.combined_bound<=0.01;
fid=fopen(fullfile(bundle_path,'runtime_fidelity_report.json'),'w');assert(fid>=0);
cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));
disp(jsonencode(report,PrettyPrint=true));assert(report.passed,'完整运行时频带误差超过 1%%');
end
