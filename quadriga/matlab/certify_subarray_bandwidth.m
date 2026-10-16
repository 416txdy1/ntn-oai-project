function bound = certify_subarray_bandwidth(h,tau,weights,positions,bandwidth_hz)
% 对整个 [-B/2,B/2] 频带的 NRMSE 给出保守界，非单个频点的相对误差。
% 泰勒余项界控制分子；用 sinc 积分精确计算平均时延模型的带内能量。
validateattributes(bandwidth_hz,{'numeric'},{'scalar','finite','positive'});
ports=1+(positions(2,:)>0)+2*(positions(3,:)>0);
count=size(h,4); errors=zeros(4,count); energy=zeros(4,count);
for port=1:4
    selected=find(ports==port);
    assert(numel(selected)==64,'每个子阵必须包含 64 阵元');
    for n=1:count
        a=reshape(h(1,selected,:,n),64,[]).*(2*weights(selected,n));
        delay=reshape(tau(1,selected,:,n),64,[]);
        delta=delay-mean(delay,1); omega=pi*bandwidth_hz;
        % 保留一阶复数抵消，二阶余项用绝对值界定，覆盖整个连续频带。
        errors(port,n)=sum(omega*abs(sum(a.*delta,1)) + ...
            0.5*omega^2*sum(abs(a).*delta.^2,1));
        b=sum(a,1); dt=mean(delay,1);
        x=bandwidth_hz*(dt.'-dt); kernel=ones(size(x));
        nonzero=x~=0;kernel(nonzero)=sin(pi*x(nonzero))./(pi*x(nonzero));
        energy(port,n)=max(0,real(sum((b.'*conj(b)).*kernel,'all')));
    end
end
error_norm=sqrt(sum(errors.^2,1));
% 反三角不等式：真实带内 RMS >= 近似模型 RMS - 误差 RMS。
lower=sqrt(sum(energy,1))-error_norm;
assert(all(lower>0),'QDCHANNEL1:UncertifiableBand','误差界超过带内信号能量，无法认证');
bound=max(error_norm./lower);
assert(isfinite(bound),'QDCHANNEL1:UncertifiableBand','无法给出有限频带误差界');
end