function manifest_path = export_stk_to_qdchannel(trace_path, output_dir, options)
%EXPORT_STK_TO_QDCHANNEL 用 STK 轨迹驱动 QuaDRiGa 并导出 QDCHANNEL1。
%
% 示例：
%   options.quadriga_path = 'D:\tools\QuaDRiGa';
%   options.center_frequency_hz = 2e9;
%   options.link_direction = 'downlink';
%   export_stk_to_qdchannel('stk_trace.csv', 'qd_downlink', options);
%
% 当前实现生成卫星与 UE 之间的 SISO service link。feeder link 仍由现有
% STKTRACE2 确定性模型负责，不在本导出器中重复建模。

if nargin < 3
    options = struct();
end
options = apply_defaults(options);
matlab_dir = fileparts(mfilename('fullpath'));
addpath(matlab_dir);
quadriga_source = fullfile(options.quadriga_path, 'quadriga_src');
if exist(quadriga_source, 'dir')
    addpath(quadriga_source);
elseif exist(options.quadriga_path, 'dir')
    addpath(options.quadriga_path);
else
    error('QDCHANNEL1:QuaDRiGaPath', 'QuaDRiGa 路径不存在: %s', options.quadriga_path);
end
if exist('qd_layout', 'class') ~= 8 && exist('qd_layout', 'file') == 0
    error('QDCHANNEL1:QuaDRiGaPath', '路径中未找到 qd_layout，请指向 QuaDRiGa 根目录');
end
if ~any(strcmp(options.link_direction, {'downlink', 'uplink'}))
    error('QDCHANNEL1:Direction', 'link_direction 必须是 downlink 或 uplink');
end

trace = read_stktrace2(trace_path);
time_steps = diff(trace.times_s);
update_rate_s = median(time_steps);
tolerance = max(1e-9, abs(update_rate_s) * 1e-6);
if any(abs(time_steps - update_rate_s) > tolerance)
    error('QDCHANNEL1:TraceRate', 'QuaDRiGa 导出要求 STKTRACE2 使用均匀时间步长');
end

reference_ecef_m = trace.ue_ecef_m(:, 1);
satellite_enu_m = ecef_to_enu_track(trace.satellite_ecef_m, reference_ecef_m);
ue_enu_m = ecef_to_enu_track(trace.ue_ecef_m, reference_ecef_m);
% QuaDRiGa NTN 场景按卫星 Tx、地面 Rx 的规范方向生成。当前为 SISO，
% uplink bundle 使用该物理信道的互易表示；STK 仍分别提供 UL/DL 绝对项。
tx_positions_m = satellite_enu_m;
rx_positions_m = ue_enu_m;
if strcmp(options.link_direction, 'downlink')
    visibility = trace.dl_valid;
    tx_name = 'STK satellite downlink';
    rx_name = 'STK UE downlink';
else
    visibility = trace.ul_valid;
    tx_name = 'STK satellite reciprocal uplink reference';
    rx_name = 'STK UE reciprocal uplink reference';
end
if ~any(visibility)
    error('QDCHANNEL1:Visibility', '所选方向在 STKTRACE2 中没有任何可见快照');
end

rng(options.random_seed, 'twister');
simulation = qd_simulation_parameters;
simulation.center_frequency = options.center_frequency_hz;
simulation.sample_density = max(2.1, options.sample_density);
simulation.use_absolute_delays = 1;
layout = qd_layout(simulation);
layout.no_tx = 1;
layout.no_rx = 1;
layout.tx_array = qd_arrayant('omni');
layout.rx_array = qd_arrayant('omni');
relative_times_s = trace.times_s - trace.times_s(1);
layout.tx_track = make_track(tx_positions_m, relative_times_s, tx_name);
layout.rx_track = make_track(rx_positions_m, relative_times_s, rx_name);
layout.update_rate = update_rate_s;
layout.set_scenario(options.scenario);

channels = layout.get_channels();
channel = channels(1);
coefficients = channel.coeff;
delays_s = channel.delay;
if size(coefficients, 4) ~= numel(trace.times_s)
    error( ...
        'QDCHANNEL1:SnapshotCount', ...
        'QuaDRiGa 返回 %d 个快照，STKTRACE2 需要 %d 个；请检查 update_rate/track', ...
        size(coefficients, 4), numel(trace.times_s));
end
if ~isequal(size(coefficients), size(delays_s))
    error('QDCHANNEL1:IndividualDelay', '当前导出器要求 QuaDRiGa 提供逐天线路径时延');
end

[coefficients, delays_s, residual_gain_db] = normalize_qd_channel(coefficients, delays_s);
metadata.center_frequency_hz = options.center_frequency_hz;
metadata.link_direction = options.link_direction;
metadata.quadriga_version = get_quadriga_version(simulation, options.quadriga_version);
metadata.scenario = options.scenario;
metadata.random_seed = options.random_seed;
metadata.stk_trace_sha256 = sha256_file(trace_path);
manifest_path = write_qdchannel1( ...
    output_dir, trace.times_s, coefficients, delays_s, residual_gain_db, metadata);
end


function track = make_track(positions_m, relative_times_s, name)
% 使用非零占位长度创建对象，随后以 STK 的完整轨迹覆盖 positions。
track = qd_track('linear', 1, 0);
track.name = name;
track.initial_position = positions_m(:, 1);
relative_positions_m = positions_m - positions_m(:, 1);
segment_lengths_m = sqrt(sum(diff(relative_positions_m, 1, 2).^2, 1));
cumulative_distance_m = [0, cumsum(segment_lengths_m)];
if cumulative_distance_m(end) <= 1e-9
    % 静止端只保留一个点；get_channels 会按另一端的仿真时长自动展开。
    track.positions = zeros(3, 1);
else
    track.positions = relative_positions_m;
    track.movement_profile = [relative_times_s(:).'; cumulative_distance_m];
end
end


function options = apply_defaults(options)
defaults = struct( ...
    'quadriga_path', '', ...
    'center_frequency_hz', 2.0e9, ...
    'link_direction', 'downlink', ...
    'scenario', 'QuaDRiGa_NTN_Rural_LOS', ...
    'random_seed', 20260925, ...
    'sample_density', 2.1, ...
    'quadriga_version', '');
allowed = fieldnames(defaults);
provided = fieldnames(options);
for index = 1:numel(provided)
    if ~any(strcmp(provided{index}, allowed))
        error('QDCHANNEL1:Option', '未知选项: %s', provided{index});
    end
end
for index = 1:numel(allowed)
    name = allowed{index};
    if ~isfield(options, name)
        options.(name) = defaults.(name);
    end
end
if isempty(options.quadriga_path)
    error('QDCHANNEL1:QuaDRiGaPath', '必须显式提供 options.quadriga_path');
end
if ~isscalar(options.center_frequency_hz) || options.center_frequency_hz <= 0
    error('QDCHANNEL1:Frequency', 'center_frequency_hz 必须大于 0');
end
if ~isscalar(options.random_seed) || options.random_seed < 0 || fix(options.random_seed) ~= options.random_seed
    error('QDCHANNEL1:Seed', 'random_seed 必须是非负整数');
end
end


function version = get_quadriga_version(simulation, override)
if ~isempty(override)
    version = char(override);
    return;
end
version = 'unreported';
if isprop(simulation, 'version')
    reported = simulation.version;
    if isnumeric(reported)
        version = num2str(reported);
    elseif ischar(reported) || isstring(reported)
        version = char(reported);
    end
end
end
