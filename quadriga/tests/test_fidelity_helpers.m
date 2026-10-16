function test_fidelity_helpers
% 独立解析几何和逐阵元频响验证，避免只复述实现。
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root,'quadriga','matlab'));
t=struct('times_s',[0;2],'satellite_ecef_m',[0,8;1,1;2,2], ...
    'satellite_velocity_ecef_m',[0,12;0,0;0,0], ...
    'gnb_ecef_m',zeros(3,2),'ue_ecef_m',ones(3,2),'dl_valid',[true;false],'ul_valid',[true;true]);
r=resample_stk_geometry(t,0.25,[]);
assert(max(abs(r.satellite_ecef_m(1,:)-r.times_s.'.^3))<1e-12);
assert(max(abs(r.satellite_velocity_ecef_m(1,:)-3*r.times_s.'.^2))<1e-12);
assert(r.dl_valid(1) && ~any(r.dl_valid(2:end)) && all(r.ul_valid));
r=resample_stk_geometry(t,[],[],[0;0.123;1.7;2]);
assert(max(abs(r.satellite_ecef_m(1,:)-r.times_s.'.^3))<1e-12);
failed=false; try, resample_stk_geometry(t,[],[],[0;0;2]); catch, failed=true; end
assert(failed,'必须拒绝重复时间');
[y,z]=ndgrid(-7.5:7.5,-7.5:7.5); positions=[zeros(1,256);y(:).';z(:).']*0.06;
h=complex(ones(1,256,1,2)); weights=ones(256,2)/16;
tau=reshape(1e-3+positions(2,:)/299792458,1,256,1,1);tau=repmat(tau,1,1,1,2);
bound=certify_subarray_bandwidth(h,tau,weights,positions,4.5e6);
assert(bound<0.01 && bound>0);
map=1+(positions(2,:)>0)+2*(positions(3,:)>0);
f=linspace(-2.25e6,2.25e6,1031); e=0;power=0;
for port=1:4
    d=reshape(tau(1,map==port,1,1),[],1);d=d-1e-3;
    exact=sum(exp(-2j*pi*d*f),1)/8;
    approx=8*exp(-2j*pi*mean(d)*f);
    e=e+sum(abs(approx-exact).^2);power=power+sum(abs(exact).^2);
end
direct_error=sqrt(e/power);
assert(direct_error<=bound);
rejected=false;
try
    rejected=certify_subarray_bandwidth(h,tau,weights,positions,1e9)>0.01;
catch exception
    assert(strcmp(exception.identifier,'QDCHANNEL1:UncertifiableBand'));
    rejected=true;
end
assert(rejected,'大带宽不能错误认证');
% 一个 129 点频率网格会完全漏检的反例：每格恰好转一圈。
[ratio,e,p]=channel_band_error(1,0,1,128/4.5e6,4.5e6);
assert(abs(ratio-sqrt(2))<1e-12 && abs(e-2)<1e-12 && p==1);
f_alias=linspace(-2.25e6,2.25e6,129);
assert(max(abs(1-exp(-2j*pi*(128/4.5e6)*f_alias)))<1e-10);
[ratio,~,~]=channel_band_error([1,0.2j],[0,2e-6],[1,0.2j],[0,2e-6],4.5e6);
assert(ratio<1e-7,'相同多径频响误差必须为零');
% 参数冲突应在创建 QuaDRiGa 对象之前拒绝。
failed=false;
try
    export_stk_to_qdchannel('unused','',struct('quadriga_path','unused', ...
        'snapshot_interval_s',0.01,'snapshot_times_s',[0;1]));
catch exception
    failed=contains(exception.message,'不得同时指定');
end
assert(failed);
fprintf('PASS fidelity helpers: cubic geometry, visibility, invalid grid, spectral bound %.9g >= direct error %.9g, unsafe bandwidth rejected\n',bound,direct_error);
end