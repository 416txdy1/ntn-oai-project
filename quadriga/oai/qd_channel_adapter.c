/* SPDX-License-Identifier: LicenseRef-CSSL-1.0
 * QDCHANNEL1 adapter for OAI RFsim.
 * QuaDRiGa owns normalized relative multipath only. STKTRACE2 remains the
 * source of bulk delay, bulk Doppler, absolute gain, visibility and noise.
 */
#include "qd_channel_reader.h"
#include <openair1/SIMULATION/TOOLS/sim.h>
#include "rfsimulator.h"
#include <common/utils/LOG/log.h>
#include <math.h>
#include <limits.h>
#include <openssl/evp.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <semaphore.h>
#if defined(__GNUC__) && defined(__AVX2__)
#include <immintrin.h>
#endif

#define QD_MAX_CHANNELS 16
#define QD_DEFAULT_MAX_HISTORY_SAMPLES 1000000U

typedef struct {
  channel_desc_t *channel;
  qd_channel_t bundle;
  qd_complex32_t *coefficients;
  double *delays_s;
  double *fir_fractions;
  double *fir_weights;
  size_t history_samples;
  float *residual_gain_db;
  bool muted;
  uint64_t timestamp;
} qd_runtime_state_t;

static pthread_mutex_t qd_lock = PTHREAD_MUTEX_INITIALIZER;
static qd_runtime_state_t qd_states[QD_MAX_CHANNELS];

static size_t configured_history_limit(void)
{
  const char *value = getenv("OAI_QD_MAX_HISTORY_SAMPLES");
  if (value == NULL || *value == '\0')
    return QD_DEFAULT_MAX_HISTORY_SAMPLES;
  char *end = NULL;
  const unsigned long long parsed = strtoull(value, &end, 10);
  AssertFatal(end != value && *end == '\0' && parsed > 0 && parsed <= SIZE_MAX,
              "Invalid OAI_QD_MAX_HISTORY_SAMPLES=%s\n", value);
  return (size_t)parsed;
}

static bool sha256_file(const char *path, char output[65], char *error, size_t error_size)
{
  FILE *stream = fopen(path, "rb");
  if (stream == NULL) {
    snprintf(error, error_size, "cannot open STK trace %s", path);
    return false;
  }
  EVP_MD_CTX *context = EVP_MD_CTX_new();
  if (context == NULL || EVP_DigestInit_ex(context, EVP_sha256(), NULL) != 1) {
    snprintf(error, error_size, "cannot initialize SHA256");
    EVP_MD_CTX_free(context);
    fclose(stream);
    return false;
  }
  unsigned char buffer[16384];
  size_t count = 0;
  while ((count = fread(buffer, 1, sizeof(buffer), stream)) > 0) {
    if (EVP_DigestUpdate(context, buffer, count) != 1) {
      snprintf(error, error_size, "cannot hash STK trace");
      EVP_MD_CTX_free(context);
      fclose(stream);
      return false;
    }
  }
  if (ferror(stream)) {
    snprintf(error, error_size, "cannot read STK trace %s", path);
    EVP_MD_CTX_free(context);
    fclose(stream);
    return false;
  }
  unsigned char digest[EVP_MAX_MD_SIZE];
  unsigned int digest_size = 0;
  const bool ok = EVP_DigestFinal_ex(context, digest, &digest_size) == 1 && digest_size == 32;
  EVP_MD_CTX_free(context);
  fclose(stream);
  if (!ok) {
    snprintf(error, error_size, "cannot finalize STK trace SHA256");
    return false;
  }
  for (unsigned int index = 0; index < digest_size; index++)
    snprintf(output + 2 * index, 3, "%02x", digest[index]);
  output[64] = '\0';
  return true;
}

bool qd_channel_requested(void)
{
  const char *bundle = getenv("OAI_QD_CHANNEL");
  return bundle != NULL && *bundle != '\0';
}

static qd_runtime_state_t *find_state(channel_desc_t *channel)
{
  for (size_t index = 0; index < QD_MAX_CHANNELS; index++)
    if (qd_states[index].channel == channel)
      return &qd_states[index];
  return NULL;
}

