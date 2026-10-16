function report = export_full_fidelity(direction,output_dir,validated_end_s)
% 对指定前缀做真实 QD 精度认证，后缀逐字节数值保留原 bundle。
% validated_end_s 必须显式给出；不得用截短 trace 掩盖已知尾段业务失败。
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
trace_path=fullfile(root,'examples','fdd-pass','trace.csv');trace=read_stktrace2(trace_path);
assert(any(strcmp(direction,{'downlink','uplink'})) && ~exist(output_dir,'dir'));
assert(validated_end_s>trace.times_s(1) && validated_end_s<=trace.times_s(end));
legacy=read_qdchannel1_arrays(fullfile(root,'examples','fdd-miso4-subarray',direction));
assert(any(legacy.times_s==validated_end_s),'保留尾段的边界必须是原始快照');
work=[char(output_dir),'.work'];if ~exist(work,'dir'),mkdir(work);end
frequency=legacy.manifest.radio.center_frequency_hz;
anchor_path=fullfile(work,'power-anchor.mat');
options=struct('quadriga_path',fullfile(root,'.runtime','quadriga'), ...
    'antenna_profile','satellite_16x16_4port_ground_omni','array_reference_frequency_hz',2488400000, ...
    'center_frequency_hz',frequency,'link_direction',direction,'fidelity_tolerance',0.01, ...
    'scenario','QuaDRiGa_NTN_Rural_LOS','random_seed',20260925);
if ~exist(anchor_path,'file')
    raw_path=fullfile(work,'original-elements.mat'); options.diagnostic_mat_path=raw_path;
    % 与旧完整轨迹相同的 1 秒网格，用于固定 QD 内部的簇功率校正。
    export_stk_to_qdchannel(trace_path,'',options);
    raw=load(raw_path,'coefficients');coefficients=raw.coefficients(:,:,:,1);
    time_s=trace.times_s(1);trace_sha256=sha256_file(trace_path);frequency_hz=frequency;
    random_seed=options.random_seed;scenario=options.scenario;
    save(anchor_path,'coefficients','time_s','trace_sha256','frequency_hz','random_seed','scenario');
    clear raw;options=rmfield(options,'diagnostic_mat_path');
end
options.normalization_anchor_path=anchor_path;
signature={direction,validated_end_s,sha256_file(trace_path),sha256_file(anchor_path)};
for name={'export_stk_to_qdchannel','generate_bounded_reference','resample_stk_geometry','normalize_spatial_channel','combine_satellite_subarrays','certify_subarray_bandwidth'}
    signature{end+1}=sha256_file(fullfile(root,'quadriga','matlab',[name{1},'.m']));
end
parameters=fullfile(work,'parameters.mat');
if exist(parameters,'file'), prior=load(parameters);assert(isequal(prior.signature,signature),'生成条件改变，请使用新输出路径');
else,save(parameters,'signature');end
cache=struct();files=dir(fullfile(work,'samples-*.mat'));
for k=1:numel(files)
    saved=load(fullfile(work,files(k).name),'part');cache=append(cache,saved.part);
end
serial=numel(files);knots=trace.times_s(trace.times_s<=validated_end_s);
for iteration=1:25
    fractions=[0.5,(3-sqrt(5))/2,(sqrt(5)-1)/2];
    candidates=unique([knots;reshape(knots(1:end-1)+diff(knots)*fractions,[],1)]);
    [cache,serial]=extend(cache,candidates,serial,work,trace_path,options);
    [bad,worst,global_error]=measure(cache,knots,candidates);
    fprintf('Full fidelity %s iteration %d: %d knots, %d cached, worst %.9g, global %.9g\n',direction,iteration,numel(knots),numel(cache.times_s),worst,global_error);
    if ~any(bad)
        % 未用于本轮选点的独立高密度时间参考；每个输出区间都有两个点。
        holdout=unique(reshape(knots(1:end-1)+diff(knots)*[0.211324865405187,0.788675134594813],[],1));
        [cache,serial]=extend(cache,holdout,serial,work,trace_path,options);
        [bad,independent_worst,independent_global]=measure(cache,knots,holdout);
        fprintf('Independent full reference: worst %.9g, global %.9g\n',independent_worst,independent_global);
        if ~any(bad)
            report=finish(cache,knots,legacy,output_dir,validated_end_s,max(worst,independent_worst),max(global_error,independent_global),iteration);
            return;
        end
    end
    widths=diff(knots);knots=unique([knots;knots(find(bad))+widths(bad)/2]);
