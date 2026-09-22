/*
 * SPDX-License-Identifier: LicenseRef-CSSL-1.0
 */

#ifndef __RFSIMULATOR_H
#define __RFSIMULATOR_H

#include <stdbool.h>
#include "radio/COMMON/common_lib.h"

void rxAddInput(c16_t **input_sig, cf_t *after_channel_sig, int rxAnt, channel_desc_t *channelDesc, int nbSamples);
void update_channel_model(channel_desc_t *channelDesc, int nbSamples, uint64_t TS);

/*
 * Returns true when the external STK model owns this update. Returns false
 * when OAI_STK_PORT is unset, allowing the built-in RFsim model to run.
 */
bool update_channel_model_from_stk(channel_desc_t *channelDesc, int nbSamples, uint64_t TS);
bool update_channel_model_from_stk_trace(channel_desc_t *channelDesc, int nbSamples, uint64_t TS);
bool get_stk_trace_sync(double frequency, openair0_ntn_sync_state_t *state, openair0_ntn_sync_status_t *status);
void stk_trace_iq_parameters(channel_desc_t *channel, c16_t **input, int samples, double *gain, double *sigma);

/* Return fresh STK-derived assistance for UE synchronization. */
openair0_ntn_sync_status_t get_stk_ue_sync_state(double downlink_frequency_hz,
                                                  openair0_ntn_sync_state_t *sync_state);

#endif
