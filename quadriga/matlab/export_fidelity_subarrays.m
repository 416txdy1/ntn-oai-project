function report = export_fidelity_subarrays(direction, output_dir, window_s)
% 用真实 QD 加密点验收非均匀时间网格，不对旧 1s 系数做伪加密。
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
trace_path=fullfile(root,'examples','fdd-pass','trace.csv');
trace=read_stktrace2(trace_path);
if nargin<3 || isempty(window_s), window_s=[trace.times_s(1),trace.times_s(end)]; end
assert(~exist(output_dir,'dir'),'禁止覆盖已有导出数据');
assert(any(strcmp(direction,{'downlink','uplink'})),'非法链路方向');
validateattributes(window_s,{'numeric'},{'vector','numel',2,'real','finite'});
assert(window_s(1)>=trace.times_s(1) && window_s(2)<=trace.times_s(end) && window_s(2)>window_s(1),'非法验收窗口');
work_dir=[char(output_dir),'.work'];
if ~exist(work_dir,'dir'), mkdir(work_dir); end
signature={direction,sha256_file(trace_path)};
for name={'export_stk_to_qdchannel','resample_stk_geometry','combine_satellite_subarrays','normalize_spatial_channel','certify_subarray_bandwidth'}
    signature{end+1}=sha256_file(fullfile(root,'quadriga','matlab',[name{1},'.m']));
end
knots=unique([window_s(1);trace.times_s(trace.times_s>window_s(1)&trace.times_s<window_s(2));window_s(2)]);
options=struct('quadriga_path',fullfile(root,'.runtime','quadriga'), ...
    'antenna_profile','satellite_16x16_4port_ground_omni','array_reference_frequency_hz',2488400000, ...
    'link_direction',direction,'fidelity_tolerance',0.01,'bandwidth_hz',4.5e6);
if strcmp(direction,'downlink'), options.center_frequency_hz=2488400000; else, options.center_frequency_hz=1614900000; end
fractions=unique([0:0.125:1,(3-sqrt(5))/2,(sqrt(5)-1)/2]);

for iteration=1:9
    candidates=unique([knots;reshape(knots(1:end-1)+(knots(2:end)-knots(1:end-1))*fractions,[],1)]);
    assert(numel(candidates)<=24000,'自适应参考超过内存保护上限；未生成声称通过的数据');
    fprintf('Fidelity %s iteration %d: %d knots, %d real reference snapshots\n',direction,iteration,numel(knots),numel(candidates));
    options.snapshot_times_s=candidates;
    cache_path=fullfile(work_dir,sprintf('iteration-%d.mat',iteration));
    cached=struct();
    if exist(cache_path,'file')
        try, cached=load(cache_path);
        catch, warning('QDCHANNEL1:Checkpoint','检查点损坏，重新生成: %s',cache_path); end
    end
    if isfield(cached,'signature') && isequal(cached.signature,signature) && isequal(cached.candidates,candidates)
        reference=cached.reference;
        fprintf('Fidelity: reused verified generation inputs from %s\n',cache_path);
    else
        [~,reference]=export_stk_to_qdchannel(trace_path,'',options);
        save(cache_path,'signature','candidates','reference','-v7.3');
    end
    clear cached;
    [present,indices]=ismember(knots,candidates); assert(all(present));
    h=reshape(reference.coefficients,4,[],numel(candidates));
    d=reshape(reference.delays_s,4,[],numel(candidates));
    bad=false(numel(knots)-1,1); error_energy=0; reference_energy=0; worst=0;
    space_bound=reference.metadata.antenna.wideband_error_bound;
    time_limit=(0.01-space_bound)/2;
    assert(time_limit>0,'子阵误差界已耗尽误差预算');
    left=1;
    for n=1:numel(candidates)
        while left<numel(knots)-1 && candidates(n)>knots(left+1), left=left+1; end
        lo=indices(left); hi=indices(left+1);
        u=(candidates(n)-knots(left))/(knots(left+1)-knots(left));
        [ratio,e,p]=channel_band_error((1-u)*h(:,:,lo)+u*h(:,:,hi), ...
            (1-u)*d(:,:,lo)+u*d(:,:,hi),h(:,:,n),d(:,:,n),options.bandwidth_hz);
         worst=max(worst,ratio); error_energy=error_energy+e; reference_energy=reference_energy+p;
        if ratio>time_limit, bad(left)=true; end
    end
    fprintf('Fidelity: worst temporal %.9g, global %.9g, continuous-band spatial bound %.9g, temporal budget %.9g\n',worst,sqrt(error_energy/reference_energy),space_bound,time_limit);
    if ~any(bad)
        metadata=reference.metadata;
        report=struct('tolerance',0.01,'bandwidth_hz',4.5e6,'temporal_worst_nrmse',worst, ...
            'temporal_global_nrmse',sqrt(error_energy/reference_energy),'spatial_continuous_band_bound',space_bound, ...
            'combined_bound_at_reference_times',worst*(1+space_bound)+space_bound, ...
            'reference_snapshots',numel(candidates),'output_snapshots',numel(knots), ...
            'minimum_interval_s',min(diff(knots)),'maximum_interval_s',max(diff(knots)), ...
            'method','real_quadriga_holdout_exact_band_integral','iterations',iteration);
        assert(report.combined_bound_at_reference_times<=0.01);
        metadata.antenna.fidelity=report;
        write_qdchannel1(output_dir,knots,reference.coefficients(:,:,:,indices),reference.delays_s(:,:,:,indices),reference.residual_gain_db(:,:,indices),metadata);
        % 保留实际验证时间轴和输出报告，使有限采样验收可复现、可追查。
        save(fullfile(output_dir,'fidelity_reference.mat'),'candidates','indices','report','reference','-v7');
        fid=fopen(fullfile(output_dir,'fidelity_report.json'),'w');fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));fclose(fid);
        return;
    end
    % 只加密未达到误差预算的区间，所有新节点仍为下一轮实际生成输入。
    refined=reshape(knots(find(bad))+(knots(find(bad)+1)-knots(find(bad)))*(0.125:0.125:0.875),[],1);
    knots=unique([knots;refined]);
end
error('QDCHANNEL1:Fidelity','达到迭代上限仍未收敛，未写出通过的 bundle');
end
