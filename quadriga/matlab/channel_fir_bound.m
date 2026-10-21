function bound = channel_fir_bound(h, delays_s, bandwidth_hz, sample_rate_hz, reference_energy)
% 对实际分数时延逐路径积分，再用三角不等式保守合成端口误差。
% 对称 12 点核与 RFsim 一致；积分覆盖整个占用频带，无频率采样混叠。
assert(isequal(size(h),size(delays_s)) && reference_energy>0);
nodes=-5:6;u=mod(delays_s(:)*sample_rate_hz,1);
w=ones(numel(u),12);
for j=1:12
    for k=1:12
        if j~=k,w(:,j)=w(:,j).*(u-nodes(k))/(nodes(j)-nodes(k));end
    end
end
q=bandwidth_hz/sample_rate_hz;
kernel=normalized_sinc(q*(nodes.'-nodes));
cross=normalized_sinc(q*(u-nodes));
energy=max(0,sum((w*kernel).*w,2)-2*sum(w.*cross,2)+1);
% 浮点消减留出保守裕量，避免零附近的负舍入误差被当成精确零。
energy=energy+128*eps.*(1+sum(abs(w),2).^2);
per_path=abs(h).*reshape(sqrt(energy),size(h));
bound=norm(sum(per_path,2))/sqrt(reference_energy);
end

function y=normalized_sinc(x)
y=ones(size(x));nz=x~=0;y(nz)=sin(pi*x(nz))./(pi*x(nz));
end
