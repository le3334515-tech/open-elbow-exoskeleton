/* SPDX-License-Identifier: Apache-2.0 */
#include "control.h"
#include "config_generated.h"
#include <string.h>
static float absolute(float x) {return x < 0 ? -x : x;}
static float clamp(float x,float lo,float hi) {return x<lo?lo:(x>hi?hi:x);}
static int finite_value(float x) {return x >= -3.4e38f && x <= 3.4e38f;}
const char *state_name(State s) {static const char *n[]={"STANDBY","CALIBRATING","RUN","FAULT","ESTOP"};return n[(unsigned)s<5?(unsigned)s:3];}
const char *fault_name(Fault f) {static const char *n[]={"NONE","ESTOP","SENSOR","RANGE","CURRENT","TEMPERATURE","HEARTBEAT","SPEED","VOLTAGE","LIMIT"};return n[(unsigned)f<10?(unsigned)f:2];}
static void off(Controller *c) {c->enabled=0;c->duty=0;c->torque=0;c->integral=0;c->reference_velocity=0;}
static void trip(Controller *c,Fault f) {if(c->state!=FAULT && c->state!=ESTOP){c->fault=f;c->state=f==F_ESTOP?ESTOP:FAULT;c->reset_latched=0;c->calibrated=0;}off(c);}
void control_init(Controller *c) {
    memset(c,0,sizeof(*c)); c->state=STANDBY;c->kp=CFG_KP;c->kd=CFG_KD;c->torque_max=CFG_T_PEAK;c->velocity_max=CFG_V_MAX;
}
static Fault physical_fault(const Controller *c,const Sensors *s) {
    if(!s->estop_ok)return F_ESTOP;
    if(!s->sensor_ok || !finite_value(s->q)||!finite_value(s->dq)||!finite_value(s->current)||!finite_value(s->temperature)||!finite_value(s->voltage))return F_SENSOR;
    if(s->voltage<CFG_VBUS_MIN || s->voltage>CFG_VBUS_MAX)return F_VOLTAGE;
    if(absolute(s->current)>CFG_I_TRIP)return F_CURRENT;
    if(s->temperature>=CFG_TEMP_TRIP)return F_TEMPERATURE;
    if(!s->limit_min_ok || !s->limit_max_ok)return F_LIMIT;
    if(s->q-c->offset<CFG_Q_HARD_MIN-0.03f || s->q-c->offset>CFG_Q_HARD_MAX+0.03f)return F_RANGE;
    if(absolute(s->dq)>CFG_V_MAX*1.25f)return F_SPEED;
    return F_NONE;
}
void control_tick(Controller *c,const Sensors *s,uint32_t now_ms) {
    uint32_t delta=now_ms-c->now_ms; float dt=(float)delta*0.001f;
    if(!delta)return;
    c->now_ms=now_ms;c->sensors=*s;c->q=s->q-c->offset;
    if(s->reset_button&&!c->reset_previous&&(c->state==FAULT||c->state==ESTOP))c->reset_latched=1;
    c->reset_previous=s->reset_button;
    Fault f=physical_fault(c,s); if(f!=F_NONE){trip(c,f);return;}
    if((c->state==RUN||c->state==CALIBRATING)&&(!c->hb_seen || (uint32_t)(now_ms-c->heartbeat_ms)>(uint32_t)(CFG_HB_SECONDS*1000.0f))){trip(c,F_HEARTBEAT);return;}
    if(delta>10 && c->state==RUN){trip(c,F_SENSOR);return;}
    if(c->state==CALIBRATING){
        off(c);
        if(absolute(s->dq)>0.03f || absolute(s->q)>0.08f){trip(c,F_SENSOR);return;}
        if(now_ms-c->cal_start_ms>=100){c->offset=s->q;c->q=0;c->calibrated=1;c->state=STANDBY;}
        return;
    }
    if(c->state!=RUN){off(c);return;}
    if(c->q<CFG_Q_MIN-0.05f || c->q>CFG_Q_MAX+0.05f){trip(c,F_RANGE);return;}
    float requested=c->assist;
    if(!c->torque_mode){
        float error=c->target-c->reference;
        float desired=clamp(error*5.0f,-c->velocity_max,c->velocity_max);
        c->reference_velocity+=clamp(desired-c->reference_velocity,-CFG_A_MAX*dt,CFG_A_MAX*dt);
        c->reference+=c->reference_velocity*dt;
        c->reference=clamp(c->reference,CFG_Q_MIN,CFG_Q_MAX);
        requested=c->kp*(c->reference-c->q)-c->kd*s->dq;
    }
    float limit=c->torque_max;
    if(absolute(requested)>CFG_T_CONT){c->peak_ms+=delta;c->recovery_ms=0;}
    else {c->recovery_ms+=delta;if(c->recovery_ms>=2000)c->peak_ms=0;}
    if(c->peak_ms>=(uint32_t)(CFG_PEAK_SECONDS*1000.0f))limit=clamp(limit,0,CFG_T_CONT);
    requested=clamp(requested,-limit,limit);
    if((s->dq>=c->velocity_max && requested>0)||(s->dq<=-c->velocity_max&&requested<0))requested=0;
    if((c->q<=CFG_Q_MIN&&requested<0)||(c->q>=CFG_Q_MAX&&requested>0))requested=0;
    float current_limit=(c->peak_ms>=(uint32_t)(CFG_PEAK_SECONDS*1000.0f))?CFG_I_CONT:CFG_I_PEAK;
    float current_target=clamp(requested/CFG_TORQUE_PER_AMP,-current_limit,current_limit);
    c->torque=current_target*CFG_TORQUE_PER_AMP;
    float err=current_target-s->current;
    float next=clamp(c->integral+CFG_CURRENT_KI*err*dt,-0.8f,0.8f);
    float raw=CFG_CURRENT_KP*err+next;
    c->duty=clamp(raw,-0.8f,0.8f);
    if(absolute(raw)<=0.8f || (raw>0&&err<0)||(raw<0&&err>0))c->integral=next;
    if(current_target==0){c->integral=0;c->duty=0;}
    c->enabled=1;
}
const char *control_command(Controller *c,const char *op,float value) {
    if(!finite_value(value))return "NONFINITE";
    if(!strcmp(op,"ESTOP")){trip(c,F_ESTOP);return "OK";}
    if(!strcmp(op,"STOP")){if(c->state==RUN||c->state==CALIBRATING)c->state=STANDBY;off(c);return "OK";}
    if(!strcmp(op,"PING"))return "OK";
    if(!strcmp(op,"HB")){c->heartbeat_ms=c->now_ms;c->hb_seen=1;return "OK";}
    if(!strcmp(op,"RESET")){
        if(c->state!=FAULT&&c->state!=ESTOP)return "STATE";
        if(!c->reset_latched || !c->sensors.reset_button)return "PHYSICAL_RESET_REQUIRED";
        if(physical_fault(c,&c->sensors)!=F_NONE || c->sensors.temperature>=CFG_TEMP_RESET)return "CONDITION_ACTIVE";
        c->state=STANDBY;c->fault=F_NONE;c->reset_latched=0;c->hb_seen=0;c->calibrated=0;off(c);return "OK";
    }
    if(c->state==FAULT||c->state==ESTOP)return "FAULT_LATCHED";
    if(!strcmp(op,"CAL")){
        if(c->state!=STANDBY)return "STATE";
        if(!c->hb_seen||c->now_ms-c->heartbeat_ms>(uint32_t)(CFG_HB_SECONDS*1000.0f))return "HEARTBEAT_REQUIRED";
        if(physical_fault(c,&c->sensors)!=F_NONE || absolute(c->sensors.q)>0.08f || absolute(c->sensors.dq)>0.03f)return "ZERO_FIXTURE_REQUIRED";
        c->state=CALIBRATING;c->cal_start_ms=c->now_ms;c->calibrated=0;off(c);return "OK";
    }
    if(!strcmp(op,"ARM")){
        if(c->state!=STANDBY || !c->calibrated)return "CALIBRATION_REQUIRED";
        if(!c->hb_seen||c->now_ms-c->heartbeat_ms>(uint32_t)(CFG_HB_SECONDS*1000.0f))return "HEARTBEAT_REQUIRED";
        if(physical_fault(c,&c->sensors)!=F_NONE || c->q<CFG_Q_MIN || c->q>CFG_Q_MAX)return "RANGE";
        c->target=c->q;c->reference=c->q;c->reference_velocity=0;c->assist=0;c->torque_mode=1;c->peak_ms=0;c->recovery_ms=0;c->state=RUN;return "OK";
    }
    if(!strcmp(op,"TARGET")){
        if(c->state!=RUN)return "STATE";
        if(value<CFG_Q_MIN||value>CFG_Q_MAX)return "RANGE";
        c->target=value;c->torque_mode=0;return "OK";
    }
    if(!strcmp(op,"ASSIST")){
        if(c->state!=RUN)return "STATE";
        if(absolute(value)>c->torque_max)return "RANGE";
        c->assist=value;c->torque_mode=1;return "OK";
    }
    if(!strcmp(op,"KP")||!strcmp(op,"KD")||!strcmp(op,"TMAX")||!strcmp(op,"VMAX")){
        if(c->state!=STANDBY)return "STANDBY_REQUIRED";
        if(!strcmp(op,"KP")){if(value<0||value>10)return "RANGE";c->kp=value;}
        if(!strcmp(op,"KD")){if(value<0||value>2)return "RANGE";c->kd=value;}
        if(!strcmp(op,"TMAX")){if(value<=0||value>CFG_T_PEAK)return "RANGE";c->torque_max=value;}
        if(!strcmp(op,"VMAX")){if(value<=0||value>CFG_V_MAX)return "RANGE";c->velocity_max=value;}
        return "OK";
    }
    return "UNKNOWN_OP";
}
