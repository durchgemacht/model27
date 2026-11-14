/* The host test's stand-ins for the OS (test_perform.c), included by perform.c when PK_HOST is defined.
 * License: MIT (LICENSE next to this file). */
#ifndef PK_HOST_OS_H
#define PK_HOST_OS_H
#include <stdint.h>

extern pk_t pk_data;
extern volatile uint8_t pk_held;
extern uint8_t host_kits[];
extern uint8_t *host_play_kit;
extern uint32_t host_key_held, host_pattern, host_masked;
extern uint8_t host_project[];

typedef struct { uint32_t pad[3], code, flags; } host_event;   /* +12 the key's code, +16 its flags */

#define KIT(n) (host_kits + KIT_SIZE * (n))
#define KEY_HELD(k) ((k) == 13u && host_key_held)
#define SEQ_STATE() ((void *)0)
#define PLAYING_PATTERN(s) ((void)(s), host_pattern)
#define PROJECT() (host_project)
#define PLAY_KIT host_play_kit
void host_kit_changed(uint8_t *obj, uint32_t n, uint32_t info);
void host_audio_kit(uint8_t *kit);
#define KIT_CHANGED host_kit_changed
#define AUDIO_KIT host_audio_kit
uint32_t host_temp_save(uint8_t *project, uint32_t temp, uint32_t n);
#define TEMP_KIT_SAVE host_temp_save
void popup(const char *text);
#define IS_PRESS(e) ((((host_event *)(e))->flags & 1u) && !(((host_event *)(e))->flags & 8u))
#define IS_RELEASE(e) (!(((host_event *)(e))->flags & 1u))
static inline uint32_t irq_off(void) { return host_masked++; }
static inline void irq_back(uint32_t sr) { host_masked = sr; }
#endif