static qd_runtime_state_t *create_state(channel_desc_t *channel)
{
  const char *bundle_path = getenv("OAI_QD_CHANNEL");
  const char *trace_path = getenv("OAI_STK_TRACE");
  AssertFatal(bundle_path != NULL && *bundle_path != '\0', "OAI_QD_CHANNEL is required\n");
  AssertFatal(trace_path != NULL && *trace_path != '\0',
              "OAI_QD_CHANNEL requires OAI_STK_TRACE so STK remains the absolute channel source\n");
  AssertFatal(channel->nb_tx > 0 && channel->nb_rx > 0, "QDCHANNEL1 requires positive antenna counts\n");
  AssertFatal(isfinite(channel->sampling_rate) && channel->sampling_rate > 0,
              "Invalid RFsim sampling rate for QDCHANNEL1\n");
  qd_runtime_state_t *state = NULL;
  for (size_t index = 0; index < QD_MAX_CHANNELS; index++)
    if (qd_states[index].channel == NULL) {
      state = &qd_states[index];
      break;
    }
  AssertFatal(state != NULL, "Too many QDCHANNEL1 RFsim channels\n");
  char expected_trace_sha256[65];
  char error[512] = {0};
  AssertFatal(sha256_file(trace_path, expected_trace_sha256, error, sizeof(error)),
              "QDCHANNEL1 provenance: %s\n", error);
  AssertFatal(qd_channel_load(bundle_path, expected_trace_sha256, &state->bundle, error, sizeof(error)),
              "QDCHANNEL1 load: %s\n", error);
  AssertFatal(state->bundle.rx_antennas == channel->nb_rx && state->bundle.tx_antennas == channel->nb_tx,
              "QDCHANNEL1 bundle %zu Tx x %zu Rx differs from RFsim %u Tx x %u Rx\n",
              state->bundle.tx_antennas, state->bundle.rx_antennas, channel->nb_tx, channel->nb_rx);
  AssertFatal(channel->nb_tx * channel->nb_rx == 1 || state->bundle.spatial_normalization,
              "Multiport QDCHANNEL1 requires shared spatial normalization\n");
  const char *expected_direction = channel->is_uplink ? "uplink" : "downlink";
  AssertFatal(strcmp(state->bundle.link_direction, expected_direction) == 0,
              "QDCHANNEL1 direction %s does not match RFsim %s channel\n",
              state->bundle.link_direction, expected_direction);
  const double frequency_tolerance_hz = fmax(1.0, state->bundle.center_frequency_hz * 1e-9);
  AssertFatal(fabs(state->bundle.center_frequency_hz - (double)channel->center_freq) <= frequency_tolerance_hz,
              "QDCHANNEL1 center frequency %.3f Hz does not match RFsim %lu Hz\n",
              state->bundle.center_frequency_hz, channel->center_freq);
  const size_t links = state->bundle.rx_antennas * state->bundle.tx_antennas;
  state->coefficients = calloc(links * state->bundle.paths, sizeof(*state->coefficients));
  state->delays_s = calloc(links * state->bundle.paths, sizeof(*state->delays_s));
  state->fir_fractions = malloc(links * state->bundle.paths * sizeof(double));
  state->fir_weights = malloc(links * state->bundle.paths * 12 * sizeof(double));
  state->residual_gain_db = calloc(links, sizeof(*state->residual_gain_db));
  AssertFatal(state->coefficients != NULL && state->delays_s != NULL && state->residual_gain_db != NULL
                  && state->fir_fractions != NULL && state->fir_weights != NULL,
              "Cannot allocate QDCHANNEL1 runtime tap buffers\n");
  for (size_t i = 0; i < links * state->bundle.paths; i++) state->fir_fractions[i] = NAN;
  double maximum_delay_s = 0.0;
  const size_t total_delays = state->bundle.snapshots * state->bundle.rx_antennas
                              * state->bundle.tx_antennas * state->bundle.paths;
  for (size_t index = 0; index < total_delays; index++)
    maximum_delay_s = fmax(maximum_delay_s, state->bundle.delays_s[index]);
  const double maximum_delay_samples = maximum_delay_s * channel->sampling_rate;
  AssertFatal(isfinite(maximum_delay_samples) && maximum_delay_samples >= 0
                  && maximum_delay_samples <= (double)(SIZE_MAX - 7),
              "QDCHANNEL1 relative delay does not fit RFsim history\n");
  state->history_samples = (size_t)ceil(maximum_delay_samples) + 7;
  AssertFatal(state->history_samples <= configured_history_limit(),
              "QDCHANNEL1 needs %zu history samples; raise OAI_QD_MAX_HISTORY_SAMPLES deliberately if valid\n",
              state->history_samples);
  state->channel = channel;
  state->muted = true;
  LOG_I(HW, "QDCHANNEL1 spatial ports: %zu Tx x %zu Rx\n", state->bundle.tx_antennas, state->bundle.rx_antennas);
  LOG_I(HW, "QDCHANNEL1 loaded %zu snapshots, %zu paths, %zu history samples, %s, %.3f Hz\n",
        state->bundle.snapshots, state->bundle.paths, state->history_samples,
        state->bundle.link_direction, state->bundle.center_frequency_hz);
  return state;
}

