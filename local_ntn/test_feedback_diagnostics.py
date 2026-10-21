"""验证可选诊断关闭时不计数，开启时并发事件不丢失。"""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = r'''
#include <assert.h>
#include <pthread.h>
#include "common/utils/ntn_feedback_diagnostics.h"
static ntn_feedback_diagnostics_t state;
static atomic_int reports;
static void *worker(void *unused) {
  (void)unused;
  uint64_t counts[3];
  for (unsigned i = 0; i < 768; ++i)
    if (ntn_feedback_diagnostics(&state, i % 3, counts))
      atomic_fetch_add(&reports, 1);
  assert(!ntn_feedback_diagnostics(&state, 3, counts));
  return NULL;
}
int main(int argc, char **argv) {
  (void)argc;
  pthread_t threads[4];
  for (int i = 0; i < 4; ++i) assert(pthread_create(&threads[i], NULL, worker, NULL) == 0);
  for (int i = 0; i < 4; ++i) assert(pthread_join(threads[i], NULL) == 0);
  int enabled = atoi(argv[1]);
  assert(atomic_load(&reports) == (enabled ? 12 : 0));
  assert(atomic_load(&state.events) == (enabled ? 3072 : 0));
  for (int i = 0; i < 3; ++i) assert(atomic_load(&state.outcomes[i]) == (enabled ? 1024 : 0));
  return 0;
}
'''


def main() -> None:
    with tempfile.TemporaryDirectory(prefix='ntn-feedback-') as directory:
        source = Path(directory)/'test.c'
        binary = Path(directory)/'test'
        source.write_text(SOURCE)
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-pthread',
                        '-I'+str(ROOT/'oai_patch/current'), str(source), '-o', str(binary)], check=True)
        for value in (None, '0', 'invalid', '1'):
            env = os.environ.copy()
            env.pop('OAI_NTN_FEEDBACK_DIAGNOSTICS', None)
            if value is not None:
                env['OAI_NTN_FEEDBACK_DIAGNOSTICS'] = value
            subprocess.run([str(binary), '1' if value == '1' else '0'], env=env, check=True, timeout=10)
    print('PASS feedback diagnostics: disabled, invalid setting, four-thread counters and cadence')


if __name__ == '__main__':
    main()
