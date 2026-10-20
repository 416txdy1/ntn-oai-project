function sampled = resample_stk_geometry(trace, interval_s, window_s, explicit_times_s)
% 使用与运行时相同的 Hermite 位置/速度约定，独立细化 QD 几何时间轴。
if nargin>=4 && ~isempty(explicit_times_s)
    times=explicit_times_s(:);
    assert(numel(times)>=2 && all(isfinite(times)) && all(diff(times)>0) && times(1)>=trace.times_s(1) && times(end)<=trace.times_s(end), '显式时间轴非法');
else
    validateattributes(interval_s, {'numeric'}, {'scalar','real','finite','positive'});
    if isempty(window_s), window_s = [trace.times_s(1),trace.times_s(end)]; end
    assert(numel(window_s)==2 && all(isfinite(window_s)) && window_s(1)>=trace.times_s(1) && window_s(2)<=trace.times_s(end) && window_s(2)>window_s(1), '采样窗口非法');
    steps = round(diff(window_s)/interval_s);
    assert(steps>=1 && abs(steps*interval_s-diff(window_s))<1e-8, '窗口必须包含整数个采样间隔');
    times = linspace(window_s(1),window_s(2),steps+1).';
end
sampled = trace;
sampled.times_s = times;
sampled.satellite_ecef_m = zeros(3,numel(times));
sampled.satellite_velocity_ecef_m = zeros(3,numel(times));
sampled.gnb_ecef_m = zeros(3,numel(times));
sampled.ue_ecef_m = zeros(3,numel(times));
sampled.dl_valid = false(numel(times),1);
sampled.ul_valid = false(numel(times),1);
for n = 1:numel(times)
    i = find(trace.times_s<=times(n),1,'last');
    i = min(i,numel(trace.times_s)-1);
    dt = trace.times_s(i+1)-trace.times_s(i);
    u = (times(n)-trace.times_s(i))/dt;
    p0 = trace.satellite_ecef_m(:,i); p1 = trace.satellite_ecef_m(:,i+1);
    v0 = trace.satellite_velocity_ecef_m(:,i); v1 = trace.satellite_velocity_ecef_m(:,i+1);
    a1=dt*v0; a2=3*(p1-p0)-dt*(2*v0+v1); a3=-2*(p1-p0)+dt*(v0+v1);
    sampled.satellite_ecef_m(:,n)=p0+u*(a1+u*(a2+u*a3));
    sampled.satellite_velocity_ecef_m(:,n)=(a1+u*(2*a2+3*u*a3))/dt;
    for field = {'gnb_ecef_m','ue_ecef_m'}
        value=trace.(field{1});
        sampled.(field{1})(:,n)=(1-u)*value(:,i)+u*value(:,i+1);
    end
    for field = {'dl_valid','ul_valid'}
        value=trace.(field{1});
        if u==0, valid=value(i); elseif u==1, valid=value(i+1); else, valid=value(i)&&value(i+1); end
        sampled.(field{1})(n)=valid;
    end
end
end
