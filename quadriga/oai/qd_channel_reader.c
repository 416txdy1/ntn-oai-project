#define _XOPEN_SOURCE 700
#define _POSIX_C_SOURCE 200809L

#include "qd_channel_reader.h"

#include <errno.h>
#include <limits.h>
#include <math.h>
#include <openssl/evp.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

typedef enum {
  JSON_OBJECT,
  JSON_ARRAY,
  JSON_STRING,
  JSON_PRIMITIVE,
} json_type_t;

typedef struct {
  json_type_t type;
  size_t start;
  size_t end;
  int parent;
} json_token_t;

typedef struct {
  const char *text;
  size_t length;
  size_t position;
  json_token_t *tokens;
  size_t count;
  size_t capacity;
} json_parser_t;

typedef struct {
  char path[PATH_MAX];
  char dtype[32];
  size_t count;
  size_t bytes;
  char sha256[65];
} qd_file_spec_t;

static int fail(char *error, size_t error_size, const char *format, ...)
{
  if (error != NULL && error_size > 0) {
    va_list arguments;
    va_start(arguments, format);
    vsnprintf(error, error_size, format, arguments);
    va_end(arguments);
  }
  return 0;
}

static void skip_space(json_parser_t *parser)
{
  while (parser->position < parser->length) {
    const char value = parser->text[parser->position];
    if (value != ' ' && value != '\t' && value != '\r' && value != '\n')
      return;
    parser->position++;
  }
}

static int add_token(json_parser_t *parser, json_type_t type, size_t start, int parent)
{
  if (parser->count == parser->capacity)
    return -1;
  const int index = (int)parser->count++;
  parser->tokens[index] = (json_token_t){.type = type, .start = start, .end = start, .parent = parent};
  return index;
}

static int parse_json_value(json_parser_t *parser, int parent);

static int parse_json_string(json_parser_t *parser, int parent)
{
  if (parser->position >= parser->length || parser->text[parser->position] != '"')
    return -1;
  parser->position++;
  const size_t start = parser->position;
  const int token = add_token(parser, JSON_STRING, start, parent);
  if (token < 0)
    return -1;
  while (parser->position < parser->length) {
    const unsigned char value = (unsigned char)parser->text[parser->position++];
    if (value == '"') {
      parser->tokens[token].end = parser->position - 1;
      return token;
    }
    if (value < 0x20)
      return -1;
    if (value == '\\') {
      if (parser->position >= parser->length)
        return -1;
      const char escaped = parser->text[parser->position++];
      if (strchr("\"\\/bfnrt", escaped) != NULL)
        continue;
      if (escaped != 'u' || parser->position + 4 > parser->length)
        return -1;
      for (int index = 0; index < 4; index++) {
        const char hex = parser->text[parser->position++];
        if (!((hex >= '0' && hex <= '9') || (hex >= 'a' && hex <= 'f') || (hex >= 'A' && hex <= 'F')))
          return -1;
      }
    }
  }
  return -1;
}

static int parse_json_primitive(json_parser_t *parser, int parent)
{
  const size_t start = parser->position;
  while (parser->position < parser->length) {
    const char value = parser->text[parser->position];
    if (value == ',' || value == ']' || value == '}' || value == ' ' || value == '\t' || value == '\r' || value == '\n')
      break;
    if ((unsigned char)value < 0x20)
      return -1;
    parser->position++;
  }
  if (parser->position == start)
    return -1;
  const int token = add_token(parser, JSON_PRIMITIVE, start, parent);
  if (token >= 0)
    parser->tokens[token].end = parser->position;
  return token;
}

static int parse_json_object(json_parser_t *parser, int parent)
{
  const int object = add_token(parser, JSON_OBJECT, parser->position++, parent);
  if (object < 0)
    return -1;
  skip_space(parser);
  if (parser->position < parser->length && parser->text[parser->position] == '}') {
    parser->tokens[object].end = ++parser->position;
    return object;
  }
  for (;;) {
    skip_space(parser);
    if (parse_json_string(parser, object) < 0)
      return -1;
    skip_space(parser);
    if (parser->position >= parser->length || parser->text[parser->position++] != ':')
      return -1;
    skip_space(parser);
    if (parse_json_value(parser, object) < 0)
      return -1;
    skip_space(parser);
    if (parser->position >= parser->length)
      return -1;
    const char separator = parser->text[parser->position++];
    if (separator == '}') {
      parser->tokens[object].end = parser->position;
      return object;
    }
    if (separator != ',')
      return -1;
  }
}

