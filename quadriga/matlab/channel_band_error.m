function [ratio,error_energy,reference_energy] = channel_band_error(h,d,reference_h,reference_d,bandwidth_hz)
% 在连续基带 [-B/2,B/2] 上积分，避免离散频率网格漏掉长时延振荡。
assert(isequal(size(h),size(d)) && isequal(size(reference_h),size(reference_d)) && size(h,1)==size(reference_h,1));
validateattributes(bandwidth_hz,{'numeric'},{'scalar','real','finite','positive'});
error_energy=0;reference_energy=0;
for port=1:size(h,1)
    error_energy=error_energy+energy([h(port,:),-reference_h(port,:)],[d(port,:),reference_d(port,:)],bandwidth_hz);
    reference_energy=reference_energy+energy(reference_h(port,:),reference_d(port,:),bandwidth_hz);
end
assert(reference_energy>0 && isfinite(error_energy),'参考带内能量必须为正且有限');
ratio=sqrt(error_energy/reference_energy);
end
function result=energy(h,d,B)
x=B*(d.'-d);kernel=ones(size(x));nonzero=x~=0;
kernel(nonzero)=sin(pi*x(nonzero))./(pi*x(nonzero));
result=max(0,real(sum((h.'*conj(h)).*kernel,'all')));
end