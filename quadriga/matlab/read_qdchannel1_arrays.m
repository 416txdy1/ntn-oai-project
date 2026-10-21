function arrays = read_qdchannel1_arrays(folder)
% 只读取本项目固定的 v1 数组，并验证 manifest 中的内容哈希。
m=jsondecode(fileread(fullfile(folder,'manifest.json')));
assert(strcmp(m.format,'QDCHANNEL1') && m.schema_version==1);
for name={'times','coefficients','delays','residual_gain_db'}
    spec=m.files.(name{1});assert(strcmp(sha256_file(fullfile(folder,spec.path)),spec.sha256),'bundle 哈希不匹配');
end
R=m.dimensions.rx_antennas;T=m.dimensions.tx_antennas;P=m.dimensions.paths;S=m.dimensions.snapshots;
arrays.times_s=read(fullfile(folder,'times.f64'),'double');
a=read(fullfile(folder,'coefficients.cf32'),'single=>double');
arrays.coefficients=permute(reshape(complex(a(1:2:end),a(2:2:end)),P,T,R,S),[3,2,1,4]);
arrays.delays_s=permute(reshape(read(fullfile(folder,'delays.f64'),'double'),P,T,R,S),[3,2,1,4]);
arrays.residual_gain_db=permute(reshape(read(fullfile(folder,'residual_gain_db.f32'),'single=>double'),T,R,S),[2,1,3]);
arrays.manifest=m;
end
function a=read(path,precision)
fid=fopen(path,'r','ieee-le');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));a=fread(fid,inf,precision);
end