/* SPDX-License-Identifier: Apache-2.0 */
#ifndef OEE_PROTOCOL_H
#define OEE_PROTOCOL_H
#include <stdint.h>
#include <stddef.h>
#include "control.h"
#define PROTOCOL_MAX_LINE 96
typedef struct {char line[PROTOCOL_MAX_LINE]; unsigned length; int dropping, sequence_seen; uint16_t last_sequence; uint32_t malformed, replay;} Protocol;
typedef void (*Emit)(const char *bytes, size_t length, void *context);
uint16_t protocol_crc(const char *data, size_t length);
void protocol_init(Protocol *p);
void protocol_feed(Protocol *p, Controller *c, unsigned char byte, Emit emit, void *context);
void protocol_status(const Controller *c, Emit emit, void *context);
void protocol_frame(const char *payload, Emit emit, void *context);
#endif
