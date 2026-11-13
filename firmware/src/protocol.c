/* SPDX-License-Identifier: Apache-2.0 */
#include "protocol.h"
#include <string.h>
typedef struct {char text[512];unsigned used;} Builder;
static void add(Builder *b,const char *s){while(*s&&b->used<sizeof(b->text)-1)b->text[b->used++]=*s++;b->text[b->used]=0;}
static void uint_add(Builder *b,uint32_t n){char digits[11];unsigned i=0;do{digits[i++]=(char)('0'+n%10);n/=10;}while(n&&i<11);while(i){char s[2]={digits[--i],0};add(b,s);}}
static void float_add(Builder *b,float v){if(v<0){add(b,"-");v=-v;}if(!(v>=0&&v<1000000)){add(b,"null");return;}uint32_t n=(uint32_t)(v*100000.0f+0.5f);uint_add(b,n/100000);add(b,".");uint32_t part=n%100000;for(uint32_t base=10000;base;base/=10){char s[2]={(char)('0'+part/base),0};add(b,s);part%=base;}}
uint16_t protocol_crc(const char *data,size_t length){uint16_t crc=0xffff;for(size_t i=0;i<length;i++){crc^=(uint16_t)(unsigned char)data[i]<<8;for(unsigned j=0;j<8;j++)crc=(uint16_t)((crc&0x8000)?(crc<<1)^0x1021:crc<<1);}return crc;}
void protocol_frame(const char *payload,Emit emit,void *context){static const char hex[]="0123456789ABCDEF";size_t length=strlen(payload);uint16_t crc=protocol_crc(payload,length);char tail[7]={'*',hex[(crc>>12)&15],hex[(crc>>8)&15],hex[(crc>>4)&15],hex[crc&15],'\n',0};emit(payload,length,context);emit(tail,6,context);}
static void error(const char *code,Emit emit,void *ctx){Builder b={{0},0};add(&b,"{\"type\":\"error\",\"code\":\"");add(&b,code);add(&b,"\"}");protocol_frame(b.text,emit,ctx);}
void protocol_init(Protocol *p){memset(p,0,sizeof(*p));}
static int hex_value(char c){if(c>='0'&&c<='9')return c-'0';if(c>='A'&&c<='F')return c-'A'+10;if(c>='a'&&c<='f')return c-'a'+10;return -1;}
static int parse_float(const char *s,float *result){
    int sign=1,exponent=0,exponent_sign=1,digits=0;float v=0;
    if(*s=='-'||*s=='+'){if(*s=='-')sign=-1;s++;}
    while(*s>='0'&&*s<='9'){v=v*10+(*s++-'0');if(++digits>9)return 0;}
    if(*s=='.'){float scale=0.1f;s++;while(*s>='0'&&*s<='9'){v+=(*s++-'0')*scale;scale*=0.1f;if(++digits>18)return 0;}}
    if(!digits)return 0;
    if(*s=='e'||*s=='E'){s++;if(*s=='-'||*s=='+'){if(*s=='-')exponent_sign=-1;s++;}int ed=0;while(*s>='0'&&*s<='9'){exponent=exponent*10+(*s++-'0');if(++ed>2||exponent>9)return 0;}if(!ed)return 0;}
    if(*s)return 0;while(exponent--)v=exponent_sign>0?v*10:v*0.1f;*result=v*sign;return *result>=-1e18f&&*result<=1e18f;
}
static void process(Protocol *p,Controller *c,Emit emit,void *ctx){
    char *star=0;for(unsigned i=0;i<p->length;i++)if(p->line[i]=='*'){if(star){p->malformed++;error("BAD_FORMAT",emit,ctx);return;}star=p->line+i;}
    if(!star||p->line+p->length-star!=5){p->malformed++;error("BAD_FORMAT",emit,ctx);return;}
    uint16_t received=0;for(unsigned i=1;i<=4;i++){int h=hex_value(star[i]);if(h<0){p->malformed++;error("BAD_CRC",emit,ctx);return;}received=(uint16_t)((received<<4)|h);}
    if(received!=protocol_crc(p->line,(size_t)(star-p->line))){p->malformed++;error("BAD_CRC",emit,ctx);return;}
    *star=0;char *s=p->line;uint32_t seq=0;int sd=0;while(*s>='0'&&*s<='9'){seq=seq*10+(*s++-'0');if(++sd>5||seq>65535){p->malformed++;error("BAD_FORMAT",emit,ctx);return;}}
    if(!sd||*s++!=' '){p->malformed++;error("BAD_FORMAT",emit,ctx);return;}
    char op[13];unsigned oi=0;while(*s>='A'&&*s<='Z'){if(oi>=12){p->malformed++;error("BAD_FORMAT",emit,ctx);return;}op[oi++]=*s++;}op[oi]=0;
    float value;if(!oi||*s++!=' '||!parse_float(s,&value)){p->malformed++;error("BAD_FORMAT",emit,ctx);return;}
    uint16_t difference=(uint16_t)((uint16_t)seq-p->last_sequence);
    if(p->sequence_seen&&(!difference||difference>=32768)){p->replay++;error("REPLAY",emit,ctx);return;}
    p->last_sequence=(uint16_t)seq;p->sequence_seen=1;
    const char *result=control_command(c,op,value);Builder b={{0},0};add(&b,"{\"type\":\"ack\",\"seq\":");uint_add(&b,seq);add(&b,",\"ok\":");add(&b,!strcmp(result,"OK")?"true":"false");add(&b,",\"error\":");if(!strcmp(result,"OK"))add(&b,"null");else{add(&b,"\"");add(&b,result);add(&b,"\"");}add(&b,",\"code\":\"");add(&b,result);add(&b,"\",\"state\":\"");add(&b,state_name(c->state));add(&b,"\"}");protocol_frame(b.text,emit,ctx);
}
void protocol_feed(Protocol *p,Controller *c,unsigned char byte,Emit emit,void *ctx){
    if(byte=='\n'){
        if(p->dropping){p->malformed++;error("LINE_TOO_LONG",emit,ctx);}else if(p->length){p->line[p->length]=0;process(p,c,emit,ctx);}
        p->length=0;p->dropping=0;return;
    }
    if(p->dropping)return;
    if(byte<32||byte>126){p->dropping=1;return;}
    if(p->length>=PROTOCOL_MAX_LINE-1){p->dropping=1;return;}
    p->line[p->length++]=(char)byte;
}
void protocol_status(const Controller *c,Emit emit,void *ctx){Builder b={{0},0};add(&b,"{\"type\":\"status\",\"state\":\"");add(&b,state_name(c->state));add(&b,"\",\"fault\":\"");add(&b,fault_name(c->fault));
    add(&b,"\",\"q\":");float_add(&b,c->q);add(&b,",\"dq\":");float_add(&b,c->sensors.dq);add(&b,",\"current\":");float_add(&b,c->sensors.current);add(&b,",\"temperature\":");float_add(&b,c->sensors.temperature);add(&b,",\"voltage\":");float_add(&b,c->sensors.voltage);add(&b,",\"torque\":");float_add(&b,c->torque);add(&b,",\"duty\":");float_add(&b,c->duty);add(&b,",\"enabled\":");add(&b,c->enabled?"true":"false");add(&b,",\"calibrated\":");add(&b,c->calibrated?"true":"false");add(&b,",\"time_ms\":");uint_add(&b,c->now_ms);add(&b,"}");protocol_frame(b.text,emit,ctx);}
