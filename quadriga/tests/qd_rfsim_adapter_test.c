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

  float phase = 0.0f;
  channel_desc_t channel = {
      .nb_tx = 1,
      .nb_rx = 1,
      .channel_length = 1,
      .sampling_rate = 30720000.0,
      .center_freq = (uint64_t)reference.center_frequency_hz,
      .Doppler_phase_cur = &phase,
      .is_uplink = uplink,
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

  /* 确定性宽带输入可以暴露常量输入无法发现的时延索引、符号错误。 */
  uint32_t random_state = 20260928;
  for (size_t index = 0; index < history + samples - 1; index++) {
    random_state = random_state * 1664525u + 1013904223u;
    input_storage[index].r = (int)(random_state % 20001) - 10000;
    random_state = random_state * 1664525u + 1013904223u;
    input_storage[index].i = (int)(random_state % 20001) - 10000;
  }
  double max_error = 0;
  for (size_t point = 0; point < 2 * reference.snapshots - 1; point++) {
    const size_t lower = point / 2;
    test_trace_time_s = reference.times_s[lower];
    if (point % 2) test_trace_time_s = (test_trace_time_s + reference.times_s[lower + 1]) / 2;
    update_channel_model_from_quadriga(&channel, 0);
    assert(qd_channel_convolve(&channel, input, 0, samples, output));
    assert(qd_channel_sample(&reference, test_trace_time_s, 0, 0, coefficients, delays,
                             &residual_gain_db, error, sizeof(error)) == QD_CHANNEL_OK);
    for (int sample = 0; sample < samples; sample++) {
      double expected_r = 0, expected_i = 0;
      for (size_t path = 0; path < reference.paths; path++) {
        const double delay = delays[path] * channel.sampling_rate;
        const double r = reference_input(input_storage, history - 1 + sample, delay, false);
        const double i = reference_input(input_storage, history - 1 + sample, delay, true);
        expected_r += r * coefficients[path].real - i * coefficients[path].imag;
        expected_i += i * coefficients[path].real + r * coefficients[path].imag;
      }
      expected_r *= pow(10.0, residual_gain_db / 20.0);
      expected_i *= pow(10.0, residual_gain_db / 20.0);
      max_error = fmax(max_error, hypot(output[sample].r - expected_r, output[sample].i - expected_i));
      assert(fabs(output[sample].r - expected_r) < 1e-7 * (1 + fabs(expected_r)));
      assert(fabs(output[sample].i - expected_i) < 1e-7 * (1 + fabs(expected_i)));
    }
  }
  printf("PASS %s varying IQ: %zu snapshot/midpoint checks, max error %.9g\n",
         reference.link_direction, 2 * reference.snapshots - 1, max_error);
  test_trace_time_s = reference.times_s[reference.snapshots - 1] + 1;
  update_channel_model_from_quadriga(&channel, 0);
  assert(qd_channel_convolve(&channel, input, 0, samples, output));
  for (int sample = 0; sample < samples; sample++)
    assert(output[sample].r == 0.0 && output[sample].i == 0.0);

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