static int parse_json_array(json_parser_t *parser, int parent)
{
  const int array = add_token(parser, JSON_ARRAY, parser->position++, parent);
  if (array < 0)
    return -1;
  skip_space(parser);
  if (parser->position < parser->length && parser->text[parser->position] == ']') {
    parser->tokens[array].end = ++parser->position;
    return array;
  }
  for (;;) {
    skip_space(parser);
    if (parse_json_value(parser, array) < 0)
      return -1;
    skip_space(parser);
    if (parser->position >= parser->length)
      return -1;
    const char separator = parser->text[parser->position++];
    if (separator == ']') {
      parser->tokens[array].end = parser->position;
      return array;
    }
    if (separator != ',')
      return -1;
  }
}

static int parse_json_value(json_parser_t *parser, int parent)
{
  skip_space(parser);
  if (parser->position >= parser->length)
    return -1;
  switch (parser->text[parser->position]) {
    case '{': return parse_json_object(parser, parent);
    case '[': return parse_json_array(parser, parent);
    case '"': return parse_json_string(parser, parent);
    default: return parse_json_primitive(parser, parent);
  }
}

static int parse_json(const char *text, size_t length, json_token_t **tokens_out, size_t *count_out)
{
  const size_t capacity = length / 2 + 32;
  json_token_t *tokens = calloc(capacity, sizeof(*tokens));
  if (tokens == NULL)
    return 0;
  json_parser_t parser = {
      .text = text,
      .length = length,
      .tokens = tokens,
      .capacity = capacity,
  };
  const int root = parse_json_value(&parser, -1);
  skip_space(&parser);
  if (root != 0 || parser.position != length || tokens[0].type != JSON_OBJECT) {
    free(tokens);
    return 0;
  }
  *tokens_out = tokens;
  *count_out = parser.count;
  return 1;
}

static size_t token_after(const json_token_t *tokens, size_t count, size_t token)
{
  size_t next = token + 1;
  while (next < count && tokens[next].start < tokens[token].end)
    next++;
  return next;
}

static int token_equals(const char *text, const json_token_t *token, const char *expected)
{
  const size_t length = token->end - token->start;
  return token->type == JSON_STRING && strlen(expected) == length
         && memcmp(text + token->start, expected, length) == 0;
}

static int object_get(const char *text,
                      const json_token_t *tokens,
                      size_t count,
                      int object,
                      const char *key)
{
  if (object < 0 || tokens[object].type != JSON_OBJECT)
    return -1;
  size_t current = (size_t)object + 1;
  while (current < count && tokens[current].start < tokens[object].end) {
    if (tokens[current].parent != object || tokens[current].type != JSON_STRING || current + 1 >= count)
      return -1;
    const size_t value = current + 1;
    if (tokens[value].parent != object)
      return -1;
    if (token_equals(text, &tokens[current], key))
      return (int)value;
    current = token_after(tokens, count, value);
  }
  return -1;
}

static size_t object_size(const json_token_t *tokens, size_t count, int object)
{
  size_t pairs = 0;
  size_t current = (size_t)object + 1;
  while (current < count && tokens[current].start < tokens[object].end) {
    if (tokens[current].parent != object || current + 1 >= count)
      return SIZE_MAX;
    current = token_after(tokens, count, current + 1);
    pairs++;
  }
  return pairs;
}

static int array_item(const json_token_t *tokens, size_t count, int array, size_t wanted)
{
  if (array < 0 || tokens[array].type != JSON_ARRAY)
    return -1;
  size_t item = 0;
  size_t current = (size_t)array + 1;
  while (current < count && tokens[current].start < tokens[array].end) {
    if (tokens[current].parent != array)
      return -1;
    if (item++ == wanted)
      return (int)current;
    current = token_after(tokens, count, current);
  }
  return -1;
}

static size_t array_size(const json_token_t *tokens, size_t count, int array)
{
  size_t items = 0;
  while (array_item(tokens, count, array, items) >= 0)
    items++;
  return items;
}

static int token_string(const char *text, const json_token_t *token, char *output, size_t output_size)
{
  if (token->type != JSON_STRING)
    return 0;
  const size_t length = token->end - token->start;
  if (length + 1 > output_size || memchr(text + token->start, '\\', length) != NULL)
    return 0;
  memcpy(output, text + token->start, length);
  output[length] = '\0';
  return 1;
}

static int token_size_value(const char *text, const json_token_t *token, size_t *output)
{
  if (token->type != JSON_PRIMITIVE || token->end - token->start >= 64)
    return 0;
  char buffer[64];
  const size_t length = token->end - token->start;
  memcpy(buffer, text + token->start, length);
  buffer[length] = '\0';
  if (length == 0 || (length > 1 && buffer[0] == '0'))
    return 0;
  for (size_t index = 0; index < length; index++)
    if (buffer[index] < '0' || buffer[index] > '9')
      return 0;
  errno = 0;
  char *end = NULL;
  const unsigned long long value = strtoull(buffer, &end, 10);
  if (errno != 0 || end == buffer || *end != '\0' || value > SIZE_MAX)
    return 0;
  *output = (size_t)value;
  return 1;
}

