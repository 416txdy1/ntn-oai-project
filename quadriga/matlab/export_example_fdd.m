function export_example_fdd()
% 使用仓库内 QuaDRiGa 源码和示例轨迹重新生成 FDD 数据，不覆盖已保存的输入。
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root, 'quadriga', 'matlab'));
options.quadriga_path = fullfile(root, '.runtime', 'quadriga');
options.random_seed = 20260925;
for direction = {'downlink', 'uplink'}
    options.link_direction = direction{1};
    if strcmp(direction{1}, 'downlink')
        options.center_frequency_hz = 2488400000;
    else
        options.center_frequency_hz = 1614900000;
    end
    output = fullfile(root, '.runtime', 'generated-fdd', direction{1});
    assert(~exist(output, 'dir'), '禁止覆盖已有输出');
    export_stk_to_qdchannel(fullfile(root, 'examples', 'fdd-pass', 'trace.csv'), output, options);
end
end