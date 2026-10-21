"""Read-only live console plus bounded orchestration of existing NTN entry points.

Raw subprocess output remains in .private. Never print arbitrary modem lines.
No existing source/configuration file is edited by this runner.
"""
import argparse
import collections
import datetime
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid

PARAMETERS = {
    'OAI_NTN_TIMING_DIAG': '1', 'OAI_NTN_TIMING_DIAG_START_IQ_S': '0',
    'OAI_NTN_PUSCH_FAILURE_THRES': '100', 'OAI_NTN_PDCP_REORDERING_MS': '500',
    'OAI_NTN_CELL_KOFFSET_MS': '80', 'OAI_RNGSEED': '20260925',
}
CASES = [('firsthandover', 'first-a'), ('firsthandover', 'first-b'),
         ('full', 'full'), ('legacy', 'legacy'), ('static', 'static')]
SCHEDULE = re.compile(
    r'STKSCHEDULE (UL|DL) IQ=([\d.]+) STK=([\d.]+) satellite_id=([A-Za-z0-9_]+) '
    r'elevation_deg=([-\d.]+) visible=([01]) switched=([01]) phase=(steady|prepare|blend|complete) '
    r'previous=([A-Za-z0-9_]*) next=([A-Za-z0-9_]*) samples=(\d+)')
CLOCK = re.compile(r'STKCLOCK (UL|DL) monotonic_ns=\d+ samples=\d+ sampling_rate=[\d.]+ iq_s=([\d.]+) stk_s=([\d.]+)')
PHYSICAL = re.compile(r'STKTRACE2 (UL|DL) IQ=([\d.]+) STK=([\d.]+) delay=([\d.]+)ms Doppler=([-\d.]+)Hz gain=([-\d.]+)dB C/N=([-\d.]+)dB valid=([01]) samples=\d+')


def say(message):
    print(time.strftime('[%H:%M:%S] ') + message, flush=True)


class Lines:
    """Incremental reader; incomplete lines are retained, never parsed early."""
    def __init__(self, path):
        self.path = Path(path)
        self.offset = 0
        self.pending = b''

    def read(self):
        try:
            with self.path.open('rb') as stream:
                stream.seek(self.offset)
                data = stream.read()
                self.offset = stream.tell()
        except FileNotFoundError:
            return []
        pieces = (self.pending + data).split(b'\n')
        self.pending = pieces.pop()
        return [p.decode('utf-8', errors='replace') for p in pieces]


class Live:
    def __init__(self, run):
        self.run = Path(run)
        self.modems = {s: Lines(self.run / (s + '-acceptance.log')) for s in ('gnb', 'ue')}
        names = ['ping', 'uplink-sender', 'uplink-receiver', 'downlink-sender', 'downlink-receiver']
        self.events = {s: Lines(self.run / 'acceptance' / (s + '.jsonl')) for s in names}
        self.counts = collections.Counter()
        self.sent = {s: {} for s in ('ping', 'uplink', 'downlink')}
        self.received = {s: set() for s in self.sent}
        self.recent_rtt = collections.deque(maxlen=100)
        self.clock = {}
        self.physical = {}
        self.phases = {}
        self.last_display = 0

    def poll(self, force=False):
        for side, tail in self.modems.items():
            for line in tail.read():
                clock = CLOCK.search(line)
                if clock:
                    self.clock[side] = (float(clock[2]), float(clock[3]))
                physical = PHYSICAL.search(line)
                if physical:
                    self.physical[side] = (float(physical[4]), float(physical[5]), float(physical[7]))
                event = SCHEDULE.search(line)
                if event:
                    direction, iq, stk, satellite, _, _, switched, phase, previous, following, _ = event.groups()
                    key = satellite, phase
                    if self.phases.get(side) != key:
                        say(f'SAT {side}/{direction} IQ={float(iq):.3f}s STK={float(stk):.3f}s '
                            f'{satellite} phase={phase} switched={switched} {previous} -> {following}')
                        self.phases[side] = key
        for name, tail in self.events.items():
            kind = name.split('-')[0]
            for line in tail.read():
                try:
                    event = json.loads(line)
                except (ValueError, TypeError):
                    raise RuntimeError('Malformed private worker event: ' + name)
                action = event.get('event')
                sequence = event.get('sequence')
                if action == 'ready':
                    say('BUSINESS worker ready: ' + name)
                elif action == 'send':
                    self.sent[kind][sequence] = event['send_ns']
                elif action == 'receive':
                    self.received[kind].add(sequence)
                    if kind == 'ping' and not event.get('duplicate'):
                        self.recent_rtt.append(float(event['wall_rtt_ms']))
                elif action == 'error':
                    say('BUSINESS worker error: ' + name + ' (details retained privately)')
        now = time.monotonic()
        if force or now - self.last_display >= 5:
            self.last_display = now
            clocks = ' '.join(f'{s}:IQ={v[0]:.2f}/STK={v[1]:.2f}' for s, v in self.clock.items())
            if clocks:
                say('CLOCK ' + clocks)
            for side, (delay, doppler, cn) in self.physical.items():
                say(f'PHY {side} delay={delay:.3f}ms Doppler={doppler:.1f}Hz C/N={cn:.2f}dB')
            if any(self.sent.values()):
                values = []
                now_ns = time.monotonic_ns()
                for kind in self.sent:
                    sent, received = self.sent[kind], self.received[kind]
                    pending = set(sent) - received
                    overdue = sum(now_ns - sent[s] > 5_000_000_000 for s in pending)
                    values.append(f'{kind}:sent={len(sent)} received={len(set(sent)&received)} '
                                  f'pending={len(pending)} pending_over_5s={overdue}')
                say('BUSINESS ' + ' | '.join(values))
                if self.recent_rtt:
                    say(f'PING last<=100 replies mean_wall_RTT={sum(self.recent_rtt)/len(self.recent_rtt):.2f}ms')


