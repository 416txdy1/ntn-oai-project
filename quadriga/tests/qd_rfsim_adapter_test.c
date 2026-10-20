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
static double test_trace_rate = 1;
bool stk_trace_time_at_timestamp(uint64_t timestamp, double sampling_rate, double *trace_time_s)
{
  *trace_time_s = test_trace_time_s + test_trace_rate * (double)timestamp / sampling_rate;
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
  const int count = 12;
  const long first = (long)current - whole + 5;
  double result = 0;
  for (int j = 0; j < count; j++) {
    const double node = j - 5;
    double weight = 1;
    for (int k = 0; k < count; k++) {
      const double other = k - 5;
      if (j != k) weight *= (fraction - other) / (node - other);
    }
    const c16_t value = input[first - j];
    result += weight * (imag ? value.i : value.r);
  }
  return result;
}

int main(int argc, char **argv)
{
  assert(argc >= 3 && argc <= 5);
  const size_t requested_checks = argc >= 4 ? strtoull(argv[3], NULL, 10) : 0;
  const double sampling_rate = argc == 5 ? strtod(argv[4], NULL) : 30720000.0;
  assert(isfinite(sampling_rate) && sampling_rate > 0);
  assert(requested_checks == 0 || requested_checks >= 2);
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
      .channel_length = 1, .sampling_rate = sampling_rate,
      .center_freq = (uint64_t)reference.center_frequency_hz,
      .Doppler_phase_cur = phase, .is_uplink = uplink,
  };
  test_trace_time_s = reference.times_s[0];
  update_channel_model_from_quadriga(&channel, 0);
  const size_t history = qd_channel_history_length(&channel);
  assert(history == (size_t)ceil(maximum_delay(&reference) * channel.sampling_rate) + 7);
  const size_t lookahead = qd_channel_lookahead_length(&channel);
  assert(lookahead == 5);
  /* 非整批长度覆盖并行分段末端与标量余数。 */
  enum { samples = 67 };
  c16_t *input[reference.tx_antennas];
  uint32_t seed = 20261015;
  for (size_t tx = 0; tx < reference.tx_antennas; tx++) {
    input[tx] = calloc(history + samples - 1 + lookahead, sizeof(c16_t));
    assert(input[tx]);
    for (size_t n = 0; n < history + samples - 1 + lookahead; n++) {
      seed = seed * 1664525u + 1013904223u;
      input[tx][n].r = (int)(seed % 20001) - 10000;
      seed = seed * 1664525u + 1013904223u;
      input[tx][n].i = (int)(seed % 20001) - 10000;
    }
  }
  struct complexd output[samples], expected[samples], batch[samples*reference.rx_antennas];
  qd_complex32_t *coefficients = calloc(reference.paths, sizeof(*coefficients));
  double *delays = calloc(reference.paths, sizeof(*delays));
  assert(coefficients && delays);
  double max_error = 0;
  const size_t available_checks = 2 * reference.snapshots - 1;
  const size_t selected_checks = requested_checks && requested_checks < available_checks ? requested_checks : available_checks;
  const double rates[] = {0, 0.5, 1, 1000000};
  for (size_t rate_index = 0; rate_index < sizeof(rates)/sizeof(rates[0]); rate_index++) {
    test_trace_rate = rates[rate_index];
  for (size_t check = 0; check < selected_checks; check++) {
    const size_t point = check * (available_checks - 1) / (selected_checks - 1);
    size_t lower = point / 2;
    test_trace_time_s = reference.times_s[lower];
    if (point % 2) test_trace_time_s = (test_trace_time_s + reference.times_s[lower + 1]) / 2;
    update_channel_model_from_quadriga(&channel, 0);
    for (size_t rx = 0; rx < reference.rx_antennas; rx++) {
      assert(qd_channel_convolve_all(&channel,input,samples,batch));
      assert(qd_channel_convolve(&channel, input, rx, samples, output));
      memset(expected, 0, sizeof(expected));
      for (size_t tx = 0; tx < reference.tx_antennas; tx++) {
        float gain;
        for (int n = 0; n < samples; n++) {
          const qd_channel_status_t status = qd_channel_sample(&reference,
              test_trace_time_s + test_trace_rate * (double)n / channel.sampling_rate, rx, tx, coefficients, delays,
              &gain, error, sizeof(error));
          assert(status != QD_CHANNEL_ERROR);
          if (status == QD_CHANNEL_MUTED) continue;
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
        max_error=fmax(max_error,hypot(batch[rx*samples+n].r-expected[n].r,batch[rx*samples+n].i-expected[n].i));
        assert(fabs(batch[rx*samples+n].r-expected[n].r)<1e-7*(1+fabs(expected[n].r)));
        assert(fabs(batch[rx*samples+n].i-expected[n].i)<1e-7*(1+fabs(expected[n].i)));
        assert(fabs(output[n].r - expected[n].r) < 1e-7 * (1 + fabs(expected[n].r)));
        assert(fabs(output[n].i - expected[n].i) < 1e-7 * (1 + fabs(expected[n].i)));
      }
      if (check == 0 || check == selected_checks - 1) {
        const int lengths[] = {0, 1, 3, 7, 8, 9, 15, 16, 17, 63, 64, 65};
        for (size_t length = 0; length < sizeof(lengths)/sizeof(lengths[0]); length++) {
          for (int n = 0; n < samples; n++) output[n] = (struct complexd){123, 456};
          assert(qd_channel_convolve(&channel, input, rx, lengths[length], output));
          for(size_t k=0;k<samples*reference.rx_antennas;k++) batch[k]=(struct complexd){123,456};
          assert(qd_channel_convolve_all(&channel,input,lengths[length],batch));
          for(size_t k=lengths[length]*reference.rx_antennas;k<samples*reference.rx_antennas;k++)
            assert(batch[k].r==123 && batch[k].i==456);
          for(int k=0;k<lengths[length];k++) {
            assert(fabs(batch[rx*lengths[length]+k].r-expected[k].r)<1e-7*(1+fabs(expected[k].r)));
            assert(fabs(batch[rx*lengths[length]+k].i-expected[k].i)<1e-7*(1+fabs(expected[k].i)));
          }
          for (int n = 0; n < samples; n++) {
            if (n >= lengths[length]) {
              assert(output[n].r == 123 && output[n].i == 456);
            } else {
              assert(fabs(output[n].r-expected[n].r) < 1e-7*(1+fabs(expected[n].r)));
              assert(fabs(output[n].i-expected[n].i) < 1e-7*(1+fabs(expected[n].i)));
            }
          }
        }
      }
    }
  }
  }
  test_trace_rate = 1;
  for (int side = 0; side < 2; side++) {
    test_trace_time_s = side ? reference.times_s[reference.snapshots - 1] + 1 : reference.times_s[0] - 1;
    update_channel_model_from_quadriga(&channel, 0);
    for (size_t rx = 0; rx < reference.rx_antennas; rx++) {
      assert(qd_channel_convolve_all(&channel,input,samples,batch));
      assert(qd_channel_convolve(&channel, input, rx, samples, output));
      for (int n = 0; n < samples; n++) assert(output[n].r == 0 && output[n].i == 0);
    }
  }
  printf("PASS QD %zu Tx x %zu Rx: %zu/%zu snapshot/midpoint checks, max error %.9g, history %zu, muted boundaries\n",
         reference.tx_antennas, reference.rx_antennas, selected_checks, available_checks, max_error, history);
  free(coefficients);
  free(delays);
  for (size_t tx = 0; tx < reference.tx_antennas; tx++) free(input[tx]);
  qd_channel_free(&reference);
  return 0;
}
