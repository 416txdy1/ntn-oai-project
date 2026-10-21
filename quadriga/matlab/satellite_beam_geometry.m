function [orientation, weights, metadata] = satellite_beam_geometry(array, trace, visibility)
%SATELLITE_BEAM_GEOMETRY 根据 VVLH 近似姿态电子跟踪地面 UE。
% qd_arrayant 的 +x=星下点，+y=惯性速度在切平面的投影，+z=两者叉积。
% STK CBIVelLHAtt 使用惯性速度；将 ECEF 速度加上 omega x r 后构造姿态。

satellite = trace.satellite_ecef_m;
velocity = trace.satellite_velocity_ecef_m;
ue = trace.ue_ecef_m;
count = numel(trace.times_s);
if ~isequal(size(satellite), [3, count], size(velocity), size(ue))
    error('QDCHANNEL1:BeamGeometry', '位置、速度必须为时间对齐的 3xSnapshot');
end
reference = ue(:, 1);
% 对单位基向量做变换取得 ECEF->ENU 旋转，避免平移位置当作方向使用。
ecef_to_enu = ecef_to_enu_track(reference + eye(3), reference);
orientation = zeros(3, count);
local_los = zeros(3, count);
for snapshot = 1:count
    r = satellite(:, snapshot);
    normal = -r / norm(r);
    inertial_velocity = velocity(:, snapshot) + cross([0; 0; 7.292115e-5], r);
    along = inertial_velocity - normal * dot(normal, inertial_velocity);
    if norm(along) < 1e-6 || norm(ue(:, snapshot) - r) < 1
        error('QDCHANNEL1:BeamGeometry', '快照 %d 无法确定卫星姿态或 LOS', snapshot);
    end
    along = along / norm(along);
    rotation = ecef_to_enu * [normal, along, cross(normal, along)];
    pitch = atan2(rotation(3, 1), hypot(rotation(1, 1), rotation(2, 1)));
    if hypot(rotation(1, 1), rotation(2, 1)) < 1e-7
        roll = 0;
        yaw = atan2(-rotation(1, 2), rotation(2, 2));
    else
        roll = atan2(rotation(3, 2), rotation(3, 3));
        yaw = atan2(rotation(2, 1), rotation(1, 1));
    end
    orientation(:, snapshot) = [roll; pitch; yaw];
    los = ue(:, snapshot) - r;
    local_los(:, snapshot) = [normal, along, cross(normal, along)].' * (los / norm(los));
end
azimuth = atan2(local_los(2, :), local_los(1, :));
elevation = atan2(local_los(3, :), hypot(local_los(1, :), local_los(2, :)));
inside_scan = abs(azimuth) <= pi/3 + 1e-9 & abs(elevation) <= pi/3 + 1e-9;
if any(visibility(:).' & ~inside_scan)
    error('QDCHANNEL1:SteeringLimit', ...
        'STK 标记可见的目标超出阵列 +/-60 度扫描限制；请核对场景与 trace');
end
% QuaDRiGa 的路径距离投影 dist=-position dot direction，系数相位为
% exp(-j*k*dist)。发射权重 exp(+j*k*dist) 才能抵消 LOS 阵元间相位。
dist_m = -array.element_position.' * local_los;
wave_number = 2*pi*array.center_frequency / qd_simulation_parameters.speed_of_light;
weights = exp(1j * wave_number * dist_m) / sqrt(array.no_elements);
% 越界且 STK 不可见的快照仅保留有限占位信道，由 STK 可见性负责静音。
weights(:, ~inside_scan) = 1 / sqrt(array.no_elements);
metadata = struct( ...
    'profile', 'satellite_16x16_ground_omni', ...
    'satellite_rows', 16, 'satellite_columns', 16, ...
    'spacing_wavelengths', 0.5, 'satellite_rf_ports', 1, 'ground_rf_ports', 1, ...
    'element_power_pattern', 'front_cosine_back_constant', ...
    'element_factor_exponent', 1, 'backlobe_suppression_db', 30, ...
    'beamformer', 'uniform_phase_only_los_tracking', ...
    'attitude', 'geocentric_vvlh_from_ecef_with_earth_rotation', ...
    'steering_limit_deg', 60, 'ground_pattern', 'quadriga_omni_vertical', ...
    'absolute_array_gain_source', 'STKTRACE2', ...
    'delay_reduction', 'uniform_element_mean_narrowband');
end
