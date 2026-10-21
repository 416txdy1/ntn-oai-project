function [coefficients, delays_s, metadata] = combine_satellite_subarrays(element_coefficients, element_delays_s, weights, positions)
% 256 阵元分为互不重叠的四个 8x8 子阵，各自保留一个 RF 端口。
% weights 是全阵单位范数 LOS 权重；子阵内乘 2 后各列范数为 1。
count = size(element_coefficients, 4);
paths = size(element_coefficients, 3);
assert(size(element_coefficients,1) == 1 && size(element_coefficients,2) == 256, '需要 256 阵元信道');
assert(isequal(size(element_coefficients),size(element_delays_s)), '系数与时延维度不一致');
assert(isequal(size(weights),[256,count]) && isequal(size(positions),[3,256]), '权重或几何维度错误');
assert(all(isfinite(weights(:))) && all(isfinite(positions(:))), '权重或几何非有限');
assert(all(isfinite(element_coefficients(:))) && all(isfinite(element_delays_s(:))) && all(element_delays_s(:)>=0), '非法信道');
% 端口顺序：(-y,-z)、(+y,-z)、(-y,+z)、(+y,+z)。
port_map = 1 + double(positions(2,:)>0) + 2*double(positions(3,:)>0);
assert(all(positions(2,:)~=0 & positions(3,:)~=0), '分区边界上存在阵元');
coefficients = complex(zeros(1,4,paths,count));
delays_s = zeros(1,4,paths,count);
max_span = 0;
for port = 1:4
    selected = find(port_map==port);
    assert(numel(selected)==64, '每个子阵必须包含 64 个阵元');
    sub_weights = 2*weights(selected,:);
    assert(all(abs(sum(abs(sub_weights).^2,1)-1)<1e-10), '每个子阵权重范数必须为 1');
    tau = element_delays_s(:,selected,:,:);
    span = max(tau,[],2)-min(tau,[],2);
    max_span = max(max_span,max(span(:)));
    for snapshot = 1:count
        taps = reshape(element_coefficients(1,selected,:,snapshot),[64,paths]);
        coefficients(1,port,:,snapshot) = sub_weights(:,snapshot).' * taps;
        % 子阵内部采用窄带时延近似，不跨 RF 端口平均。
        delays_s(1,port,:,snapshot) = mean(tau(1,:,:,snapshot),2);
    end
end
metadata = struct('subarray_rows',8,'subarray_columns',8, ...
    'element_port_map',port_map,'element_index_base',1, ...
    'port_order','negative_y_negative_z,positive_y_negative_z,negative_y_positive_z,positive_y_positive_z', ...
    'subarray_weight_norm2',1,'max_subarray_delay_span_s',max_span, ...
    'delay_reduction','uniform_subarray_mean_narrowband');
end
