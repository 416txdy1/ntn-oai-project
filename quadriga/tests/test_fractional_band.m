function test_fractional_band()
% 独立复频率积分验证 FIR 上界，包含相消多径和整数时延。
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));addpath(fullfile(root,'quadriga','matlab'));
bandwidth=4.5e6;fs=7680000;nodes=-5:6;
worst=0;
for fraction=[0,1e-8,0.07,0.25,0.5,0.99,1-1e-8]
    h=[1,0.2j;0.7,-0.3];delay=[fraction,2.2;0.125,3.87]/fs;
    expanded=zeros(2,24);grid=zeros(2,24);
    for port=1:2
        for path=1:2
            x=delay(port,path)*fs;u=x-floor(x);w=ones(1,12);
            for j=1:12
                others=setdiff(1:12,j);w(j)=prod((u-nodes(others))./(nodes(j)-nodes(others)));
            end
            ix=(path-1)*12+(1:12);expanded(port,ix)=h(port,path)*w;grid(port,ix)=(floor(x)+nodes)/fs;
        end
    end
    [actual,~,power]=channel_band_error(expanded,grid,h,delay,bandwidth);
    certified=channel_fir_bound(h,delay,bandwidth,fs,power);
    assert(actual<=certified+1e-8);worst=max(worst,actual);
end
% 旧三次插值在半采样处不满足 1%，新核可由直接频带积分证明改善。
u=0.5;old_nodes=0:3;w=ones(1,4);
for j=1:4
    other=setdiff(1:4,j);w(j)=prod((u-old_nodes(other))./(old_nodes(j)-old_nodes(other)));
end
old=channel_band_error(w,old_nodes/fs,1,u/fs,bandwidth);
new_bound=channel_fir_bound(1,u/fs,bandwidth,fs,1);
assert(old>0.01 && new_bound<0.005);
fprintf('PASS fractional bandwidth: old %.9g, symmetric bound %.9g, multipath worst %.9g\n',old,new_bound,worst);
end
