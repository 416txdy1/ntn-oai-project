/*
 * QDCHANNEL1 offline bundle reader for OAI RFsim.
 *
 * Loading and interpolation stay separate from the RFsim sparse-convolution
 * adapter so the binary contract remains independently testable.
 */
#ifndef QD_CHANNEL_READER_H
#define QD_CHANNEL_READER_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
  float real;
  float imag;
} qd_complex32_t;

typedef enum {
  QD_CHANNEL_ERROR = -1,
  QD_CHANNEL_MUTED = 0,
  QD_CHANNEL_OK = 1,
} qd_channel_status_t;

typedef struct {
  size_t snapshots;
  size_t rx_antennas;
  size_t tx_antennas;
  size_t paths;
  double center_frequency_hz;
  char link_direction[9];
  char stk_trace_sha256[65];
  double *times_s;
  double *delays_s;
  qd_complex32_t *coefficients;
  float *residual_gain_db;
} qd_channel_t;

/*
 * Load and validate one QDCHANNEL1 bundle.
 *
 * expected_stk_trace_sha256 may be NULL. When provided, it must be a lowercase
 * 64-character SHA256 and must match the manifest provenance.
 */
int qd_channel_load(const char *bundle_dir,
                    const char *expected_stk_trace_sha256,
                    qd_channel_t *channel,
                    char *error,
                    size_t error_size);

void qd_channel_free(qd_channel_t *channel);

/*
 * Interpolate one Rx/Tx link at trace_time_s.
 *
 * coefficients_out and delays_out each require channel->paths elements.
 * Out-of-range time returns QD_CHANNEL_MUTED and zeroes every output.
 */
qd_channel_status_t qd_channel_sample(const qd_channel_t *channel,
                                      double trace_time_s,
                                      size_t rx,
                                      size_t tx,
                                      qd_complex32_t *coefficients_out,
                                      double *delays_out,
                                      float *residual_gain_db_out,
                                      char *error,
                                      size_t error_size);

#ifdef __cplusplus
}
#endif

#endif
