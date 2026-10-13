#!/usr/bin/env python3
"""Exercise actual OAI PRACH IQ generation/extraction/decoding; no live resources.

Run on Linux after prepare_sources and nr_prachsim build. Artifacts stay private.
R25 is required by the stock simulator bandwidth helper; TX/RX index formulas
both use 12*k1-6*N_RB_UL. Fs/FFT and A1/NCS34 equal the 24-RB live geometry.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile


def run(argv, cwd, output, env=None):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
    output.write_text(result.stdout + result.stderr)
    assert result.returncode == 0, (argv[0], result.returncode, str(output))
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    oai = root / '.runtime/oai'
    build = oai / 'cmake_targets/ran_build/build'
    source = oai / 'openair1/SIMULATION/NR_PHY/prachsim.c'
    driver = source.read_text()
    driver = driver.replace('frame_parms->frame_type       = TDD;', 'frame_parms->frame_type       = FDD;')
    driver = driver.replace('uint64_t absoluteFrequencyPointA =', 'frame_parms->frame_type = FDD;\n  uint64_t absoluteFrequencyPointA =')
    driver = driver.replace('uint8_t subframe = 9;', 'uint8_t subframe = 4;')
    driver = driver.replace('uint8_t slot = 10 * frame_parms->slots_per_subframe - 1;', 'uint8_t slot = 4 * frame_parms->slots_per_subframe;')
    driver = driver.replace('if (config_index<67 && mu != 3)  { prach_sequence_length=0; slot = subframe * frame_parms->slots_per_subframe; }', 'if (config_index<67 && mu != 3) { subframe=1; prach_sequence_length=0; slot = subframe * frame_parms->slots_per_subframe; }')
    needle = '  for (i = 0; i < frame_parms->samples_per_subframe; i++) {'
    assert driver.count(needle) == 1
    driver = driver.replace(needle, '''  c16_t *fixture_shifted = calloc(frame_parms->samples_per_frame, sizeof(c16_t));
  AssertFatal(fixture_shifted != NULL, "fixture allocation failed");
  for (int dst = 0; dst < frame_parms->samples_per_frame; ++dst) {
    long src = (long)dst - (long)delay;
    if (src >= 0 && src < frame_parms->samples_per_frame)
      fixture_shifted[dst] = txdata[0][src];
  }
  printf("FIXTURE_CONFIG Fs=%d FFT=%d FDD=%d format=%d NCS=%d expected=%d shift=%d\\n", frame_parms->samples_per_subframe*1000,frame_parms->ofdm_symbol_size,frame_parms->frame_type==FDD,prach_format,prach_pdu.num_cs,preamble_tx,delay);
''' + needle)
    driver = driver.replace('txdata[aa][prach_start + i]', 'fixture_shifted[prach_start + i]')
    driver = driver.replace('  free_channel_desc_scm(UE2gNB);', '  free(fixture_shifted);\n  free_channel_desc_scm(UE2gNB);')
    driver = driver.replace('1+(64/(N_ZC/prach_pdu.num_cs))', '(prach_pdu.num_cs == 0 ? 64 : 1+(64/(N_ZC/prach_pdu.num_cs)))')
    driver = driver.replace('  generate_nr_prach(UE, 0, frame, slot, tx);', '  printf("FIXTURE_RESTRICTED TX=%d RX=%d TXNCS=%d RXNCS=%d TXROOTS=%d RXROOTS=%d\\n", ue_prach_pdu->restricted_set,prach_config->restricted_set_config.value,ue_prach_pdu->num_cs,prach_pdu.num_cs,ue_prach_config->num_prach_fd_occasions_list[0].num_root_sequences,prach_config->num_prach_fd_occasions_list[0].num_root_sequences.value);\n  tx_lev = generate_nr_prach(UE, 0, frame, slot, tx);')
    driver = driver.replace('        //        printf(" preamble_energy', '        printf("FIXTURE_RESULT expected=%d actual=%d delay=%d energy=%d shift=%d\\n", preamble_tx,out.max_preamble,out.max_preamble_delay,out.max_preamble_energy,delay);\n        //        printf(" preamble_energy')
    (output / 'driver.c').write_text(driver)
    commands = subprocess.check_output(['ninja', '-t', 'commands', 'nr_prachsim'], cwd=build, text=True).splitlines()
    def compile_command(original, copied, obj):
        argv = shlex.split(next(x for x in commands if ' -c ' in x and str(original) in x))
        argv.insert(2, '-I' + str(source.parent))
        for flag, dest in [('-MT', obj), ('-MF', str(obj)+'.d'), ('-o', obj), ('-c', copied)]:
            argv[argv.index(flag)+1] = str(dest)
        return argv
    original_detector = oai / 'openair1/PHY/NR_TRANSPORT/nr_prach.c'
    # A real pinned baseline, rather than a Python mirror of the detector.
    archive = root/'vendor/oai-source.tar.gz'
    checks = json.loads((root/'vendor/checksums.json').read_text(encoding='utf-8-sig'))
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == checks[archive.name]
    with tarfile.open(archive) as tar:
        member = next(x for x in tar.getmembers() if x.name.removeprefix('./') == 'openair1/PHY/NR_TRANSPORT/nr_prach.c')
        baseline = tar.extractfile(member).read().decode()
    (output / 'baseline.c').write_text(baseline)
    proof = {'commands': [], 'linked_sha256': {}, 'baseline_sha256': hashlib.sha256(baseline.encode()).hexdigest()}
    compiles = [('driver', source, output/'driver.c'), ('baseline', original_detector, output/'baseline.c'), ('candidate', original_detector, original_detector)]
    for name, original, copied in compiles:
        argv = compile_command(original, copied, output/(name+'.o'))
        proof['commands'].append(argv)
        run(argv, build, output/(name+'-compile.log'))
    link = shlex.split(commands[-1].removeprefix(': && ').removesuffix(' && :'))
    link[link.index('CMakeFiles/nr_prachsim.dir/openair1/SIMULATION/NR_PHY/prachsim.c.o')] = str(output/'driver.o')
    for name in ['baseline', 'candidate']:
        argv = link.copy()
        argv.insert(argv.index('-o'), str(output/(name+'.o')))
        argv[argv.index('-o')+1] = str(output/name)
        proof['commands'].append(argv)
        run(argv, build, output/(name+'-link.log'))
        for argument in argv:
            path = Path(argument) if argument.startswith('/') else build/argument
            if path.is_file() and argument.endswith(('.o', '.a')):
                proof['linked_sha256'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output/'proof.json').write_text(json.dumps(proof, indent=2))
    rows = []
    def decode(binary, profile, preamble, shift, config=98, zcz=13, restricted=False):
        env = os.environ.copy()
        env['OAI_RNGSEED'] = '42'
        env.pop('OAI_NTN_PROFILE', None)
        if profile is not None:
            env['OAI_NTN_PROFILE'] = profile
        argv = [str(output/binary), '-c', str(config), '-Z', str(zcz), '-L', '1', '-m', '0', '-R', '25', '-p', str(preamble), '-d', str(shift), '-a', '-n', '1', '-s', '30']
        if restricted:
            argv += ['-H']
        label = f'{len(rows):04d}-{binary}'
        text = run(argv, build, output/(label+'.log'), env)
        geometry = next(x for x in text.splitlines() if x.startswith('FIXTURE_CONFIG'))
        geometry = {k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)', geometry)}
        assert geometry['Fs'] == 7680000 and geometry['FFT'] == 512 and geometry['FDD'] == 1, geometry
        if config == 98:
            assert geometry['format'] == 4 and geometry['NCS'] == (34 if zcz == 13 else 0), geometry
        configured = next(x for x in text.splitlines() if x.startswith('FIXTURE_RESTRICTED'))
        configured = {k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)', configured)}
        assert configured['TX'] == configured['RX'] == int(restricted), configured
        assert configured['TXNCS'] == configured['RXNCS'] and configured['TXROOTS'] == configured['RXROOTS'], configured
        records = [x for x in text.splitlines() if x.startswith('FIXTURE_RESULT')]
        assert len(records) == 1, label
        result = {k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)', records[0])}
        result.update(geometry=geometry, configured=configured, binary=binary, profile=profile, config=config, zcz=zcz, restricted=restricted, argv=argv)
        rows.append(result)
        (output/'results.json').write_text(json.dumps(rows, indent=2))
        return result
    def same(a,b):
        assert all(a[k] == b[k] for k in ['actual','delay','energy']), (a,b)
    # Six preambles span all four shifts and the two root boundaries.
    for preamble in [31,32,33,34,35,36]:
        for shift in [0,-4,-8,-12,-16,4,8,12,16,-56,-60,56,60]:
            old = decode('baseline', None, preamble, shift)
            new = decode('candidate', 'legacy-handover', preamble, shift)
            if preamble == 33 and shift == -12:
                assert old['actual'] != preamble and old['delay'] > 0, ('missing production RED',old)
            if abs(shift) <= 56:
                assert new['actual'] == preamble, new
                assert new['delay'] == 0 if shift <= 0 else new['delay'] >= 0
            if shift >= 0 and shift <= 16:
                assert old['actual'] == preamble, old
    for profile in [None,'zky','foreign','integrated-handover']:
        for shift in [0,-12,8]:
            old = decode('baseline', None, 33, shift)
            new = decode('candidate', profile, 33, shift)
            if profile == 'integrated-handover':
                assert new['actual'] == 33, new
            else:
                same(old,new)
    # NCS0 and long839 remain identical under the new profile as well.
    for config,zcz,pre in [(98,0,33),(0,13,1)]:
        for shift in [0,8]:
            old = decode('baseline', None, pre, shift, config,zcz)
            new = decode('candidate','legacy-handover',pre,shift,config,zcz)
            same(old,new)
            assert old['actual'] == pre, old
    for pre in [0,1]:
        for shift in [0,8]:
            old = decode('baseline', None, pre, shift, 0,13,True)
            new = decode('candidate','legacy-handover',pre,shift,0,13,True)
            same(old,new)
            if pre == 0:
                assert old['actual'] == pre, old
            # The stock restricted pre1 fixture itself misidentifies it; retain
            # that exact baseline behavior rather than fixing an excluded path.
    for shift in [-68,-64,64,68]:
        decode('candidate','legacy-handover',33,shift) # outside the bounded window: recorded, no universal correctness claim
    print(json.dumps({'passed': True, 'cases':len(rows), 'output':str(output)}))

if __name__ == '__main__':
    main()