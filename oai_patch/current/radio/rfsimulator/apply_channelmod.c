/*
 * SPDX-License-Identifier: LicenseRef-CSSL-1.0
 */

#include <complex.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <common/utils/LOG/log.h>
#include <openair1/SIMULATION/TOOLS/sim.h>
#include "openair2/LAYER2/NR_MAC_gNB/mac_config.h"
#include "rfsimulator.h"


/* ------------------------------------------------------------------ */
/* STK static channel file support (SAT_LEO_STK)                      */
/* ------------------------------------------------------------------ */
static void load_stk_channel_file(channel_desc_t *cd) {
  FILE *fp = fopen(cd->stk_channel_file, "r");
  if (fp == NULL) {
    LOG_E(HW, "STK channel file %s cannot be opened, fall back to built-in model\n", cd->stk_channel_file);
    cd->stk_loaded = 1;
    cd->stk_visible = 1;
    return;
  }
  char line[1024];
  int n = 0;
  int has_posvel = 0;
  int has_vis = 0;
  while (fgets(line, sizeof(line), fp)) {
    if (line[0] == 't' && line[1] == '_') {
      if (strstr(line, "visibility") != NULL)
        has_vis = 1;
      continue; /* header */
    }
    n++;
  }
  if (n == 0) {
    LOG_E(HW, "STK channel file %s is empty\n", cd->stk_channel_file);
    cd->stk_loaded = 1;
    cd->stk_visible = 1;
    fclose(fp);
    return;
  }
  cd->stk_time = malloc(n * sizeof(double));
  cd->stk_delay = malloc(n * sizeof(double));
  cd->stk_doppler = malloc(n * sizeof(double));
  cd->stk_posvel = malloc(n * 6 * sizeof(double));
  cd->stk_vis = malloc(n * sizeof(double));
  rewind(fp);
  int i = 0;
  while (fgets(line, sizeof(line), fp) && i < n) {
    if (line[0] == 't' && line[1] == '_') continue;
    char *tok = strtok(line, ", \t\r\n");
    if (tok == NULL) continue;
    cd->stk_time[i] = strtod(tok, NULL);
    tok = strtok(NULL, ", \t\r\n");
    if (tok == NULL) break;
    cd->stk_delay[i] = strtod(tok, NULL);
    tok = strtok(NULL, ", \t\r\n");
    if (tok == NULL) break;
    cd->stk_doppler[i] = strtod(tok, NULL);
    /* visibility: 4th column when present (legacy files default to visible) */
    cd->stk_vis[i] = has_vis ? 0.0 : 1.0;
    if (has_vis) {
      tok = strtok(NULL, ", \t\r\n");
      if (tok != NULL)
        cd->stk_vis[i] = strtod(tok, NULL);
    }
    for (int k = 0; k < 6; k++) {
      tok = strtok(NULL, ", \t\r\n");
      if (tok == NULL)
        break;
      cd->stk_posvel[i * 6 + k] = strtod(tok, NULL);
      has_posvel = 1;
    }
    i++;
  }
  fclose(fp);
  cd->stk_n = i;
  if (!has_posvel) {
    free(cd->stk_posvel);
    cd->stk_posvel = NULL;
  }
  cd->stk_loaded = 1;
  LOG_I(HW, "Loaded STK channel file %s: %d rows%s\n", cd->stk_channel_file, cd->stk_n,
        cd->stk_posvel ? " with position/velocity" : "");
}

