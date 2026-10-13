# NTN short-PRACH arrival window

The integrated and legacy handover profiles precompensate satellite delay. A small remaining early arrival can fall outside OAI's positive-only PRACH correlation search and be attributed to another cyclic shift. A real FDD A1 production-IQ fixture reproduced generated preamble 33 becoming detected preamble 34 with TA28 after advancing its waveform by 12 samples at 7.68 MHz. Zero advance decoded 33 with TA0. The UE therefore rejected the different RAPID and did not transmit Msg3; gNB Msg3 retransmission logs did not prove UE Msg3 CRC failures.

The new overlay changes only unrestricted short139 detection with nonzero NCS in `integrated-handover` and `legacy-handover`. It searches the same number of correlation bins on both sides of the existing preamble center, uses a signed winning delay for peak selection and ties, then clamps a negative winning delay to zero before the existing RAR conversion. Energy thresholds, waveform generation, compensation, timing-advance formulas, and clocks are unchanged. Absent, zky, foreign profiles, NCS0, restricted sets and long839 retain the original positive search. No known UE preamble is used to choose a candidate.

The bounded window is not a general solution for arbitrary arrival errors. For NCS34 it covers 62 correlation bins around the existing floored center. The production regression asserts truth through conservative ±56 hardware samples and records ±60/64/68 boundaries without claiming universal correctness at those offsets.

Run after formal source preparation and building `nr_prachsim`:

```bash
python3 scripts/test_prach_centered_iq.py --output .private/prach-iq-fresh
```

The test links actual `generate_nr_prach`, `rx_nr_prach_ru`, and `rx_nr_prach` objects; it compares the candidate with the checksum-verified original vendor source. Private outputs retain exact commands, object/library hashes, configurations, expected preamble truth, decoded IDs, energy, and TA. It requires the actual failing baseline and a passing candidate, plus zero/positive controls, six preambles across root boundaries, both new-profile gates, unchanged default gates, NCS0, restricted and long839 compatibility controls. Simulator exit0 alone does not mean decoder correctness.

The stock simulator's bandwidth helper rejects 24 RB, so the fixture initializes 25 RB with the same Fs7680000, FFT512, FDD A1 and NCS34. Both production TX and RX use `k=12*k1-6*N_RB_UL`, giving matched indices −150 instead of −144. This is a focused decoder-window test, not a claim of the complete live configuration. The private driver also selects FDD PRACH occasions, safely shifts a separate buffer with signed bounds, handles the simulator's NCS0 root-count division, and uses the actual generator's returned transmit energy for 30 dB AWGN. Earlier geometric reproductions using the stock untouched energy variable had zero noise and are recorded separately.

Final acceptance still requires the actual continuous IQ/STK-aligned live business cases and two complete satellite-switch windows; this regression does not replace them.
Restricted-set controls verify that both TX and RX use the same actual flag, NCS and stock root count. They preserve stock outputs, including its preamble1 fixture misidentification; preamble0 provides separately verified zero/positive truth controls. This demonstrates compatibility of an excluded path, not new restricted-set support or a diagnosis of its original behavior.
