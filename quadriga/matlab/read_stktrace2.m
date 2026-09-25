function trace = read_stktrace2(trace_path)
%READ_STKTRACE2 严格读取本项目使用的 22 列 STKTRACE2 CSV。

fid = fopen(trace_path, 'rt');
if fid < 0
    error('QDCHANNEL1:TraceOpen', '无法打开 STKTRACE2: %s', trace_path);
end
cleanup = onCleanup(@() fclose(fid));

magic = '';
rows = zeros(0, 22);
line_number = 0;
while ~feof(fid)
    line = fgetl(fid);
    line_number = line_number + 1;
    if ~ischar(line)
        break;
    end
    line = strtrim(line);
    if isempty(line)
        continue;
    end
    if isempty(magic) && strcmp(line, 'STKTRACE2')
        magic = line;
        continue;
    end
    if startsWith(line, '#')
        comment = strtrim(line(2:end));
        if isempty(magic) && strcmp(comment, 'STKTRACE2')
            magic = comment;
        end
        continue;
    end
    values = str2double(strsplit(line, ','));
    if numel(values) ~= 22 || any(~isfinite(values))
        error('QDCHANNEL1:TraceRow', '第 %d 行不是 22 个有限数值', line_number);
    end
    rows(end + 1, :) = values; %#ok<AGROW>
end

if ~strcmp(magic, 'STKTRACE2')
    error('QDCHANNEL1:TraceMagic', '首个注释标记必须是 # STKTRACE2');
end
if size(rows, 1) < 2
    error('QDCHANNEL1:TraceLength', 'STKTRACE2 至少需要两个快照');
end
if any(diff(rows(:, 1)) <= 0)
    error('QDCHANNEL1:TraceTime', 'STKTRACE2 时间必须严格递增');
end
validity = rows(:, 21:22);
if any(validity(:) ~= 0 & validity(:) ~= 1)
    error('QDCHANNEL1:TraceValidity', 'ul_valid/dl_valid 只能是 0 或 1');
end

trace.times_s = rows(:, 1);
trace.satellite_ecef_m = rows(:, 2:4).';
trace.gnb_ecef_m = rows(:, 11:13).';
trace.ue_ecef_m = rows(:, 14:16).';
trace.dl_valid = logical(rows(:, 21));
trace.ul_valid = logical(rows(:, 22));
end
