function [manifest_path, result] = export_stk_to_qdchannel(trace_path, output_dir, options)
%EXPORT_STK_TO_QDCHANNEL 用 STK 轨迹驱动 QuaDRiGa 并导出 QDCHANNEL1。
%
% 示例：
%   options.quadriga_path = 'D:\tools\QuaDRiGa';
%   options.center_frequency_hz = 2e9;
%   options.link_direction = 'downlink';
%   export_stk_to_qdchannel('stk_trace.csv', 'qd_downlink', options);
%
% 当前实现生成卫星与 UE 之间的单/多端口 service link。feeder link 仍由现有
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
explicit_grid = ~isempty(options.snapshot_times_s);
if explicit_grid
    trace = resample_stk_geometry(trace, [], [], options.snapshot_times_s);
elseif ~isempty(options.snapshot_interval_s)
    trace = resample_stk_geometry(trace, options.snapshot_interval_s, options.time_window_s);
elseif ~isempty(options.time_window_s)
    error('QDCHANNEL1:TimeWindow', '指定窗口时必须同时指定 snapshot_interval_s');
end
time_steps = diff(trace.times_s);
update_rate_s = median(time_steps);
tolerance = max(1e-9, abs(update_rate_s) * 1e-6);
if ~explicit_grid && any(abs(time_steps - update_rate_s) > tolerance)
    error('QDCHANNEL1:TraceRate', 'QuaDRiGa 导出要求 STKTRACE2 使用均匀时间步长');
end

reference_ecef_m = trace.ue_ecef_m(:, 1);
satellite_enu_m = ecef_to_enu_track(trace.satellite_ecef_m, reference_ecef_m);
ue_enu_m = ecef_to_enu_track(trace.ue_ecef_m, reference_ecef_m);
% QuaDRiGa NTN 场景按卫星 Tx、地面 Rx 的规范方向生成。
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
layout.rx_array = qd_arrayant('omni');
layout.rx_array.center_frequency = options.center_frequency_hz;
relative_times_s = trace.times_s - trace.times_s(1);
layout.tx_track = make_track(tx_positions_m, relative_times_s, tx_name, explicit_grid);
layout.rx_track = make_track(rx_positions_m, relative_times_s, rx_name, explicit_grid);
if any(strcmp(options.antenna_profile, {'satellite_16x16_ground_omni', 'satellite_16x16_4port_ground_omni'}))
    layout.tx_array = create_satellite_array(options.center_frequency_hz);
    if strcmp(options.antenna_profile, 'satellite_16x16_4port_ground_omni')
        % FDD 两方向使用同一个物理孔径，波数仍按实际载频计算。
        layout.tx_array.element_position = layout.tx_array.element_position * ...
            options.center_frequency_hz / options.array_reference_frequency_hz;
    end
    [orientation, beam_weights, antenna_metadata] = satellite_beam_geometry( ...
        layout.tx_array, trace, visibility);
    layout.tx_track.orientation = orientation;
elseif any(strcmp(options.antenna_profile, {'satellite_2port_ground_omni', 'satellite_4port_ground_omni'}))
    % 独立半波长间距阵元，固定 ENU 朝向；不离线合成。
    ports = 2;
    if strcmp(options.antenna_profile, 'satellite_4port_ground_omni'), ports = 4; end
    layout.tx_array = qd_arrayant('omni');
    layout.tx_array.center_frequency = options.center_frequency_hz;
    layout.tx_array.no_elements = ports;
    spacing = qd_simulation_parameters.speed_of_light / options.center_frequency_hz / 2;
    layout.tx_array.element_position = [zeros(1, ports); ((0:ports-1)-(ports-1)/2)*spacing; zeros(1, ports)];
    layout.tx_array.coupling = eye(ports);
    antenna_metadata = struct('profile', options.antenna_profile, ...
        'satellite_rf_ports', ports, 'ground_rf_ports', 1, 'spacing_wavelengths', 0.5, ...
        'orientation', 'fixed_ENU', 'absolute_array_gain_source', 'not_calibrated_STK_reference');