void update_channel_model_from_quadriga(channel_desc_t *channel, uint64_t timestamp)
{
  if (!qd_channel_requested())
    return;
  double trace_time_s = 0.0;
  AssertFatal(stk_trace_time_at_timestamp(timestamp, channel->sampling_rate, &trace_time_s),
              "QDCHANNEL1 requires the active STKTRACE2 sample clock\n");
  pthread_mutex_lock(&qd_lock);
  qd_runtime_state_t *state = find_state(channel);
  if (state == NULL)
    state = create_state(channel);
  char error[512] = {0};
  state->timestamp = timestamp;
  state->muted = false;
  for (size_t rx = 0; rx < state->bundle.rx_antennas; rx++) {
    for (size_t tx = 0; tx < state->bundle.tx_antennas; tx++) {
      const size_t link = rx * state->bundle.tx_antennas + tx;
      const size_t tap = link * state->bundle.paths;
      const qd_channel_status_t status = qd_channel_sample(&state->bundle, trace_time_s, rx, tx,
          state->coefficients + tap, state->delays_s + tap,
          state->residual_gain_db + link, error, sizeof(error));
      AssertFatal(status != QD_CHANNEL_ERROR, "QDCHANNEL1 sample: %s\n", error);
      state->muted |= status == QD_CHANNEL_MUTED;
    }
  }
  pthread_mutex_unlock(&qd_lock);
}

size_t qd_channel_history_length(channel_desc_t *channel)
{
  if (!qd_channel_requested())
    return channel->channel_length;
  pthread_mutex_lock(&qd_lock);
  qd_runtime_state_t *state = find_state(channel);
  AssertFatal(state != NULL, "QDCHANNEL1 channel was not updated before RFsim input collection\n");
  const size_t history = state->history_samples;
  pthread_mutex_unlock(&qd_lock);
  return history;
}

size_t qd_channel_lookahead_length(channel_desc_t *channel)
{
  if (!qd_channel_requested()) return 0;
  pthread_mutex_lock(&qd_lock);
  qd_runtime_state_t *state = find_state(channel);
  AssertFatal(state != NULL, "QD channel not updated before input collection\n");
  /* 块起点静音仍可能在块内进入有效区间，必须预留完整前视缓冲。 */
  const size_t count = 5;
  pthread_mutex_unlock(&qd_lock);
  return count;
}

