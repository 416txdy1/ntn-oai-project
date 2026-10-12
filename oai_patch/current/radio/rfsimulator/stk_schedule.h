#ifndef OAI_STK_SCHEDULE_H
#define OAI_STK_SCHEDULE_H

#include <stdbool.h>
#include <stddef.h>

typedef struct {
  double time;
  double elevation_deg;
  bool visible;
  bool switched;
  char satellite_id[96];
  char handover_phase[16];
  char previous_satellite_id[96];
  char next_satellite_id[96];
} stk_schedule_entry;

typedef struct {
  stk_schedule_entry *rows;
  size_t count;
} stk_schedule;

bool stk_schedule_load(const char *path, stk_schedule *schedule,
                       char *error, size_t error_size);
bool stk_schedule_at(const stk_schedule *schedule, double time,
                     stk_schedule_entry *entry);
void stk_schedule_free(stk_schedule *schedule);

#endif
