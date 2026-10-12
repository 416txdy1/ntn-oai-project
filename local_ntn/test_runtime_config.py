"""Behavioral tests for isolated runtime profiles; no modem or secret reads."""
import dataclasses
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

from runtime_config import resolve_runtime


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ntn-runtime-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_integrated_defaults(self):
        config = resolve_runtime(self.root, 'integrated-handover', 'run-a', {})
        self.assertEqual(config.rf_port, 4044)
        self.assertEqual(config.namespace, 'ntn-qd-ue')
        self.assertEqual(config.ue_pdu_subnet, '12.2.1.0/24')
        self.assertEqual(config.core_project, 'ntn-qd-integrated')
        self.assertEqual(config.host_veth, 'ntn-qd-host')
        self.assertEqual(config.ue_veth, 'ntn-qd-peer')
        self.assertEqual(config.rf_host_ip, '10.202.0.1')
        self.assertEqual(config.rf_ue_ip, '10.202.0.2')
        self.assertEqual(config.amf_ip, '192.168.71.132')
        self.assertEqual(config.gnb_ip_cidr, '192.168.71.129/26')
        self.assertEqual(config.owner_file, Path('/run/ntn-qd-ue.owner.json'))
        self.assertEqual(config.private_dir, self.root / '.private/profiles/integrated-handover')
        self.assertEqual(config.trace, self.root / 'local_ntn/stk_trace_seamless.csv')
        self.assertEqual(config.schedule, self.root / 'local_ntn/satellite_schedule_seamless.csv')
        self.assertEqual(config.dl_bundle, self.root / 'examples/handover/downlink')
        self.assertEqual(config.ul_bundle, self.root / 'examples/handover/uplink')
        self.assertEqual(config.interpolation, 'legacy-linear')
        self.assertFalse(config.timing_assist)
        self.assertTrue(config.qd_required)
        other = resolve_runtime(self.root, 'integrated-handover', 'run-b', {})
        for name in ('run_dir', 'state_file', 'gnb_config', 'initial_delay_file'):
            self.assertNotEqual(getattr(config, name), getattr(other, name))
        self.assertNotEqual(config.run_dir / 'gnb.log', other.run_dir / 'gnb.log')
        for field in dataclasses.fields(config):
            if field.name in ('schedule', 'dl_bundle', 'ul_bundle'):
                continue
            if field.name.endswith('_dir') or field.name in ('root', 'oai_repo', 'state_file', 'gnb_config', 'initial_delay_file', 'ue_config', 'trace', 'owner_file'):
                self.assertIsInstance(getattr(config, field.name), Path)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            config.rf_port = 4043

    def test_zky_legacy_defaults(self):
        zky = resolve_runtime(self.root, 'zky', 'default', {})
        self.assertEqual(zky.oai_repo, self.root / '.runtime/oai')
        self.assertEqual(zky.build_dir, zky.oai_repo / 'cmake_targets/ran_build/build')
        self.assertEqual(zky.ue_config, Path.home() / '.local/share/oai-stk/ue.local.conf')
        self.assertEqual(zky.trace, self.root / 'examples/fdd-pass/trace.csv')
        self.assertEqual(zky.state_file, self.root / 'local_ntn/processes.json')
        self.assertEqual(zky.namespace, 'oai-stk-ue')
        self.assertEqual(zky.rf_port, 4043)
        self.assertEqual(zky.interpolation, 'hermite')
        self.assertEqual(zky.owner_file, Path('/run/oai-stk-ue.owner.json'))
        override = resolve_runtime(self.root, 'zky', 'default', {'OAI_REPO': '/tmp/custom-oai', 'OAI_UE_CONFIG': '/tmp/custom-ue.conf'})
        self.assertEqual(override.oai_repo, Path('/tmp/custom-oai'))
        self.assertEqual(override.ue_config, Path('/tmp/custom-ue.conf'))
        legacy = resolve_runtime(self.root, 'legacy-handover', 'default', {})
        self.assertFalse(legacy.qd_required)
        self.assertIsNone(legacy.dl_bundle)
        self.assertIsNone(legacy.ul_bundle)
        self.assertEqual(legacy.private_dir, self.root / '.private/profiles/integrated-handover')
        self.assertEqual(legacy.interpolation, 'legacy-linear')
        self.assertEqual(resolve_runtime(self.root, '', '', {'OAI_NTN_PROFILE': 'legacy-handover', 'OAI_NTN_RUN_ID': 'env-run'}).run_id, 'env-run')
        self.assertEqual(resolve_runtime(self.root, 'zky', 'explicit', {'OAI_NTN_PROFILE': 'legacy-handover', 'OAI_NTN_RUN_ID': 'env-run'}).profile, 'zky')

    def test_invalid_run_id(self):
        for run_id in ('../escape', 'a/b', '-first', '_first', 'a b', 'a' * 65, 'x;echo bad'):
            with self.subTest(run_id=run_id), self.assertRaises(ValueError):
                resolve_runtime(self.root, 'integrated-handover', run_id, {})
        for run_id in ('a', 'A0_', 'a' * 64):
            self.assertEqual(resolve_runtime(self.root, 'integrated-handover', run_id, {}).run_id, run_id)
        with self.assertRaises(ValueError):
            resolve_runtime(self.root, 'unknown', 'default', {})

    def test_contaminated_environment_rejected(self):
        values = {'OAI_REPO': '/home/kayoko/OAI/openairinterface5g',
                  'OAI_BUILD_DIR': '/home/kayoko/OAI/openairinterface5g/cmake_targets/ran_build/build',
                  'OAI_BUILD_REPO': '/home/kayoko/OAI/openairinterface5g',
                  'OAI_UE_CONFIG': str(self.root / '.private/ue.conf'),
                  'OAI_NTN_PRIVATE_DIR': str(self.root / '.private'),
                  'OAI_NTN_RUN_DIR': str(self.root / 'local_ntn'),
                  'OAI_NTN_NAMESPACE': 'oai-stk-ue', 'OAI_NTN_HOST_VETH': 'oai-stk-host',
                  'OAI_NTN_UE_VETH': 'oai-stk-peer', 'OAI_RF_HOST_IP': '10.201.0.1',
                  'OAI_RF_UE_IP': '10.201.0.2', 'OAI_RF_PORT': '4043',
                  'OAI_CORE_PROJECT': 'oai', 'OAI_AMF_IP': '192.168.70.132',
                  'OAI_GNB_IP_CIDR': '192.168.70.129/26', 'OAI_EXT_DN_IP': '192.168.70.135',
                  'OAI_EXT_DN_CONTAINER': 'oai-ext-dn', 'OAI_UE_PDU_SUBNET': '12.1.1.0/24',
                  'OAI_NTN_OWNER_FILE': '/run/oai-stk-ue.owner.json',
                  'OAI_STK_TRACE': '/tmp/original-trace.csv',
                  'OAI_QD_DL_CHANNEL': str(self.root / 'examples/fdd-pass/downlink'),
                  'OAI_QD_UL_CHANNEL': str(self.root / 'examples/fdd-pass/uplink')}
        for profile in ('integrated-handover', 'legacy-handover'):
            for key, value in values.items():
                with self.subTest(profile=profile, key=key), self.assertRaises(ValueError):
                    resolve_runtime(self.root, profile, 'default', {key: value})
        original_private = self.root / '.private/original'
        original_private.mkdir(parents=True)
        profile_parent = self.root / '.private/profiles'
        profile_parent.mkdir()
        alias = profile_parent / 'integrated-handover'
        alias.symlink_to(original_private, target_is_directory=True)
        with self.assertRaises(ValueError):
            resolve_runtime(self.root, 'integrated-handover', 'default', {})
        alias.unlink()
        outside = self.root.parent / (self.root.name + '-outside')
        outside.mkdir()
        self.addCleanup(outside.rmdir)
        (self.root / '.runtime').mkdir()
        (self.root / '.runtime/oai').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            resolve_runtime(self.root, 'integrated-handover', 'default', {})

    def test_isolated_oai_source_and_build_are_exact(self):
        repo = self.root / '.runtime/oai'
        build = repo / 'cmake_targets/ran_build/build'
        accepted = {'OAI_REPO': str(repo), 'OAI_BUILD_DIR': str(build),
                    'OAI_BUILD_REPO': str(repo)}
        conflicting = (
            {'OAI_REPO': str(self.root / '.runtime/alternate-oai')},
            {'OAI_REPO': str(repo / 'alternate-source')},
            {'OAI_BUILD_DIR': str(self.root / '.runtime/alternate-build')},
            {'OAI_BUILD_DIR': str(repo / 'alternate-build')},
            {'OAI_REPO': str(repo), 'OAI_BUILD_REPO': str(self.root / '.runtime/alternate-oai')},
        )
        for profile in ('integrated-handover', 'legacy-handover'):
            config = resolve_runtime(self.root, profile, 'exact', accepted)
            self.assertEqual(config.oai_repo, repo)
            self.assertEqual(config.build_dir, build)
            self.assertEqual(config.to_env()['OAI_BUILD_REPO'], str(repo))
            for env in conflicting:
                with self.subTest(profile=profile, environ=env), self.assertRaises(ValueError):
                    resolve_runtime(self.root, profile, 'exact', env)
        custom_repo = self.root / '.runtime/alternate-oai'
        custom_build = self.root / '.runtime/alternate-build'
        zky = resolve_runtime(self.root, 'zky', 'exact',
                              {'OAI_REPO': str(custom_repo), 'OAI_BUILD_DIR': str(custom_build)})
        self.assertEqual(zky.oai_repo, custom_repo)
        self.assertEqual(zky.build_dir, custom_build)
        custom_repo.mkdir(parents=True)
        repo.symlink_to(custom_repo, target_is_directory=True)
        for profile in ('integrated-handover', 'legacy-handover'):
            with self.subTest(profile=profile, symlink=True), self.assertRaises(ValueError):
                resolve_runtime(self.root, profile, 'exact', {})
    def test_env_roundtrip_and_private_settings(self):
        config = resolve_runtime(self.root, 'integrated-handover', 'first', {})
        env = config.to_env()
        self.assertEqual(env['OAI_STK_TRACE_INTERPOLATION'], 'legacy-linear')
        self.assertEqual(env['OAI_STK_BLEND_TIMING_ASSIST'], '0')
        self.assertEqual(resolve_runtime(self.root, 'integrated-handover', 'first', env), config)
        private = config.private_dir
        private.mkdir(parents=True)
        (private / 'settings.json').write_text(json.dumps({'amf_ip': '192.168.70.132', 'db_password': 'secret-fixture'}))
        with self.assertRaises(ValueError):
            resolve_runtime(self.root, 'integrated-handover', 'first', {})
        (private / 'settings.json').write_text(json.dumps({'amf_ip': '192.168.71.132', 'db_password': 'secret-fixture'}))
        with self.assertRaises(ValueError):
            resolve_runtime(self.root, 'integrated-handover', 'first', {'OAI_AMF_IP': '192.168.70.132'})
        self.assertNotIn('secret-fixture', json.dumps(resolve_runtime(self.root, 'integrated-handover', 'first', {}).to_env()))

    def test_cli_and_shell_compatibility(self):
        source_root = Path(__file__).resolve().parents[1]
        cli = [sys.executable, str(source_root / 'local_ntn/runtime_config.py')]
        clean = {key: value for key, value in os.environ.items() if not key.startswith('OAI_')}
        result = subprocess.run(cli + ['--profile', 'integrated-handover', '--run-id', 'cli-test', '--format', 'json'], env=clean, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['rf_port'], 4044)
        result = subprocess.run(cli + ['--profile', 'integrated-handover', '--format', 'env'], env=clean, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        shell = subprocess.run(['bash', '-c', result.stdout + '\nprintf "%s" "$OAI_NTN_NAMESPACE"'], env=clean, capture_output=True, text=True)
        self.assertEqual(shell.stdout, 'ntn-qd-ue')
        script = shlex.quote(str(source_root / 'scripts/env.sh'))
        shell = subprocess.run(['bash', '-c', f'source {script}; printf "%s\\n" "$OAI_UE_CONFIG" "$OAI_STK_TRACE"'], env=clean, capture_output=True, text=True)
        self.assertEqual(shell.returncode, 0, shell.stderr)
        self.assertEqual(shell.stdout.splitlines(), [str(source_root / '.private/ue.conf'), str(source_root / 'examples/fdd-pass/trace.csv')])
        bad = dict(clean, OAI_NTN_PROFILE='integrated-handover', OAI_REPO='/home/kayoko/OAI/openairinterface5g')
        shell = subprocess.run(['bash', '-c', f'source {script}; status=$?; printf "%s\\n" "$status" "${{OAI_NTN_NAMESPACE-unset}}" "$OAI_REPO"'], env=bad, capture_output=True, text=True)
        self.assertEqual(shell.stdout.splitlines(), ['1', 'unset', bad['OAI_REPO']])


if __name__ == '__main__':
    unittest.main()