static void fractional_sample(const c16_t *input, size_t current, size_t integer_delay,
                              double fraction, double *last_fraction, double *weights,
                              double *real, double *imag)
{
  if (fraction == 0) {
    *real = input[current - integer_delay].r;
    *imag = input[current - integer_delay].i;
    return;
  }
  /* 对称 12 点 Lagrange；前看 5 点来自已有 STK 传播缓冲，不添加群时延。 */
  static const double inverse_denominator[12] = {
      -1.0/39916800, 1.0/3628800, -1.0/725760, 1.0/241920, -1.0/120960, 1.0/86400,
      -1.0/86400, 1.0/120960, -1.0/241920, 1.0/725760, -1.0/3628800, 1.0/39916800};
  /* 前后缀积直接形成基函数；避免每条路径每个 IQ 样本执行 12 次除法。
   * 这是同一多项式的代数改写，不引入查表或分数时延量化。 */
  /* 完全相等才复用；静态链路和固定时延 tap 不必重复计算同一组权重。 */
  if (fraction != *last_fraction) {
#if defined(__GNUC__) && defined(__AVX2__)
    /* fraction 在 (0,1)，与12个整数节点均不重合。共享完整乘积，
     * 再并行除去各节点因子；仍是精确的 Lagrange 公式，无量化。 */
    typedef double qd_weight4 __attribute__((vector_size(32)));
    double product = fraction * (fraction - 1);
    for (int j = 1; j <= 5; j++) product *= (fraction + j) * (fraction - j - 1);
    for (int j = 0; j < 12; j += 4) {
      const qd_weight4 denominator = {fraction-(j-5), fraction-(j-4), fraction-(j-3), fraction-(j-2)};
      const qd_weight4 scale = {inverse_denominator[j], inverse_denominator[j+1],
                                inverse_denominator[j+2], inverse_denominator[j+3]};
      const qd_weight4 result = (product * scale) / denominator;
      memcpy(weights + j, &result, sizeof(result));
    }
#else
    double prefix[13];
    prefix[0] = 1;
    for (int j = 0; j < 12; j++) prefix[j + 1] = prefix[j] * (fraction - (j - 5));
    double suffix = 1;
    for (int j = 11; j >= 0; j--) {
      weights[j] = prefix[j] * suffix * inverse_denominator[j];
      suffix *= fraction - (j - 5);
    }
#endif
    *last_fraction = fraction;
  }
  *real = *imag = 0;
  const size_t first = current - integer_delay + 5;
#if defined(__GNUC__) && defined(__AVX2__)
  /* 四路双精度并行点积；仅改变浮点求和次序，保留同一12点核。
   * 不支持 AVX2 的目标沿用下面的标量实现。 */
  typedef double qd_double4 __attribute__((vector_size(32)));
  qd_double4 sum_real = {0, 0, 0, 0}, sum_imag = {0, 0, 0, 0};
  for (int j = 0; j < 12; j += 4) {
    const qd_double4 w = {weights[j], weights[j+1], weights[j+2], weights[j+3]};
    const qd_double4 r = {input[first-j].r, input[first-j-1].r, input[first-j-2].r, input[first-j-3].r};
    const qd_double4 i = {input[first-j].i, input[first-j-1].i, input[first-j-2].i, input[first-j-3].i};
    sum_real += w * r;
    sum_imag += w * i;
  }
  *real = (sum_real[0] + sum_real[1]) + (sum_real[2] + sum_real[3]);
  *imag = (sum_imag[0] + sum_imag[1]) + (sum_imag[2] + sum_imag[3]);
#else
  double sum_real = 0, sum_imag = 0;
  for (int j = 11; j >= 0; j--) {
    const double weight = weights[j];
    sum_real += weight * input[first - j].r;
    sum_imag += weight * input[first - j].i;
  }
  *real = sum_real;
  *imag = sum_imag;
#endif
}

#if defined(__GNUC__) && defined(__AVX2__)
#if defined(__AVX512F__)
#define QD_SIMD_LANES 8
typedef double qd_samplev __attribute__((vector_size(64)));
#define QD_SIMD_ONES ((qd_samplev){1,1,1,1,1,1,1,1})
#else
#define QD_SIMD_LANES 4
typedef double qd_samplev __attribute__((vector_size(32)));
#define QD_SIMD_ONES ((qd_samplev){1,1,1,1})
#endif

