function matlab_test_export_handover_fdd()
% Exercise the real MATLAB entry point, including existing directory and file.
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root, 'quadriga', 'matlab'));
temporary = tempname;
mkdir(temporary);
cleanup = onCleanup(@() rmdir(temporary, 's'));
for kind = {'directory', 'file'}
    output = fullfile(temporary, kind{1});
    if strcmp(kind{1}, 'directory')
        mkdir(output);
        marker = fullfile(output, 'keep.txt');
    else
        marker = output;
    end
    fid = fopen(marker, 'wt');
    fprintf(fid, 'existing output must remain intact');
    fclose(fid);
    try
        export_handover_fdd('missing-trace', 'missing-schedule', output);
        error('TEST:UnexpectedSuccess', 'Existing output was accepted');
    catch failure
        assert(strcmp(failure.identifier, 'QDCHANNEL1:OutputExists'), ...
            'Wrong rejection: %s: %s', failure.identifier, failure.message);
    end
    assert(strcmp(fileread(marker), 'existing output must remain intact'));
end
% Invalid aligned inputs must be rejected before creating any output directory.
bad_schedule = fullfile(temporary, 'schedule.csv');
fid = fopen(bad_schedule, 'wt');
fprintf(fid, 'time,satellite_id,elevation_deg,visible,switched\n0,SAT_A,10,1,0\n1,SAT_B,10,1,1\n');
fclose(fid);
output = fullfile(temporary, 'bad-input-output');
try
    export_handover_fdd(fullfile(root, 'local_ntn', 'stk_trace_firsthandover.csv'), bad_schedule, output);
    error('TEST:UnexpectedSuccess', 'Misaligned schedule was accepted');
catch failure
    assert(strcmp(failure.identifier, 'QDCHANNEL1:ScheduleTime'), ...
        'Wrong rejection: %s: %s', failure.identifier, failure.message);
end
assert(~exist(output, 'file'));
% Force a real exporter failure after the wrapper creates its output root.
% Nonuniform trace rows and an exactly aligned schedule reach the unchanged
% export_stk_to_qdchannel TraceRate rejection without any QuaDRiGa mutation.
trace_lines = strsplit(fileread(fullfile(root, 'local_ntn', 'stk_trace_firsthandover.csv')), sprintf('\n'));
schedule_lines = strsplit(fileread(fullfile(root, 'local_ntn', 'satellite_schedule_firsthandover.csv')), sprintf('\n'));
fields = strsplit(trace_lines{4}, ',');
fields{1} = '8201.25';
trace_lines{4} = strjoin(fields, ',');
fields = strsplit(schedule_lines{3}, ',');
fields{1} = '8201.25';
schedule_lines{3} = strjoin(fields, ',');
nonuniform_trace = fullfile(temporary, 'nonuniform-trace.csv');
aligned_schedule = fullfile(temporary, 'aligned-schedule.csv');
fid = fopen(nonuniform_trace, 'wt');
fprintf(fid, '%s', strjoin(trace_lines, sprintf('\n')));
fclose(fid);
fid = fopen(aligned_schedule, 'wt');
fprintf(fid, '%s', strjoin(schedule_lines, sprintf('\n')));
fclose(fid);
partial = fullfile(temporary, 'partial-output');
try
    export_handover_fdd(nonuniform_trace, aligned_schedule, partial);
    error('TEST:UnexpectedSuccess', 'Nonuniform trace was accepted');
catch failure
    assert(strcmp(failure.identifier, 'QDCHANNEL1:TraceRate'), ...
        'Wrong rejection: %s: %s', failure.identifier, failure.message);
end
assert(exist(partial, 'dir') == 7);
assert(~exist(fullfile(partial, 'provenance.json'), 'file'));
try
    export_handover_fdd(nonuniform_trace, aligned_schedule, partial);
    error('TEST:UnexpectedSuccess', 'Partial output was overwritten');
catch failure
    assert(strcmp(failure.identifier, 'QDCHANNEL1:OutputExists'));
end
disp('PASS MATLAB real partial failure has no completion record and cannot be overwritten');
disp('PASS MATLAB handover export no-overwrite and input alignment');
end