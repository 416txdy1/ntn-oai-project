/* SPDX-License-Identifier: LicenseRef-CSSL-1.0 */
/* Bounded numerical observation only; does not change native MAC TA logic. */
#ifndef NR_NTN_TA_DIAG_H
#define NR_NTN_TA_DIAG_H
#include <stdbool.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include "ntn_ta_feedback.h"
static inline bool nr_ntn_ta_diag_enabled(void)
{
  const char *profile=getenv("OAI_NTN_PROFILE"), *flag=getenv("OAI_NTN_TIMING_DIAG");
  return profile && (!strcmp(profile,"integrated-handover") || !strcmp(profile,"legacy-handover"))
      && flag && !strcmp(flag,"1");
}
static inline void nr_ntn_ta_diag(bool scheduled,int frame,int slot,int command,
                                  int previous,int crc_ok,int snr_x10,int retained,int feedback_used)
{
  static atomic_uint measurements, schedules;
  if (!nr_ntn_ta_diag_enabled()) return;
  atomic_uint *counter=scheduled?&schedules:&measurements;
  const unsigned limit=scheduled?2000:20000;
  if (atomic_load_explicit(counter,memory_order_relaxed)>=limit) return;
  const unsigned sequence=atomic_fetch_add_explicit(counter,1,memory_order_relaxed)+1;
  if (sequence>limit) return;
  LOG_I(NR_MAC,"%s call %u frame %d slot %d command %d previous %d crcOk %d snrX10 %d retained %d feedbackUsed %d\n",
        scheduled?"STKGNB_TA_SCHEDULE":"STKGNB_TA_MEAS",sequence,frame,slot,
        command,previous,crc_ok,snr_x10,retained,feedback_used);
}
#endif