/* 同一快照区间内并行计算4或8个相邻IQ样本；每个样本仍有独立的
 * 插值权重、时延及复系数。避免每个tap重复水平归约，不冻结信道。 */
static void convolve_vector(const qd_runtime_state_t *state, c16_t **input, int rx,
                          size_t current, size_t lower, size_t upper,
                          qd_samplev weight, double sampling_rate, struct complexd *output)
{
  const qd_channel_t *bundle = &state->bundle;
  const size_t links = bundle->rx_antennas * bundle->tx_antennas;
  const qd_samplev inverse = 1.0 - weight;
  qd_samplev out_r = {0}, out_i = {0};
  static const double denominator[12] = {
    -1.0/39916800,1.0/3628800,-1.0/725760,1.0/241920,-1.0/120960,1.0/86400,
    -1.0/86400,1.0/120960,-1.0/241920,1.0/725760,-1.0/3628800,1.0/39916800};
  for (size_t tx = 0; tx < bundle->tx_antennas; tx++) {
    const size_t link = (size_t)rx * bundle->tx_antennas + tx;
    const size_t lo = lower * links + link, hi = upper * links + link;
    qd_samplev amplitude;
    const qd_samplev gains = inverse*bundle->residual_gain_db[lo] + weight*bundle->residual_gain_db[hi];
    for (int k=0;k<QD_SIMD_LANES;k++) {
      const float gain = (float)gains[k];
      amplitude[k] = gain == 0 ? 1 : pow(10.0,gain/20.0);
    }
    for (size_t path=0;path<bundle->paths;path++) {
      const size_t left=lo*bundle->paths+path, right=hi*bundle->paths+path;
      const qd_samplev delay=(inverse*bundle->delays_s[left]+weight*bundle->delays_s[right])*sampling_rate;
      size_t whole[QD_SIMD_LANES]; bool integral[QD_SIMD_LANES]; qd_samplev fraction;
      for (int k=0;k<QD_SIMD_LANES;k++) {
        whole[k]=(size_t)floor(delay[k]); fraction[k]=delay[k]-(double)whole[k];
        integral[k]=fraction[k]==0;
        /* 整数采样直接取原值；占位分数仅避免并行除法出现0/0。 */
        if (integral[k]) fraction[k]=0.5;
      }
      /* 用前后缀积计算同一 Lagrange 多项式，去掉逐 lane 除法。 */
      qd_samplev prefix[13], weights[12];
      prefix[0]=QD_SIMD_ONES;
      for (int j=0;j<12;j++) prefix[j+1]=prefix[j]*(fraction-(j-5));
      qd_samplev suffix=QD_SIMD_ONES;
      for (int j=11;j>=0;j--) {
        weights[j]=(prefix[j]*suffix)*denominator[j];
        suffix *= fraction-(j-5);
      }
      qd_samplev in_r={0}, in_i={0};
      bool contiguous=true;
      for (int k=1;k<QD_SIMD_LANES;k++) contiguous = contiguous && whole[0]==whole[k];
      for (int j=0;j<12;j++) {
        const qd_samplev w=weights[j];
        qd_samplev r,i;
        if (contiguous) {
          /* 相邻样本的整数时延相同时可连续读入一组复数；分数时延
           * 仍逐样本独立计算，跨整数时延边界时使用通用路径。 */
          _Static_assert(sizeof(c16_t)==4,"unexpected complex sample layout");
#if defined(__AVX512F__)
          const __m256i packed=_mm256_loadu_si256((const __m256i *)(input[tx]+current-whole[0]+5-j));
          r=_mm512_cvtepi32_pd(_mm256_srai_epi32(_mm256_slli_epi32(packed,16),16));
          i=_mm512_cvtepi32_pd(_mm256_srai_epi32(packed,16));
#else
          const __m128i packed=_mm_loadu_si128((const __m128i *)(input[tx]+current-whole[0]+5-j));
          r=_mm256_cvtepi32_pd(_mm_srai_epi32(_mm_slli_epi32(packed,16),16));
          i=_mm256_cvtepi32_pd(_mm_srai_epi32(packed,16));
#endif
        } else {
          for (int k=0;k<QD_SIMD_LANES;k++) {
            const c16_t value=input[tx][current+(size_t)k-whole[k]+5-j];
            r[k]=value.r; i[k]=value.i;
          }
        }
        in_r += w*r; in_i += w*i;
      }
      qd_samplev real=inverse*bundle->coefficients[left].real+weight*bundle->coefficients[right].real;
      qd_samplev imag=inverse*bundle->coefficients[left].imag+weight*bundle->coefficients[right].imag;
      for (int k=0;k<QD_SIMD_LANES;k++) {
        if (integral[k]) {
          in_r[k]=input[tx][current+(size_t)k-whole[k]].r;
          in_i[k]=input[tx][current+(size_t)k-whole[k]].i;
        }
        real[k]=(float)real[k]; imag[k]=(float)imag[k];
      }
      real *= amplitude; imag *= amplitude;
      out_r += in_r*real-in_i*imag;
      out_i += in_i*real+in_r*imag;
    }
  }
  for (int k=0;k<QD_SIMD_LANES;k++) {output[k].r=out_r[k];output[k].i=out_i[k];}
}
#endif

