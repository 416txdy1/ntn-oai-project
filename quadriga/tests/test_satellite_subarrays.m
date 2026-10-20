function test_satellite_subarrays()
% 可手算的相干场验证，独立检查功率、端口映射和全阵等价性。
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root,'quadriga','matlab'));
[y,z] = ndgrid((0:15)-7.5,(0:15)-7.5);
pos = [zeros(1,256); y(:).'; z(:).'];
map = 1 + (pos(2,:)>0) + 2*(pos(3,:)>0);
phase = (1:256)'*[0.01,0.03];
w = exp(1j*phase)/16;
a = [1,2i,-1,0.5];
h = complex(zeros(1,256,2,2));
tau = zeros(size(h));
for snap = 1:2
    for path = 1:2
        h(1,:,path,snap) = a(map).*exp(-1j*phase(:,snap).')/path;
        tau(1,:,path,snap) = 1e-3 + map*1e-9 + path*1e-6;
    end
end
[c,d,m] = combine_satellite_subarrays(h,tau,w,pos);
assert(isequal(size(c),[1,4,2,2]));
assert(isequal(m.element_port_map,map));
for snap = 1:2
    W = complex(zeros(256,4));
    for port = 1:4
        W(map==port,port) = 2*w(map==port,snap);
        assert(abs(c(1,port,1,snap)-8*a(port))<1e-12);
        assert(abs(d(1,port,1,snap)-(1e-3+port*1e-9+1e-6))<1e-15);
    end
    assert(max(abs(W'*W-eye(4)),[],'all')<1e-12);
    x = [1;2i;-3;0.5];
    assert(abs(norm(W*x)^2-norm(x)^2)<1e-12);
end
assert(abs(abs(c(1,1,1,1))^2-64)<1e-12);
[full,full_delay] = combine_satellite_beam(h,tau,w);
assert(max(abs(sum(c,2)/2-full),[],'all')<1e-12);
assert(max(abs(mean(d,2)-full_delay),[],'all')<1e-15);
[n,~,~] = normalize_spatial_channel(c,d);
assert(abs(n(1,2,1,1)/n(1,1,1,1)-2i)<1e-12);
% 重排元素后仍按物理坐标分区，避免把连续 64 个元素误当 8x8。
order = 256:-1:1;
[permuted,~,~] = combine_satellite_subarrays(h(:,order,:,:),tau(:,order,:,:),w(order,:),pos(:,order));
assert(max(abs(permuted-c),[],'all')<1e-12);
rejected = false;
try
    combine_satellite_subarrays(h,tau,2*w,pos);
catch
    rejected = true;
end
assert(rejected,'必须拒绝功率翻倍的错误权重');
fprintf('PASS four subarrays: 64 elements/port, gain 64, W^H W=I, power conservation, full-array equivalence, phase/delay, permutation\n');
end
