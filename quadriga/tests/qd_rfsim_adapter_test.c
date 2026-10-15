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

/* 用通用 Lagrange 基函数独立验算分数采样，不复用适配器权重公式。 */
static double reference_input(const c16_t *input, size_t current, double delay, bool imag)
{
  const long whole = (long)floor(delay);
  const double fraction = delay - whole;
  const int count = whole == 0 ? 2 : 4;
  const long first = whole == 0 ? (long)current : (long)current - whole + 1;
  double result = 0;
  for (int j = 0; j < count; j++) {
    const double node = whole == 0 ? j : j - 1;
    double weight = 1;
    for (int k = 0; k < count; k++) {
      const double other = whole == 0 ? k : k - 1;
      if (j != k) weight *= (fraction - other) / (node - other);
    }
    const c16_t value = input[first - j];
    result += weight * (imag ? value.i : value.r);
  }
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
  const bool uplink = strcmp(reference.link_direction, "uplink") == 0;

  float phase[reference.rx_antennas];
  memset(phase, 0, sizeof(phase));
  channel_desc_t channel = {
      .nb_tx = reference.tx_antennas, .nb_rx = reference.rx_antennas,
      .channel_length = 1, .sampling_rate = 30720000.0,
      .center_freq = (uint64_t)reference.center_frequency_hz,
      .Doppler_phase_cur = phase, .is_uplink = uplink,
  };
  test_trace_time_s = reference.times_s[0];
  update_channel_model_from_quadriga(&channel, 0);
  const size_t history = qd_channel_history_length(&channel);
  assert(history == (size_t)ceil(maximum_delay(&reference) * channel.sampling_rate) + 3);
  enum { samples = 32 };
  c16_t *input[reference.tx_antennas];
  uint32_t seed = 20261015;
  for (size_t tx = 0; tx < reference.tx_antennas; tx++) {
    input[tx] = calloc(history + samples - 1, sizeof(c16_t));
    assert(input[tx]);
    for (size_t n = 0; n < history + samples - 1; n++) {
      seed = seed * 1664525u + 1013904223u;
      input[tx][n].r = (int)(seed % 20001) - 10000;
      seed = seed * 1664525u + 1013904223u;
      input[tx][n].i = (int)(seed % 20001) - 10000;
    }
  }
  struct complexd output[samples], expected[samples];
  qd_complex32_t *coefficients = calloc(reference.paths, sizeof(*coefficients));
  double *delays = calloc(reference.paths, sizeof(*delays));
  assert(coefficients && delays);
  double max_error = 0;
  for (size_t point = 0; point < 2 * reference.snapshots - 1; point++) {
    size_t lower = point / 2;
    test_trace_time_s = reference.times_s[lower];
    if (point % 2) test_trace_time_s = (test_trace_time_s + reference.times_s[lower + 1]) / 2;
    update_channel_model_from_quadriga(&channel, 0);
    for (size_t rx = 0; rx < reference.rx_antennas; rx++) {
      assert(qd_channel_convolve(&channel, input, rx, samples, output));
      memset(expected, 0, sizeof(expected));
      for (size_t tx = 0; tx < reference.tx_antennas; tx++) {
        float gain;
        assert(qd_channel_sample(&reference, test_trace_time_s, rx, tx, coefficients, delays,
                                &gain, error, sizeof(error)) == QD_CHANNEL_OK);
        for (int n = 0; n < samples; n++) {
          for (size_t p = 0; p < reference.paths; p++) {
            double delay = delays[p] * channel.sampling_rate;
            double r = reference_input(input[tx], history - 1 + n, delay, false);
            double i = reference_input(input[tx], history - 1 + n, delay, true);
            expected[n].r += pow(10.0, gain / 20.0) * (r * coefficients[p].real - i * coefficients[p].imag);
            expected[n].i += pow(10.0, gain / 20.0) * (i * coefficients[p].real + r * coefficients[p].imag);
          }
        }
      }
      for (int n = 0; n < samples; n++) {
        max_error = fmax(max_error, hypot(output[n].r - expected[n].r, output[n].i - expected[n].i));
        assert(fabs(output[n].r - expected[n].r) < 1e-7 * (1 + fabs(expected[n].r)));
        assert(fabs(output[n].i - expected[n].i) < 1e-7 * (1 + fabs(expected[n].i)));
      }
    }
  }
  for (int side = 0; side < 2; side++) {
    test_trace_time_s = side ? reference.times_s[reference.snapshots - 1] + 1 : reference.times_s[0] - 1;
    update_channel_model_from_quadriga(&channel, 0);
    for (size_t rx = 0; rx < reference.rx_antennas; rx++) {
      assert(qd_channel_convolve(&channel, input, rx, samples, output));
      for (int n = 0; n < samples; n++) assert(output[n].r == 0 && output[n].i == 0);
    }
  }
  printf("PASS QD %zu Tx x %zu Rx: %zu snapshot/midpoint checks, max error %.9g, history %zu, muted boundaries\n",
         reference.tx_antennas, reference.rx_antennas, 2 * reference.snapshots - 1, max_error, history);
  free(coefficients);
  free(delays);
  for (size_t tx = 0; tx < reference.tx_antennas; tx++) free(input[tx]);
  qd_channel_free(&reference);
  return 0;
}
