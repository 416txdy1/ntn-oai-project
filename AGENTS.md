# NTN OAI project instructions

## Scope

This repository coordinates an OAI 5G NTN experiment using STK, RFsim, and
OAI 5GC. OAI, QuaDRiGa and build-tool source snapshots are delivered in vendor/; keep their
exact versions and current overlays documented. Do not commit .runtime/ build trees or .private/ credentials. Current OAI overlays live in oai_patch/current/, QD C modules in quadriga/oai/. Use scripts/build.sh and scripts/test.sh.

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
bash scripts/build.sh
```

Before claiming a change works, run the trace parser and IQ regression tests
and record the exact command and result in the project notes.
