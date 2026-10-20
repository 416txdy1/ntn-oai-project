#!/usr/bin/env bash
# Windows 入口的 WSL 实现；只同步源码，保留 Linux 构建缓存和私有配置。
set -euo pipefail
ACTION=${1:?action required}
SOURCE=$(realpath -- "${2:?source required}")
TARGET=$(realpath -- "${3:?runtime project required}")
MAX_WALL=${4:-1800}
[[ "$SOURCE" != "$TARGET" && "$TARGET" != / && "$TARGET" != /mnt/* ]] || { echo 'Invalid runtime project'; exit 2; }
[[ -f "$TARGET/scripts/env.sh" && -f "$TARGET/.private/settings.json" && -f "$TARGET/.runtime/oai/CMakeLists.txt" ]] || {
  echo 'Runtime project must already contain the configured lab and OAI sources'; exit 2;
}
# smoke.py 的 finally 会停止控制器记录的进程，因此启动前必须拒绝已有 modem。
if [[ "$ACTION" == smoke-* ]]; then
  for process in nr-softmodem nr-uesoftmodem; do
    if pgrep -x "$process" >/dev/null; then echo "Refusing smoke while $process runs"; exit 2; fi
  done
fi
case "$ACTION" in
 sync|build)
  for process in nr-softmodem nr-uesoftmodem; do
    if pgrep -x "$process" >/dev/null; then echo "Refusing source update while $process runs"; exit 2; fi
  done
  BACKUP="$TARGET/.runtime/source-backups/$(date +%Y%m%d-%H%M%S)-$$"
  mkdir -p "$BACKUP"
  # Git 仅用于列出主目录受管理的文件；不复制 .git、凭据、运行状态或旧日志。
  git -c safe.directory="$SOURCE" -C "$SOURCE" ls-files -z -- scripts local_ntn oai_patch/current quadriga examples configs vendor docs README.md AGENTS.md sources.lock .gitignore .gitattributes > "$BACKUP/files.list"
  rsync -rlt --checksum --backup --backup-dir="$BACKUP/files" --from0 --files-from="$BACKUP/files.list" "$SOURCE/" "$TARGET/"
  echo "Source synchronized; changed runtime source files backed up in $BACKUP"
  ;;
esac
cd "$TARGET"
source scripts/env.sh
# 每次从明确的已记录基线开始；不继承终端中的实验修正开关。
export OAI_STK_TRACE_INTERPOLATION=hermite
export OAI_STK_BLEND_TIMING_ASSIST=0
case "$ACTION" in
 sync) ;;
 build) JOBS=4 bash scripts/build.sh ;;
 test) bash scripts/test.sh ;;
 up) bash scripts/core.sh up; bash scripts/prepare_iperf.sh ;;
 preflight) python3 local_ntn/experiment.py preflight --rate 1 ;;
 smoke-static) python3 scripts/smoke.py --rate 0 ;;
 smoke-dynamic) python3 scripts/smoke.py --rate 1 ;;
 full-pass) python3 scripts/full_pass.py --max-wall-seconds "$MAX_WALL" ;;
 status) bash scripts/core.sh status; ps -eo pid,comm | awk '$2=="nr-softmodem" || $2=="nr-uesoftmodem"' ;;
 stop) python3 local_ntn/experiment.py stop; bash scripts/core.sh stop ;;
 *) echo 'Unknown action'; exit 2 ;;
esac