static int valid_json_number(const char *value, size_t length)
{
  size_t index = 0;
  if (index < length && value[index] == '-')
    index++;
  if (index >= length)
    return 0;
  if (value[index] == '0') {
    index++;
  } else {
    if (value[index] < '1' || value[index] > '9')
      return 0;
    while (index < length && value[index] >= '0' && value[index] <= '9')
      index++;
  }
  if (index < length && value[index] == '.') {
    index++;
    const size_t digits = index;
    while (index < length && value[index] >= '0' && value[index] <= '9')
      index++;
    if (index == digits)
      return 0;
  }
  if (index < length && (value[index] == 'e' || value[index] == 'E')) {
    index++;
    if (index < length && (value[index] == '+' || value[index] == '-'))
      index++;
    const size_t digits = index;
    while (index < length && value[index] >= '0' && value[index] <= '9')
      index++;
    if (index == digits)
      return 0;
  }
  return index == length;
}

static int token_double_value(const char *text, const json_token_t *token, double *output)
{
  if (token->type != JSON_PRIMITIVE || token->end - token->start >= 128)
    return 0;
  char buffer[128];
  const size_t length = token->end - token->start;
  if (!valid_json_number(text + token->start, length))
    return 0;
  memcpy(buffer, text + token->start, length);
  buffer[length] = '\0';
  errno = 0;
  char *end = NULL;
  const double value = strtod(buffer, &end);
  if (errno != 0 || end == buffer || *end != '\0' || !isfinite(value))
    return 0;
  *output = value;
  return 1;
}

static int valid_sha256(const char *value)
{
  if (value == NULL || strlen(value) != 64)
    return 0;
  for (size_t index = 0; index < 64; index++)
    if (!((value[index] >= '0' && value[index] <= '9') || (value[index] >= 'a' && value[index] <= 'f')))
      return 0;
  return 1;
}

static int safe_multiply(size_t left, size_t right, size_t *output)
{
  if (left != 0 && right > SIZE_MAX / left)
    return 0;
  *output = left * right;
  return 1;
}

static int safe_relative_path(const char *path)
{
  if (path == NULL || path[0] == '\0' || path[0] == '/' || path[0] == '\\' || strchr(path, ':') != NULL
      || strchr(path, '\\') != NULL)
    return 0;
  const char *segment = path;
  for (const char *cursor = path;; cursor++) {
    if (*cursor == '/' || *cursor == '\0') {
      const size_t length = (size_t)(cursor - segment);
      if (length == 0 || (length == 1 && segment[0] == '.')
          || (length == 2 && segment[0] == '.' && segment[1] == '.'))
        return 0;
      if (*cursor == '\0')
        return 1;
      segment = cursor + 1;
    }
  }
}

static int join_path(char *output, size_t output_size, const char *root, const char *relative)
{
  if (!safe_relative_path(relative))
    return 0;
  const int written = snprintf(output, output_size, "%s/%s", root, relative);
  return written > 0 && (size_t)written < output_size;
}

static int read_whole_file(const char *path, unsigned char **data, size_t *size, char *error, size_t error_size)
{
  struct stat status;
  if (stat(path, &status) != 0)
    return fail(error, error_size, "cannot stat %s: %s", path, strerror(errno));
  if (status.st_size < 0 || (uintmax_t)status.st_size > SIZE_MAX)
    return fail(error, error_size, "invalid file size: %s", path);
  const size_t length = (size_t)status.st_size;
  FILE *stream = fopen(path, "rb");
  if (stream == NULL)
    return fail(error, error_size, "cannot open %s: %s", path, strerror(errno));
  unsigned char *buffer = malloc(length == 0 ? 1 : length);
  if (buffer == NULL) {
    fclose(stream);
    return fail(error, error_size, "out of memory reading %s", path);
  }
  const size_t read = fread(buffer, 1, length, stream);
  const int extra = fgetc(stream);
  const int close_result = fclose(stream);
  if (read != length || extra != EOF || close_result != 0) {
    free(buffer);
    return fail(error, error_size, "incomplete read: %s", path);
  }
  *data = buffer;
  *size = length;
  return 1;
}

