function array = create_satellite_array(center_frequency_hz)
%CREATE_SATELLITE_ARRAY 16x16、0.5lambda 矩形阵列，局部 +x 为机械法线。
% 保留 256 个阵元端口，逐快照的电子权重在信道生成后合成；不能先
% 对各阵元分别归一化，否则相干合成需要的阵元间幅度/相位会丢失。

validateattributes(center_frequency_hz, {'numeric'}, {'scalar', 'real', 'finite', 'positive'});
array = qd_arrayant('omni');
array.name = 'NTN satellite 16x16 half-wavelength planar array';
array.center_frequency = center_frequency_hz;
% 与保存的 STK 配置对应的功率余弦阵元近似：前半球 cos(theta)^1，
% 后半球恒定抑制 30 dB。QuaDRiGa Fa 存储电场，所以取功率平方根。
normal_cosine = cos(array.elevation_grid(:)) * cos(array.azimuth_grid);
power_pattern = max(normal_cosine, 0);
power_pattern(normal_cosine < 0) = 10^(-30 / 10);
array.Fa = sqrt(power_pattern);
array.no_elements = 256;
lambda_m = qd_simulation_parameters.speed_of_light / center_frequency_hz;
axis_m = ((0:15) - 7.5) * 0.5 * lambda_m;
[y_m, z_m] = ndgrid(axis_m, axis_m);
array.element_position = [zeros(1, 256); y_m(:).'; z_m(:).'];
array.coupling = eye(256);
end