else
    layout.tx_array = qd_arrayant('omni');
    layout.tx_array.center_frequency = options.center_frequency_hz;
    antenna_metadata = struct('profile', 'omni', 'satellite_rf_ports', 1, 'ground_rf_ports', 1);
end
if explicit_grid, layout.update_rate = []; else, layout.update_rate = update_rate_s; end
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

if ~isempty(options.normalization_anchor_path)
    % QuaDRiGa 的簇功率校正依赖生成网格；使用原完整轨迹的同一初始快照
    % 固定各阵元/路径的实数缩放，防止分块后改变信道实现或出现幅度接缝。
    anchor=load(options.normalization_anchor_path);
    assert(anchor.frequency_hz==options.center_frequency_hz && ...
        strcmp(anchor.trace_sha256,sha256_file(trace_path)) && anchor.random_seed==options.random_seed && ...
        strcmp(anchor.scenario,options.scenario),'功率参考来源不匹配');
    assert(trace.times_s(1)==anchor.time_s && isequal(size(coefficients(:,:,:,1)),size(anchor.coefficients)), ...
        '分块生成必须保留共同初始快照');
    current=coefficients(:,:,:,1);
    assert(all(abs(current(:))>0) && all(abs(anchor.coefficients(:))>0),'零系数无法用初始点标定');
    phase_difference=angle(current./anchor.coefficients);
    assert(max(abs(phase_difference),[],'all')<1e-5,'QDCHANNEL1:AnchorPhase','分块信道相位不一致，禁止拼接');
    coefficients=coefficients.*(abs(anchor.coefficients)./abs(current));
    antenna_metadata.cluster_power_reference_sha256=sha256_file(options.normalization_anchor_path);
end

if ~isempty(options.diagnostic_mat_path)
    % 诊断缓存只由调用者显式指定；保留未平均的逐阵元路径和时延。
    positions = layout.tx_array.element_position;
    assert(exist('beam_weights','var')==1, '逐阵元诊断仅支持阵列 profile');
    frequency_hz = options.center_frequency_hz;
    times_s = trace.times_s;
    save(options.diagnostic_mat_path, 'coefficients','delays_s','beam_weights','positions','frequency_hz','times_s','-v7.3');
end
if strcmp(options.antenna_profile, 'satellite_16x16_4port_ground_omni')
    element_coefficients=coefficients; element_delays=delays_s;
    [coefficients, delays_s, mapping] = combine_satellite_subarrays(coefficients, delays_s, beam_weights, layout.tx_array.element_position);
    if ~isempty(options.fidelity_tolerance)
        mapping.wideband_error_bound = certify_subarray_bandwidth(element_coefficients,element_delays,beam_weights,layout.tx_array.element_position,options.bandwidth_hz);
        assert(mapping.wideband_error_bound<=options.fidelity_tolerance, 'QDCHANNEL1:WidebandTolerance', '子阵时延近似超过误差门限');
        mapping.validated_bandwidth_hz = options.bandwidth_hz;
    end
    fields = fieldnames(mapping);
    for k = 1:numel(fields), antenna_metadata.(fields{k}) = mapping.(fields{k}); end
    antenna_metadata.profile = options.antenna_profile;
    antenna_metadata.satellite_rf_ports = 4;
    antenna_metadata.absolute_array_gain_source = 'not_calibrated_STK_reference';
    antenna_metadata.array_reference_frequency_hz = options.array_reference_frequency_hz;
    antenna_metadata.element_spacing_m = qd_simulation_parameters.speed_of_light / options.array_reference_frequency_hz / 2;
    antenna_metadata.spacing_wavelengths_at_carrier = options.center_frequency_hz / options.array_reference_frequency_hz / 2;
elseif strcmp(options.antenna_profile, 'satellite_16x16_ground_omni')
    delay_span_s = max(delays_s, [], 2) - min(delays_s, [], 2);
    antenna_metadata.max_element_delay_span_s = max(delay_span_s(:));
    [coefficients, delays_s] = combine_satellite_beam(coefficients, delays_s, beam_weights);