static int sha256_bytes(const unsigned char *data,
                        size_t size,
                        char output[65],
                        char *error,
                        size_t error_size)
{
  EVP_MD_CTX *context = EVP_MD_CTX_new();
  if (context == NULL || EVP_DigestInit_ex(context, EVP_sha256(), NULL) != 1) {
    EVP_MD_CTX_free(context);
    return fail(error, error_size, "cannot initialize SHA256");
  }
  if (EVP_DigestUpdate(context, data, size) != 1) {
    EVP_MD_CTX_free(context);
    return fail(error, error_size, "SHA256 update failed");
  }
  unsigned char digest[EVP_MAX_MD_SIZE];
  unsigned int digest_size = 0;
  if (EVP_DigestFinal_ex(context, digest, &digest_size) != 1 || digest_size != 32) {
    EVP_MD_CTX_free(context);
    return fail(error, error_size, "SHA256 finalize failed");
  }
  EVP_MD_CTX_free(context);
  for (size_t index = 0; index < 32; index++)
    snprintf(output + index * 2, 3, "%02x", digest[index]);
  output[64] = '\0';
  return 1;
}

static int require_object_fields(const char *text,
                                 const json_token_t *tokens,
                                 size_t token_count,
                                 int object,
                                 const char *const *fields,
                                 size_t field_count,
                                 char *error,
                                 size_t error_size)
{
  if (object < 0 || tokens[object].type != JSON_OBJECT || object_size(tokens, token_count, object) != field_count)
    return fail(error, error_size, "manifest object has unexpected fields");
  for (size_t index = 0; index < field_count; index++)
    if (object_get(text, tokens, token_count, object, fields[index]) < 0)
      return fail(error, error_size, "manifest missing field: %s", fields[index]);
  return 1;
}

static int require_string(const char *text,
                          const json_token_t *tokens,
                          int token,
                          const char *expected,
                          char *error,
                          size_t error_size)
{
  if (token < 0 || !token_equals(text, &tokens[token], expected))
    return fail(error, error_size, "manifest value must be %s", expected);
  return 1;
}

static int read_file_spec(const char *text,
                          const json_token_t *tokens,
                          size_t token_count,
                          int object,
                          const char *expected_dtype,
                          size_t expected_count,
                          size_t expected_bytes,
                          qd_file_spec_t *spec,
                          char *error,
                          size_t error_size)
{
  static const char *const fields[] = {"path", "dtype", "count", "bytes", "sha256"};
  if (!require_object_fields(text, tokens, token_count, object, fields, 5, error, error_size))
    return 0;
  const int path = object_get(text, tokens, token_count, object, "path");
  const int dtype = object_get(text, tokens, token_count, object, "dtype");
  const int count = object_get(text, tokens, token_count, object, "count");
  const int bytes = object_get(text, tokens, token_count, object, "bytes");
  const int sha256 = object_get(text, tokens, token_count, object, "sha256");
  if (!token_string(text, &tokens[path], spec->path, sizeof(spec->path)) || !safe_relative_path(spec->path))
    return fail(error, error_size, "unsafe or invalid bundle file path");
  if (!token_string(text, &tokens[dtype], spec->dtype, sizeof(spec->dtype))
      || strcmp(spec->dtype, expected_dtype) != 0)
    return fail(error, error_size, "bundle file dtype mismatch for %s", spec->path);
  if (!token_size_value(text, &tokens[count], &spec->count) || spec->count != expected_count)
    return fail(error, error_size, "bundle file count mismatch for %s", spec->path);
  if (!token_size_value(text, &tokens[bytes], &spec->bytes) || spec->bytes != expected_bytes)
    return fail(error, error_size, "bundle file byte count mismatch for %s", spec->path);
  if (!token_string(text, &tokens[sha256], spec->sha256, sizeof(spec->sha256)) || !valid_sha256(spec->sha256))
    return fail(error, error_size, "invalid SHA256 for %s", spec->path);
  return 1;
}

enum {
  QD_TIMES,
  QD_DELAYS,
  QD_COEFFICIENTS,
  QD_RESIDUAL_GAIN,
  QD_FILE_COUNT,
};

