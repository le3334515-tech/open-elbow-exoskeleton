/* SPDX-License-Identifier: Apache-2.0 */
#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L
#endif
/* This native adapter runs the identical control.c/protocol.c used on STM32. */
#include "control.h"
#include "protocol.h"
#include "config_generated.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#ifdef _WIN32
#include <windows.h>
#include <io.h>
#else
#include <unistd.h>
#include <sys/select.h>
#include <time.h>
#endif
static void output(const char *p,size_t n,void *ctx){(void)ctx;fwrite(p,1,n,stdout);fflush(stdout);}
static uint64_t clock_ms(void){
#ifdef _WIN32
return GetTickCount64();
#else
struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000+(uint64_t)t.tv_nsec/1000000;
#endif
}
static int byte_available(void){
#ifdef _WIN32
DWORD n=0;HANDLE in=GetStdHandle(STD_INPUT_HANDLE);if(GetFileType(in)==FILE_TYPE_PIPE){if(!PeekNamedPipe(in,0,0,0,&n,0))return -1;return n>0;}return 0;
#else
struct timeval tv={0,0};fd_set set;FD_ZERO(&set);FD_SET(STDIN_FILENO,&set);return select(STDIN_FILENO+1,&set,0,0,&tv)>0;
#endif
}
static void idle(void){
#ifdef _WIN32
Sleep(1);
#else
struct timespec delay={0,1000000};nanosleep(&delay,0);
#endif
}
static void inject(Sensors *s,char *line,int *hold_current){char key[32];float value;if(sscanf(line,"!INJECT %31s %f",key,&value)!=2||!isfinite(value))return;
    if(!strcmp(key,"Q")){s->q=value;s->dq=0;}
    else if(!strcmp(key,"DQ"))s->dq=value;
    else if(!strcmp(key,"TEMP"))s->temperature=value;
    else if(!strcmp(key,"CURRENT")){s->current=value;*hold_current=1;}
    else if(!strcmp(key,"CURRENT_AUTO"))*hold_current=0;
    else if(!strcmp(key,"VOLTAGE"))s->voltage=value;
    else if(!strcmp(key,"SENSOR"))s->sensor_ok=value!=0;
    else if(!strcmp(key,"ESTOP"))s->estop_ok=value==0;
    else if(!strcmp(key,"RESET_BUTTON"))s->reset_button=value!=0;
    else if(!strcmp(key,"LIMIT_MIN"))s->limit_min_ok=value==0;
    else if(!strcmp(key,"LIMIT_MAX"))s->limit_max_ok=value==0;
}
int main(void){Controller c;Protocol p;Sensors s={0,0,0,25,24,1,1,1,1,0};control_init(&c);protocol_init(&p);uint64_t start=clock_ms();uint32_t ticks=0;char line[192];unsigned length=0;int hold_current=0,overflow=0;
    setvbuf(stdin,0,_IONBF,0);setvbuf(stdout,0,_IONBF,0);
    for(;;){int available;while((available=byte_available())>0){int ch=getchar();if(ch==EOF)return 0;
        if(ch=='\n'){
            line[length]=0;
            if(!overflow&&length&&line[0]=='!')inject(&s,line,&hold_current);
            else {for(unsigned i=0;i<length;i++)protocol_feed(&p,&c,(unsigned char)line[i],output,0);if(overflow)for(unsigned i=0;i<PROTOCOL_MAX_LINE+1;i++)protocol_feed(&p,&c,'x',output,0);protocol_feed(&p,&c,'\n',output,0);}
            length=0;overflow=0;
        }else if(length<sizeof(line)-1)line[length++]=(char)ch;else overflow=1;
    }
        if(available<0)return 0;
        uint32_t elapsed=(uint32_t)(clock_ms()-start);
        if(elapsed-ticks>100){/* A delayed host cannot silently pretend real-time execution. */if(c.state==RUN){control_tick(&c,&s,elapsed);ticks=elapsed;}}
        while(ticks<elapsed){ticks++;
            if(c.enabled){float actual=c.duty*3.0f;if(!hold_current)s.current+=(actual-s.current)*0.15f;float acceleration=(s.current*CFG_TORQUE_PER_AMP-CFG_MODEL_DAMPING*s.dq-CFG_MODEL_GRAVITY*sinf(s.q))/CFG_MODEL_INERTIA;s.dq+=acceleration*0.001f;s.q+=s.dq*0.001f;}
            else {if(!hold_current)s.current*=0.8f;s.dq=0;/* The disabled joint is held by the calibration/bench fixture. */}
            if(s.q<CFG_Q_HARD_MIN){s.q=CFG_Q_HARD_MIN;s.dq=0;}if(s.q>CFG_Q_HARD_MAX){s.q=CFG_Q_HARD_MAX;s.dq=0;}
            control_tick(&c,&s,ticks);if(ticks%CFG_STATUS_MS==0)protocol_status(&c,output,0);
        }idle();
    }
}
