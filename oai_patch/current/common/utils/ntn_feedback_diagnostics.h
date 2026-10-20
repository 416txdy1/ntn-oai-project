/* 可选去敏统计：只观察结果，不参与 HARQ 或功率控制决策。 */
#ifndef NTN_FEEDBACK_DIAGNOSTICS_H
#define NTN_FEEDBACK_DIAGNOSTICS_H
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
  atomic_int enabled;
  atomic_uint_fast64_t outcomes[3]; /* ACK、有效 NACK、低置信度/CRC失败 */
  atomic_uint_fast64_t events;
} ntn_feedback_diagnostics_t;

static inline bool ntn_feedback_diagnostics(ntn_feedback_diagnostics_t *state,
                                            unsigned outcome, uint64_t counts[3])
{
  int enabled = atomic_load_explicit(&state->enabled, memory_order_relaxed);
  if (!enabled) {
    const char *value = getenv("OAI_NTN_FEEDBACK_DIAGNOSTICS");
    enabled = value && strcmp(value, "1") == 0 ? 2 : 1;
    atomic_store_explicit(&state->enabled, enabled, memory_order_relaxed);
  }
  if (enabled != 2 || outcome >= 3)
    return false;
  atomic_fetch_add_explicit(&state->outcomes[outcome], 1, memory_order_relaxed);
  uint64_t total = atomic_fetch_add_explicit(&state->events, 1, memory_order_relaxed) + 1;
  if (total % 256)
    return false;
  // 多线程下是近同时累计快照；不得当作逐HARQ事务配对结果。
  for (unsigned i = 0; i < 3; ++i)
    counts[i] = atomic_load_explicit(&state->outcomes[i], memory_order_relaxed);
  return true;
}
#endif
