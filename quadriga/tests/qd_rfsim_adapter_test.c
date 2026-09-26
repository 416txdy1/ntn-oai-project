/* Regression for the actual QDCHANNEL1 RFsim sparse adapter. */
#include <assert.h>
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <common/utils/LOG/log.h>
#include <openair1/SIMULATION/TOOLS/sim.h>
#include "radio/rfsimulator/qd_channel_reader.h"
#include "radio/rfsimulator/rfsimulator.h"

static log_t log_state;
log_t *g_log = &log_state;
void logRecord_mt(const char *file, const char *function, int line, int component,
                  int level, const char *format, ...)
{
  (void)file;
  (void)function;
  (void)line;
  (void)component;
  (void)level;
  (void)format;
}
void exit_function(const char *file, const char *function, const int line,
                   const char *message, const int kind)
{
  (void)file;
  (void)function;
  (void)line;
  (void)message;
  (void)kind;
  abort();
}

static double test_trace_time_s;
bool stk_trace_time_at_timestamp(uint64_t timestamp, double sampling_rate, double *trace_time_s)
{
  (void)timestamp;
  (void)sampling_rate;
  *trace_time_s = test_trace_time_s;
  return true;
}

static double maximum_delay(const qd_channel_t *bundle)
{
  const size_t count = bundle->snapshots * bundle->rx_antennas * bundle->tx_antennas * bundle->paths;
  double result = 0.0;
  for (size_t index = 0; index < count; index++)
    result = fmax(result, bundle->delays_s[index]);
  return result;
}

int main(int argc, char **argv)
{
  assert(argc == 3);
  setenv("OAI_QD_CHANNEL", argv[1], 1);
  setenv("OAI_STK_TRACE", argv[2], 1);

  qd_channel_t reference = {0};
  char error[512] = {0};
  assert(qd_channel_load(argv[1], NULL, &reference, error, sizeof(error)));
  assert(strcmp(reference.link_direction, "downlink") == 0);

  float phase = 0.0f;
  channel_desc_t channel = {
      .nb_tx = 1,
      .nb_rx = 1,
      .channel_length = 1,
      .sampling_rate = 30720000.0,
      .center_freq = (uint64_t)reference.center_frequency_hz,
      .Doppler_phase_cur = &phase,
      .is_uplink = false,
  };
  test_trace_time_s = reference.times_s[0];
  update_channel_model_from_quadriga(&channel, 0);
  const size_t history = qd_channel_history_length(&channel);
  const size_t expected_history = (size_t)ceil(maximum_delay(&reference) * channel.sampling_rate) + 3;
  assert(history == expected_history);
  assert(history > 255);

  enum { samples = 32 };
  c16_t *input_storage = calloc(history + samples - 1, sizeof(*input_storage));
  struct complexd *output = calloc(samples, sizeof(*output));
  assert(input_storage != NULL && output != NULL);
  for (size_t index = 0; index < history + samples - 1; index++)
    input_storage[index] = (c16_t){.r = 1000, .i = -500};
  c16_t *input[] = {input_storage};
  assert(qd_channel_convolve(&channel, input, 0, samples, output));

  qd_complex32_t *coefficients = calloc(reference.paths, sizeof(*coefficients));
  double *delays = calloc(reference.paths, sizeof(*delays));
  float residual_gain_db = 0.0f;
  assert(coefficients != NULL && delays != NULL);
  assert(qd_channel_sample(&reference, test_trace_time_s, 0, 0, coefficients, delays,
                           &residual_gain_db, error, sizeof(error)) == QD_CHANNEL_OK);
  double sum_real = 0.0;
  double sum_imag = 0.0;
  for (size_t path = 0; path < reference.paths; path++) {
    sum_real += coefficients[path].real;
    sum_imag += coefficients[path].imag;
  }
  const double residual_amplitude = pow(10.0, residual_gain_db / 20.0);
  const double expected_real = residual_amplitude * (1000.0 * sum_real + 500.0 * sum_imag);
  const double expected_imag = residual_amplitude * (-500.0 * sum_real + 1000.0 * sum_imag);
  for (int sample = 0; sample < samples; sample++) {
    assert(fabs(output[sample].r - expected_real) < 1e-5 * (1.0 + fabs(expected_real)));
    assert(fabs(output[sample].i - expected_imag) < 1e-5 * (1.0 + fabs(expected_imag)));
  }

  test_trace_time_s = reference.times_s[0] - 1.0;
  update_channel_model_from_quadriga(&channel, 0);
  assert(qd_channel_convolve(&channel, input, 0, samples, output));
  for (int sample = 0; sample < samples; sample++)
    assert(output[sample].r == 0.0 && output[sample].i == 0.0);

  printf("PASS QD RFsim sparse adapter: history=%zu, paths=%zu, out-of-range muted\n",
         history, reference.paths);
  free(coefficients);
  free(delays);
  free(input_storage);
  free(output);
  qd_channel_free(&reference);
  return 0;
}
