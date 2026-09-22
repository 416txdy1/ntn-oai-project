/*
 * SPDX-License-Identifier: LicenseRef-CSSL-1.0
 *
 * External STK ephemeris input for the RF simulator.
 *
 * Enable it by setting OAI_STK_PORT to a UDP port before starting the
 * softmodem. The sender must transmit one ASCII CSV datagram per state:
 *
 * STK1,seq,time_s,
 * sat_x,sat_y,sat_z,sat_vx,sat_vy,sat_vz,sat_ax,sat_ay,sat_az,
 * gnb_x,gnb_y,gnb_z,ue_x,ue_y,ue_z
 *
 * All Cartesian values use the Earth-fixed frame and SI units.
 */

#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <math.h>
#include <netinet/in.h>
#include <poll.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#include <common/utils/LOG/log.h>
#include <openair1/SIMULATION/TOOLS/sim.h>
#include "openair2/LAYER2/NR_MAC_gNB/mac_config.h"
#include "rfsimulator.h"

typedef struct {
  uint64_t sequence;
  double stk_time_s;
  double sat_position[3];
  double sat_velocity[3];
  double sat_acceleration[3];
  double gnb_position[3];
  double ue_position[3];
  struct timespec received_at;
  bool valid;
} stk_ephemeris_state_t;

static pthread_once_t stk_init_once = PTHREAD_ONCE_INIT;
static pthread_mutex_t stk_state_mutex = PTHREAD_MUTEX_INITIALIZER;
static int stk_socket = -1;
static int stk_timeout_ms = 1000;
static bool stk_configured;
static stk_ephemeris_state_t latest_state;
static double last_warning_s;
static bool stk_receiver_thread_started;

static void receive_pending_packets(void);
static void *stk_receiver_loop(void *unused);

static double monotonic_seconds(void)
{
  struct timespec now;
  clock_gettime(CLOCK_MONOTONIC, &now);
  return now.tv_sec + now.tv_nsec * 1e-9;
}

static void warn_throttled(const char *message)
{
  const double now = monotonic_seconds();
  if (now - last_warning_s >= 1.0) {
    LOG_W(HW, "%s\n", message);
    last_warning_s = now;
  }
}

