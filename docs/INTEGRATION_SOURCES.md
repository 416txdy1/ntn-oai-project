# Integration source preservation inventory

Frozen Git source inventory at f2a3d27413a9f99d85fd51afec33b8850a7112f9. This
generated inventory and subsequent test-result documentation are additional
review artifacts. Source preservation is independent of runtime acceptance:
the complete live matrix and final original-platform business recheck remain
pending; no remote push is established by this inventory.

Zky base: 70a38b5492b615498cea2332bd077c0d4f958d25.
Original pseudo-handover source: f30bc90a626214d227a7991d7429cf7723233f96.
Independent archived OAI commit: 1e0c78bfbb80424f275e73a3103f582e0f903413.
Original external OAI c4125d1c740181ab1f7da0e7dd1d04ed07c37670 and original
5GC 212f92fc6a2fb82b5df1e8f4ef20075e75acefb3 remain reference/protection targets,
not deployment targets. Builds and private credentials/logs are excluded.

Every zky path is retained. All vendor archives and the existing FDD bundle
are Git-blob-identical to zky; examples/fdd-pass/trace.csv intentionally keeps
its original CRLF working representation. There are 158 unchanged zky files,
32 compatible extensions, 13 byte-identical original restorations and 80 new
integration files, excluding this inventory document. Extensions retain old
interfaces and add isolated profiles or reviewed fixes. Provenance sidecars
and the source lock record trace/schedule/manifest/data checksums.

The independent deployed OAI consists of the pinned archive and 28 documented
overlays, with six binary hashes captured in private build proofs. The archive
audit compared 3740 non-overlay source files with no missing, differing or
unexpected source files. Neither original OAI/5GC checkout is overwritten.
Detailed actual build/test outcomes and remaining failures are recorded in
[INTEGRATION_TEST_RESULTS.md](INTEGRATION_TEST_RESULTS.md).