static void interp_stk(channel_desc_t *cd, double t, double *delay_s, double *doppler_hz,
                       double *vis, double *pos, double *vel) {
  if (cd->stk_n == 1) {
    *delay_s = cd->stk_delay[0] / 1000.0;
    *doppler_hz = cd->stk_doppler[0];
    *vis = (cd->stk_vis[0] >= 0.5) ? 1.0 : 0.0;
    if (pos && cd->stk_posvel) {
      for (int k = 0; k < 3; k++) pos[k] = cd->stk_posvel[k];
      for (int k = 0; k < 3; k++) vel[k] = cd->stk_posvel[3 + k];
    }
    return;
  }
  double t0 = cd->stk_time[0];
  double t1 = cd->stk_time[cd->stk_n - 1];
  if (t <= t0) {
    *delay_s = cd->stk_delay[0] / 1000.0;
    *doppler_hz = cd->stk_doppler[0];
    *vis = (cd->stk_vis[0] >= 0.5) ? 1.0 : 0.0;
    if (pos && cd->stk_posvel) {
      for (int k = 0; k < 3; k++) pos[k] = cd->stk_posvel[k];
      for (int k = 0; k < 3; k++) vel[k] = cd->stk_posvel[3 + k];
    }
    return;
  }
  if (t >= t1) {
    int j = cd->stk_n - 1;
    *delay_s = cd->stk_delay[j] / 1000.0;
    *doppler_hz = cd->stk_doppler[j];
    *vis = (cd->stk_vis[j] >= 0.5) ? 1.0 : 0.0;
    if (pos && cd->stk_posvel) {
      for (int k = 0; k < 3; k++) pos[k] = cd->stk_posvel[j * 6 + k];
      for (int k = 0; k < 3; k++) vel[k] = cd->stk_posvel[j * 6 + 3 + k];
    }
    return;
  }
  int lo = 0, hi = cd->stk_n - 1;
  while (hi - lo > 1) {
    int mid = (lo + hi) / 2;
    if (cd->stk_time[mid] <= t) lo = mid; else hi = mid;
  }
  const double dt = cd->stk_time[hi] - cd->stk_time[lo];
  const double w = (dt > 0.0) ? (t - cd->stk_time[lo]) / dt : 0.0;
  *delay_s = (cd->stk_delay[lo] * (1.0 - w) + cd->stk_delay[hi] * w) / 1000.0;
  *doppler_hz = cd->stk_doppler[lo] * (1.0 - w) + cd->stk_doppler[hi] * w;
  *vis = ((cd->stk_vis[lo] * (1.0 - w) + cd->stk_vis[hi] * w) >= 0.5) ? 1.0 : 0.0;
  if (pos && cd->stk_posvel) {
    for (int k = 0; k < 3; k++)
      pos[k] = cd->stk_posvel[lo * 6 + k] * (1.0 - w) + cd->stk_posvel[hi * 6 + k] * w;
    for (int k = 0; k < 3; k++)
      vel[k] = cd->stk_posvel[lo * 6 + 3 + k] * (1.0 - w) + cd->stk_posvel[hi * 6 + 3 + k] * w;
  }
}