end
error('QDCHANNEL1:Fidelity','完整轨迹精度未收敛，未输出认证数据');
end
function [cache,serial]=extend(cache,times,serial,work,trace_path,options)
if isempty(fieldnames(cache)),missing=times;else,missing=setdiff(times,cache.times_s);end
for first=1:1024:numel(missing)
    last=min(first+1023,numel(missing));
    requested=missing(first:last);overlap=[];
    if ~isempty(fieldnames(cache))
        available=cache.times_s(cache.times_s<=requested(1));
        if ~isempty(available),overlap=max(available);end
    end
    query=unique([overlap;requested]);
    part=generate_bounded_reference(trace_path,query,options,1025);
    if ~isempty(overlap)
        old=find(cache.times_s==overlap,1);new=find(part.times_s==overlap,1);
        a=cache.coefficients(:,:,:,old);b=part.coefficients(:,:,:,new);
        assert(norm(a(:)-b(:))/norm(a(:))<1e-7 && ...
            max(abs(cache.delays_s(:,:,:,old)-part.delays_s(:,:,:,new)),[],'all')<1e-12, ...
            'QDCHANNEL1:CacheContinuity','缓存批次的公共边界不连续');
    end
    [yes,index]=ismember(requested,part.times_s);assert(all(yes));
    part.times_s=requested;part.coefficients=part.coefficients(:,:,:,index);
    part.delays_s=part.delays_s(:,:,:,index);part.residual_gain_db=part.residual_gain_db(:,:,index);
    serial=serial+1;destination=fullfile(work,sprintf('samples-%06d.mat',serial));
    temporary=[destination,'.pending'];save(temporary,'part','-v7.3');
    movefile(temporary,destination);
    cache=append(cache,part);
    fprintf('Full reference cache: %d snapshots; batch %d/%d\n',numel(cache.times_s),last,numel(missing));
end
end
function cache=append(cache,part)
if isempty(fieldnames(cache)),cache=part;return;end
cache.times_s=[cache.times_s;part.times_s];
cache.coefficients=cat(4,cache.coefficients,part.coefficients);cache.delays_s=cat(4,cache.delays_s,part.delays_s);
cache.residual_gain_db=cat(3,cache.residual_gain_db,part.residual_gain_db);
cache.metadata.antenna.wideband_error_bound=max(cache.metadata.antenna.wideband_error_bound,part.metadata.antenna.wideband_error_bound);
end
function [bad,worst,global_error]=measure(cache,knots,times)
[yes,node]=ismember(knots,cache.times_s);assert(all(yes));[yes,index]=ismember(times,cache.times_s);assert(all(yes));
h=reshape(cache.coefficients,4,[],numel(cache.times_s));d=reshape(cache.delays_s,4,[],numel(cache.times_s));
bad=false(numel(knots)-1,1);worst=0;e_total=0;p_total=0;left=1;
limit=(0.01-cache.metadata.antenna.wideband_error_bound)/2;assert(limit>0);
for n=1:numel(times)
    while left<numel(knots)-1 && times(n)>knots(left+1),left=left+1;end
    u=(times(n)-knots(left))/(knots(left+1)-knots(left));a=node(left);b=node(left+1);r=index(n);
    hp=(1-u)*h(:,:,a)+u*h(:,:,b);dp=(1-u)*d(:,:,a)+u*d(:,:,b);
    [ratio,e,p]=channel_band_error(hp,dp,h(:,:,r),d(:,:,r),4.5e6);
    fir=channel_fir_bound(hp,dp,4.5e6,7680000,p);
    space=cache.metadata.antenna.wideband_error_bound;
    % 某些衰落点 FIR 占用较多预算，仅这些区间需要进一步加密。
    % 0.95% 为选点裕量，最终仍独立按用户给定的 1% 门限验收。
    bad(left)=bad(left) || ratio>limit || (ratio+fir)*(1+space)+space>0.0095;
    worst=max(worst,ratio);e_total=e_total+e;p_total=p_total+p;
end
global_error=sqrt(e_total/p_total);
end
function report=finish(cache,knots,legacy,output_dir,endpoint,worst,global_error,iteration)
[yes,index]=ismember(knots,cache.times_s);assert(all(yes));old=find(legacy.times_s==endpoint);
c=cache.coefficients(:,:,:,index(end));ref=legacy.coefficients(:,:,:,old);
assert(norm(c(:)-ref(:))/norm(ref(:))<1e-5,'原尾段连接点系数不一致');
assert(max(abs(cache.delays_s(:,:,:,index(end))-legacy.delays_s(:,:,:,old)),[],'all')<1e-12,'原尾段连接点时延不一致');
tail=find(legacy.times_s>endpoint);times=[knots;legacy.times_s(tail)];
h=cat(4,cache.coefficients(:,:,:,index),legacy.coefficients(:,:,:,tail));
d=cat(4,cache.delays_s(:,:,:,index),legacy.delays_s(:,:,:,tail));
g=cat(3,cache.residual_gain_db(:,:,index),legacy.residual_gain_db(:,:,tail));
space=cache.metadata.antenna.wideband_error_bound;
report=struct('tolerance',0.01,'bandwidth_hz',4.5e6,'temporal_worst_nrmse',worst,'temporal_global_nrmse',global_error, ...
    'spatial_continuous_band_bound',space,'combined_bound_at_reference_times',worst*(1+space)+space, ...
    'reference_snapshots',numel(cache.times_s),'output_snapshots',numel(times),'minimum_interval_s',min(diff(times)), ...
    'maximum_interval_s',max(diff(times)),'validated_time_start_s',knots(1),'validated_time_end_s',endpoint, ...
    'unchanged_tail_snapshots',numel(tail),'method','fixed_original_power_bounded_quadriga_exact_band_integral', ...
    'iterations',iteration,'scope','prefix_before_unchanged_legacy_tail');
assert(report.combined_bound_at_reference_times<=0.01);
metadata=cache.metadata;metadata.antenna.fidelity=report;
write_qdchannel1(output_dir,times,h,d,g,metadata);
fid=fopen(fullfile(output_dir,'fidelity_report.json'),'w');fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));fclose(fid);
disp(jsonencode(report,PrettyPrint=true));
end
