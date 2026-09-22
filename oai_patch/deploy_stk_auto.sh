#!/usr/bin/env bash
set -euo pipefail

root=/home/kayoko/OAI/openairinterface5g
stage='/mnt/d/实验室学习工作/杂活/雄安/OAI调研/oai_patch'

files=(
  radio/COMMON/common_lib.h
  radio/rfsimulator/rfsimulator.h
  radio/rfsimulator/stk_channel_model.c
  radio/rfsimulator/simulator.cpp
  executables/nr-ue-ru.h
  executables/nr-ue-ru.c
  executables/nr-ue.c
)

for relative in "${files[@]}"; do
  cp "$root/$relative" "$root/$relative.before_stk_auto"
done

cp "$stage/common_lib.h" "$root/radio/COMMON/common_lib.h"
cp "$stage/rfsimulator.h" "$root/radio/rfsimulator/rfsimulator.h"
cp "$stage/stk_channel_model.c" "$root/radio/rfsimulator/stk_channel_model.c"
cp "$stage/simulator.cpp" "$root/radio/rfsimulator/simulator.cpp"
cp "$stage/nr-ue-ru.h" "$root/executables/nr-ue-ru.h"
cp "$stage/nr-ue-ru.c" "$root/executables/nr-ue-ru.c"
cp "$stage/nr-ue.c" "$root/executables/nr-ue.c"

printf 'Deployed %d files with .before_stk_auto backups\n' "${#files[@]}"