def process_start(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    except FileNotFoundError:
        return None


class Runner:
    def __init__(self, root, output, environment):
        self.root, self.output, self.environment = root, output, environment
        self.records = []

    def stage(self, name, argv, timeout=1800, live=None, cwd=None):
        say('START ' + name)
        start = time.monotonic()
        record = {'stage': name, 'argv': [str(v) for v in argv], 'exit': None}
        self.records.append(record)
        with (self.output / (name + '.private.log')).open('xb') as stream:
            process = subprocess.Popen(argv, cwd=cwd or self.root, env=self.environment,
                                       stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            identity = process_start(process.pid)
            next_note = start + 15
            try:
                while process.poll() is None:
                    if live:
                        live.poll()
                    now = time.monotonic()
                    if now - start > timeout:
                        raise RuntimeError('Stage wall timeout: ' + name)
                    if now >= next_note:
                        say(f'RUNNING {name}: {now-start:.0f} wall seconds; private log is being recorded')
                        next_note = now + 15
                    time.sleep(.5)
            finally:
                if process.poll() is None:
                    # Signal only our still-live child session with unchanged start identity.
                    if identity is not None and process_start(process.pid) == identity:
                        os.killpg(process.pid, signal.SIGINT)
                    try:
                        process.wait(timeout=45)
                    except subprocess.TimeoutExpired:
                        if identity is not None and process_start(process.pid) == identity:
                            os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=10)
                record.update(exit=process.returncode, wall_seconds=time.monotonic()-start)
        if live:
            live.poll(force=True)
        say(f'END {name}: exit={process.returncode}, wall={record["wall_seconds"]:.1f}s')
        if process.returncode:
            raise RuntimeError('Stage failed: ' + name + '; inspect its private log')

    def case(self, case, suffix, tag):
        profile = 'legacy-handover' if case == 'legacy' else 'integrated-handover'
        run_id = tag + '-' + suffix
        core_id = run_id + '-core'
        core = [sys.executable, 'scripts/core_lab.py']
        selector = ['--profile', profile, '--run-id', core_id]
        run_dir = self.root / '.runtime/runs' / profile / run_id
        started = False
        problem = None
        try:
            self.stage(suffix + '-core-up', core + ['up'] + selector, timeout=300)
            started = True
            self.stage(suffix + '-core-health', [sys.executable, '-c',
                "import json,subprocess,time,sys\n"
                "for i in range(120):\n"
                " rows=subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project=ntn-qd-integrated']).decode().split()\n"
                " data=json.loads(subprocess.check_output(['docker','inspect',*rows])) if rows else []\n"
                " if len(data)==9 and all(x['State']['Running'] and x['State'].get('Health',{}).get('Status')=='healthy' for x in data):sys.exit(0)\n"
                " time.sleep(1)\n"
                "sys.exit(1)"], timeout=180)
            self.stage(suffix + '-acceptance', [sys.executable, '-u', 'scripts/handover_acceptance.py',
                '--case', case, '--profile', profile, '--run-id', run_id, '--max-wall-seconds', '3600'],
                timeout=3720, live=Live(run_dir))
            report = json.loads((run_dir / 'acceptance/report.json').read_text())
            if not report.get('passed') or report.get('stop_exit') != 0 or report.get('failure_reasons'):
                raise RuntimeError('Acceptance report did not pass: ' + suffix)
            say(f'PASS {suffix}: Ping {report["ping"]["received"]}/{report["ping"]["sent"]}; '
                f'UL {report["udp"]["uplink"]["received"]}/{report["udp"]["uplink"]["sent"]}; '
                f'DL {report["udp"]["downlink"]["received"]}/{report["udp"]["downlink"]["sent"]}')
            for window in report.get('windows', []):
                say(f'SWITCH RESULT STK={window["complete_stk_s"]}: coverage={window["coverage_ok"]}; '
                    f'Ping {window["ping"]["received"]}/{window["ping"]["sent"]}; '
                    f'UL {window["udp"]["uplink"]["received"]}/{window["udp"]["uplink"]["sent"]}; '
                    f'DL {window["udp"]["downlink"]["received"]}/{window["udp"]["downlink"]["sent"]}')
            say('REPORT ' + str(run_dir / 'acceptance/report.json'))
            say('TIMELINE ' + str(run_dir / 'acceptance/timeline.png'))
        except BaseException as error:
            problem = error
        finally:
            # Existing commands independently enforce PID/start/owner/resource identity.
            if (run_dir / 'run.json').exists():
                try:
                    self.stage(suffix + '-stop-check', [sys.executable, 'local_ntn/experiment.py',
                        'stop', '--profile', profile, '--run-id', run_id], timeout=90)
                except BaseException as error:
                    say('CLEANUP FAILED: ' + suffix + '; inspect private evidence')
                    problem = problem or error
            if started:
                try:
                    self.stage(suffix + '-core-down', core + ['down'] + selector, timeout=180)
                except BaseException as error:
                    say('CORE CLEANUP FAILED: ' + suffix)
                    problem = problem or error
        if problem:
            raise problem


def validate(root):
    if sys.platform != 'linux':
        raise RuntimeError('Run this program inside WSL/Linux using the CMD entry point')
    if not root.is_dir() or root == Path('/mnt/d/实验室学习工作/杂活/雄安/OAI调研'):
        raise RuntimeError('Select the independent integration checkout, not the original platform')
    for path in ('scripts/handover_acceptance.py', 'scripts/original_platform_check.py',
                 'local_ntn/runtime_config.py', 'vendor/source-manifest.json'):
        if not (root / path).is_file():
            raise RuntimeError('Independent platform file missing: ' + path)
    branch = subprocess.check_output(['git', '-c', 'safe.directory=' + str(root),
                                     '-C', str(root), 'branch', '--show-current'], text=True).strip()
    if branch != 'codex/ntn-quadriga-handover':
        raise RuntimeError('Unexpected checkout branch: ' + branch)
    for executable in ('docker', 'cmake', 'cc', 'ip'):
        import shutil
        if not shutil.which(executable):
            raise RuntimeError('Required executable missing: ' + executable)
    say('CHECK OK: independent checkout and required command paths')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--check-only', action='store_true', help='validate paths only; do not build/start tests')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    validate(root)
    if args.check_only:
        return 0
    if os.geteuid() != 0:
        raise RuntimeError('The CMD launcher must invoke this runner through sudo')
    # Never build/run against an already active modem experiment or borrow its core.
    for item in Path('/proc').iterdir():
        if item.name.isdigit():
            try:
                executable = (item / 'exe').resolve(strict=True).name
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
            if executable in ('nr-softmodem', 'nr-uesoftmodem'):
                raise RuntimeError('An OAI modem is already running; stop its own experiment first')
    existing_core = subprocess.check_output(['docker', 'ps', '-aq', '--filter',
        'label=com.docker.compose.project=ntn-qd-integrated'], text=True).strip()
    if existing_core:
        raise RuntimeError('An isolated core deployment already exists; stop it with its original run-id first')
    import fcntl
    os.umask(0o077)
    private = root / '.private'
    private.mkdir(exist_ok=True, mode=0o700)
    lock = (private / 'full-test-launcher.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError('Another full-test launcher is already running')
    tag = 'suite-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
    output = private / tag
    output.mkdir(mode=0o700)
    # Only this child environment is cleared; the user's shell is untouched.
    environment = {k: v for k, v in os.environ.items() if not k.startswith('OAI_')}
    environment.update(PARAMETERS, PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1')
    runner = Runner(root, output, environment)
    snapshot = output / 'original-before.json'
    checker = [sys.executable, 'scripts/original_platform_check.py']
    result = {'tag': tag, 'passed': False, 'parameters': PARAMETERS, 'stages': runner.records}
    def interrupt(_sig, _frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupt)
    say('SUITE ' + tag)
    say('PRIVATE LOG DIRECTORY ' + str(output))
    say('Live pending packets are NOT final loss; the acceptance report applies the original loss/deadline gates.')
    try:
        runner.stage('original-before', checker + ['snapshot', '--snapshot', str(snapshot)])
        if not (private / 'profiles/integrated-handover').exists():
            runner.stage('initialize-profile', [sys.executable, 'scripts/init_lab.py', '--profile', 'integrated-handover'])
        runner.stage('build', ['bash', 'scripts/build.sh'], timeout=7200)
        runner.stage('build-phy-tests', ['cmake', '--build', '.runtime/oai/cmake_targets/ran_build/build',
                     '--target', 'nr_prachsim', 'nr_pbchsim', '-j', '6'], timeout=3600)
        runner.stage('trace-iq-regressions', ['bash', 'local_ntn/run_regressions.sh'])
        runner.stage('scripts-regressions', ['bash', 'scripts/test.sh'])
        for case, suffix in CASES:
            runner.case(case, suffix, tag)
        runner.stage('original-business', checker + ['short-run', '--snapshot', str(snapshot), '--tag', tag], timeout=900)
        original = Path('/mnt/d/实验室学习工作/杂活/雄安/OAI调研')
        executable = str(output / 'original-trace-test')
        runner.stage('original-parser-build', ['cc', '-Wall', '-Wextra', '-Werror', '-I', 'local_ntn',
                     'local_ntn/test_trace.c', 'local_ntn/stk_trace.c', '-lm', '-o', executable], cwd=original)
        runner.stage('original-parser-run', [executable], cwd=original)
        runner.stage('original-trace-validation', [sys.executable, 'local_ntn/test_trace_validation.py'], cwd=original)
        runner.stage('original-iq-stock', [sys.executable, 'local_ntn/test_real_iq.py'], cwd=original)
        runner.stage('original-final-compare', checker + ['compare', '--snapshot', str(snapshot)])
        result['passed'] = True
    except (Exception, KeyboardInterrupt) as error:
        result['error_type'] = type(error).__name__
        # Do not echo captured child output or arbitrary private exception text.
        say('SUITE STOPPED: ' + type(error).__name__ + '; see the last stage/private logs; later cases were not started')
    finally:
        if not result['passed'] and snapshot.is_file():
            try:
                runner.stage('original-compare-after-failure', checker + ['compare', '--snapshot', str(snapshot)])
            except (Exception, KeyboardInterrupt):
                result['original_compare_after_failure_passed'] = False
                say('Original-platform comparison also failed; preserve evidence and inspect before retrying')
            else:
                result['original_compare_after_failure_passed'] = True
        (output / 'suite-report.json').write_text(json.dumps(result, indent=2))
        say(('ALL TESTS PASSED' if result['passed'] else 'SUITE FAILED / INTERRUPTED') + ': ' + str(output / 'suite-report.json'))
        lock.close()
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        say('PRECHECK FAILED: ' + str(error))
        sys.exit(1)