static void convolve_range(qd_runtime_state_t *state, channel_desc_t *channel,
                           c16_t **input, int rx_antenna, int begin, int end,
                           struct complexd *output)
{
  /* 按接收采样时刻更新；不能把加密后的信道冻结到整个 IQ 块末尾。
   * 每个 Rx 都使用同一块起点，支持 rate=0、非均匀快照和块内越界静音。 */
  const qd_channel_t *bundle = &state->bundle;
  const size_t links = bundle->rx_antennas * bundle->tx_antennas;
  size_t lower = 0, upper = bundle->snapshots - 1;
  double start_time;
  AssertFatal(stk_trace_time_at_timestamp(state->timestamp+(uint64_t)begin, channel->sampling_rate, &start_time),
              "QD sample clock unavailable\n");
  /* 一个块只二分一次，随后随样本时钟向前移动；保持逐采样精度。 */
  while (upper - lower > 1) {
    const size_t middle = lower + (upper - lower) / 2;
    if (bundle->times_s[middle] <= start_time) lower = middle;
    else upper = middle;
  }
  for (int sample = begin; sample < end; sample++) {
    double time_s;
    AssertFatal(stk_trace_time_at_timestamp(state->timestamp + (uint64_t)sample,
                channel->sampling_rate, &time_s), "QD sample clock unavailable\n");
    if (time_s < bundle->times_s[0] || time_s > bundle->times_s[bundle->snapshots - 1]) continue;
    while (lower + 1 < bundle->snapshots && bundle->times_s[lower + 1] <= time_s) lower++;
    upper = lower + 1 < bundle->snapshots ? lower + 1 : lower;
#if defined(__GNUC__) && defined(__AVX2__)
    if (end - sample >= QD_SIMD_LANES && upper != lower) {
      double times[QD_SIMD_LANES] = {time_s};
      for (int k=1;k<QD_SIMD_LANES;k++)
        AssertFatal(stk_trace_time_at_timestamp(state->timestamp+(uint64_t)sample+k,
                    channel->sampling_rate,&times[k]),"QD sample clock unavailable\n");
      if (times[QD_SIMD_LANES-1] >= times[0] && times[QD_SIMD_LANES-1] < bundle->times_s[upper]) {
        qd_samplev weights;
        for (int k=0;k<QD_SIMD_LANES;k++) weights[k]=(times[k]-bundle->times_s[lower])/
            (bundle->times_s[upper]-bundle->times_s[lower]);
        convolve_vector(state,input,rx_antenna,state->history_samples-1+(size_t)sample,
                      lower,upper,weights,channel->sampling_rate,output+sample);
        sample += QD_SIMD_LANES-1;
        continue;
      }
    }
#endif
    const double weight = upper == lower ? 0 :
        (time_s - bundle->times_s[lower]) / (bundle->times_s[upper] - bundle->times_s[lower]);
    const double inverse = 1 - weight;
    const size_t current = state->history_samples - 1 + (size_t)sample;
    for (size_t tx = 0; tx < state->bundle.tx_antennas; tx++) {
      const size_t link = (size_t)rx_antenna * state->bundle.tx_antennas + tx;
      const size_t lo = lower * links + link, hi = upper * links + link;
      const float gain = (float)(inverse * bundle->residual_gain_db[lo] + weight * bundle->residual_gain_db[hi]);
      const double residual_amplitude = gain == 0 ? 1 : pow(10.0, gain / 20.0);
      for (size_t path = 0; path < bundle->paths; path++) {
        const size_t left = lo * bundle->paths + path, right = hi * bundle->paths + path;
        const double delay_samples = (inverse * bundle->delays_s[left] + weight * bundle->delays_s[right]) * channel->sampling_rate;
        const size_t integer_delay = (size_t)floor(delay_samples);
        const double fraction = delay_samples - (double)integer_delay;
        double input_real, input_imag;
        const size_t tap = link * bundle->paths + path;
        fractional_sample(input[tx], current, integer_delay, fraction,
                          &state->fir_fractions[tap], &state->fir_weights[tap * 12], &input_real, &input_imag);
        const double tap_real = residual_amplitude * (float)(inverse * bundle->coefficients[left].real + weight * bundle->coefficients[right].real);
        const double tap_imag = residual_amplitude * (float)(inverse * bundle->coefficients[left].imag + weight * bundle->coefficients[right].imag);
        output[sample].r += input_real * tap_real - input_imag * tap_imag;
        output[sample].i += input_imag * tap_real + input_real * tap_imag;
      }
    }
  }
}

