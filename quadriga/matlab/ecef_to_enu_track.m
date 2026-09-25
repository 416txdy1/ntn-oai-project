function enu_m = ecef_to_enu_track(ecef_m, reference_ecef_m)
%ECEF_TO_ENU_TRACK 将 3xN WGS84 ECEF 轨迹变换到局部 ENU 坐标。

if size(ecef_m, 1) ~= 3 || numel(reference_ecef_m) ~= 3
    error('QDCHANNEL1:ECEFShape', 'ECEF 输入必须是 3xN，参考点必须有三个分量');
end
reference_ecef_m = reference_ecef_m(:);
x = reference_ecef_m(1);
y = reference_ecef_m(2);
z = reference_ecef_m(3);
a = 6378137.0;
e2 = 6.69437999014e-3;
longitude = atan2(y, x);
horizontal = hypot(x, y);
latitude = atan2(z, horizontal * (1 - e2));
for iteration = 1:10 %#ok<NASGU>
    prime_vertical = a / sqrt(1 - e2 * sin(latitude)^2);
    height = horizontal / cos(latitude) - prime_vertical;
    latitude = atan2(z, horizontal * (1 - e2 * prime_vertical / (prime_vertical + height)));
end

rotation = [ ...
    -sin(longitude), cos(longitude), 0; ...
    -sin(latitude) * cos(longitude), -sin(latitude) * sin(longitude), cos(latitude); ...
    cos(latitude) * cos(longitude), cos(latitude) * sin(longitude), sin(latitude)];
enu_m = rotation * (ecef_m - reference_ecef_m);
end