| Path | Classification | Git blob |
| --- | --- | --- |
| .gitattributes | compatible extension | d20958c0a74b3e3d047386b6d8c101819899eee0 |
| .gitignore | unchanged zky | 5ec04c1dda459d8144fd13f75911fb21901024eb |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/backups/step-00-baseline-20260924-161100/RESTORE-INSTRUCTIONS.txt | unchanged zky | 91bc891de31b22772abc9717c7e5fc1c04eb2f31 |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/backups/step-00-baseline-20260924-161100/STEP00_DONE.json | unchanged zky | 9e242ce024199a3dae97ebbb11e706fba775c9f4 |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/backups/step-00-baseline-20260924-161100/STEP00_VERIFIED.json | unchanged zky | b3d9d30dea8f5630dcebf0105cd04ab72ac1e207 |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/backups/step-00-baseline-20260924-161100/baseline-manifest.json | unchanged zky | ce89a27b549c3f34be53ab785b55c7096290008f |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/backups/step-00-baseline-20260924-161100/baseline-regressions.txt | unchanged zky | ae9365cb4bb52402012efc7ef8ec8d356f3fbfea |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/backups/step-00-baseline-20260924-161100/sha256.csv | unchanged zky | 9b52ef7e0f9df971df6e3505e64250ebcec50109 |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/findings.md | unchanged zky | c1bbc7fbff09ee907618fcb9ae94c687229661fb |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/progress.md | unchanged zky | d4c11a49673b37ebbe42c3fcc8c606266e2db3a4 |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/step00_baseline.ps1 | unchanged zky | 7aa6eb61021515508551284ba04f4d9fc45d4621 |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/step00_verify_visible.ps1 | unchanged zky | aa59b79e9316eadea44406a4cc3ec35e5abc3511 |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/step01_commit_visible.ps1 | unchanged zky | ed7508b3a122cda7752857332e908a7edc68d0f0 |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/step01_discovery.ps1 | unchanged zky | 970f4e5487a20aa660611c66ae93415038c8efe3 |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/step01_verify_visible.ps1 | unchanged zky | fc3e58803683dd356a5d0ded7867c8a68e4b7c62 |
| .planning/2026-09-24-stk-quadriga-oai-integration-plan/task_plan.md | unchanged zky | 7f2b928ba9ae581ebbc49bba82938884b936baf2 |
| AGENTS.md | unchanged zky | 1614cb9b254bcf80f729f4ca25abbab2164a7d4d |
| README.md | compatible extension | 2f04da87dc216966acd4111a742a9a9e53aa1194 |
| STK_LEO_Constellation_20260923_train_v2/satellite_schedule_blend.csv | unchanged zky | 4b0b69a6e22c8b966bdaa91f27280c7458635e7a |
| STK_LEO_Constellation_20260923_train_v2/stk_constellation_trace_blend.csv | unchanged zky | 1e771a5a3e5bb001dfcc781a0ff76a23e2e5274d |
| configs/core/compose.yaml.in | unchanged zky | c7839f4992ea37f77c1155ed38f5c35256381b5c |
| configs/core/config.yaml.in | unchanged zky | 559344755928bb39d454fe614403caea6c4d39c3 |
| configs/core/schema.sql | unchanged zky | 2acd24806117db331877e9c51ff3ce61a6b1c783 |
| configs/core/ue.conf.in | unchanged zky | 7014bbac79c0c3c209cdfab37e831a33cccdbfbe |
| configure_stk_phased_array.py | unchanged zky | bc232d6797fdf30547413048e761889fb045b9c4 |
| docs/BLEND_REPAIR_20261003.md | unchanged zky | 968d3a04e5b1a7d5d0e532759524ef03a6658305 |
| docs/DEBUG_ZKY.md | unchanged zky | b602e1dc03085097d9cfa7bc2482d88b449475d2 |
| docs/FULL_PASS_ACCEPTANCE_20261002.md | unchanged zky | a3ab096a1a443f4a1ac395fdd334d43d08494781 |
| docs/INTEGRATED_HANDOVER.md | new integration content | 8907a467ac86a5110edaed9c509c8d602ed361ec |
| docs/INTEGRATION_TEST_RESULTS.md | new integration content | 918a6d0385c793dc27cfd8239304595cbf2ede14 |
| docs/SELF_CONTAINED_VALIDATION.md | unchanged zky | 192a2ea94ea2f2c4e231569b40b6215d41c201ec |
| docs/continuous-handover-acceptance.md | new integration content | 71f990c84d9d4060d27ffb7a8ca67226eb342a6f |
| docs/prach-centered-search.md | new integration content | 1a813bb9c9be63b57699c7e65e60fccfe12c1bd9 |
| docs/receiver-pilot-tracking.md | new integration content | aad17ac52c75288ee21553018f737e2070ec7228 |
| docs/receiver-tx-prediction.md | new integration content | 3bb751af4051b389952f27a39e5937c560d66495 |
| docs/superpowers/plans/2026-09-10-local-ntn.md | unchanged zky | deaad17e5c82bd2e58e48b10a271ab3a2795d113 |
| docs/superpowers/plans/2026-10-09-ntn-quadriga-handover.md | new integration content | b3dbfde6d6db392e4c4a52605eafa4cae06f2d52 |
| docs/superpowers/specs/2026-10-09-ntn-quadriga-handover-design.md | new integration content | 54d74c4f6db99edf8c535692a5272b23cc3cc25b |
| examples/fdd-pass/downlink/coefficients.cf32 | unchanged zky | fe94ed057532675a52fa6053350724fd154d02e6 |
| examples/fdd-pass/downlink/delays.f64 | unchanged zky | 8b87375087a5360ef2e5c995d5a02535131b5510 |
| examples/fdd-pass/downlink/manifest.json | unchanged zky | aade4d5f3da5cb1df2299760d64589b58cbe6dd5 |
| examples/fdd-pass/downlink/residual_gain_db.f32 | unchanged zky | b5a1f728eca034669f2d96edd91fcb8af6f59809 |
| examples/fdd-pass/downlink/times.f64 | unchanged zky | 8278e1e3fdd0e3bce0c794b70968dedd9c40db19 |
| examples/fdd-pass/trace.csv | unchanged zky | 3a9472ab859cff46b76da575b94d7b3439dfab25 |
| examples/fdd-pass/uplink/coefficients.cf32 | unchanged zky | f9e071f1b7e69b6e0b4dbb2fea98c9b6ed192335 |
| examples/fdd-pass/uplink/delays.f64 | unchanged zky | b47eeb399f12d380e38e9f93dfc7e48d04627134 |
| examples/fdd-pass/uplink/manifest.json | unchanged zky | 6fa3574a57b08ae1fa87a4d440ffa72aedb81cd2 |
| examples/fdd-pass/uplink/residual_gain_db.f32 | unchanged zky | b5a1f728eca034669f2d96edd91fcb8af6f59809 |
| examples/fdd-pass/uplink/times.f64 | unchanged zky | 8278e1e3fdd0e3bce0c794b70968dedd9c40db19 |
| examples/handover/downlink/coefficients.cf32 | new integration content | 1d45d64705e9cdd3db7866076963c7fb232564af |
| examples/handover/downlink/delays.f64 | new integration content | 731ca55efd35861144c8f84bc7cb025fe5be56d0 |
| examples/handover/downlink/manifest.json | new integration content | 61038b26bcdb87bbf707d317463183f35cf504f3 |
| examples/handover/downlink/residual_gain_db.f32 | new integration content | 44c96fdbac1c9becbfabb8b5ea9414b98367edd5 |
| examples/handover/downlink/times.f64 | new integration content | aaa6486f1c6d1365dad7410b6cfb17f6afa9fa6e |
| examples/handover/firsthandover/downlink/coefficients.cf32 | new integration content | 5c4914bc36e12de6ebd59e692b25eeeb9e8896ed |
| examples/handover/firsthandover/downlink/delays.f64 | new integration content | 3cbe3b0a95d05e129c4a6f0ca1fff1d8fdbb14e5 |
| examples/handover/firsthandover/downlink/manifest.json | new integration content | 47f1cbcab02205b5d35ff84bc00004efaaeb41a8 |
| examples/handover/firsthandover/downlink/residual_gain_db.f32 | new integration content | 01727ba964c92aad112647ee3864123a1b601631 |
| examples/handover/firsthandover/downlink/times.f64 | new integration content | 309a6124b43d5ced86f6896658e9b6932bbd913d |
| examples/handover/firsthandover/provenance.json | new integration content | ee58027395e5dcf506716ecb740a2087a1a87f48 |
| examples/handover/firsthandover/uplink/coefficients.cf32 | new integration content | 4b7218a266098dbaaed47c63c58f522c6cb32408 |
| examples/handover/firsthandover/uplink/delays.f64 | new integration content | c32f5f10803d713909897e5f2a21e68b0fd21d80 |
| examples/handover/firsthandover/uplink/manifest.json | new integration content | 5b5bf5a1c9f5a5738a18dac203da85c8fd9b9880 |
| examples/handover/firsthandover/uplink/residual_gain_db.f32 | new integration content | 01727ba964c92aad112647ee3864123a1b601631 |
| examples/handover/firsthandover/uplink/times.f64 | new integration content | 309a6124b43d5ced86f6896658e9b6932bbd913d |
| examples/handover/provenance.json | new integration content | 37c405270d43463f29217e3cd594cd646e43e5e8 |
| examples/handover/uplink/coefficients.cf32 | new integration content | 473f651a5eb4c1f4b4a27c4caa70f34009aebd04 |
| examples/handover/uplink/delays.f64 | new integration content | fb24f6d576fe70b00c8d148e12d84691501379c2 |
| examples/handover/uplink/manifest.json | new integration content | f274355cac19e057259d131e1e118ec7167b6140 |
| examples/handover/uplink/residual_gain_db.f32 | new integration content | 44c96fdbac1c9becbfabb8b5ea9414b98367edd5 |
| examples/handover/uplink/times.f64 | new integration content | aaa6486f1c6d1365dad7410b6cfb17f6afa9fa6e |
| forward_stk_csv.py | unchanged zky | 640c143d941fea6ab28ba1893d6aee05c7d567e1 |
| local_ntn/DEBUG-2026-09-23.md | unchanged zky | 50cf8f8748cca1449a370160fc067619b79ab88a |
| local_ntn/DEBUG-2026-09-24.md | unchanged zky | b16b334525baab6f3a59403b96924d8fa0ce60ef |
| local_ntn/DEBUGGING_GUIDE.md | unchanged zky | 9b49a2cfb5ab875219dbcb8c2340e3d1924cec3a |
| local_ntn/JOINT_SIMULATION.md | unchanged zky | 01daf216558e01f4f96640ae1ae0ac6f60ac5c9b |
| local_ntn/MANUAL_RUN.md | unchanged zky | 069f070dcdcc2fb7be6c07e9bac6ff13ecb1ac74 |
| local_ntn/README.md | unchanged zky | 8313e6943ff5064aec1aeece86c283bc00536814 |
| local_ntn/audit_auth.py | unchanged zky | c72c4ca70f4ed259d039bd4cd9818f6700a0961c |
| local_ntn/audit_runtime_numbers.py | compatible extension | a080c094091c12cb0b8b80b2930055b17a36a633 |
| local_ntn/create_leo_constellation.py | byte-identical original restoration | 695674f4f1ceaceeeed9c45590283690f0556623 |
| local_ntn/debug_console.ps1 | unchanged zky | ceeb3d6c7c87be793eec60bc7b32d848bba469c4 |
| local_ntn/debug_run.ps1 | unchanged zky | bc72f79d45b78bb811f956a69e8677034857644a |
| local_ntn/experiment.py | compatible extension | 8ea2df9687fa50b3a9d9eee5253d3789d582621a |
| local_ntn/export_constellation_trace.py | byte-identical original restoration | 18ccf07fefe5eb189dfdb09683886c257ce5465c |
| local_ntn/export_stk_trace.py | unchanged zky | 8abbea8ee86a1af111486cad3fac08708ca49143 |
| local_ntn/handover_blend.py | byte-identical original restoration | ef32dd6ae90625bc6c5d7ec11761dba2b52b1b0a |
| local_ntn/handover_profiles.py | new integration content | aee1c1a688ebc036ac53381e52e053be770817bc |
| local_ntn/local_network.sh | compatible extension | 34d1b3517ced4aaeadc5f80122497cfc5508c4db |
| local_ntn/network_config.py | unchanged zky | 76f2021e45858adc384a6f869d1ce6929d1d9904 |
| local_ntn/network_owner.py | new integration content | 08035a301638b6b73a4d5472e8b852f1490b0bb7 |
| local_ntn/ntn_timing_budget.py | new integration content | ae8dd1c6bae023e98a1e0fe4ab81fbeb80546ba5 |
| local_ntn/original/CMakeLists.txt | unchanged zky | 979b1b26fdff56f9dcd03ad2dd19784a44028fce |
| local_ntn/original/apply_channelmod.c | unchanged zky | ae68ac4a6e0da454675c31642ea4b6f72e665e68 |
| local_ntn/original/common_lib.c | unchanged zky | 0b4f1dfcd104997ed147d2db832c22c5548a3c9e |
| local_ntn/original/rfsimulator.h | unchanged zky | d4bfeda527bdb42969ead4cdb474ccbe4d80b97b |
| local_ntn/original/stk_channel_model.c | unchanged zky | 485d18a8204c242c4e75d206ccf38953f4bbf807 |
| local_ntn/paths.py | compatible extension | 6867418c2f6ec797d987ca0fc580e759d261ce43 |
| local_ntn/preflight.py | compatible extension | 320db90f27c390ce8bea59d0b4b13f0397c7b4e4 |
| local_ntn/prepare_local.py | compatible extension | 57b0cee1c8a70a20b890c66bae37ccf803a3f62d |
| local_ntn/provision_subscriber.py | unchanged zky | 0f7282fd3c3e6aa1213a95ddcffaa52ee3ad5f35 |
| local_ntn/run_constellation_validation.sh | new integration content | 2b651c5361c42d81cef9b9d2b5d556af2414791d |
| local_ntn/run_local.sh | compatible extension | 6fdd6b001a297ad5ac0d8169e30d714a72c1fb1c |
| local_ntn/run_regressions.sh | compatible extension | efc1c866b082a9003a2691874135b6f07e1b9c56 |
| local_ntn/run_seamless_validation.sh | new integration content | 22a53fcd0070a61e99f801833b517f3b7b8ddddd |
| local_ntn/run_state.py | new integration content | 2dc591207dee87eddc68b7e6f1972748d4503289 |
| local_ntn/runtime_config.py | new integration content | 38c483bb1cae028a5b2bc76bafd329fc5bb0ed49 |
| local_ntn/satellite_schedule.csv | byte-identical original restoration | 03d8d7c261f2feb362cdc88ed7ccee089935aeae |
| local_ntn/satellite_schedule.py | byte-identical original restoration | 11ec17448295b3cd0ac09e17b084b1a9c5074e8f |
| local_ntn/satellite_schedule_firsthandover.csv | byte-identical original restoration | d8694e089cf0cf4be86054bf91bff114772aa229 |
| local_ntn/satellite_schedule_seamless.csv | byte-identical original restoration | e3ada151bccbb4618d2b42356ad3f81dbc4a4d45 |
| local_ntn/slice_trace.py | new integration content | 2eb0a832529221164ba94a6f04f413d3baf8a384 |
| local_ntn/staged/CMakeLists.txt | unchanged zky | f6f685ff4869c35a9f1ba17726582d222fad71c0 |
| local_ntn/staged/apply_channelmod.c | unchanged zky | 7266d8eb1ea69c182be6c395878a65d4cf9efb84 |
| local_ntn/staged/common_lib.c | unchanged zky | bb97a9dce97600c793e3db33eece46b35f037206 |
| local_ntn/staged/rfsimulator.h | unchanged zky | 7b12e4655d95c4c9247a5185455102347aaebc38 |
| local_ntn/staged/stk_channel_model.c | unchanged zky | 1199a3b34fa4af089022dce1c38191ffea5873c9 |
| local_ntn/stk_schedule.c | byte-identical original restoration | 83123a8cbe40e55c97eb55f8bfbb1718b2339629 |
| local_ntn/stk_schedule.h | byte-identical original restoration | 2775dcddd169053ca71045e4a839f94118a068da |
| local_ntn/stk_trace.c | compatible extension | 711040dda6604607122d44ebdb2af93d1119945c |
| local_ntn/stk_trace.h | compatible extension | a8b7dbd19fcb58f2fccf9d6d0200517711ab3195 |
| local_ntn/stk_trace_channel.c | compatible extension | 8daed97a13ef2446f8deaff81c04df7a6dab5e84 |
| local_ntn/stk_trace_firsthandover.csv | byte-identical original restoration | f7685ee7e97d675c2aea130be3d1fb505578ed69 |
| local_ntn/stk_trace_seamless.csv | byte-identical original restoration | 4f507206a7980773907e8f7884a15c7c7c2ef562 |
| local_ntn/test_blend_interpolation.c | unchanged zky | 40266077b0f0dc2504465c973a9f6e0f4b929294 |
| local_ntn/test_blend_interpolation.py | unchanged zky | 128d03d2e37446362d42bc06c39149cb0cd173b1 |
| local_ntn/test_handover_blend.py | byte-identical original restoration | 69add70df7a1326132ee731167d7e534fc444cdf |
| local_ntn/test_handover_profiles.py | new integration content | be6c36887eb23b49f4f3b6207033e8bc21d5a09c |
| local_ntn/test_legacy_interpolation.c | new integration content | f258a91984426afcd156b8e5f25d46e913bb3c8f |
| local_ntn/test_legacy_interpolation.py | new integration content | 7a56365b3eed5058f1926bbf956c17ad21b72535 |
| local_ntn/test_local_setup.py | compatible extension | a7ad852eb052fbb6326bde1dac1418b6c13ed1fb |
| local_ntn/test_manifest_provenance.py | new integration content | 71ffa2f6a0510aebbf7da93447704bc316c15469 |
| local_ntn/test_network_config.py | unchanged zky | 60e14258e0d20a7bc1538dcfddbd43b7b6f1fd45 |
| local_ntn/test_network_owner.py | new integration content | c06681fb2805c9aac8970364391fe735e9251a88 |
| local_ntn/test_numeric_audit.py | new integration content | e334b9c40a72864202cde93b085953ce947d5ee3 |
| local_ntn/test_preflight.py | compatible extension | 96496737e345434d3975bb371564e0865317b3ed |
| local_ntn/test_real_iq.c | compatible extension | d5b9a2a7e1d58a3965453e9b307de4d3bcbe3446 |
| local_ntn/test_real_iq.py | compatible extension | 3bf152d7749a9ccaca598aaaa9137d01512add34 |
| local_ntn/test_run_state.py | new integration content | 7e5713cbe8bd90f3c5b780bd80541040c20a5812 |
| local_ntn/test_runtime_config.py | new integration content | 46e4a4eb6dbda33fcf2565b88111a177cc242b0d |
| local_ntn/test_satellite_schedule.py | byte-identical original restoration | 4c50973ba3e6cdae86b185b174a4fb725de654fd |
| local_ntn/test_seamless.py | new integration content | 87ee4ea58503b2af5fd63347766945f6339f93cd |
| local_ntn/test_stk_schedule.py | new integration content | fcd60a69125c7c88014727756be18a5af4085839 |
| local_ntn/test_stk_timing_assist.c | unchanged zky | 21c8860eed40b0acb5dd58712302782abc4d6f90 |
| local_ntn/test_stk_timing_assist.py | unchanged zky | c8cdef1206e7d3bef05d826573830560fefeb80d |
| local_ntn/test_trace.c | unchanged zky | bb03e7695be9351f44af92623623afb9f9a8871b |
| local_ntn/test_trace_checkout.py | new integration content | db1a92e0e69953bafac0281fffa72cf7b6dc7f50 |
| local_ntn/test_trace_validation.c | unchanged zky | 6c86a480d553523aa13d0047d48c3ec5d87e9e75 |
| local_ntn/test_trace_validation.py | unchanged zky | 6924ef05403f69fc687fa5a9e0a37dd70167b972 |
| local_ntn/validate_dynamic.py | unchanged zky | af1b24b81b83a64d3b778552af7ee34447fb18ab |
| local_ntn/verify_network.py | compatible extension | 75b2576f8f4818c063e795195f1fefe5aeef0eae |
| oai_patch/.gitkeep | unchanged zky | 8b137891791fe96927ad78e64b0aad7bded08bdc |
| oai_patch/common_lib.h | unchanged zky | 7257bf02eff8969dca7087f3e660fca000577f00 |
| oai_patch/current/CMakeLists.txt | unchanged zky | dce85ebc2c7b3c86bcae46948d5b23ed1f53b066 |
| oai_patch/current/executables/nr-ue-ru.c | unchanged zky | c67c13e60c78430b71edfcd72ebd722d2a7560a6 |
| oai_patch/current/executables/nr-ue-ru.h | unchanged zky | 88a93e2c7207b379f3ea290fa44c4a851708e2f9 |
| oai_patch/current/executables/nr-ue.c | compatible extension | aabb5376ac004dfeb4a41e63e6a538ea964ef1d5 |
| oai_patch/current/executables/stk_timing_assist.h | unchanged zky | b8958120000cf02b6a3087f262de782d529ab6e7 |
| oai_patch/current/openair1/PHY/MODULATION/modulation_UE.h | new integration content | def34d753ebf29261cdf88c84c77fb6bfb7cbf00 |
| oai_patch/current/openair1/PHY/MODULATION/slot_fep_nr.c | new integration content | 028e7f90b68457ae988780760bd9e708c8311333 |
| oai_patch/current/openair1/PHY/NR_TRANSPORT/nr_prach.c | new integration content | dbecc905524ac541cf2fd288329c91c7579ce2f2 |
| oai_patch/current/openair1/PHY/NR_UE_ESTIMATION/nr_ntn_rx_tracker.h | new integration content | e1dcb198216bfbdf520f5b1d1f78ce655d034a3e |
| oai_patch/current/openair1/PHY/NR_UE_ESTIMATION/nr_ntn_tx_predictor.h | new integration content | 44a4492f35e88ab8e350e4958b8834f91e25f138 |
| oai_patch/current/openair1/PHY/defs_nr_UE.h | new integration content | d9ae9724702430815f94ff820a092a20a224bf83 |
| oai_patch/current/openair1/SCHED_NR_UE/phy_procedures_nr_ue.c | new integration content | d418bea35a93eca1478decd0806e15685a005916 |
| oai_patch/current/openair1/SIMULATION/TOOLS/sim.h | unchanged zky | 93572d8ee0ccac1663b5b5e32e4d6ed40e3a89d2 |
| oai_patch/current/radio/COMMON/common_lib.c | unchanged zky | bb97a9dce97600c793e3db33eece46b35f037206 |
| oai_patch/current/radio/COMMON/common_lib.h | unchanged zky | e26b150179daa9d3d34f262556945838c9a8df88 |
| oai_patch/current/radio/rfsimulator/CMakeLists.txt | compatible extension | c1a38a685fbd3aa690c2dba6920c3e633b4c1684 |
| oai_patch/current/radio/rfsimulator/apply_channelmod.c | compatible extension | 6830cc631d63dbb3a8030f508da77389e5d87901 |
| oai_patch/current/radio/rfsimulator/rfsimulator.h | unchanged zky | 85f60eec9c05446c73d92c27dfc3f096e56634b1 |
| oai_patch/current/radio/rfsimulator/simulator.cpp | compatible extension | 99a30c44335d72ceb5410c45fecd1f7e8e44e7a7 |
| oai_patch/current/radio/rfsimulator/stk_channel_model.c | unchanged zky | 1199a3b34fa4af089022dce1c38191ffea5873c9 |
| oai_patch/current/radio/rfsimulator/stk_schedule.c | new integration content | 83123a8cbe40e55c97eb55f8bfbb1718b2339629 |
| oai_patch/current/radio/rfsimulator/stk_schedule.h | new integration content | 2775dcddd169053ca71045e4a839f94118a068da |
| oai_patch/current/radio/rfsimulator/stk_trace.c | compatible extension | 711040dda6604607122d44ebdb2af93d1119945c |
| oai_patch/current/radio/rfsimulator/stk_trace.h | compatible extension | a8b7dbd19fcb58f2fccf9d6d0200517711ab3195 |
| oai_patch/current/radio/rfsimulator/stk_trace_channel.c | compatible extension | 8daed97a13ef2446f8deaff81c04df7a6dab5e84 |
| oai_patch/deploy_stk_auto.sh | unchanged zky | b2b6b55faa57a4c26a876b9666db16a2ef4503b0 |
| oai_patch/nr-ue-ru.c | unchanged zky | c67c13e60c78430b71edfcd72ebd722d2a7560a6 |
| oai_patch/nr-ue-ru.h | unchanged zky | 88a93e2c7207b379f3ea290fa44c4a851708e2f9 |
| oai_patch/nr-ue.c | unchanged zky | f3b8902986be79f828e234b75340f767c6987f9d |
| oai_patch/rfsimulator.h | unchanged zky | d4bfeda527bdb42969ead4cdb474ccbe4d80b97b |
| oai_patch/simulator.cpp | unchanged zky | 3af79ec249408084b56d74e520b061c5e3c9277c |
| oai_patch/stk_channel_model.c | unchanged zky | 87f7f25368c320c7dc28963f2a9ef6b460fe7391 |
| quadriga/README.md | unchanged zky | 7976cc86a6badbf620de252e2df44a27da762d4d |
| quadriga/__init__.py | unchanged zky | bd1b8b92d4c64141332431f5f93de13a95b74987 |
| quadriga/docs/handover_export.md | new integration content | 4caa6369e40f3276ea650ecd043fc3915d31bf89 |
| quadriga/docs/recheck_20260928.md | unchanged zky | 0f2fb3fa40bab989277b5e6efb17f800d828fb94 |
| quadriga/docs/step03_numerical_audit.md | unchanged zky | 3c971f80c6b80aa55c97e5363be06b754000d2c1 |
| quadriga/docs/step04_rfsim_integration.md | unchanged zky | e3eb666504ac2768e6b89fb0d9717188a27f1854 |
| quadriga/examples/siso_two_path/coefficients.cf32 | unchanged zky | 0ea8f99b6de0e2e89e1c79195c5b910a253ba979 |
| quadriga/examples/siso_two_path/delays.f64 | unchanged zky | 12c1f66cfceb54a3bdcec1fc88a14dcad4d78396 |
| quadriga/examples/siso_two_path/manifest.json | unchanged zky | b5129ed1fc0d9c7b6f1f01ca90a71e4021607e16 |
| quadriga/examples/siso_two_path/residual_gain_db.f32 | unchanged zky | a93264c6cd171252b4e8bad792bcd9c75b960255 |
| quadriga/examples/siso_two_path/times.f64 | unchanged zky | 369a63d9b54c4a24eb905e14eb5d60282fd306ee |
| quadriga/matlab/ecef_to_enu_track.m | unchanged zky | 5a377060c144c703817fdada6e714b62f06a402a |
| quadriga/matlab/export_example_fdd.m | unchanged zky | 4306272d93a61a1db2cc5a0508b8789df256b20b |
| quadriga/matlab/export_handover_fdd.m | new integration content | ba1f7a582451d39f2a1dc17e449d9e987cdbb286 |
| quadriga/matlab/export_stk_to_qdchannel.m | unchanged zky | 0fa17fc4bcc4f09c9b1a1b9d56d110aca423629a |
| quadriga/matlab/normalize_qd_channel.m | unchanged zky | 404eb67c4f4198f8224ced2c7ed022b741afe9d2 |
| quadriga/matlab/read_stktrace2.m | unchanged zky | 5a9cd20ad837e78fdb1f3b2c80b818b2998f2dcb |
| quadriga/matlab/sha256_file.m | unchanged zky | c6ba9de1935493e1fc9ee7fa1f75a107786784c2 |
| quadriga/matlab/write_qdchannel1.m | unchanged zky | ea08dd99eb7aba95d3d44b1c231ed42db002d6b2 |
| quadriga/oai/qd_channel_adapter.c | unchanged zky | e6fb9b79041b715dd803b3a7d2da3b6f37f43d26 |
| quadriga/oai/qd_channel_reader.c | unchanged zky | 1dd0dbdd56abda3b2992c19369af4cd02b989841 |
| quadriga/oai/qd_channel_reader.h | unchanged zky | 3ddc20eabbce910c15e92aa88e71871d415cd0f9 |
| quadriga/oai/rfsim-history-fix.diff | unchanged zky | 4a5617d35fdf86c59a1e1c5bd5a83b14b4f6f49f |
| quadriga/schema/channel_bundle_v1.schema.json | unchanged zky | 9ce5a76f9c5137111f6cb86b79136849cda13474 |
| quadriga/tests/__init__.py | unchanged zky | 75576b647eb84f76bb0fa3a2566f21308af0cb93 |
| quadriga/tests/matlab_test_export_handover_fdd.m | new integration content | 4421c6903f7eb82dfc19987c93df19abd333a82a |
| quadriga/tests/qd_channel_reader_test.c | unchanged zky | 7037ee51c8f8953fa8dd46466759262abf57e311 |
| quadriga/tests/qd_rfsim_adapter_test.c | unchanged zky | 4476fe395782326ca322142228a91a98a0fb1115 |
| quadriga/tests/run_qd_channel_reader_tests.py | unchanged zky | 44807d024c4bcd37f88f8fb388f9b65081834561 |
| quadriga/tests/run_qd_rfsim_adapter_test.py | unchanged zky | 2acb58cd465c6c978049254b87b9e8b5fc72f5b7 |
| quadriga/tests/test_audit_link_budget.py | unchanged zky | 0bdc87ee8db2981e8f545ac9a5f5693e502a6a9b |
| quadriga/tests/test_channel_math.py | unchanged zky | 52c9c7508a0ff4c9dd43e3f9ad703e915def0a6b |
| quadriga/tests/test_handover_bundle.py | new integration content | 199f6f771fc957ef7dde11bcba96c727fb888085 |
| quadriga/tests/test_rfsim_history.py | compatible extension | af37e067dc6203aaeaee1535243c2a281028ca09 |
| quadriga/tests/test_validate_bundle.py | unchanged zky | 89811d1dda72729f707f01651af15de5622c2b24 |
| quadriga/tools/__init__.py | unchanged zky | 54f0ea315b3ad03f6cc4ca592f7cb013a6f3f013 |
| quadriga/tools/audit_link_budget.py | unchanged zky | a70895e72ba26fca81bc348cc2db8df6d577a819 |
| quadriga/tools/channel_math.py | unchanged zky | 1ce04f40250ce9046a60882b7c366852bca440e1 |
| quadriga/tools/create_example_bundle.py | unchanged zky | 96e4e04857b0166d087ba815295d8349f1b7a7f0 |
| quadriga/tools/validate_bundle.py | unchanged zky | 29e365e824b3452f31d2a9ee9bf7d6ebc4ce169a |
| receive_all_oai.py | unchanged zky | 66e5caddff11b6a231422bc542453eada994b6f2 |
| receive_oai_logs.py | unchanged zky | ad484fd115978081550804c13d4844f95ef6fc94 |
| receive_ping_iperf_logs.py | unchanged zky | 7f4543979d2a626a0c86bbc8c208091184f544a6 |
| run_bridge_forward.py | unchanged zky | 5720307420941e35f31a3208c1b52d86b3d8f07b |
| run_ping_iperf_forward.py | unchanged zky | 4a1233705c24d8b1cf817b0c602af5b180a1cfbc |
| scripts/audit_trace_continuity.py | unchanged zky | 45dc5178ea8671ef03674f47315de977ee08aa71 |
| scripts/build.sh | unchanged zky | f0996a660ddc6e8ee4e5bfba5fd7d35badb668e4 |
| scripts/check_delivery.py | unchanged zky | 3f1f83ae56e494cffc6ff43f59cd9c295523e391 |
| scripts/continuous_ping.py | new integration content | 857cdcd246a1cfee562dea5f9698c5d4fc1ce27b |
| scripts/continuous_udp.py | new integration content | 237b1931037b5d270284ae143afc76c742724beb |
| scripts/core.sh | unchanged zky | 6b3c17ecc5e7ac912b6639d49eabe85e56a28bc3 |
| scripts/core_lab.py | new integration content | fe469a2435953ac346c7841e089d700c473c797f |
| scripts/env.sh | compatible extension | d4ca1e50789edd7387248d70194425ee967775a3 |
| scripts/full_pass.py | compatible extension | 621d01db3612b9fd80202be3e3ee6c90317b601f |
| scripts/handover_acceptance.py | new integration content | 6766ac61c4226e9134e0ab0fc7a761d0f7a92e39 |
| scripts/handover_metrics.py | new integration content | 9b454abfaa020e26918eda0415fff72e0b84ba98 |
| scripts/handover_plot.py | new integration content | 25462cc18df2fde798f30eaf071e683a122bf033 |
| scripts/init_lab.py | compatible extension | d9fe6eb302e9ed639a87e7db6616bdec21b4b23e |
| scripts/install_deps.sh | unchanged zky | 1594d56707ce2cab07163d78ce552d9ba91cd1a8 |
| scripts/monotonic_ping.py | unchanged zky | 494b905e816c9febdee46a0dcad22d61a1174b56 |
| scripts/original_platform_check.py | new integration content | 5aab1fcae4e0cc1fa3fecdd2cc8b65f02d8fc452 |
| scripts/prepare_iperf.sh | unchanged zky | e3d4ecdb56dcaf7e0eb50cfc8ad566b7aebb5228 |
| scripts/prepare_sources.py | unchanged zky | e24607a56d12c32400c3b5f212e7c8cd8b2f13d5 |
| scripts/smoke.py | unchanged zky | 25cc211f25ba11dea11e3787c2f3d9597660fae5 |
| scripts/test.sh | compatible extension | 303b030e9b2016aa686c53ecd91ee3eb625591de |
| scripts/test_core_lab.py | new integration content | 636746e4f6d04461dea549d21b73b39ca2fee79d |
| scripts/test_diag_window.py | new integration content | c3625a469d3984510d45490f26532a1cbcb48240 |
| scripts/test_full_pass.py | compatible extension | 9b4d65196e4192191db94f87fb80e043b76ff68c |
| scripts/test_handover_driver.py | new integration content | 3622ece4315e15221b00b095f297d721d5def3e1 |
| scripts/test_handover_metrics.py | new integration content | 2ca179aea7891dcf3cb84246b7583f1d7b77ae4b |
| scripts/test_monotonic_ping.py | unchanged zky | 2c7896a54aae02e1cdeb7c3b5c0ca8bf7b418c05 |
| scripts/test_ntn_dtx_config.py | new integration content | 366189a2a284510f9b0bef2424376c4de37dd05f |
| scripts/test_original_platform_check.py | new integration content | eb55cd36e4cd7f8bc4a9783c5f392c8bbeaa466a |
| scripts/test_physical_start.py | new integration content | e1ea74a1f7f008d66aed3a8e3ec580d8c37f8bfc |
| scripts/test_prach_centered_iq.py | new integration content | f25b42c8c681b6bdd24b3aa7aaea77f7c056298b |
| scripts/test_rx_tracker_iq.py | new integration content | 2bacdc93d902e005633cef7f30f76a4131e44142 |
| scripts/test_tx_predictor_contract.py | new integration content | 0476d9383ce999a1fd1e980ba8fb77616b30a594 |
| scripts/test_tx_predictor_math.c | new integration content | 476c8c95cdc3ad5b94a03486131ac5daadc89f8e |
| sources.lock | compatible extension | ad8eaf29098c91d6468325a7d65fe649fd49ed88 |
| stk_api_metrics.py | unchanged zky | ee6e85816cb1cd68ee4b375958e68f25d60f8ba4 |
| stk_build_oai_ntn_scene.py | unchanged zky | 78d4fef314f4e91ef058a25d4c1a495e2127d48d |
| stk_dump_comm_models.py | unchanged zky | 7db2260ae24b60baff1bda4359b67c584b752bef |
| stk_inspect_comm.py | unchanged zky | 928fdbb616499c92d2f4ca8cc1620a9aa1d27793 |
| stk_link_metrics.py | unchanged zky | b473ee7101cfdec3830db5f63a306db31a9932d6 |
| stk_oai_bridge_generic.py | unchanged zky | b1dd7e0a7bfbbe1400031d3d299b35df15ac9383 |
| stk_oai_bridge_generic_detailed.py | unchanged zky | ca45f239d7967906bdd07c9a856d55738cf5b011 |
| stk_set_visible_time.py | unchanged zky | 648f0c0e88e5524843e2ac6eb396b9cc49b120d3 |
| stk_show_state.py | unchanged zky | af914f1b0e2f0f3368e62ded34bda47b89a9d8e3 |
| stop_oai_stk_tools.py | unchanged zky | 6c0fe27d20d2d58fcb18f3de2b2a107ba14884a7 |
| vendor/OAI-LICENSE | unchanged zky | 8c3081fcf0612dc6e66bc4c4dfe2e4618a53ec55 |
| vendor/QuaDRiGa-LICENSE.txt | unchanged zky | 6cca113f2ba24a22e09c5bf36dfa5e4e73552916 |
| vendor/README.md | unchanged zky | 9da4f2bc5eba23a4d1cfefb5e602518dba0eb55f |
| vendor/asn1c-source.tar.gz | unchanged zky | ee4a6332d2f1149d24986478e35cae82753cf255 |
| vendor/checksums.json | unchanged zky | 26e7c288854b280ace5815a7d2132628db02a081 |
| vendor/oai-source.tar.gz | unchanged zky | 5d9b5293197d7f9af11fcad0e9db93bf95774df9 |
| vendor/quadriga-source.tar.gz | unchanged zky | 5d1e486a9e0be4a6d556848f35b6c366e89a5ae4 |
| vendor/simde-source.tar.gz | unchanged zky | 9b869928278edddbabf2c9617a348b7d1cb31129 |
| vendor/source-manifest.json | unchanged zky | 5489db477243453d8b08b83e8b46f79febaf58ac |
