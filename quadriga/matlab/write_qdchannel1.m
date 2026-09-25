function manifest_path = write_qdchannel1(output_dir, times_s, coefficients, delays_s, residual_gain_db, metadata)
%WRITE_QDCHANNEL1 将 [Rx,Tx,Path,Snapshot] 数组写为 QDCHANNEL1 bundle。

times_s = times_s(:);
rx_count = size(coefficients, 1);
tx_count = size(coefficients, 2);
path_count = size(coefficients, 3);
snapshot_count = size(coefficients, 4);
if snapshot_count < 2 || numel(times_s) ~= snapshot_count
    error('QDCHANNEL1:WriteShape', '时间数量必须等于至少两个信道快照');
end
if ~isequal(size(coefficients), size(delays_s))
    error('QDCHANNEL1:WriteShape', '系数和时延维度必须一致');
end
if ~isequal(size(residual_gain_db), [rx_count, tx_count, snapshot_count])
    error('QDCHANNEL1:WriteShape', '残余增益必须是 [Rx,Tx,Snapshot]');
end
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

times_path = fullfile(output_dir, 'times.f64');
delays_path = fullfile(output_dir, 'delays.f64');
coefficients_path = fullfile(output_dir, 'coefficients.cf32');
gain_path = fullfile(output_dir, 'residual_gain_db.f32');

write_numeric(times_path, times_s, 'double');
% MATLAB 按列存储。P,T,R,S 排列使磁盘上 path 最快、snapshot 最慢。
ordered_delays = permute(delays_s, [3, 2, 1, 4]);
write_numeric(delays_path, ordered_delays, 'double');
ordered_coefficients = single(permute(coefficients, [3, 2, 1, 4]));
interleaved = zeros(2, numel(ordered_coefficients), 'single');
interleaved(1, :) = real(ordered_coefficients(:));
interleaved(2, :) = imag(ordered_coefficients(:));
write_numeric(coefficients_path, interleaved, 'single');
ordered_gain = single(permute(residual_gain_db, [2, 1, 3]));
write_numeric(gain_path, ordered_gain, 'single');

manifest.format = 'QDCHANNEL1';
manifest.schema_version = 1;
manifest.byte_order = 'little';
manifest.axes = {'snapshot', 'rx', 'tx', 'path'};
manifest.dimensions = struct( ...
    'snapshots', snapshot_count, ...
    'rx_antennas', rx_count, ...
    'tx_antennas', tx_count, ...
    'paths', path_count);
manifest.radio = struct( ...
    'center_frequency_hz', metadata.center_frequency_hz, ...
    'link_direction', metadata.link_direction);
manifest.time = struct( ...
    'coordinate', 'stk_trace_seconds', ...
    'interpolation', 'linear_complex_and_delay', ...
    'out_of_range', 'mute');
manifest.composition = struct( ...
    'bulk_delay_source', 'STKTRACE2', ...
    'bulk_doppler_source', 'STKTRACE2', ...
    'absolute_gain_source', 'STKTRACE2', ...
    'quadriga_delay', 'relative_excess_seconds', ...
    'quadriga_coefficients', 'unit_snapshot_link_power', ...
    'quadriga_large_scale_gain', 'zero_mean_residual_db');
manifest.provenance = struct( ...
    'quadriga_version', metadata.quadriga_version, ...
    'scenario', metadata.scenario, ...
    'random_seed', metadata.random_seed, ...
    'stk_trace_sha256', metadata.stk_trace_sha256);
tap_count = snapshot_count * rx_count * tx_count * path_count;
link_count = snapshot_count * rx_count * tx_count;
manifest.files = struct( ...
    'times', file_spec(times_path, 'float64', snapshot_count), ...
    'delays', file_spec(delays_path, 'float64', tap_count), ...
    'coefficients', file_spec(coefficients_path, 'complex64_interleaved', tap_count), ...
    'residual_gain_db', file_spec(gain_path, 'float32', link_count));

manifest_path = fullfile(output_dir, 'manifest.json');
fid = fopen(manifest_path, 'wt');
if fid < 0
    error('QDCHANNEL1:ManifestOpen', '无法写入 manifest: %s', manifest_path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, '%s\n', jsonencode(manifest));
end


function write_numeric(path, values, precision)
fid = fopen(path, 'wb', 'ieee-le');
if fid < 0
    error('QDCHANNEL1:BinaryOpen', '无法写入: %s', path);
end
cleanup = onCleanup(@() fclose(fid));
written = fwrite(fid, values, precision);
if written ~= numel(values)
    error('QDCHANNEL1:BinaryWrite', '写入不完整: %s', path);
end
end


function spec = file_spec(path, dtype, count)
info = dir(path);
spec = struct( ...
    'path', info.name, ...
    'dtype', dtype, ...
    'count', count, ...
    'bytes', info.bytes, ...
    'sha256', sha256_file(path));
end