static int parse_manifest(const char *text,
                          size_t text_size,
                          qd_channel_t *channel,
                          qd_file_spec_t specs[QD_FILE_COUNT],
                          char *error,
                          size_t error_size)
{
  json_token_t *tokens = NULL;
  size_t token_count = 0;
  if (!parse_json(text, text_size, &tokens, &token_count))
    return fail(error, error_size, "manifest is not valid JSON");

  int result = 0;
  static const char *const top_fields[] = {
      "format", "schema_version", "byte_order", "axes", "dimensions",
      "radio", "time", "composition", "provenance", "files",
  };
  if (!require_object_fields(text, tokens, token_count, 0, top_fields, 10, error, error_size))
    goto done;
  if (!require_string(text, tokens, object_get(text, tokens, token_count, 0, "format"), "QDCHANNEL1", error, error_size)
      || !require_string(text, tokens, object_get(text, tokens, token_count, 0, "byte_order"), "little", error, error_size))
    goto done;

  size_t schema_version = 0;
  const int schema_token = object_get(text, tokens, token_count, 0, "schema_version");
  if (!token_size_value(text, &tokens[schema_token], &schema_version) || schema_version != 1) {
    fail(error, error_size, "schema_version must be 1");
    goto done;
  }

  const int axes = object_get(text, tokens, token_count, 0, "axes");
  static const char *const expected_axes[] = {"snapshot", "rx", "tx", "path"};
  if (axes < 0 || tokens[axes].type != JSON_ARRAY || array_size(tokens, token_count, axes) != 4) {
    fail(error, error_size, "axes must have four entries");
    goto done;
  }
  for (size_t index = 0; index < 4; index++) {
    const int item = array_item(tokens, token_count, axes, index);
    if (item < 0 || !token_equals(text, &tokens[item], expected_axes[index])) {
      fail(error, error_size, "axes order mismatch");
      goto done;
    }
  }

  const int dimensions = object_get(text, tokens, token_count, 0, "dimensions");
  static const char *const dimension_fields[] = {"snapshots", "rx_antennas", "tx_antennas", "paths"};
  if (!require_object_fields(text, tokens, token_count, dimensions, dimension_fields, 4, error, error_size))
    goto done;
  const char *const dimension_names[] = {"snapshots", "rx_antennas", "tx_antennas", "paths"};
  size_t *const dimension_values[] = {
      &channel->snapshots, &channel->rx_antennas, &channel->tx_antennas, &channel->paths,
  };
  for (size_t index = 0; index < 4; index++) {
    const int token = object_get(text, tokens, token_count, dimensions, dimension_names[index]);
    if (!token_size_value(text, &tokens[token], dimension_values[index]) || *dimension_values[index] < 1
        || (index == 0 && *dimension_values[index] < 2)) {
      fail(error, error_size, "invalid dimension: %s", dimension_names[index]);
      goto done;
    }
  }

  size_t links_per_snapshot = 0;
  size_t links = 0;
  size_t taps = 0;
  if (!safe_multiply(channel->rx_antennas, channel->tx_antennas, &links_per_snapshot)
      || !safe_multiply(channel->snapshots, links_per_snapshot, &links)
      || !safe_multiply(links, channel->paths, &taps)) {
    fail(error, error_size, "bundle dimensions overflow size_t");
    goto done;
  }

  const int radio = object_get(text, tokens, token_count, 0, "radio");
  static const char *const radio_fields[] = {"center_frequency_hz", "link_direction"};
  if (!require_object_fields(text, tokens, token_count, radio, radio_fields, 2, error, error_size))
    goto done;
  const int frequency = object_get(text, tokens, token_count, radio, "center_frequency_hz");
  const int direction = object_get(text, tokens, token_count, radio, "link_direction");
  if (!token_double_value(text, &tokens[frequency], &channel->center_frequency_hz)
      || channel->center_frequency_hz <= 0.0) {
    fail(error, error_size, "center_frequency_hz must be positive and finite");
    goto done;
  }
  if (!token_string(text, &tokens[direction], channel->link_direction, sizeof(channel->link_direction))
      || (strcmp(channel->link_direction, "downlink") != 0 && strcmp(channel->link_direction, "uplink") != 0)) {
    fail(error, error_size, "link_direction must be downlink or uplink");
    goto done;
  }

  const int time = object_get(text, tokens, token_count, 0, "time");
  static const char *const time_fields[] = {"coordinate", "interpolation", "out_of_range"};
  if (!require_object_fields(text, tokens, token_count, time, time_fields, 3, error, error_size)
      || !require_string(text, tokens, object_get(text, tokens, token_count, time, "coordinate"), "stk_trace_seconds", error, error_size)
      || !require_string(text, tokens, object_get(text, tokens, token_count, time, "interpolation"), "linear_complex_and_delay", error, error_size)
      || !require_string(text, tokens, object_get(text, tokens, token_count, time, "out_of_range"), "mute", error, error_size))
    goto done;

  const int composition = object_get(text, tokens, token_count, 0, "composition");
  static const char *const composition_fields[] = {
      "bulk_delay_source", "bulk_doppler_source", "absolute_gain_source",
      "quadriga_delay", "quadriga_coefficients", "quadriga_large_scale_gain",
  };
  static const char *const composition_values[] = {
      "STKTRACE2", "STKTRACE2", "STKTRACE2", "relative_excess_seconds",
      "unit_snapshot_link_power", "zero_mean_residual_db",
  };
  if (!require_object_fields(text, tokens, token_count, composition, composition_fields, 6, error, error_size))
    goto done;
  for (size_t index = 0; index < 6; index++)
    if (!require_string(text,
                        tokens,
                        object_get(text, tokens, token_count, composition, composition_fields[index]),
                        composition_values[index],
                        error,
                        error_size))
      goto done;

  const int provenance = object_get(text, tokens, token_count, 0, "provenance");
  static const char *const provenance_fields[] = {
      "quadriga_version", "scenario", "random_seed", "stk_trace_sha256",
  };
  if (!require_object_fields(text, tokens, token_count, provenance, provenance_fields, 4, error, error_size))
    goto done;
  char required_text[256];
  for (size_t index = 0; index < 2; index++) {
    const int token = object_get(text, tokens, token_count, provenance, provenance_fields[index]);
    if (!token_string(text, &tokens[token], required_text, sizeof(required_text)) || required_text[0] == '\0') {
      fail(error, error_size, "invalid provenance field: %s", provenance_fields[index]);
      goto done;
    }
  }
  size_t random_seed = 0;
  const int seed = object_get(text, tokens, token_count, provenance, "random_seed");
  if (!token_size_value(text, &tokens[seed], &random_seed)) {
    fail(error, error_size, "random_seed must be a non-negative integer");
    goto done;
  }
  const int trace_sha = object_get(text, tokens, token_count, provenance, "stk_trace_sha256");
  if (!token_string(text, &tokens[trace_sha], channel->stk_trace_sha256, sizeof(channel->stk_trace_sha256))
      || !valid_sha256(channel->stk_trace_sha256)) {
    fail(error, error_size, "invalid STK trace SHA256");
    goto done;
  }

  size_t delay_bytes = 0;
  size_t coefficient_bytes = 0;
  size_t gain_bytes = 0;
  size_t time_bytes = 0;
  if (!safe_multiply(channel->snapshots, sizeof(double), &time_bytes)
      || !safe_multiply(taps, sizeof(double), &delay_bytes)
      || !safe_multiply(taps, sizeof(qd_complex32_t), &coefficient_bytes)
      || !safe_multiply(links, sizeof(float), &gain_bytes)) {
    fail(error, error_size, "bundle byte counts overflow size_t");
    goto done;
  }

  const int files = object_get(text, tokens, token_count, 0, "files");
  static const char *const file_fields[] = {"times", "delays", "coefficients", "residual_gain_db"};
  if (!require_object_fields(text, tokens, token_count, files, file_fields, 4, error, error_size)
      || !read_file_spec(text, tokens, token_count, object_get(text, tokens, token_count, files, "times"),
                         "float64", channel->snapshots, time_bytes, &specs[QD_TIMES], error, error_size)
      || !read_file_spec(text, tokens, token_count, object_get(text, tokens, token_count, files, "delays"),
                         "float64", taps, delay_bytes, &specs[QD_DELAYS], error, error_size)
      || !read_file_spec(text, tokens, token_count, object_get(text, tokens, token_count, files, "coefficients"),
                         "complex64_interleaved", taps, coefficient_bytes, &specs[QD_COEFFICIENTS], error, error_size)
      || !read_file_spec(text, tokens, token_count, object_get(text, tokens, token_count, files, "residual_gain_db"),
                         "float32", links, gain_bytes, &specs[QD_RESIDUAL_GAIN], error, error_size))
    goto done;

  result = 1;
done:
  free(tokens);
  return result;
}

