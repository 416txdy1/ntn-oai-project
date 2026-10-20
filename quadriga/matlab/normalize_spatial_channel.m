function [normalized, excess, gain] = normalize_spatial_channel(coefficients, delays)
% 全空间矩阵共享参考：保留天线间幅度、相位及传播时延差。
assert(isequal(size(coefficients), size(delays)), '系数与时延维度不一致');
assert(all(isfinite(coefficients(:))) && all(isfinite(delays(:))) && all(delays(:) >= 0), '非法信道');
normalized = complex(zeros(size(coefficients)));
excess = zeros(size(delays));
links = size(coefficients, 1) * size(coefficients, 2);
gain = zeros(size(coefficients, 1), size(coefficients, 2), size(coefficients, 4));
reference = 1;
for snapshot = 1:size(coefficients, 4)
    values = coefficients(:, :, :, snapshot);
    tau = delays(:, :, :, snapshot);
    powers = abs(values).^2;
    total = sum(powers(:));
    assert(total > 0, '快照信道全零');
    active = powers > max(powers(:)) * 1e-12;
    earliest = min(tau(active));
    candidates = find(active & abs(tau - earliest) <= 1e-15);
    [~, strongest] = max(powers(candidates));
    current = values(candidates(strongest)) / abs(values(candidates(strongest)));
    if snapshot == 1
        reference = current;
    end
    normalized(:, :, :, snapshot) = values * (reference / current) / sqrt(total / links);
    excess(:, :, :, snapshot) = max(0, tau - earliest);
end
end