static void update_channel_model_stk(channel_desc_t *channelDesc, int nbSamples, uint64_t TS) {
  (void) SPEED_OF_LIGHT;
  const double t = ((double)(TS - channelDesc->start_TS)) / (double)channelDesc->sampling_rate;
  double delay_s = 0.0, doppler_hz = 0.0, vis = 1.0;
  double pos[3] = {0.0}, vel[3] = {0.0};
  interp_stk(channelDesc, t, &delay_s, &doppler_hz, &vis,
             channelDesc->is_uplink ? pos : NULL,
             channelDesc->is_uplink ? vel : NULL);
  channelDesc->stk_visible = (vis >= 0.5);
  if (!channelDesc->stk_visible) {
    channelDesc->channel_offset = 0;
    channelDesc->Doppler_phase_inc = 0;
    if (TS / (unsigned int)channelDesc->sampling_rate != (TS + nbSamples) / (unsigned int)channelDesc->sampling_rate)
      LOG_I(HW, "STK channel: time %f s, INVISIBLE (signal off)\n", t);
    return;
  }

  if (channelDesc->enable_dynamic_delay)
    channelDesc->channel_offset = (uint64_t) llround(delay_s * channelDesc->sampling_rate);
  if (channelDesc->enable_dynamic_Doppler)
    channelDesc->Doppler_phase_inc = (float)(2.0 * M_PI * doppler_hz / channelDesc->sampling_rate);

  if (TS / (unsigned int)channelDesc->sampling_rate != (TS + nbSamples) / (unsigned int)channelDesc->sampling_rate) {
    LOG_I(HW, "STK channel: time %f s, %s delay %f ms, Doppler shift %f kHz\n", t,
          channelDesc->is_uplink ? "Uplink" : "Downlink", delay_s * 1000.0, doppler_hz / 1000.0);
    if (channelDesc->is_uplink)
      LOG_I(HW, "STK satellite ECEF: Position=(%f, %f, %f) m, Velocity=(%f, %f, %f) m/s\n",
            pos[0], pos[1], pos[2], vel[0], vel[1], vel[2]);
  }

  if (channelDesc->is_uplink && channelDesc->stk_posvel != NULL) {
    const int samples_per_subframe = channelDesc->sampling_rate / 1000;
    const int abs_subframe = TS / samples_per_subframe;
    if (abs_subframe % 10 == 0) {
      double d_prev = 0.0, d_next = 0.0, dop = 0.0;
      double p_prev[3], v_prev[3], p_next[3], v_next[3];
      double vis_dummy = 1.0;
      interp_stk(channelDesc, t - 5.0, &d_prev, &dop, &vis_dummy, p_prev, v_prev);
      interp_stk(channelDesc, t + 5.0, &d_next, &dop, &vis_dummy, p_next, v_next);
      const double drift = (d_next - d_prev) / 10.0; /* s/s of round-trip delay */
      gnb_sat_position_update_t sat_position = {
          .sfn = (abs_subframe / 10 + 1) % 1024,
          .subframe = 0,
          .delay = delay_s / 4.072e-9,
          .drift = drift / 0.2e-9,
          .accel = 0.0,
          .position.X = pos[0] / 1.3,
          .position.Y = pos[1] / 1.3,
          .position.Z = pos[2] / 1.3,
          .velocity.X = vel[0] / 0.06,
          .velocity.Y = vel[1] / 0.06,
          .velocity.Z = vel[2] / 0.06,
      };
      nr_update_sib19(&sat_position);
    }
  }
}
void update_channel_model(channel_desc_t *channelDesc, int nbSamples, uint64_t TS)
{
  if (update_channel_model_from_stk_trace(channelDesc, nbSamples, TS)) {
    update_channel_model_from_quadriga(channelDesc, TS);
    return;
  }
  AssertFatal(!qd_channel_requested(), "OAI_QD_CHANNEL requires active OAI_STK_TRACE\n");
  if (update_channel_model_from_stk(channelDesc, nbSamples, TS))
    return;
  if (channelDesc->stk_channel_file != NULL && !channelDesc->stk_loaded)
    load_stk_channel_file(channelDesc);
  if (channelDesc->stk_n > 0) {
    update_channel_model_stk(channelDesc, nbSamples, TS);
    return;
  }
  if ((channelDesc->sat_height > 0)
      && (channelDesc->enable_dynamic_delay
          || channelDesc->enable_dynamic_Doppler)) { // model for transparent satellite on circular orbit
    /* assumptions:
       - The Earth is spherical, the ground station is static, and that the Earth does not rotate.
       - An access or link is possible from the satellite to the ground station at all times.
       - The ground station is located at the North Pole (positive Zaxis), and the satellite starts from the initial elevation angle
       0° in the second quadrant of the YZplane.
       - Satellite moves in the clockwise direction in its circular orbit.
    */
    const double radius_earth = 6377900; // m
    const double radius_sat = radius_earth + channelDesc->sat_height;
    const double GM_earth = 3.986e14; // m^3/s^2
    const double w_sat = sqrt(GM_earth / (radius_sat * radius_sat * radius_sat)); // rad/s

    // start_time and end_time are when the pos_sat_z == pos_gnb_z (elevation angle == 0 and 180 degree)
    const double start_phase = -acos(radius_earth / radius_sat); // SAT is just rising above the horizon
    const double end_phase = -start_phase; // SAT is just falling behind the horizon
    const double start_time = start_phase / w_sat; // in seconds
    const double end_time = end_phase / w_sat; // in seconds
    const uint64_t duration_samples = (end_time - start_time) * channelDesc->sampling_rate;
    const double t = start_time + ((TS - channelDesc->start_TS) % duration_samples) / channelDesc->sampling_rate;

    const double pos_sat_x = 0;
    const double pos_sat_y = radius_sat * sin(w_sat * t);
    const double pos_sat_z = radius_sat * cos(w_sat * t);

    const double vel_sat_x = 0;
    const double vel_sat_y = w_sat * radius_sat * cos(w_sat * t);
    const double vel_sat_z = -w_sat * radius_sat * sin(w_sat * t);

    const double pos_ue_x = 0;
    const double pos_ue_y = 0;
    const double pos_ue_z = radius_earth;

    const double c = (double) SPEED_OF_LIGHT;

    if (channelDesc->is_uplink) {
      const double dir_ue_sat_x = pos_sat_x - pos_ue_x;
      const double dir_ue_sat_y = pos_sat_y - pos_ue_y;
      const double dir_ue_sat_z = pos_sat_z - pos_ue_z;

      const double dist_ue_sat = sqrt(dir_ue_sat_x * dir_ue_sat_x + dir_ue_sat_y * dir_ue_sat_y + dir_ue_sat_z * dir_ue_sat_z);
      const double vel_ue_sat = (vel_sat_x * dir_ue_sat_x + vel_sat_y * dir_ue_sat_y + vel_sat_z * dir_ue_sat_z) / dist_ue_sat;

      double dist_sat_gnb = 0;
      double vel_sat_gnb = 0;
      double acc_sat_gnb = 0;
      if (channelDesc->modelid == SAT_LEO_TRANS) {
        const double t5 = t + 5;
        const double t10 = t + 10;

        const double pos_gnb_x = 0;
        const double pos_gnb_y = 0;
        const double pos_gnb_z = radius_earth;

        const double pos_sat_x5 = 0;
        const double pos_sat_y5 = radius_sat * sin(w_sat * t5);
        const double pos_sat_z5 = radius_sat * cos(w_sat * t5);

        const double pos_sat_x10 = 0;
        const double pos_sat_y10 = radius_sat * sin(w_sat * t10);
        const double pos_sat_z10 = radius_sat * cos(w_sat * t10);

        const double dir_sat_gnb_x = pos_gnb_x - pos_sat_x;
        const double dir_sat_gnb_y = pos_gnb_y - pos_sat_y;
        const double dir_sat_gnb_z = pos_gnb_z - pos_sat_z;

        const double dir_sat_gnb_x5 = pos_gnb_x - pos_sat_x5;
        const double dir_sat_gnb_y5 = pos_gnb_y - pos_sat_y5;
        const double dir_sat_gnb_z5 = pos_gnb_z - pos_sat_z5;

        const double dir_sat_gnb_x10 = pos_gnb_x - pos_sat_x10;
        const double dir_sat_gnb_y10 = pos_gnb_y - pos_sat_y10;
        const double dir_sat_gnb_z10 = pos_gnb_z - pos_sat_z10;

        dist_sat_gnb = sqrt(dir_sat_gnb_x * dir_sat_gnb_x + dir_sat_gnb_y * dir_sat_gnb_y + dir_sat_gnb_z * dir_sat_gnb_z);
        const double dist_sat_gnb5 = sqrt(dir_sat_gnb_x5 * dir_sat_gnb_x5 + dir_sat_gnb_y5 * dir_sat_gnb_y5 + dir_sat_gnb_z5 * dir_sat_gnb_z5);
        const double dist_sat_gnb10 = sqrt(dir_sat_gnb_x10 * dir_sat_gnb_x10 + dir_sat_gnb_y10 * dir_sat_gnb_y10 + dir_sat_gnb_z10 * dir_sat_gnb_z10);

        // calculate vel_sat_gnb and acc_sat_gnb, so the delay is correct for epoch_time, epoch_time + 5 seconds and epoch_time + 10 seconds
        //
        // dist_sat_gnb   = dist_sat_gnb +  0 * vel_sat_gnb +   0 * acc_sat_gnb;
        // dist_sat_gnb5  = dist_sat_gnb +  5 * vel_sat_gnb +  25 * acc_sat_gnb;
        // dist_sat_gnb10 = dist_sat_gnb + 10 * vel_sat_gnb + 100 * acc_sat_gnb;
        //
        // vel_sat_gnb = (dist_sat_gnb5 - dist_sat_gnb) / 5 - 5 * acc_sat_gnb;
        // acc_sat_gnb = (dist_sat_gnb10 - dist_sat_gnb) / 100 - vel_sat_gnb / 10;
        //
        // vel_sat_gnb = (dist_sat_gnb5 - dist_sat_gnb) / 5 - 5 * ((dist_sat_gnb10 - dist_sat_gnb) / 100 - vel_sat_gnb / 10);

        vel_sat_gnb = 2 * (dist_sat_gnb5 - dist_sat_gnb) / 5 - (dist_sat_gnb10 - dist_sat_gnb) / 10;
        acc_sat_gnb = (dist_sat_gnb10 - dist_sat_gnb) / 50 - (dist_sat_gnb5 - dist_sat_gnb) / 25;

        // in the moment when the satellite disappears behind the horizon acc_sat_gnb might become negative, what is invalid
        if (acc_sat_gnb < 0)
          acc_sat_gnb = 0;
      }

      const double prop_delay = (dist_ue_sat + dist_sat_gnb) / c;
      if (channelDesc->enable_dynamic_delay)
        channelDesc->channel_offset = prop_delay * channelDesc->sampling_rate;

      const double f_Doppler_shift_ue_sat = (-vel_ue_sat / c) * channelDesc->center_freq;
      if (channelDesc->enable_dynamic_Doppler)
        channelDesc->Doppler_phase_inc = 2 * M_PI * f_Doppler_shift_ue_sat / channelDesc->sampling_rate;

      if (TS / (unsigned int)channelDesc->sampling_rate != (TS + nbSamples) / (unsigned int)channelDesc->sampling_rate) {
        LOG_I(HW,
              "Satellite orbit: time %f s, Position = (%f, %f, %f), Velocity = (%f, %f, %f)\n",
              t,
              pos_sat_x,
              pos_sat_y,
              pos_sat_z,
              vel_sat_x,
              vel_sat_y,
              vel_sat_z);
        LOG_I(HW, "Uplink delay %f ms, Doppler shift UE->SAT %f kHz\n", prop_delay * 1000, f_Doppler_shift_ue_sat / 1000);
        LOG_I(HW, "Satellite velocity towards gNB: %f m/s, acceleration towards gNB: %f m/s²\n", -vel_sat_gnb, acc_sat_gnb);
      }

      const int samples_per_subframe = channelDesc->sampling_rate / 1000;
      const int abs_subframe = TS / samples_per_subframe;
      if (abs_subframe % 10 == 0) { // update SIB19 information for the next frame
        gnb_sat_position_update_t sat_position = {
            .sfn = (abs_subframe / 10 + 1) % 1024,
            .subframe = 0,
            .delay = 2 * dist_sat_gnb / (c * 4.072e-9),
            .drift = 2 * vel_sat_gnb / (c * 0.2e-9),
            .accel = 2 * acc_sat_gnb / (c * 0.2e-10),
            .position.X = pos_sat_x / 1.3,
            .position.Y = pos_sat_y / 1.3,
            .position.Z = pos_sat_z / 1.3,
            .velocity.X = vel_sat_x / 0.06,
            .velocity.Y = vel_sat_y / 0.06,
            .velocity.Z = vel_sat_z / 0.06,
        };
        // Here we update the SIB19 information directly in the gNB MAC layer.
        // Without rf-simulaor, in a real system or with an external channel emulator, the SIB19 updates would
        // be provided via an external interface (e.g. O-RAN E2 interface) to the MAC layer (in the O-DU).
        // We do it directly here, because we can, and an E2 Interface implementation (e.g using FlexRIC)
        // would pull too many dependencies into rf-simulator, just for updating SIB19.
        nr_update_sib19(&sat_position);
      }
    } else {
      const double dir_sat_ue_x = pos_ue_x - pos_sat_x;
      const double dir_sat_ue_y = pos_ue_y - pos_sat_y;
      const double dir_sat_ue_z = pos_ue_z - pos_sat_z;

      const double dist_sat_ue = sqrt(dir_sat_ue_x * dir_sat_ue_x + dir_sat_ue_y * dir_sat_ue_y + dir_sat_ue_z * dir_sat_ue_z);
      const double vel_sat_ue = (vel_sat_x * dir_sat_ue_x + vel_sat_y * dir_sat_ue_y + vel_sat_z * dir_sat_ue_z) / dist_sat_ue;

      double dist_gnb_sat = 0;
      if (channelDesc->modelid == SAT_LEO_TRANS) {
        const double pos_gnb_x = 0;
        const double pos_gnb_y = 0;
        const double pos_gnb_z = radius_earth;

        const double dir_gnb_sat_x = pos_sat_x - pos_gnb_x;
        const double dir_gnb_sat_y = pos_sat_y - pos_gnb_y;
        const double dir_gnb_sat_z = pos_sat_z - pos_gnb_z;

        dist_gnb_sat = sqrt(dir_gnb_sat_x * dir_gnb_sat_x + dir_gnb_sat_y * dir_gnb_sat_y + dir_gnb_sat_z * dir_gnb_sat_z);
      }

      const double prop_delay = (dist_gnb_sat + dist_sat_ue) / c;
      if (channelDesc->enable_dynamic_delay)
        channelDesc->channel_offset = prop_delay * channelDesc->sampling_rate;

      const double f_Doppler_shift_sat_ue = (vel_sat_ue / (c - vel_sat_ue)) * channelDesc->center_freq;
      if (channelDesc->enable_dynamic_Doppler)
        channelDesc->Doppler_phase_inc = 2 * M_PI * f_Doppler_shift_sat_ue / channelDesc->sampling_rate;

      if (TS / (unsigned int)channelDesc->sampling_rate != (TS + nbSamples) / (unsigned int)channelDesc->sampling_rate) {
        LOG_I(HW,
              "Satellite orbit: time %f s, Position = (%f, %f, %f), Velocity = (%f, %f, %f)\n",
              t,
              pos_sat_x,
              pos_sat_y,
              pos_sat_z,
              vel_sat_x,
              vel_sat_y,
              vel_sat_z);
        LOG_I(HW, "Downlink delay %f ms, Doppler shift SAT->UE %f kHz\n", prop_delay * 1000, f_Doppler_shift_sat_ue / 1000);
      }
    }
  }
}