static int resolve_bundle_file(const char *bundle_dir,
                               const char *relative,
                               char output[PATH_MAX],
                               char *error,
                               size_t error_size)
{
  char root[PATH_MAX];
  char candidate[PATH_MAX];
  if (realpath(bundle_dir, root) == NULL)
    return fail(error, error_size, "cannot resolve bundle directory: %s", strerror(errno));
  if (!join_path(candidate, sizeof(candidate), root, relative))
    return fail(error, error_size, "bundle path is too long or unsafe: %s", relative);
  if (realpath(candidate, output) == NULL)
    return fail(error, error_size, "cannot resolve bundle file %s: %s", relative, strerror(errno));
  const size_t root_length = strlen(root);
  if (strncmp(output, root, root_length) != 0 || output[root_length] != '/')
    return fail(error, error_size, "bundle file escapes root: %s", relative);
  return 1;
}

static int load_bundle_file(const char *bundle_dir,
                            const qd_file_spec_t *spec,
                            void **data,
                            char *error,
                            size_t error_size)
{
  char path[PATH_MAX];
  if (!resolve_bundle_file(bundle_dir, spec->path, path, error, error_size))
    return 0;
  unsigned char *payload = NULL;
  size_t payload_size = 0;
  if (!read_whole_file(path, &payload, &payload_size, error, error_size))
    return 0;
  if (payload_size != spec->bytes) {
    free(payload);
    return fail(error, error_size, "bundle file size mismatch: %s", spec->path);
  }
  char actual_sha256[65];
  if (!sha256_bytes(payload, payload_size, actual_sha256, error, error_size)) {
    free(payload);
    return 0;
  }
  if (strcmp(actual_sha256, spec->sha256) != 0) {
    free(payload);
    return fail(error, error_size, "bundle file SHA256 mismatch: %s", spec->path);
  }
  *data = payload;
  return 1;
}

