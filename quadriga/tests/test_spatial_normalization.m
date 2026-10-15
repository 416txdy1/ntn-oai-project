function test_spatial_normalization()
% 保留阵元间相位、幅度和延迟，且共同相位演化只消除一次。
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root, 'quadriga', 'matlab'));
h = complex(zeros(1, 2, 2, 2));
h(1, :, :, 1) = [1, 0.5; 2i, -0.25i];
h(:, :, :, 2) = h(:, :, :, 1) * exp(0.7i);
tau = repmat(reshape([1e-3, 1e-3+2e-9, 1e-3+3e-6, 1e-3+4e-6], [1, 2, 2]), [1,1,1,2]);
[c, d, g] = normalize_spatial_channel(h, tau);
assert(max(abs(c(:,:,:,1)-c(:,:,:,2)), [], 'all') < 1e-12);
assert(abs(c(1,2,1,1)/c(1,1,1,1)-2i) < 1e-12);
assert(abs(d(1,2,1,1)-2e-9) < 1e-15);
assert(abs(sum(abs(c(:,:,:,1)).^2, 'all') / 2 - 1) < 1e-12);
assert(all(g(:) == 0));
[cu, du, ~] = normalize_spatial_channel(permute(h,[2,1,3,4]), permute(tau,[2,1,3,4]));
assert(max(abs(cu-permute(c,[2,1,3,4])),[],'all') < 1e-12);
assert(max(abs(du-permute(d,[2,1,3,4])),[],'all') < 1e-15);
fprintf('PASS spatial reference: relative phase/amplitude/delay, mean power, reciprocal axes\n');
end
