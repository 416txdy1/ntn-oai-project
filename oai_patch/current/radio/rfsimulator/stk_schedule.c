#include "stk_schedule.h"

#include <ctype.h>
#include <errno.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STK_SCHEDULE_MAX_ROWS 1000000U

static void fail(char *error, size_t size, const char *message)
{
  if (size == 0) return;
  snprintf(error, size, "%s", message);
}

static char *trim(char *text)
{
  while (isspace((unsigned char)*text)) text++;
  char *end = text + strlen(text);
  while (end > text && isspace((unsigned char)end[-1])) *--end = '\0';
  return text;
}

static bool finite_number(const char *text, double *value)
{
  char *end = NULL;
  errno = 0;
  *value = strtod(text, &end);
  return end != text && errno == 0 && isfinite(*value);
}

bool stk_schedule_load(const char *path, stk_schedule *schedule,
                       char *error, size_t error_size)
{
  if (!schedule) {
    fail(error, error_size, "null schedule");
    return false;
  }
  memset(schedule, 0, sizeof(*schedule));
  FILE *file = fopen(path, "rb");
  if (!file) {
    snprintf(error, error_size, "cannot open %s", path ? path : "(null)");
    return false;
  }
  size_t capacity = 1024;
  schedule->rows = calloc(capacity, sizeof(*schedule->rows));
  if (!schedule->rows) {
    fclose(file);
    fail(error, error_size, "out of memory");
    return false;
  }
  char line[512];
  bool header = false;
  double previous = -INFINITY;
  while (fgets(line, sizeof(line), file)) {
    char *text = trim(line);
    if (!*text || *text == '#') continue;
    if (!header) {
      header = true;
      if (strncmp(text, "time,", 5) == 0) continue;
    }
    char *fields[8] = {0};
    char *cursor = text;
    size_t field_count = 0;
    while (field_count < 8) {
      fields[field_count++] = cursor;
      char *comma = strchr(cursor, ',');
      if (!comma) break;
      *comma = '\0';
      cursor = comma + 1;
    }
    if (field_count != 5 && field_count != 8) {
      stk_schedule_free(schedule);
      fclose(file);
      fail(error, error_size, "schedule row must have 5 or 8 fields");
      return false;
    }
    if (field_count == 8 && strchr(fields[7], ',') != NULL) {
      stk_schedule_free(schedule);
      fclose(file);
      fail(error, error_size, "schedule row has too many fields");
      return false;
    }
    if (field_count == 5) {
      fields[5] = "steady";
      fields[6] = "";
      fields[7] = "";
    } else if (!*trim(fields[5])) {
      stk_schedule_free(schedule);
      fclose(file);
      fail(error, error_size, "handover phase is empty");
      return false;
    }
    if (schedule->count >= STK_SCHEDULE_MAX_ROWS) {
      stk_schedule_free(schedule);
      fclose(file);
      fail(error, error_size, "schedule has too many rows");
      return false;
    }
    double time = 0.0, elevation = 0.0, visible = 0.0, switched = 0.0;
    if (!finite_number(trim(fields[0]), &time) ||
        !finite_number(trim(fields[2]), &elevation) ||
        !finite_number(trim(fields[3]), &visible) ||
        !finite_number(trim(fields[4]), &switched) || time < previous ||
        !*trim(fields[1])) {
      stk_schedule_free(schedule);
      fclose(file);
      fail(error, error_size, "invalid schedule values");
      return false;
    }
    if (schedule->count == capacity) {
      capacity *= 2;
      stk_schedule_entry *grown = realloc(schedule->rows,
                                           capacity * sizeof(*grown));
      if (!grown) {
        stk_schedule_free(schedule);
        fclose(file);
        fail(error, error_size, "out of memory");
        return false;
      }
      schedule->rows = grown;
    }
    stk_schedule_entry *row = &schedule->rows[schedule->count++];
    row->time = time;
    row->elevation_deg = elevation;
    row->visible = visible != 0.0;
    row->switched = switched != 0.0;
    snprintf(row->satellite_id, sizeof(row->satellite_id), "%s", trim(fields[1]));
    snprintf(row->handover_phase, sizeof(row->handover_phase), "%s", trim(fields[5]));
    snprintf(row->previous_satellite_id, sizeof(row->previous_satellite_id), "%s", trim(fields[6]));
    snprintf(row->next_satellite_id, sizeof(row->next_satellite_id), "%s", trim(fields[7]));
    previous = time;
  }
  fclose(file);
  if (schedule->count == 0) {
    stk_schedule_free(schedule);
    fail(error, error_size, "schedule is empty");
    return false;
  }
  return true;
}

bool stk_schedule_at(const stk_schedule *schedule, double time,
                     stk_schedule_entry *entry)
{
  if (!schedule || !schedule->count || !entry || !isfinite(time)) return false;
  size_t lo = 0, hi = schedule->count;
  while (lo < hi) {
    size_t mid = lo + (hi - lo) / 2;
    if (schedule->rows[mid].time <= time) lo = mid + 1;
    else hi = mid;
  }
  size_t index = lo ? lo - 1 : 0;
  *entry = schedule->rows[index];
  return true;
}

void stk_schedule_free(stk_schedule *schedule)
{
  if (!schedule) return;
  free(schedule->rows);
  schedule->rows = NULL;
  schedule->count = 0;
}
