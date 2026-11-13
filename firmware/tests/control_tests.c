/* SPDX-License-Identifier: Apache-2.0 */
#include "control.h"
#include "protocol.h"
#include "config_generated.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
static unsigned passed;
#define CHECK(expr) do {if(!(expr)){fprintf(stderr,"FAIL line %u: %s\n",(unsigned)__LINE__,#expr);exit(1);}passed++;}while(0)
static Sensors healthy(void){Sensors s={0,0,0,25,24,1,1,1,1,0};return s;}
static void tick(Controller *c,Sensors *s){control_tick(c,s,c->now_ms+1);}
static void running(Controller *c,Sensors *s){control_init(c);*s=healthy();tick(c,s);CHECK(!strcmp(control_command(c,"HB",0),"OK"));CHECK(!strcmp(control_command(c,"CAL",0),"OK"));for(unsigned i=0;i<101;i++)tick(c,s);CHECK(c->state==STANDBY&&c->calibrated);s->q=0.5f;tick(c,s);CHECK(!strcmp(control_command(c,"ARM",0),"OK"));tick(c,s);CHECK(c->enabled);}
static char output[8192];static unsigned output_length;
static void capture(const char *p,size_t n,void *ctx){(void)ctx;CHECK(output_length+n<sizeof(output));memcpy(output+output_length,p,n);output_length+=(unsigned)n;output[output_length]=0;}
static void line(Protocol *p,Controller *c,const char *text){for(size_t i=0;i<strlen(text);i++)protocol_feed(p,c,(unsigned char)text[i],capture,0);}
static void command(Protocol *p,Controller *c,const char *payload){char frame[160];snprintf(frame,sizeof(frame),"%s*%04X\n",payload,protocol_crc(payload,strlen(payload)));line(p,c,frame);}
int main(void){Controller c;Sensors s;Protocol p;
    control_init(&c);s=healthy();tick(&c,&s);CHECK(!c.enabled&&c.state==STANDBY);CHECK(strcmp(control_command(&c,"ARM",0),"OK"));CHECK(strcmp(control_command(&c,"CAL",0),"OK"));
    running(&c,&s);CHECK(!strcmp(control_command(&c,"ASSIST",0.7f),"OK"));tick(&c,&s);CHECK(c.torque>0&&c.duty>0);CHECK(strcmp(control_command(&c,"ASSIST",1.01f),"OK"));CHECK(strcmp(control_command(&c,"TARGET",3),"OK"));CHECK(strcmp(control_command(&c,"KP",4),"OK"));
    CHECK(!strcmp(control_command(&c,"STOP",0),"OK"));CHECK(!c.enabled&&c.duty==0);CHECK(!strcmp(control_command(&c,"TMAX",0.4f),"OK"));CHECK(strcmp(control_command(&c,"TMAX",2),"OK"));CHECK(strcmp(control_command(&c,"VMAX",2),"OK"));CHECK(strcmp(control_command(&c,"KP",NAN),"OK"));
    running(&c,&s);control_command(&c,"ASSIST",1);for(unsigned i=0;i<1200;i++){if(i%100==0)control_command(&c,"HB",0);tick(&c,&s);}CHECK(c.state==RUN);CHECK(c.torque<=CFG_T_CONT+0.0001f);CHECK(c.duty<=0.8f);
    running(&c,&s);control_command(&c,"ASSIST",0.4f);s.dq=CFG_V_MAX;tick(&c,&s);CHECK(c.torque==0);s.dq=0;s.q=CFG_Q_MIN;control_command(&c,"ASSIST",-0.4f);tick(&c,&s);CHECK(c.torque==0);s.q=CFG_Q_MAX;control_command(&c,"ASSIST",0.4f);tick(&c,&s);CHECK(c.torque==0);
    running(&c,&s);control_command(&c,"TARGET",1);float previous=c.reference_velocity;for(unsigned i=0;i<100;i++){tick(&c,&s);CHECK(fabsf(c.reference_velocity-previous)<=CFG_A_MAX*0.0011f);CHECK(fabsf(c.reference_velocity)<=CFG_V_MAX);previous=c.reference_velocity;}CHECK(c.reference>s.q);
    running(&c,&s);for(unsigned i=0;i<260;i++)tick(&c,&s);CHECK(c.state==FAULT&&c.fault==F_HEARTBEAT&&!c.enabled);
    const Fault expected[]={F_ESTOP,F_SENSOR,F_RANGE,F_CURRENT,F_TEMPERATURE,F_SPEED,F_VOLTAGE,F_LIMIT,F_SENSOR};
    for(unsigned k=0;k<sizeof(expected)/sizeof(expected[0]);k++){running(&c,&s);switch(k){case 0:s.estop_ok=0;break;case 1:s.sensor_ok=0;break;case 2:s.q=3;break;case 3:s.current=1.21f;break;case 4:s.temperature=60;break;case 5:s.dq=1.26f;break;case 6:s.voltage=29;break;case 7:s.limit_max_ok=0;break;case 8:s.q=NAN;break;}tick(&c,&s);CHECK(c.fault==expected[k]&&!c.enabled&&c.duty==0);CHECK(strcmp(control_command(&c,"ARM",0),"OK"));CHECK(strcmp(control_command(&c,"RESET",0),"OK"));s=healthy();tick(&c,&s);s.reset_button=1;tick(&c,&s);CHECK(!strcmp(control_command(&c,"RESET",0),"OK"));CHECK(c.state==STANDBY&&!c.calibrated);}
    running(&c,&s);s.reset_button=1;tick(&c,&s);s.estop_ok=0;tick(&c,&s);s.estop_ok=1;tick(&c,&s);CHECK(strcmp(control_command(&c,"RESET",0),"OK"));s.reset_button=0;tick(&c,&s);s.reset_button=1;tick(&c,&s);CHECK(!strcmp(control_command(&c,"RESET",0),"OK"));
    running(&c,&s);control_tick(&c,&s,c.now_ms+20);CHECK(c.fault==F_SENSOR&&!c.enabled);
    control_init(&c);s=healthy();tick(&c,&s);control_command(&c,"HB",0);s.q=0.2f;tick(&c,&s);CHECK(strcmp(control_command(&c,"CAL",0),"OK"));s.q=0;tick(&c,&s);control_command(&c,"CAL",0);s.dq=0.04f;tick(&c,&s);CHECK(c.fault==F_SENSOR);
    CHECK(protocol_crc("123456789",9)==0x29b1);protocol_init(&p);control_init(&c);s=healthy();tick(&c,&s);
    command(&p,&c,"65535 HB 0");CHECK(c.hb_seen);CHECK(strstr(output,"\"ok\":true")!=0);uint32_t hb=c.heartbeat_ms;tick(&c,&s);command(&p,&c,"65535 HB 0");CHECK(p.replay==1&&c.heartbeat_ms==hb);command(&p,&c,"0 HB 0");CHECK(p.last_sequence==0&&c.heartbeat_ms==c.now_ms);command(&p,&c,"32768 HB 0");CHECK(p.replay==2);
    line(&p,&c,"1 HB 0*0000\n");CHECK(p.malformed==1);CHECK(p.last_sequence==0);command(&p,&c,"1 HB nan");CHECK(p.malformed==2&&p.last_sequence==0);command(&p,&c,"1 HB inf");CHECK(p.malformed==3);command(&p,&c,"1 HB 0 trailing");CHECK(p.malformed==4);command(&p,&c,"999999 HB 0");CHECK(p.malformed==5);command(&p,&c,"1 HB 0");CHECK(p.last_sequence==1);
    for(unsigned i=0;i<300;i++)protocol_feed(&p,&c,'x',capture,0);protocol_feed(&p,&c,'\n',capture,0);CHECK(p.malformed==6);command(&p,&c,"2 PING 0");CHECK(p.last_sequence==2);protocol_feed(&p,&c,0,capture,0);protocol_feed(&p,&c,'\n',capture,0);CHECK(p.malformed==7);
    printf("PASS %u assertions: control states, limits, calibration, watchdogs, faults, reset edge, CRC/parser/replay.\n",passed);return 0;
}
