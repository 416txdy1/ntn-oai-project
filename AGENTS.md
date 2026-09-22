# NTN OAI project instructions

## Scope

This repository coordinates an OAI 5G NTN experiment using STK, RFsim, and
OAI 5GC. The OAI and 5GC source trees are external repositories; keep their
exact commits and local patches documented rather than committing build trees.

## Safety

- Never commit K, OPc, subscriber secrets, database passwords, or private keys.
- Do not publish raw UE logs: they may contain test credentials.
- Do not use broad `pkill -f` cleanup commands.
- Do not overwrite original OAI configuration templates.

## Runtime model

The supported deterministic mode exports an STK trace and replays it using the
RFsim IQ sample clock. Both gNB and UE must use the same trace and rate.

## Main commands

```bash
sudo python3 local_ntn/validate_dynamic.py --tag codex-test
sudo python3 local_ntn/experiment.py stop
```

Build the OAI binaries with:

```bash
cmake --build /home/kayoko/OAI/openairinterface5g/cmake_targets/ran_build/build \
  --target nr-softmodem nr-uesoftmodem rfsimulator -j 6
```

Before claiming a change works, run the trace parser and IQ regression tests
and record the exact command and result in the project notes.
