function export_example_miso()
% 真实 QuaDRiGa 双端口数据；保存到独立目录，禁止覆盖已存在结果。
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root, 'quadriga', 'matlab'));
options.quadriga_path = fullfile(root, '.runtime', 'quadriga');
options.random_seed = 20260925;
options.antenna_profile = 'satellite_2port_ground_omni';
for direction = {'downlink', 'uplink'}
    options.link_direction = direction{1};
    if strcmp(direction{1}, 'downlink')
        options.center_frequency_hz = 2488400000;
    else
        options.center_frequency_hz = 1614900000;
    end
    output = fullfile(root, 'examples', 'fdd-miso', direction{1});
    assert(~exist(output, 'dir'), '禁止覆盖已有输出');
    export_stk_to_qdchannel(fullfile(root, 'examples', 'fdd-pass', 'trace.csv'), output, options);
end
end