/* 将 Rx×样本展平后分派；各端口仍独立滤波，不混合系数或噪声。 */
static void convolve_flat(qd_runtime_state_t *state, channel_desc_t *channel,
                          c16_t **input, int first_rx, int samples,
                          int begin, int end, struct complexd *output)
{
  while (begin < end) {
    const int port = begin / samples;
    const int local_begin = begin % samples;
    const int local_end = end - port*samples < samples ? end - port*samples : samples;
    convolve_range(state,channel,input,first_rx+port,local_begin,local_end,output+port*samples);
    begin = port*samples + local_end;
  }
}

/* qd_lock 覆盖完整卷积，保护信道更新；工作线程写互不重叠的样本，
 * 分数 FIR 缓存各自独立。逐样本 tap 求和顺序与串行版本一致。 */
typedef struct {
  pthread_t thread;
  sem_t ready, done;
  bool stop;
  qd_runtime_state_t state;
  double *fractions, *weights;
  size_t capacity;
  channel_desc_t *channel;
  c16_t **input;
  struct complexd *output;
  int rx, samples, begin, end;
} qd_worker_t;
static qd_worker_t qd_workers[7];
static int qd_worker_count;

static void wait_qd(sem_t *semaphore)
{
  int result;
  do {result=sem_wait(semaphore);} while(result && errno==EINTR);
  AssertFatal(result==0,"QD worker semaphore wait failed\n");
}

static void *qd_worker_main(void *argument)
{
  qd_worker_t *worker=argument;
  for (;;) {
    wait_qd(&worker->ready);
    if (worker->stop) return NULL;
    convolve_flat(&worker->state,worker->channel,worker->input,worker->rx,worker->samples,
                  worker->begin,worker->end,worker->output);
    AssertFatal(sem_post(&worker->done)==0,"QD worker completion failed\n");
  }
}

