function digest = sha256_file(path)
%SHA256_FILE 使用操作系统自带工具计算二进制文件 SHA256。

quoted_path = ['"' strrep(char(path), '"', '""') '"'];
if ispc
    [status, output] = system(['certutil -hashfile ' quoted_path ' SHA256']);
else
    [status, output] = system(['sha256sum ' quoted_path]);
end
if status ~= 0
    error('QDCHANNEL1:SHA256', 'SHA256 计算失败: %s', output);
end
matches = regexp(lower(output), '[0-9a-f]{64}', 'match');
if isempty(matches)
    error('QDCHANNEL1:SHA256', '无法从系统工具输出解析 SHA256: %s', output);
end
digest = matches{1};
end
