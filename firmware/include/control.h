/* SPDX-License-Identifier: Apache-2.0 */
#ifndef OEE_CONTROL_H
#define OEE_CONTROL_H
#include <stdint.h>
typedef enum {STANDBY, CALIBRATING, RUN, FAULT, ESTOP} State;
typedef enum {F_NONE, F_ESTOP, F_SENSOR, F_RANGE, F_CURRENT, F_TEMPERATURE, F_HEARTBEAT, F_SPEED, F_VOLTAGE, F_LIMIT} Fault;
typedef struct {
    float q, dq, current, temperature, voltage;
    int sensor_ok, estop_ok, limit_min_ok, limit_max_ok, reset_button;
} Sensors;
typedef struct {
    State state; Fault fault;
    uint32_t now_ms, heartbeat_ms, cal_start_ms, peak_ms, recovery_ms;
    float offset, q, target, reference, reference_velocity, assist, torque, duty, integral;
    float kp, kd, torque_max, velocity_max;
    int enabled, calibrated, hb_seen, torque_mode, reset_latched, reset_previous;
    Sensors sensors;
} Controller;
void control_init(Controller *c);
void control_tick(Controller *c, const Sensors *s, uint32_t now_ms);
const char *control_command(Controller *c, const char *op, float value);
const char *state_name(State s);
const char *fault_name(Fault f);
#endif