/*
  Legacy study:
  The parameters are:
  gain&loss (decay, signal power, ...)
  either a fixed gain in dB, a target power in dBm or ACG (automatic control gain) to a target average
  => don't redo the AGC, as it was used in UE case, that must have a AGC inside the UE
  will be better to handle the "set_gain()" called by UE to apply it's gain (enable test of UE power loop)
  lin_amp = pow(10.0,.05*txpwr_dBm)/sqrt(nb_tx_antennas);
  a lot of operations in legacy, grouped in one simulation signal decay: txgain*decay*rxgain

  multi_path (auto convolution, ISI, ...)
  either we regenerate the channel (call again random_channel(desc,0)), or we keep it over subframes
  legacy: we regenerate each sub frame in UL, and each frame only in DL
*/
void rxAddInput(c16_t **input_sig, cf_t *after_channel_sig, int rxAnt, channel_desc_t *channelDesc, int nbSamples)
{
  // channelDesc->path_loss_dB should contain the total path gain
  // so, in actual RF: tx gain + path loss + rx gain (+antenna gain, ...)
  // UE and NB gain control to be added
  // Fixme: not sure when it is "volts" so dB is 20*log10(...) or "power", so dB is 10*log10(...)
  double pathLossLinear = (channelDesc->stk_n > 0 && !channelDesc->stk_visible) ? 0.0 : pow(10, channelDesc->path_loss_dB / 20.0);
  // Energy in one sample to calibrate input noise
  // the normalized OAI value seems to be 256 as average amplitude (numerical amplification = 1)
  double noise_per_sample = pow(10, channelDesc->noise_power_dB / 10.0) * 256;
  const size_t input_history = qd_channel_history_length(channelDesc);
  AssertFatal(input_history >= 1 && input_history <= INT_MAX, "Invalid RFsim input history length %zu\n", input_history);
  const int input_offset = (int)input_history - 1;
  stk_trace_iq_parameters(channelDesc, input_sig, input_offset, nbSamples, &pathLossLinear, &noise_per_sample);
  struct complexd *qd_output = NULL;
  bool qd_applied = false;
  if (qd_channel_requested()) {
    qd_output = calloc((size_t)nbSamples, sizeof(*qd_output));
    AssertFatal(qd_output != NULL, "Cannot allocate QDCHANNEL1 convolution output\n");
    qd_applied = qd_channel_convolve(channelDesc, input_sig, rxAnt, nbSamples, qd_output);
    AssertFatal(qd_applied, "QDCHANNEL1 was requested but not applied\n");
  }
  const int nbTx = channelDesc->nb_tx;
  double Doppler_phase_cur = channelDesc->Doppler_phase_cur[rxAnt];
  Doppler_phase_cur -= 2 * M_PI * round(Doppler_phase_cur / (2 * M_PI));

  for (int i = 0; i < nbSamples; i++) {
    cf_t *out_ptr = after_channel_sig + i;
    struct complexd rx_tmp = {0};

    if (qd_applied) {
      rx_tmp = qd_output[i];
    } else {
      for (int txAnt = 0; txAnt < nbTx; txAnt++) {
        const struct complexd *channelModel = channelDesc->ch[rxAnt + (txAnt * channelDesc->nb_rx)];

        // const struct complex *channelModelEnd=channelModel+channelDesc->channel_length;
        for (int l = 0; l < (int)channelDesc->channel_length; l++) {
          const int idx = i - l + channelDesc->channel_length - 1;
          const struct complex16 tx16 = input_sig[txAnt][idx];
          rx_tmp.r += tx16.r * channelModel[l].r - tx16.i * channelModel[l].i;
          rx_tmp.i += tx16.i * channelModel[l].r + tx16.r * channelModel[l].i;
        } // l
      }
    }

    if (channelDesc->Doppler_phase_inc != 0.0 || Doppler_phase_cur != 0.0) {
#ifdef CMPLX
      double complex in = CMPLX(rx_tmp.r, rx_tmp.i);
#else
      double complex in = rx_tmp.r + rx_tmp.i * I;
#endif
      double complex out = in * cexp(Doppler_phase_cur * I);
      rx_tmp.r = creal(out);
      rx_tmp.i = cimag(out);
      Doppler_phase_cur += channelDesc->Doppler_phase_inc;
    }

    out_ptr->r += rx_tmp.r * pathLossLinear + noise_per_sample * gaussZiggurat(0.0, 1.0);
    out_ptr->i += rx_tmp.i * pathLossLinear + noise_per_sample * gaussZiggurat(0.0, 1.0);
    out_ptr++;
  }

  free(qd_output);
  channelDesc->Doppler_phase_cur[rxAnt] = Doppler_phase_cur;

  // Cast to a wrong type for compatibility !
  LOG_D(HW,
        "Input power %f, output power: %f, channel path loss %f, noise coeff: %f \n",
        10 * log10((double)signal_energy((int32_t *)&input_sig[0], nbSamples)),
        10 * log10((double)signal_energy((int32_t *)after_channel_sig, nbSamples)),
        channelDesc->path_loss_dB,
        10 * log10(noise_per_sample));
}
