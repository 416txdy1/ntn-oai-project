function provenance_path = export_handover_fdd(trace_path, schedule_path, output_dir)
%EXPORT_HANDOVER_FDD Export a complete two-frequency handover dataset.
% Existing output is always refused. Failure leaves an incomplete directory,
% without provenance.json, which integrated-handover preflight rejects.
% The original QuaDRiGa generation and normalization math is reused unchanged.
if exist(output_dir, 'file') || exist(output_dir, 'dir')
    error('QDCHANNEL1:OutputExists', 'Refusing to overwrite existing output: %s', output_dir);
end
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root, 'quadriga', 'matlab'));
trace = read_stktrace2(trace_path);
schedule = readtable(schedule_path, 'FileType', 'text', 'Delimiter', ',', ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
required = {'time', 'satellite_id', 'elevation_deg', 'visible', 'switched'};
if ~all(ismember(required, schedule.Properties.VariableNames))
    error('QDCHANNEL1:ScheduleColumns', 'Schedule is missing required fields');
end
if height(schedule) ~= numel(trace.times_s) || any(~isfinite(schedule.time)) || ...
        any(abs(schedule.time(:) - trace.times_s) > 1e-9)
    error('QDCHANNEL1:ScheduleTime', 'Schedule and trace must have identical row times');
end
if any(ismissing(schedule.satellite_id) | strlength(schedule.satellite_id) == 0) || ...
        any(~isfinite(schedule.elevation_deg) | abs(schedule.elevation_deg) > 90) || ...
        any(~ismember(schedule.visible, [0, 1])) || any(~ismember(schedule.switched, [0, 1]))
    error('QDCHANNEL1:ScheduleRows', 'Schedule identity/elevation/flags are invalid');
end
if ismember('handover_phase', schedule.Properties.VariableNames) && ...
        any(~ismember(schedule.handover_phase, ["steady", "blend", "complete"]))
    error('QDCHANNEL1:ScheduleRows', 'Schedule phase is invalid');
end
checksums = jsondecode(fileread(fullfile(root, 'vendor', 'checksums.json')));
archive_sha = sha256_file(fullfile(root, 'vendor', 'quadriga-source.tar.gz'));
assert(strcmp(archive_sha, checksums.(matlab.lang.makeValidName('quadriga-source.tar.gz'))), ...
    'QDCHANNEL1:VendorChecksum', 'QuaDRiGa archive checksum mismatch');
[status, commit] = system(['git -C "' strrep(root, '"', '""') '" rev-parse HEAD']);
commit = strtrim(commit);
if status ~= 0 || isempty(regexp(commit, '^[0-9a-f]{40}$', 'once'))
    error('QDCHANNEL1:SourceCommit', 'Cannot identify exporter source commit');
end
source_files = {
    'quadriga/matlab/export_handover_fdd.m', ...
    'quadriga/matlab/export_stk_to_qdchannel.m', ...
    'quadriga/matlab/normalize_qd_channel.m', ...
    'quadriga/matlab/write_qdchannel1.m', ...
    'quadriga/matlab/read_stktrace2.m', ...
    'quadriga/matlab/ecef_to_enu_track.m', ...
    'quadriga/matlab/sha256_file.m'};
% containers.Map preserves slash/dot keys in JSON, unlike struct field names.
file_hashes = containers.Map('KeyType', 'char', 'ValueType', 'char');
for index = 1:numel(source_files)
    name = source_files{index};
    file_hashes(name) = sha256_file(fullfile(root, strrep(name, '/', filesep)));
end
options.quadriga_path = fullfile(root, '.runtime', 'quadriga');
options.random_seed = 20260925;
options.scenario = 'QuaDRiGa_NTN_Rural_LOS';
mkdir(output_dir);
bundles = struct();
quadriga_version = '';
for direction = {'downlink', 'uplink'}
    name = direction{1};
    options.link_direction = name;
    if strcmp(name, 'downlink')
        options.center_frequency_hz = 2488400000;
    else
        options.center_frequency_hz = 1614900000;
    end
    bundle = fullfile(output_dir, name);
    manifest_path = export_stk_to_qdchannel(trace_path, bundle, options);
    % Only the newly generated JSON text is canonicalized to LF. Binary arrays
    % and existing exporter math are untouched; hashes survive OS checkouts.
    manifest_text = strrep(fileread(manifest_path), sprintf('\r\n'), sprintf('\n'));
    write_text(manifest_path, manifest_text);
    manifest = jsondecode(manifest_text);
    if isempty(quadriga_version)
        quadriga_version = manifest.provenance.quadriga_version;
    else
        assert(strcmp(quadriga_version, manifest.provenance.quadriga_version), ...
            'QDCHANNEL1:Version', 'Two directions used different QuaDRiGa versions');
    end
    data_hashes = struct();
    data_fields = fieldnames(manifest.files);
    for index = 1:numel(data_fields)
        key = data_fields{index};
        data_hashes.(key) = sha256_file(fullfile(bundle, manifest.files.(key).path));
    end
    bundles.(name) = struct('path', name, 'manifest_sha256', sha256_file(manifest_path), ...
        'data_sha256', data_hashes);
end
provenance = struct('format', 'NTN_HANDOVER_FDD1', 'schema_version', 1, 'state', 'complete');
descriptor = @(path) struct('sha256', sha256_file(path), 'rows', numel(trace.times_s), ...
    'start_time_s', trace.times_s(1), 'end_time_s', trace.times_s(end));
provenance.inputs = struct('trace', descriptor(trace_path), 'schedule', descriptor(schedule_path));
provenance.tools = struct('matlab_version', version, 'quadriga_version', quadriga_version, ...
    'scenario', options.scenario, 'random_seed', options.random_seed);
provenance.source = struct('commit', commit, 'quadriga_archive_sha256', archive_sha, 'files', file_hashes);
provenance.bundles = bundles;
% Write the completion record last. A failure in either direction cannot make
% a valid completed dataset. A temporary file is never accepted by preflight.
provenance_path = fullfile(output_dir, 'provenance.json');
temporary_path = fullfile(output_dir, 'provenance.json.pending');
write_text(temporary_path, [jsonencode(provenance) sprintf('\n')]);
[success, message] = movefile(temporary_path, provenance_path);
if ~success
    error('QDCHANNEL1:CompletionWrite', '%s', message);
end
fprintf('PASS complete handover FDD export: %d snapshots, %s\n', numel(trace.times_s), provenance_path);
end


function write_text(path, text)
fid = fopen(path, 'wb');
if fid < 0
    error('QDCHANNEL1:TextOpen', 'Cannot write %s', path);
end
cleanup = onCleanup(@() fclose(fid));
payload = unicode2native(text, 'UTF-8');
written = fwrite(fid, payload, 'uint8');
if written ~= numel(payload)
    error('QDCHANNEL1:TextWrite', 'Incomplete write: %s', path);
end
end