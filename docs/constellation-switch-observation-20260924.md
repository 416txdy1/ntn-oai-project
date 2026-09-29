# 三颗卫星的切换过程：实际运行记录

## 已观察到的顺序

`OAI_LEO_P01_S06 → OAI_LEO_P01_S05 → OAI_LEO_P01_S04`

2026-09-24 读取上一轮后台运行日志，两端均有两次卫星变更记录。
以下是 OAI 实际运行日志，不是仅从调度 CSV 推算的结果。

| 阶段 | gNB 日志 STK 时间 | UE 日志 STK 时间 | 新卫星仰角 |
|---|---:|---:|---:|
| 首次选择 S06 | 7615.999 s | 7616.000 s | 10.08° |
| S06 → S05 | 8244.999 s | 8245.000 s | 17.13° |
| S05 → S04 | 8799.999 s | 8800.000 s | 21.05° |

时间来自日志打印点；调度 CSV 中两次变更时刻分别为 8244 s 和 8799 s。
日志约每 IQ 秒打印一次，因此打印时刻不等于精确的切换生效时刻。
这些是 STK/IQ 仿真时间，不是墙钟时间。

## gNB 实际日志

```text
[HW] STK satellite handover: none -> OAI_LEO_P01_S06 at STK time 7615.999 s (elevation 10.08 deg)
[HW] STK satellite handover: OAI_LEO_P01_S06 -> OAI_LEO_P01_S05 at STK time 8244.999 s (elevation 17.13 deg)
[HW] STK satellite handover: OAI_LEO_P01_S05 -> OAI_LEO_P01_S04 at STK time 8799.999 s (elevation 21.05 deg)
```

## UE 实际日志及切换后信道

```text
[HW] STK satellite handover: none -> OAI_LEO_P01_S06 at STK time 7616.000 s (elevation 10.08 deg)
[HW] STK satellite handover: OAI_LEO_P01_S06 -> OAI_LEO_P01_S05 at STK time 8245.000 s (elevation 17.13 deg)
[HW] STKTRACE2 DL IQ=630.999755 STK=8244.999755 satellite_id=OAI_LEO_P01_S05 elevation_deg=17.133 delay=15.523133ms Doppler=26556.073Hz gain=1.969dB C/N=19.441dB valid=1 samples=4846078117
[HW] STK satellite handover: OAI_LEO_P01_S05 -> OAI_LEO_P01_S04 at STK time 8800.000 s (elevation 21.05 deg)
[HW] STKTRACE2 DL IQ=1185.999737 STK=8799.999737 satellite_id=OAI_LEO_P01_S04 elevation_deg=21.048 delay=14.103184ms Doppler=25912.584Hz gain=3.004dB C/N=20.477dB valid=1 samples=9108477980
```

## 必须区分的结论

- 已确认：gNB 和 UE 均执行了选星轨迹回放，并记录三颗卫星及两次状态变更。
- 当前机制是单条 OAI 链路切换所用的卫星信道状态，不是多个真实 gNB 之间的标准 RRC/NGAP 切换。
- 未确认：切换期间 ping、iperf 业务连续。此前短测试的零丢包结果不覆盖这两次切换。
- 已发现：两次切换前后 UE 均存在 `Error decoding PBCH!`。不能将这些记录表述为无缝业务切换成功，也不能仅凭这些日志判定错误由切换引起。
- 轨迹在 STK 9000 s 结束后，RFsim 输出 `STKTRACE2 exhausted ... signal muted`；不会自动循环。此时的同步暂停提示不能直接解读为真实卫星已经落到地平线下。

## 查看原始切换记录（PowerShell）

```powershell
Select-String -Path 'D:\实验室学习工作\杂活\雄安\OAI调研\local_ntn\gnb-dynamic-constellation-20260923.log','D:\实验室学习工作\杂活\雄安\OAI调研\local_ntn\ue-dynamic-constellation-20260923.log' -Pattern 'STK satellite handover:'
```

原始 UE 日志可能含测试凭据，仅在本机查看，不应上传或公开。
