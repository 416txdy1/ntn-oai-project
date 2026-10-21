function test_satellite_antennas(quadriga_path, output_dir)
%TEST_SATELLITE_ANTENNAS 实际阵元方向图、相干合成、姿态与导出集成测试。
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root, 'quadriga', 'matlab'));
addpath(fullfile(quadriga_path, 'quadriga_src'));
assert(~exist(output_dir, 'dir'), '禁止覆盖已有测试结果');
mkdir(output_dir);
fc = 2488400000;
array = create_satellite_array(fc);
assert(array.no_elements == 256 && isequal(size(array.coupling), [256, 256]));
lambda = qd_simulation_parameters.speed_of_light / fc;
assert(max(abs(mean(array.element_position, 2))) < 1e-14);
assert(max(abs(diff(unique(array.element_position(2, :))) - lambda/2)) < 1e-14);
[front, ~] = array.interpolate(0, 0);
[back, ~] = array.interpolate(pi, 0);
assert(abs(abs(back(1)/front(1))^2 - 1e-3) < 1e-12);
% 两个快照都测试非零扫描角：闭式平面波相位为 exp(+j*k*y*sin(theta))。
scan = pi/6;
y = array.element_position(2, :).';
k = 2*pi/lambda;
weights = repmat(exp(-1j*k*y*sin(scan))/16, 1, 2);
raw = complex(zeros(1, 256, 2, 2));
raw(1, :, 1, :) = repmat(reshape(exp(1j*k*y*sin(scan)), [1,256,1,1]), [1,1,1,2]);
% 方位正弦相差 2/16，使一维 16 阵元阵列出现第一个零点。
raw(1, :, 2, :) = repmat(reshape(exp(1j*k*y*(sin(scan)+2/16)), [1,256,1,1]), [1,1,1,2]);
delays = repmat(reshape([0.01, 0.010001], [1,1,2,1]), [1,256,1,2]);
[beam, beam_delays] = combine_satellite_beam(raw, delays, weights);
assert(abs(abs(beam(1,1,1,1))^2 - 256) < 1e-9);
assert(abs(beam(1,1,2,1)) < 1e-12, '波束相位符号错误或误用了共轭转置');
[normalized, excess, gain] = normalize_qd_channel(beam, beam_delays);
assert(abs(sum(abs(normalized(1,1,:,1)).^2) - 1) < 1e-12);
assert(all(gain(:) == 0) && excess(1,1,1,1) == 0);
fprintf('PASS array: 256 elements, half-wavelength spacing, 30dB backlobe, 24.082dB coherent gain, scanned null\n');

trace_path = fullfile(output_dir, 'trace.csv');
fid = fopen(trace_path, 'wt');
fprintf(fid, 'STKTRACE2\n');
for t = 0:2
    row = [t, 7000000, 7500*t, 0, 0, 7500, 0, 0, 0, 0, ...
        6378137, 0, 0, 6378137, 0, 0, -100, -100, 20, 20, 1, 1];
    fprintf(fid, '%.12g', row(1));
    fprintf(fid, ',%.12g', row(2:end));
    fprintf(fid, '\n');
end
fclose(fid);
trace = read_stktrace2(trace_path);
[orientation, geometric_weights] = satellite_beam_geometry(array, trace, trace.dl_valid);
satellite_enu = ecef_to_enu_track(trace.satellite_ecef_m, trace.ue_ecef_m(:,1));
ue_enu = ecef_to_enu_track(trace.ue_ecef_m, trace.ue_ecef_m(:,1));
los = ue_enu - satellite_enu;
azimuth = atan2(los(2,:), los(1,:));
elevation = atan2(los(3,:), hypot(los(1,:), los(2,:)));
[~, ~, dist] = array.interpolate(azimuth, elevation, [], orientation);
response = sum(exp(-1j*k*dist).*geometric_weights, 1);
assert(max(abs(response - 16)) < 1e-5, 'VVLH/Euler 旋转或 LOS 权重不一致');
bad_trace = trace;
bad_trace.ue_ecef_m = 2*trace.satellite_ecef_m;
try
    satellite_beam_geometry(array, bad_trace, trace.dl_valid);
    error('Test:ExpectedSteeringError', '可见但越界的目标必须被拒绝');
catch err
    assert(strcmp(err.identifier, 'QDCHANNEL1:SteeringLimit'));
end
fprintf('PASS beam geometry: moving LOS, nadir Euler singularity and visible scan-limit rejection\n');
% 对真实过境轨迹的全部方向检查旋转/相位补偿，而不只测试赤道合成样例。
real_trace = read_stktrace2(fullfile(root, 'examples', 'fdd-pass', 'trace.csv'));
real_satellite = ecef_to_enu_track(real_trace.satellite_ecef_m, real_trace.ue_ecef_m(:,1));
real_ue = ecef_to_enu_track(real_trace.ue_ecef_m, real_trace.ue_ecef_m(:,1));
real_los = real_ue - real_satellite;
real_azimuth = atan2(real_los(2,:), real_los(1,:));
real_elevation = atan2(real_los(3,:), hypot(real_los(1,:), real_los(2,:)));
for frequency = [2488400000, 1614900000]
    real_array = create_satellite_array(frequency);
    [real_orientation, real_weights] = satellite_beam_geometry( ...
        real_array, real_trace, real_trace.dl_valid | real_trace.ul_valid);
    [~, ~, real_dist] = real_array.interpolate(real_azimuth, real_elevation, [], real_orientation);
    real_response = sum(exp(-1j*2*pi*frequency/qd_simulation_parameters.speed_of_light*real_dist).*real_weights, 1);
    assert(max(abs(real_response - 16)) < 1e-5, '真实轨迹的 Euler 姿态或相位权重不一致');
end
fprintf('PASS real 362-snapshot LOS steering at both FDD carrier frequencies\n');
options = struct('quadriga_path', quadriga_path, 'center_frequency_hz', fc, ...
    'link_direction', 'downlink', 'random_seed', 20260925);
manifest_path = export_stk_to_qdchannel(trace_path, fullfile(output_dir, 'array'), options);
manifest = jsondecode(fileread(manifest_path));
assert(manifest.dimensions.tx_antennas == 1 && manifest.dimensions.rx_antennas == 1);
antenna = jsondecode(fileread(fullfile(fileparts(manifest_path), 'antenna.json')));
assert(strcmp(antenna.profile, 'satellite_16x16_ground_omni'));
assert(antenna.max_element_delay_span_s < 1e-8);
assert(strcmp(antenna.manifest_sha256, sha256_file(manifest_path)));
options.antenna_profile = 'omni';
legacy_path = export_stk_to_qdchannel(trace_path, fullfile(output_dir, 'omni'), options);
legacy = jsondecode(fileread(legacy_path));
legacy_antenna = jsondecode(fileread(fullfile(fileparts(legacy_path), 'antenna.json')));
assert(strcmp(legacy_antenna.profile, 'omni'));
assert(~strcmp(manifest.files.coefficients.sha256, legacy.files.coefficients.sha256));
fprintf('PASS actual QuaDRiGa exports: default 16x16 single beam and explicit legacy omni\n');
end