end
if any(strcmp(options.antenna_profile, {'satellite_2port_ground_omni', 'satellite_4port_ground_omni', 'satellite_16x16_4port_ground_omni'}))
    % 上行的输入是 UE，输出是卫星阵列；转置空间轴但不取共轭。
    if strcmp(options.link_direction, 'uplink')
        coefficients = permute(coefficients, [2, 1, 3, 4]);
        delays_s = permute(delays_s, [2, 1, 3, 4]);
    end
    [coefficients, delays_s, residual_gain_db] = normalize_spatial_channel(coefficients, delays_s);
    metadata.coefficient_normalization = 'unit_snapshot_mean_link_power';
else
    [coefficients, delays_s, residual_gain_db] = normalize_qd_channel(coefficients, delays_s);
end
metadata.center_frequency_hz = options.center_frequency_hz;
metadata.link_direction = options.link_direction;
metadata.quadriga_version = get_quadriga_version(simulation, options.quadriga_version);
metadata.scenario = options.scenario;
metadata.random_seed = options.random_seed;
metadata.stk_trace_sha256 = sha256_file(trace_path);
metadata.antenna = antenna_metadata;
result=struct('times_s',trace.times_s,'coefficients',coefficients,'delays_s',delays_s,'residual_gain_db',residual_gain_db,'metadata',metadata);
if isempty(output_dir)
    manifest_path='';
else
    manifest_path = write_qdchannel1(output_dir,trace.times_s,coefficients,delays_s,residual_gain_db,metadata);
end
end


function track = make_track(positions_m, relative_times_s, name, force_snapshots)
% 使用非零占位长度创建对象，随后以 STK 的完整轨迹覆盖 positions。
track = qd_track('linear', 1, 0);
track.name = name;
track.initial_position = positions_m(:, 1);
relative_positions_m = positions_m - positions_m(:, 1);
segment_lengths_m = sqrt(sum(diff(relative_positions_m, 1, 2).^2, 1));
cumulative_distance_m = [0, cumsum(segment_lengths_m)];
if cumulative_distance_m(end) <= 1e-9 && ~force_snapshots
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
    'array_reference_frequency_hz', [], ...
    'snapshot_interval_s', [], ...
    'snapshot_times_s', [], ...
    'fidelity_tolerance', [], ...
    'bandwidth_hz', 4.5e6, ...
    'time_window_s', [], ...
    'diagnostic_mat_path', '', ...
    'normalization_anchor_path', '', ...
    'antenna_profile', 'satellite_16x16_ground_omni', ...
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
if ~any(strcmp(options.antenna_profile, {'satellite_16x16_ground_omni', 'satellite_2port_ground_omni', 'satellite_4port_ground_omni', 'satellite_16x16_4port_ground_omni', 'omni'}))
    error('QDCHANNEL1:AntennaProfile', '不支持的 antenna_profile');
end
if ~isscalar(options.center_frequency_hz) || options.center_frequency_hz <= 0
    error('QDCHANNEL1:Frequency', 'center_frequency_hz 必须大于 0');
end
if isempty(options.array_reference_frequency_hz)
    options.array_reference_frequency_hz = options.center_frequency_hz;
end
validateattributes(options.array_reference_frequency_hz, {'numeric'}, {'scalar','real','finite','positive'});
validateattributes(options.bandwidth_hz, {'numeric'}, {'scalar','real','finite','positive'});
if ~isempty(options.fidelity_tolerance)
    validateattributes(options.fidelity_tolerance, {'numeric'}, {'scalar','real','finite','positive','<=',1});
    assert(strcmp(options.antenna_profile,'satellite_16x16_4port_ground_omni'), '精度认证仅支持 4 子阵 profile');
end
assert(isempty(options.snapshot_times_s) || isempty(options.snapshot_interval_s), '不得同时指定均匀间隔和显式时间轴');
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
