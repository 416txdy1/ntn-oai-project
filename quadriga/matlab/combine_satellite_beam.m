function [coefficients, delays_s] = combine_satellite_beam(element_coefficients, element_delays_s, weights)
%COMBINE_SATELLITE_BEAM [1,256,Path,Snapshot] -> [1,1,Path,Snapshot]。
% 这是一个 256 阵元单波束端口，不是 256 个 OAI 发射端口。
% 互易上行使用同一个标量有效信道，不对传播系数取共轭。

count = size(element_coefficients, 4);
elements = size(element_coefficients, 2);
paths = size(element_coefficients, 3);
if size(element_coefficients, 1) ~= 1 || elements ~= 256 || ...
        ~isequal(size(element_coefficients), size(element_delays_s)) || ...
        ~isequal(size(weights), [elements, count])
    error('QDCHANNEL1:BeamShape', '需要 [1,256,Path,Snapshot] 信道与 [256,Snapshot] 权重');
end
if any(~isfinite(weights(:))) || any(abs(sum(abs(weights).^2, 1) - 1) > 1e-10)
    error('QDCHANNEL1:BeamWeights', '每快照权重必须有限且总功率为 1');
end
coefficients = complex(zeros(1, 1, paths, count));
delays_s = zeros(1, 1, paths, count);
for snapshot = 1:count
    % MATLAB 普通转置 .' 不取共轭；权重已按发射相位补偿定义。
    taps = reshape(element_coefficients(1, :, :, snapshot), [elements, paths]);
    coefficients(1, 1, :, snapshot) = weights(:, snapshot).' * taps;
    % 与 QuaDRiGa 等幅耦合的时延约定一致：按阵元平均时延合成。
    % 小孔径时延不能精确变成一条宽带 tap，此处采用窄带阵列近似。
    delays_s(1, 1, :, snapshot) = mean(element_delays_s(1, :, :, snapshot), 2);
end
end
