/* SPDX-License-Identifier: LicenseRef-CSSL-1.0 */
/* Slow residual MAC TA feedback for receiver-derived RFsim geometry tracking. */
#ifndef NR_NTN_TA_FEEDBACK_H
#define NR_NTN_TA_FEEDBACK_H
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#define NR_NTN_TA_FEEDBACK_POLICY "crc-good-quarter-gain-v1"
static inline bool nr_ntn_ta_isolated_profile(void)
{
  const char *profile=getenv("OAI_NTN_PROFILE");
  return profile && (!strcmp(profile,"integrated-handover") || !strcmp(profile,"legacy-handover"));
}
static inline bool nr_ntn_ta_feedback_enabled(void)
{
  const char *rx=getenv("OAI_NTN_RX_TRACKER"), *tx=getenv("OAI_NTN_TX_PREDICTOR");
  return nr_ntn_ta_isolated_profile() && (!rx || !strcmp(rx,"1")) && (!tx || !strcmp(tx,"1"));
}
static inline bool nr_ntn_ta_feedback_accept(bool crc_ok)
{
  return !nr_ntn_ta_feedback_enabled() || crc_ok;
}
static inline int nr_ntn_ta_feedback_value(int command)
{
  /* Preserve native invalid-value handling rather than masking an error. */
  if (!nr_ntn_ta_feedback_enabled() || command<0 || command>63) return command;
  const int delta=command-31;
  const int correction=delta<0?-((-delta+2)/4):(delta+2)/4;
  return 31+correction;
}
#endif
