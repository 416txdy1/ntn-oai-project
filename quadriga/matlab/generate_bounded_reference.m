function reference = generate_bounded_reference(trace_path,times,options,batch_size)
% 仅在固定原完整轨迹的功率参考下分块；每块包含共同初始点和前块末点。
assert(~isempty(options.normalization_anchor_path),'分块生成必须提供共同功率参考');
anchor=load(options.normalization_anchor_path,'time_s');times=times(:);
reference=struct();previous=[];max_bound=0;
for first=1:batch_size:numel(times)
    last=min(first+batch_size-1,numel(times));requested=times(first:last);
    options.snapshot_times_s=unique([anchor.time_s;previous;requested]);
    [~,part]=export_stk_to_qdchannel(trace_path,'',options);
    [present,indices]=ismember(requested,part.times_s);assert(all(present));
    if first==1
        shape=size(part.coefficients);shape(4)=numel(times);
        reference=part;reference.times_s=times;
        reference.coefficients=complex(zeros(shape));reference.delays_s=zeros(shape);
        reference.residual_gain_db=zeros(shape(1),shape(2),numel(times));
    else
        i=find(part.times_s==previous,1);
        c=part.coefficients(:,:,:,i);prior=reference.coefficients(:,:,:,first-1);
        delta=part.delays_s(:,:,:,i)-reference.delays_s(:,:,:,first-1);
        assert(norm(c(:)-prior(:))/norm(prior(:))<1e-7 && max(abs(delta),[],'all')<1e-12, ...
            'QDCHANNEL1:ChunkContinuity','共同边界不连续，禁止拼接信道');
    end
    reference.coefficients(:,:,:,first:last)=part.coefficients(:,:,:,indices);
    reference.delays_s(:,:,:,first:last)=part.delays_s(:,:,:,indices);
    reference.residual_gain_db(:,:,first:last)=part.residual_gain_db(:,:,indices);
    max_bound=max(max_bound,part.metadata.antenna.wideband_error_bound);
    previous=times(last);
    fprintf('Bounded QD: %d/%d snapshots, verified common boundary\n',last,numel(times));
end
reference.metadata.antenna.wideband_error_bound=max_bound;
end