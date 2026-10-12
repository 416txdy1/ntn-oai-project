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
disp('PASS MATLAB handover export no-overwrite and input alignment');
end