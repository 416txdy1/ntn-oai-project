#include "qd_channel_reader.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition, message) \
  do { \
    if (!(condition)) { \
      fprintf(stderr, "FAIL: %s\n", message); \
      return 1; \
    } \
  } while (0)

static int nearly(double left, double right, double tolerance)
{
  return fabs(left - right) <= tolerance;
}

static int sample_smoke(const qd_channel_t *channel)
{
  qd_complex32_t *coefficients = calloc(channel->paths, sizeof(*coefficients));
  double *delays = calloc(channel->paths, sizeof(*delays));
  CHECK(coefficients != NULL && delays != NULL, "cannot allocate sample buffers");
  const double time = 0.5 * (channel->times_s[0] + channel->times_s[channel->snapshots - 1]);
  float gain = 0.0f;
  char error[512];
  const qd_channel_status_t status = qd_channel_sample(
      channel, time, 0, 0, coefficients, delays, &gain, error, sizeof(error));
  if (status != QD_CHANNEL_OK)
    fprintf(stderr, "sample error: %s\n", error);
  free(coefficients);
  free(delays);
  return status == QD_CHANNEL_OK ? 0 : 1;
}

static int test_example(const char *bundle, const char *trace_sha256)
{
  qd_channel_t channel = {0};
  char error[512];
  CHECK(qd_channel_load(bundle, trace_sha256, &channel, error, sizeof(error)), error);
  CHECK(channel.snapshots == 3, "example snapshot count");
  CHECK(channel.rx_antennas == 1 && channel.tx_antennas == 1, "example antenna dimensions");
  CHECK(channel.paths == 2, "example path count");
  CHECK(strcmp(channel.link_direction, "downlink") == 0, "example direction");
  CHECK(nearly(channel.center_frequency_hz, 2.0e9, 1.0), "example center frequency");

  qd_complex32_t coefficients[2];
  double delays[2];
  float gain = 0.0f;
  qd_channel_status_t status = qd_channel_sample(
      &channel, 0.0005, 0, 0, coefficients, delays, &gain, error, sizeof(error));
  CHECK(status == QD_CHANNEL_OK, error);
  CHECK(nearly(coefficients[0].real,
               0.5 * (channel.coefficients[0].real + channel.coefficients[2].real),
               1e-7),
        "midpoint first-path real coefficient");
  CHECK(nearly(coefficients[0].imag,
               0.5 * (channel.coefficients[0].imag + channel.coefficients[2].imag),
               1e-7),
        "midpoint first-path imaginary coefficient");
  CHECK(nearly(delays[1], 252.5e-9, 1e-15), "midpoint excess delay");
  CHECK(nearly(gain, -0.125, 1e-7), "midpoint residual gain");

  memset(coefficients, 0x7f, sizeof(coefficients));
  memset(delays, 0x7f, sizeof(delays));
  gain = 99.0f;
  status = qd_channel_sample(&channel, -1.0, 0, 0, coefficients, delays, &gain, error, sizeof(error));
  CHECK(status == QD_CHANNEL_MUTED, "before-range query must mute");
  CHECK(coefficients[0].real == 0.0f && coefficients[1].imag == 0.0f, "muted coefficients must be zero");
  CHECK(delays[0] == 0.0 && delays[1] == 0.0 && gain == 0.0f, "muted delay/gain must be zero");

  status = qd_channel_sample(
      &channel, channel.times_s[channel.snapshots - 1], 0, 0, coefficients, delays, &gain, error, sizeof(error));
  CHECK(status == QD_CHANNEL_OK, "last snapshot must be in range");
  CHECK(nearly(coefficients[0].real, channel.coefficients[4].real, 1e-7), "last snapshot coefficient");

  qd_channel_t wrong_provenance = {0};
  const char *wrong_hash = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
  CHECK(!qd_channel_load(bundle, wrong_hash, &wrong_provenance, error, sizeof(error)),
        "wrong STK provenance must fail");
  CHECK(strstr(error, "STK trace SHA256") != NULL, "wrong provenance error message");

  qd_channel_free(&channel);
  puts("PASS example: load, exact metadata, interpolation, mute, provenance rejection");
  return 0;
}

static int expect_failure(const char *bundle)
{
  qd_channel_t channel = {0};
  char error[512];
  if (qd_channel_load(bundle, NULL, &channel, error, sizeof(error))) {
    qd_channel_free(&channel);
    fprintf(stderr, "FAIL: malformed bundle unexpectedly loaded\n");
    return 1;
  }
  printf("PASS rejected malformed bundle: %s\n", error);
  return 0;
}

static int smoke_real(const char *bundle, const char *trace_sha256)
{
  qd_channel_t channel = {0};
  char error[512];
  CHECK(qd_channel_load(bundle, trace_sha256, &channel, error, sizeof(error)), error);
  CHECK(channel.snapshots >= 2 && channel.paths >= 1, "real bundle dimensions");
  CHECK(sample_smoke(&channel) == 0, "real bundle midpoint sample");
  printf("PASS real bundle: snapshots=%zu rx=%zu tx=%zu paths=%zu direction=%s\n",
         channel.snapshots,
         channel.rx_antennas,
         channel.tx_antennas,
         channel.paths,
         channel.link_direction);
  qd_channel_free(&channel);
  return 0;
}

int main(int argc, char **argv)
{
  if (argc == 3 && strcmp(argv[1], "--expect-fail") == 0)
    return expect_failure(argv[2]);
  if (argc == 4 && strcmp(argv[1], "--example") == 0)
    return test_example(argv[2], argv[3]);
  if (argc == 4 && strcmp(argv[1], "--smoke") == 0)
    return smoke_real(argv[2], argv[3]);
  fprintf(stderr, "usage: %s --example|--smoke BUNDLE TRACE_SHA256\n", argv[0]);
  fprintf(stderr, "       %s --expect-fail BUNDLE\n", argv[0]);
  return 2;
}