static int validate_channel_data(const qd_channel_t *channel, char *error, size_t error_size)
{
  for (size_t snapshot = 0; snapshot < channel->snapshots; snapshot++) {
    const double time = channel->times_s[snapshot];
    if (!isfinite(time))
      return fail(error, error_size, "times contains a non-finite value");
    if (snapshot > 0 && !(channel->times_s[snapshot - 1] < time))
      return fail(error, error_size, "times must be strictly increasing");
  }

  const size_t links_per_snapshot = channel->rx_antennas * channel->tx_antennas;
  const size_t links = channel->snapshots * links_per_snapshot;
  for (size_t link = 0; link < links; link++) {
    const size_t start = link * channel->paths;
    double total_power = 0.0;
    double minimum_active_delay = INFINITY;
    for (size_t path = 0; path < channel->paths; path++) {
      const qd_complex32_t coefficient = channel->coefficients[start + path];
      const double delay = channel->delays_s[start + path];
      if (!isfinite(coefficient.real) || !isfinite(coefficient.imag))
        return fail(error, error_size, "coefficients contains a non-finite value");
      if (!isfinite(delay) || delay < 0.0)
        return fail(error, error_size, "delays must be finite and non-negative");
      const double power = (double)coefficient.real * coefficient.real + (double)coefficient.imag * coefficient.imag;
      total_power += power;
      if (power > 1e-12 && delay < minimum_active_delay)
        minimum_active_delay = delay;
    }
    if (fabs(total_power - 1.0) > 1e-5)
      return fail(error, error_size, "link %zu path power is not normalized", link);
    if (!isfinite(minimum_active_delay) || minimum_active_delay > 1e-12)
      return fail(error, error_size, "link %zu has no zero-reference active path", link);
  }

  for (size_t antenna_link = 0; antenna_link < links_per_snapshot; antenna_link++) {
    double sum = 0.0;
    for (size_t snapshot = 0; snapshot < channel->snapshots; snapshot++) {
      const float gain = channel->residual_gain_db[snapshot * links_per_snapshot + antenna_link];
      if (!isfinite(gain))
        return fail(error, error_size, "residual_gain_db contains a non-finite value");
      sum += gain;
    }
    if (fabs(sum / (double)channel->snapshots) > 1e-3)
      return fail(error, error_size, "antenna link %zu residual gain mean is not zero", antenna_link);
  }
  return 1;
}

void qd_channel_free(qd_channel_t *channel)
{
  if (channel == NULL)
    return;
  free(channel->times_s);
  free(channel->delays_s);
  free(channel->coefficients);
  free(channel->residual_gain_db);
  *channel = (qd_channel_t){0};
}

int qd_channel_load(const char *bundle_dir,
                    const char *expected_stk_trace_sha256,
                    qd_channel_t *channel,
                    char *error,
                    size_t error_size)
{
  if (error != NULL && error_size > 0)
    error[0] = '\0';
  if (bundle_dir == NULL || channel == NULL)
    return fail(error, error_size, "bundle_dir and channel are required");
  *channel = (qd_channel_t){0};
  if (sizeof(float) != 4 || sizeof(double) != 8 || sizeof(qd_complex32_t) != 8)
    return fail(error, error_size, "QDCHANNEL1 requires IEEE float32/float64 sizes");
  const uint16_t endian_probe = 1;
  if (*(const unsigned char *)&endian_probe != 1)
    return fail(error, error_size, "QDCHANNEL1 v1 requires a little-endian host");

  char manifest_path[PATH_MAX];
  if (!join_path(manifest_path, sizeof(manifest_path), bundle_dir, "manifest.json"))
    return fail(error, error_size, "bundle manifest path is too long");
  unsigned char *manifest = NULL;
  size_t manifest_size = 0;
  if (!read_whole_file(manifest_path, &manifest, &manifest_size, error, error_size))
    return 0;
  if (manifest_size == 0 || manifest_size > 4 * 1024 * 1024) {
    free(manifest);
    return fail(error, error_size, "manifest size must be between 1 byte and 4 MiB");
  }

  qd_file_spec_t specs[QD_FILE_COUNT] = {0};
  if (!parse_manifest((const char *)manifest, manifest_size, channel, specs, error, error_size)) {
    free(manifest);
    qd_channel_free(channel);
    return 0;
  }
  free(manifest);

  if (expected_stk_trace_sha256 != NULL
      && (!valid_sha256(expected_stk_trace_sha256)
          || strcmp(expected_stk_trace_sha256, channel->stk_trace_sha256) != 0)) {
    qd_channel_free(channel);
    return fail(error, error_size, "STK trace SHA256 does not match bundle provenance");
  }
  for (size_t left = 0; left < QD_FILE_COUNT; left++)
    for (size_t right = left + 1; right < QD_FILE_COUNT; right++)
      if (strcmp(specs[left].path, specs[right].path) == 0) {
        qd_channel_free(channel);
        return fail(error, error_size, "bundle arrays must use distinct files");
      }

  if (!load_bundle_file(bundle_dir, &specs[QD_TIMES], (void **)&channel->times_s, error, error_size)
      || !load_bundle_file(bundle_dir, &specs[QD_DELAYS], (void **)&channel->delays_s, error, error_size)
      || !load_bundle_file(bundle_dir, &specs[QD_COEFFICIENTS], (void **)&channel->coefficients, error, error_size)
      || !load_bundle_file(bundle_dir, &specs[QD_RESIDUAL_GAIN], (void **)&channel->residual_gain_db, error, error_size)
      || !validate_channel_data(channel, error, error_size)) {
    qd_channel_free(channel);
    return 0;
  }
  return 1;
}

