# LEO constellation validation — 2026-09-23

## Scenario and trace

- STK scenario: `STK_LEO_Constellation_20260923_train_v2/OAI_LEO_Constellation.sc`
- Six-satellite LEO train: `OAI_LEO_P01_S01` … `OAI_LEO_P01_S06`
- RFsim replay trace: `local_ntn/stk_trace.csv`
- Satellite schedule: `local_ntn/satellite_schedule.csv`
- Trace interval: STK 7614–9000 s, 1 Hz, 1387 rows
- Trace metadata: 1387 valid downlink rows and 1387 valid uplink rows; three schedule state changes

## Verification commands

```text
python -m pytest -q local_ntn/test_satellite_schedule.py
# Windows result: 4 passed

wsl.exe -d Ubuntu-22.04 -- python3 /mnt/d/实验室学习工作/杂活/雄安/OAI调研/local_ntn/test_trace_validation.py
# PASS: trace physical bounds, finite fields, flags and valid input

wsl.exe -d Ubuntu-22.04 -- python3 /mnt/d/实验室学习工作/杂活/雄安/OAI调研/local_ntn/test_real_iq.py
# PASS actual rxAddInput: 10dB loss energy ratio=0.100000000; outage=0; noise ratio=0.038400000; delay and Doppler changed

wsl.exe -d Ubuntu-22.04 -- cmake --build /home/kayoko/OAI/openairinterface5g/cmake_targets/ran_build/build --target rfsimulator -j 6
# Built target rfsimulator

wsl.exe -d Ubuntu-22.04 -- cmake --build /home/kayoko/OAI/openairinterface5g/cmake_targets/ran_build/build --target nr-softmodem nr-uesoftmodem rfsimulator -j 6
# Built target nr-uesoftmodem; Built target rfsimulator; `BUILD_RC=0`
```

## End-to-end command

The interactive runner was started in a visible WSL terminal. It requested the
sudo password once, started the 5GC compose stack, then ran:

```text
sudo -E env OAI_STK_TRACE=.../local_ntn/stk_trace.csv OAI_STK_SCHEDULE=.../local_ntn/satellite_schedule.csv OAI_STK_TRACE_RATE=1 python3 local_ntn/validate_dynamic.py --tag constellation-20260923
```

## Results

- PDU session established; UE received IPv4 `12.1.1.66` and created `oaitun_ue1`.
- UE and gNB logs both loaded the schedule and selected `OAI_LEO_P01_S06`.
- Ping to ext-DN `192.168.70.135`: 10/10 replies, 0% loss, RTT 113.486–256.284 ms, average 168.887 ms.
- Uplink UDP iperf3: 100 Kbit/s target, 0/130 datagrams lost, receiver 99.3 Kbit/s, jitter 47.503 ms.
- Downlink UDP iperf3 (`-R`): 100 Kbit/s target, 0/130 datagrams lost, receiver 100 Kbit/s, jitter 3.906 ms.

The bounded validation window did not run long enough to reach the later
schedule handovers at STK 8244 s and 8799 s; those rows are present in the
trace/schedule and will be used by a longer handover-specific run.

The gNB and UE are intentionally left running after the test for inspection.
Stop only the controller-owned processes with:

```text
sudo python3 local_ntn/experiment.py stop
```