static void init_stk_receiver(void)
{
  const char *port_text = getenv("OAI_STK_PORT");
  if (!port_text || !port_text[0])
    return;

  stk_configured = true;
  char *end = NULL;
  const long port = strtol(port_text, &end, 10);
  if (!end || *end != '\0' || port < 1 || port > 65535) {
    LOG_E(HW, "Invalid OAI_STK_PORT value '%s'\n", port_text);
    return;
  }

  const char *timeout_text = getenv("OAI_STK_TIMEOUT_MS");
  if (timeout_text && timeout_text[0]) {
    char *timeout_end = NULL;
    const long timeout = strtol(timeout_text, &timeout_end, 10);
    if (timeout_end && *timeout_end == '\0' && timeout >= 100 && timeout <= 60000)
      stk_timeout_ms = timeout;
    else
      LOG_W(HW, "Ignoring invalid OAI_STK_TIMEOUT_MS value '%s'\n", timeout_text);
  }

  stk_socket = socket(AF_INET, SOCK_DGRAM, 0);
  if (stk_socket < 0) {
    LOG_E(HW, "Unable to create STK UDP socket: %s\n", strerror(errno));
    return;
  }

  int reuse = 1;
  setsockopt(stk_socket, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

  struct sockaddr_in address = {
      .sin_family = AF_INET,
      .sin_port = htons((uint16_t)port),
      .sin_addr.s_addr = htonl(INADDR_ANY),
  };

  if (bind(stk_socket, (struct sockaddr *)&address, sizeof(address)) < 0) {
    LOG_E(HW, "Unable to bind STK UDP port %ld: %s\n", port, strerror(errno));
    close(stk_socket);
    stk_socket = -1;
    return;
  }

  const int flags = fcntl(stk_socket, F_GETFL, 0);
  if (flags < 0 || fcntl(stk_socket, F_SETFL, flags | O_NONBLOCK) < 0) {
    LOG_E(HW, "Unable to make STK UDP socket non-blocking: %s\n", strerror(errno));
    close(stk_socket);
    stk_socket = -1;
    return;
  }

  LOG_I(HW, "STK ephemeris receiver listening on UDP port %ld (timeout %d ms)\n", port, stk_timeout_ms);

  pthread_t receiver_thread;
  const int thread_error = pthread_create(&receiver_thread, NULL, stk_receiver_loop, NULL);
  if (thread_error == 0) {
    pthread_detach(receiver_thread);
    stk_receiver_thread_started = true;
  } else {
    LOG_W(HW, "Unable to start STK receiver thread: %s; using synchronous polling\n", strerror(thread_error));
  }
}

static bool parse_stk_packet(const char *packet, stk_ephemeris_state_t *state)
{
  stk_ephemeris_state_t parsed = {0};
  const int count = sscanf(packet,
                           "STK1,%" SCNu64 ",%lf,"
                           "%lf,%lf,%lf,%lf,%lf,%lf,%lf,%lf,%lf,"
                           "%lf,%lf,%lf,%lf,%lf,%lf",
                           &parsed.sequence,
                           &parsed.stk_time_s,
                           &parsed.sat_position[0],
                           &parsed.sat_position[1],
                           &parsed.sat_position[2],
                           &parsed.sat_velocity[0],
                           &parsed.sat_velocity[1],
                           &parsed.sat_velocity[2],
                           &parsed.sat_acceleration[0],
                           &parsed.sat_acceleration[1],
                           &parsed.sat_acceleration[2],
                           &parsed.gnb_position[0],
                           &parsed.gnb_position[1],
                           &parsed.gnb_position[2],
                           &parsed.ue_position[0],
                           &parsed.ue_position[1],
                           &parsed.ue_position[2]);

  if (count != 17)
    return false;

  for (int i = 0; i < 3; ++i) {
    if (!isfinite(parsed.sat_position[i]) || !isfinite(parsed.sat_velocity[i])
        || !isfinite(parsed.sat_acceleration[i]) || !isfinite(parsed.gnb_position[i])
        || !isfinite(parsed.ue_position[i]))
      return false;
  }

  clock_gettime(CLOCK_MONOTONIC, &parsed.received_at);
  parsed.valid = true;
  *state = parsed;
  return true;
}

static void receive_pending_packets(void)
{
  if (stk_socket < 0)
    return;

  char packet[1024];
  for (;;) {
    const ssize_t bytes = recvfrom(stk_socket, packet, sizeof(packet) - 1, 0, NULL, NULL);
    if (bytes < 0) {
      if (errno != EAGAIN && errno != EWOULDBLOCK)
        warn_throttled("Error receiving STK ephemeris datagram");
      break;
    }

    packet[bytes] = '\0';
    stk_ephemeris_state_t candidate;
    if (!parse_stk_packet(packet, &candidate)) {
      warn_throttled("Discarding malformed STK ephemeris datagram");
      continue;
    }

    pthread_mutex_lock(&stk_state_mutex);
    if (!latest_state.valid || candidate.sequence > latest_state.sequence
        || candidate.stk_time_s > latest_state.stk_time_s)
      latest_state = candidate;
    pthread_mutex_unlock(&stk_state_mutex);
  }
}

static void *stk_receiver_loop(void *unused)
{
  (void)unused;
  struct pollfd descriptor = {.fd = stk_socket, .events = POLLIN};
  for (;;) {
    const int result = poll(&descriptor, 1, 100);
    if (result > 0 && (descriptor.revents & POLLIN))
      receive_pending_packets();
    else if (result < 0 && errno != EINTR)
      warn_throttled("Error polling STK ephemeris socket");
  }
  return NULL;
}

static bool get_stk_state(stk_ephemeris_state_t *state)
{
  if (!stk_receiver_thread_started)
    receive_pending_packets();

  pthread_mutex_lock(&stk_state_mutex);
  *state = latest_state;
  pthread_mutex_unlock(&stk_state_mutex);

  if (!state->valid)
    return false;

  struct timespec now;
  clock_gettime(CLOCK_MONOTONIC, &now);
  const double age_s = (now.tv_sec - state->received_at.tv_sec)
                       + (now.tv_nsec - state->received_at.tv_nsec) * 1e-9;
  if (age_s < 0.0 || age_s * 1000.0 > stk_timeout_ms)
    return false;

  /*
   * Remove most UDP scheduling jitter by propagating the STK state from its
   * reception instant to the current RFsim instant. This is deliberately
   * limited by OAI_STK_TIMEOUT_MS.
   */
  for (int i = 0; i < 3; ++i) {
    state->sat_position[i] += state->sat_velocity[i] * age_s
                              + 0.5 * state->sat_acceleration[i] * age_s * age_s;
    state->sat_velocity[i] += state->sat_acceleration[i] * age_s;
  }
  return true;
}

static double dot3(const double a[3], const double b[3])
{
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

static void range_kinematics(const double moving_position[3],
                             const double fixed_position[3],
                             const double moving_velocity[3],
                             const double moving_acceleration[3],
                             double *range,
                             double *range_rate,
                             double *range_second_derivative)
{
  double relative_position[3];
  for (int i = 0; i < 3; ++i)
    relative_position[i] = moving_position[i] - fixed_position[i];

  *range = sqrt(dot3(relative_position, relative_position));
  if (*range <= 0.0) {
    *range_rate = 0.0;
    *range_second_derivative = 0.0;
    return;
  }

  *range_rate = dot3(relative_position, moving_velocity) / *range;
  const double velocity_squared = dot3(moving_velocity, moving_velocity);
  const double position_acceleration = dot3(relative_position, moving_acceleration);
  *range_second_derivative =
      (velocity_squared + position_acceleration - (*range_rate) * (*range_rate)) / *range;
}

static bool above_local_horizon(const double satellite_position[3], const double site_position[3])
{
  const double line_of_sight[3] = {
      satellite_position[0] - site_position[0],
      satellite_position[1] - site_position[1],
      satellite_position[2] - site_position[2],
  };
  return dot3(line_of_sight, site_position) > 0.0;
}

openair0_ntn_sync_status_t get_stk_ue_sync_state(double downlink_frequency_hz,
                                                  openair0_ntn_sync_state_t *sync_state)
{
  memset(sync_state, 0, sizeof(*sync_state));
  pthread_once(&stk_init_once, init_stk_receiver);
  if (!stk_configured)
    return OPENAIR0_NTN_SYNC_DISABLED;

  stk_ephemeris_state_t state;
  if (!get_stk_state(&state))
    return OPENAIR0_NTN_SYNC_WAITING;

  sync_state->stk_time_s = state.stk_time_s;
  if (!above_local_horizon(state.sat_position, state.gnb_position)
      || !above_local_horizon(state.sat_position, state.ue_position))
    return OPENAIR0_NTN_SYNC_NOT_VISIBLE;

  double service_range;
  double service_range_rate;
  double service_range_acceleration;
  range_kinematics(state.sat_position,
                   state.ue_position,
                   state.sat_velocity,
                   state.sat_acceleration,
                   &service_range,
                   &service_range_rate,
                   &service_range_acceleration);

  double feeder_range;
  double feeder_range_rate;
  double feeder_range_acceleration;
  range_kinematics(state.sat_position,
                   state.gnb_position,
                   state.sat_velocity,
                   state.sat_acceleration,
                   &feeder_range,
                   &feeder_range_rate,
                   &feeder_range_acceleration);

  const double c = (double)SPEED_OF_LIGHT;
  const double satellite_to_ue_speed = -service_range_rate;
  sync_state->propagation_delay_ms = (service_range + feeder_range) / c * 1000.0;
  sync_state->dl_doppler_hz =
      satellite_to_ue_speed / (c - satellite_to_ue_speed) * downlink_frequency_hz;
  sync_state->dl_time_drift_us_s = (service_range_rate + feeder_range_rate) / c * 1e6;
  return OPENAIR0_NTN_SYNC_READY;
}

static long long clamp_i64(long long value, long long minimum, long long maximum)
{
  if (value < minimum)
    return minimum;
  if (value > maximum)
    return maximum;
  return value;
}

static unsigned long long clamp_u64(unsigned long long value, unsigned long long maximum)
{
  return value > maximum ? maximum : value;
}

bool update_channel_model_from_stk(channel_desc_t *channel_desc, int nb_samples, uint64_t timestamp)
{
  if (channel_desc->modelid != SAT_LEO_TRANS && channel_desc->modelid != SAT_LEO_REGEN)
    return false;

  pthread_once(&stk_init_once, init_stk_receiver);
  if (!stk_configured)
    return false;

  stk_ephemeris_state_t state;
  if (!get_stk_state(&state)) {
    warn_throttled("STK ephemeris is missing or stale; holding the last RFsim channel state");
    return true;
  }

  const double c = (double)SPEED_OF_LIGHT;
  double service_range;
  double service_range_rate;
  double service_range_acceleration;
  range_kinematics(state.sat_position,
                   state.ue_position,
                   state.sat_velocity,
                   state.sat_acceleration,
                   &service_range,
                   &service_range_rate,
                   &service_range_acceleration);

  double feeder_range = 0.0;
  double feeder_range_rate = 0.0;
  double feeder_range_acceleration = 0.0;
  if (channel_desc->modelid == SAT_LEO_TRANS) {
    range_kinematics(state.sat_position,
                     state.gnb_position,
                     state.sat_velocity,
                     state.sat_acceleration,
                     &feeder_range,
                     &feeder_range_rate,
                     &feeder_range_acceleration);
  }

  const double propagation_delay_s = (service_range + feeder_range) / c;
  if (channel_desc->enable_dynamic_delay)
    channel_desc->channel_offset = propagation_delay_s * channel_desc->sampling_rate;

  double doppler_shift_hz;
  if (channel_desc->is_uplink) {
    doppler_shift_hz = (-service_range_rate / c) * channel_desc->center_freq;
  } else {
    const double velocity_sat_to_ue = -service_range_rate;
    doppler_shift_hz = (velocity_sat_to_ue / (c - velocity_sat_to_ue)) * channel_desc->center_freq;
  }

  if (channel_desc->enable_dynamic_Doppler)
    channel_desc->Doppler_phase_inc = 2 * M_PI * doppler_shift_hz / channel_desc->sampling_rate;

  if (timestamp / (unsigned int)channel_desc->sampling_rate
      != (timestamp + nb_samples) / (unsigned int)channel_desc->sampling_rate) {
    LOG_I(HW,
          "STK satellite: STK time %.6f s, Position = (%.3f, %.3f, %.3f), "
          "Velocity = (%.3f, %.3f, %.3f)\n",
          state.stk_time_s,
          state.sat_position[0],
          state.sat_position[1],
          state.sat_position[2],
          state.sat_velocity[0],
          state.sat_velocity[1],
          state.sat_velocity[2]);
    LOG_I(HW,
          "%s delay %.6f ms, Doppler shift %.6f kHz\n",
          channel_desc->is_uplink ? "Uplink" : "Downlink",
          propagation_delay_s * 1000.0,
          doppler_shift_hz / 1000.0);
  }

  /*
   * The uplink RFsim channel runs in the gNB process. Update SIB19 once per
   * frame for the following frame, matching the existing circular-orbit path.
   */
  if (channel_desc->is_uplink) {
    const int samples_per_subframe = channel_desc->sampling_rate / 1000;
    const int absolute_subframe = timestamp / samples_per_subframe;
    if (absolute_subframe % 10 == 0) {
      /*
       * ta-CommonDriftVariant is the quadratic coefficient of range versus
       * time, hence one half of the physical second derivative.
       */
      double feeder_quadratic = 0.5 * feeder_range_acceleration;
      if (feeder_quadratic < 0.0)
        feeder_quadratic = 0.0;

      const long long delay = llround(2.0 * feeder_range / (c * 4.072e-9));
      const long long drift = llround(2.0 * feeder_range_rate / (c * 0.2e-9));
      const unsigned long long accel =
          llround(2.0 * feeder_quadratic / (c * 0.2e-10));

      gnb_sat_position_update_t update = {
          .sfn = (absolute_subframe / 10 + 1) % 1024,
          .subframe = 0,
          .delay = (uint32_t)clamp_u64(delay < 0 ? 0 : (unsigned long long)delay, 66485757ULL),
          .drift = (int)clamp_i64(drift, -257303, 257303),
          .accel = (uint32_t)clamp_u64(accel, 28949ULL),
          .position.X = (int)clamp_i64(llround(state.sat_position[0] / 1.3), -33554432, 33554431),
          .position.Y = (int)clamp_i64(llround(state.sat_position[1] / 1.3), -33554432, 33554431),
          .position.Z = (int)clamp_i64(llround(state.sat_position[2] / 1.3), -33554432, 33554431),
          .velocity.X = (int)clamp_i64(llround(state.sat_velocity[0] / 0.06), -131072, 131071),
          .velocity.Y = (int)clamp_i64(llround(state.sat_velocity[1] / 0.06), -131072, 131071),
          .velocity.Z = (int)clamp_i64(llround(state.sat_velocity[2] / 0.06), -131072, 131071),
      };
      nr_update_sib19(&update);
    }
  }

  return true;
}