static void init_qd_workers(void)
{
  if (qd_worker_count) return;
  const char *setting=getenv("OAI_QD_WORKERS");
  qd_worker_count=1;
  if (setting) {
    AssertFatal(strlen(setting)==1 && setting[0]>='1' && setting[0]<='8',
                "OAI_QD_WORKERS must be 1..8\n");
    qd_worker_count=setting[0]-'0';
  }
  LOG_I(HW,"QDCHANNEL1 compute workers: %d\n",qd_worker_count);
  for (int index=0;index<qd_worker_count-1;index++) {
    qd_worker_t *worker=&qd_workers[index];
    AssertFatal(sem_init(&worker->ready,0,0)==0 && sem_init(&worker->done,0,0)==0,
                "QD worker semaphore initialization failed\n");
    AssertFatal(pthread_create(&worker->thread,NULL,qd_worker_main,worker)==0,
                "QD worker creation failed\n");
  }
}

__attribute__((destructor)) static void close_qd_workers(void)
{
  pthread_mutex_lock(&qd_lock);
  for (int index=0;index<qd_worker_count-1;index++) {
    qd_worker_t *worker=&qd_workers[index];
    worker->stop=true;
    sem_post(&worker->ready);
    pthread_join(worker->thread,NULL);
    sem_destroy(&worker->ready); sem_destroy(&worker->done);
    free(worker->fractions); free(worker->weights);
  }
  pthread_mutex_unlock(&qd_lock);
}

static bool convolve_ports(channel_desc_t *channel, c16_t **input, int rx_antenna,
                           int ports, int samples, struct complexd *output)
{
  if (!qd_channel_requested()) return false;
  AssertFatal(rx_antenna>=0 && rx_antenna<channel->nb_rx,"QDCHANNEL1 invalid receive antenna\n");
  AssertFatal(samples>=0 && output!=NULL && ports>0 && ports<=channel->nb_rx-rx_antenna
              && samples<=INT_MAX/ports,"Invalid QDCHANNEL1 convolution output\n");
  const int total=samples*ports;
  pthread_mutex_lock(&qd_lock);
  qd_runtime_state_t *state=find_state(channel);
  AssertFatal(state!=NULL,"QDCHANNEL1 channel was not updated before convolution\n");
  AssertFatal((uint64_t)samples<=UINT64_MAX-state->timestamp,"QD timestamp overflow\n");
  memset(output,0,(size_t)total*sizeof(*output));
  init_qd_workers();
  const int count=total>=4*qd_worker_count?qd_worker_count:1;
  const int chunk=(total/count)/4*4;
  const size_t taps=state->bundle.rx_antennas*state->bundle.tx_antennas*state->bundle.paths;
  for (int index=0;index<count-1;index++) {
    qd_worker_t *worker=&qd_workers[index];
    if (worker->capacity<taps) {
      free(worker->fractions); free(worker->weights);
      worker->fractions=malloc(taps*sizeof(double));
      worker->weights=malloc(taps*12*sizeof(double));
      AssertFatal(worker->fractions && worker->weights,"QD worker allocation failed\n");
      for(size_t tap=0;tap<taps;tap++) worker->fractions[tap]=NAN;
      worker->capacity=taps;
    }
    worker->state=*state;
    worker->state.fir_fractions=worker->fractions;
    worker->state.fir_weights=worker->weights;
    worker->channel=channel; worker->input=input; worker->rx=rx_antenna; worker->output=output;
    worker->samples=samples;
    worker->begin=(index+1)*chunk;
    worker->end=index==count-2?total:(index+2)*chunk;
    AssertFatal(sem_post(&worker->ready)==0,"QD worker dispatch failed\n");
  }
  convolve_flat(state,channel,input,rx_antenna,samples,0,count==1?total:chunk,output);
  for(int index=0;index<count-1;index++) wait_qd(&qd_workers[index].done);
  pthread_mutex_unlock(&qd_lock);
  return true;
}

bool qd_channel_convolve(channel_desc_t *channel, c16_t **input, int rx_antenna,
                         int samples, struct complexd *output)
{
  return convolve_ports(channel,input,rx_antenna,1,samples,output);
}

bool qd_channel_convolve_all(channel_desc_t *channel, c16_t **input,
                             int samples, struct complexd *output)
{
  return convolve_ports(channel,input,0,channel->nb_rx,samples,output);
}
