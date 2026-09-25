function [normalized, excess_delays_s, residual_gain_db] = normalize_qd_channel(coefficients, delays_s)
%NORMALIZE_QD_CHANNEL 将 QuaDRiGa [Rx,Tx,Path,Snapshot] 输出转换为残余信道。
%
% STKTRACE2 已负责公共传播时延、主体 Doppler 和绝对增益。本函数：
% 1. 用最早激活路径稳定每个天线链路的公共相位；
% 2. 每个快照按路径总功率归一化；
% 3. 将绝对路径时延改为相对超额时延；
% 4. 将原总功率转换为每个天线链路零均值的残余增益。

if ~isequal(size(coefficients), size(delays_s))
    error('QDCHANNEL1:ChannelShape', 'coefficients 与 delays 必须具有相同维度');
end
if ndims(coefficients) ~= 4 || size(coefficients, 4) < 2
    error('QDCHANNEL1:ChannelShape', '输入必须是至少两个快照的 [Rx,Tx,Path,Snapshot]');
end
if any(~isfinite(real(coefficients(:)))) || any(~isfinite(imag(coefficients(:))))
    error('QDCHANNEL1:ChannelFinite', '系数包含非有限值');
end
if any(~isfinite(delays_s(:))) || any(delays_s(:) < 0)
    error('QDCHANNEL1:DelayFinite', '时延必须有限且非负');
end

rx_count = size(coefficients, 1);
tx_count = size(coefficients, 2);
path_count = size(coefficients, 3);
snapshot_count = size(coefficients, 4);
relative_power_epsilon = 1e-12;
normalized = complex(zeros(size(coefficients)), zeros(size(coefficients)));
excess_delays_s = zeros(size(delays_s));
raw_gain_db = zeros(rx_count, tx_count, snapshot_count);
phase_reference = complex(zeros(rx_count, tx_count), zeros(rx_count, tx_count));
reference_set = false(rx_count, tx_count);

for snapshot = 1:snapshot_count
    for rx = 1:rx_count
        for tx = 1:tx_count
            group = reshape(coefficients(rx, tx, :, snapshot), [path_count, 1]);
            group_delays = reshape(delays_s(rx, tx, :, snapshot), [path_count, 1]);
            powers = abs(group).^2;
            total_power = sum(powers);
            if ~isfinite(total_power) || total_power <= 0
                error('QDCHANNEL1:InactiveLink', '快照 %d 的 Rx %d/Tx %d 没有激活路径', snapshot, rx, tx);
            end
            % NTN 绝对路径功率可能远小于 1e-15，激活判断必须相对峰值进行。
            active = powers > max(powers) * relative_power_epsilon;
            earliest_delay = min(group_delays(active));
            candidates = find(active & abs(group_delays - earliest_delay) <= 1e-15);
            [~, strongest] = max(powers(candidates));
            reference_path = candidates(strongest);
            current_reference = group(reference_path) / abs(group(reference_path));
            if ~reference_set(rx, tx)
                phase_reference(rx, tx) = current_reference;
                reference_set(rx, tx) = true;
            end
            rotation = phase_reference(rx, tx) / current_reference;
            normalized(rx, tx, :, snapshot) = group * rotation / sqrt(total_power);
            excess_delays_s(rx, tx, :, snapshot) = max(0, group_delays - earliest_delay);
            raw_gain_db(rx, tx, snapshot) = 10 * log10(total_power);
        end
    end
end

residual_gain_db = raw_gain_db - mean(raw_gain_db, 3);
end