qd_channel_status_t qd_channel_sample(const qd_channel_t *channel,
                                      double trace_time_s,
                                      size_t rx,
                                      size_t tx,
                                      qd_complex32_t *coefficients_out,
                                      double *delays_out,
                                      float *residual_gain_db_out,
                                      char *error,
                                      size_t error_size)
{
  if (error != NULL && error_size > 0)
    error[0] = '\0';
  if (channel == NULL || channel->times_s == NULL || channel->coefficients == NULL
      || channel->delays_s == NULL || channel->residual_gain_db == NULL
      || coefficients_out == NULL || delays_out == NULL || residual_gain_db_out == NULL) {
    fail(error, error_size, "loaded channel and output buffers are required");
    return QD_CHANNEL_ERROR;
  }
  if (!isfinite(trace_time_s)) {
    fail(error, error_size, "trace_time_s must be finite");
    return QD_CHANNEL_ERROR;
  }
  if (rx >= channel->rx_antennas || tx >= channel->tx_antennas) {
    fail(error, error_size, "antenna index is out of range");
    return QD_CHANNEL_ERROR;
  }

  if (trace_time_s < channel->times_s[0] || trace_time_s > channel->times_s[channel->snapshots - 1]) {
    memset(coefficients_out, 0, channel->paths * sizeof(*coefficients_out));
    memset(delays_out, 0, channel->paths * sizeof(*delays_out));
    *residual_gain_db_out = 0.0f;
    return QD_CHANNEL_MUTED;
  }

  size_t lower = 0;
  size_t upper = channel->snapshots - 1;
  while (upper - lower > 1) {
    const size_t middle = lower + (upper - lower) / 2;
    if (channel->times_s[middle] <= trace_time_s)
      lower = middle;
    else
      upper = middle;
  }
  if (trace_time_s == channel->times_s[channel->snapshots - 1])
    lower = upper = channel->snapshots - 1;
  else if (trace_time_s == channel->times_s[lower])
    upper = lower;

  double weight = 0.0;
  if (upper != lower)
    weight = (trace_time_s - channel->times_s[lower]) / (channel->times_s[upper] - channel->times_s[lower]);
  const double inverse = 1.0 - weight;
  const size_t links_per_snapshot = channel->rx_antennas * channel->tx_antennas;
  const size_t antenna_link = rx * channel->tx_antennas + tx;
  const size_t lower_link = lower * links_per_snapshot + antenna_link;
  const size_t upper_link = upper * links_per_snapshot + antenna_link;
  const size_t lower_start = lower_link * channel->paths;
  const size_t upper_start = upper_link * channel->paths;

  for (size_t path = 0; path < channel->paths; path++) {
    const qd_complex32_t left = channel->coefficients[lower_start + path];
    const qd_complex32_t right = channel->coefficients[upper_start + path];
    coefficients_out[path].real = (float)(inverse * left.real + weight * right.real);
    coefficients_out[path].imag = (float)(inverse * left.imag + weight * right.imag);
    delays_out[path] = inverse * channel->delays_s[lower_start + path]
                       + weight * channel->delays_s[upper_start + path];
  }
  *residual_gain_db_out = (float)(inverse * channel->residual_gain_db[lower_link]
                                  + weight * channel->residual_gain_db[upper_link]);
  return QD_CHANNEL_OK;
}
