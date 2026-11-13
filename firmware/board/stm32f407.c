/* SPDX-License-Identifier: Apache-2.0 */
/* Minimal original register-level BSP, STM32F407VET6; HSI 16MHz, no vendor HAL. */
#include <stdint.h>
#include <stddef.h>
#include "control.h"
#include "protocol.h"
#define R32(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define RCC 0x40023800u
#define GPIOA 0x40020000u
#define GPIOB 0x40020400u
#define USART1 0x40011000u
#define TIM2 0x40000000u
#define TIM3 0x40000400u
#define ADC1 0x40012000u
#define IWDG 0x40003000u
static volatile uint32_t milliseconds;
static volatile unsigned rx_write,rx_read,tx_write,tx_read,rx_overflow;
static unsigned char rx_ring[128],tx_ring[1024];
void SysTick_Handler(void){milliseconds++;}
static void gpio_mode(uint32_t port,unsigned pin,unsigned mode){R32(port)=(R32(port)&~(3u<<(2*pin)))|(mode<<(2*pin));}
static void gpio_af(uint32_t port,unsigned pin,unsigned af){unsigned reg=0x20+(pin/8)*4,shift=(pin%8)*4;R32(port+reg)=(R32(port+reg)&~(15u<<shift))|(af<<shift);gpio_mode(port,pin,2);}
static void output_pin(uint32_t port,unsigned pin,int level){R32(port+0x18)=level?(1u<<pin):(1u<<(pin+16));}
static int input_pin(uint32_t port,unsigned pin){return (R32(port+0x10)&(1u<<pin))!=0;}
static void motor_off(void){R32(TIM3+0x34)=0;output_pin(GPIOB,0,0);}
void USART1_IRQHandler(void){uint32_t sr=R32(USART1);if(sr&((1u<<5)|(1u<<3))){unsigned char b=(unsigned char)R32(USART1+4);unsigned next=(rx_write+1)&127;if(next==rx_read||sr&(1u<<3))rx_overflow=1;else {rx_ring[rx_write]=b;rx_write=next;}}
    if((sr&(1u<<7))&&(R32(USART1+0x0c)&(1u<<7))){if(tx_read==tx_write)R32(USART1+0x0c)&=~(1u<<7);else {R32(USART1+4)=tx_ring[tx_read];tx_read=(tx_read+1)&1023;}}
}
static void emit(const char *bytes,size_t n,void *context){(void)context;for(size_t i=0;i<n;i++){unsigned next=(tx_write+1)&1023;if(next==tx_read){motor_off();return;}tx_ring[tx_write]=(unsigned char)bytes[i];tx_write=next;}R32(USART1+0x0c)|=1u<<7;}
static void delay_half(void){for(volatile unsigned i=0;i<10;i++)__asm volatile("nop");}
static void scl(int high){output_pin(GPIOB,6,high);delay_half();}
static void sda(int high){output_pin(GPIOB,7,high);delay_half();}
static int clock_high(void){scl(1);for(unsigned i=0;i<200;i++)if(input_pin(GPIOB,6))return 1;return 0;}
static int i2c_start(void){sda(1);if(!clock_high())return 0;if(!input_pin(GPIOB,7))return 0;sda(0);scl(0);return 1;}
static void i2c_stop(void){sda(0);scl(1);sda(1);}
static int i2c_write(unsigned byte){for(unsigned i=0;i<8;i++){sda(byte&128);if(!clock_high())return 0;scl(0);byte<<=1;}sda(1);if(!clock_high())return 0;int ack=!input_pin(GPIOB,7);scl(0);return ack;}
static int i2c_read(unsigned *byte,int nack){unsigned result=0;sda(1);for(unsigned i=0;i<8;i++){if(!clock_high())return 0;result=(result<<1)|(unsigned)input_pin(GPIOB,7);scl(0);}sda(nack);if(!clock_high())return 0;scl(0);sda(1);*byte=result;return 1;}
static int as5600(unsigned *angle){unsigned status,hi,lo;int ok=i2c_start()&&i2c_write(0x36<<1)&&i2c_write(0x0b)&&i2c_start()&&i2c_write((0x36<<1)|1)&&i2c_read(&status,0)&&i2c_read(&hi,0)&&i2c_read(&lo,1);i2c_stop();if(!ok||(status&0x38)!=0x20)return 0;*angle=((hi&15)<<8)|lo;return 1;}
static int adc(unsigned channel,unsigned *result){R32(ADC1+0x34)=channel;R32(ADC1+8)|=1u<<30;for(unsigned i=0;i<20000;i++)if(R32(ADC1)&2){*result=R32(ADC1+0x4c);return 1;}return 0;}
static float ntc_temperature(unsigned raw){/* 10k B3950 NTC to GND, 10k 1% pull-up to3.3V. Piecewise linear; threshold exact at60C. */
    static const float v[]={2.543f,2.207f,1.650f,1.145f,0.657f,0.372f,0.215f};
    static const float t[]={0,10,25,40,60,80,100};float input=(float)raw*3.3f/4095.0f;
    if(input>=v[0])return -1;if(input<=v[6])return 101;
    for(unsigned i=0;i<6;i++)if(input<=v[i]&&input>=v[i+1])return t[i]+(t[i+1]-t[i])*(v[i]-input)/(v[i]-v[i+1]);return 101;
}
static void init(void){
    R32(RCC)|=1;while(!(R32(RCC)&2)){}R32(RCC+8)=0;/* HSI, no PLL, no external crystal assumption. */
    R32(RCC+0x30)|=3;R32(RCC+0x40)|=3;R32(RCC+0x44)|=(1u<<8)|(1u<<4);
    output_pin(GPIOB,0,0);gpio_mode(GPIOB,0,1);output_pin(GPIOA,7,0);gpio_mode(GPIOA,7,1);
    const unsigned inputs[]={1,2,10,11};for(unsigned i=0;i<4;i++){unsigned pin=inputs[i];gpio_mode(GPIOB,pin,0);R32(GPIOB+0x0c)=(R32(GPIOB+0x0c)&~(3u<<(pin*2)))|(2u<<(pin*2));}
    gpio_af(GPIOA,6,2);R32(TIM3+0x28)=0;R32(TIM3+0x2c)=799;R32(TIM3+0x18)=(6u<<4)|(1u<<3);R32(TIM3+0x20)=1;R32(TIM3+0x14)=1;R32(TIM3)=0x81;
    gpio_af(GPIOA,0,1);gpio_af(GPIOB,3,1);R32(TIM2+0x18)=0x0101;R32(TIM2+8)=3;R32(TIM2+0x2c)=0xffffffff;R32(TIM2)=1;
    gpio_af(GPIOA,9,7);gpio_af(GPIOA,10,7);R32(USART1+8)=139;R32(USART1+0x0c)=(1u<<13)|(1u<<5)|(1u<<3)|(1u<<2);R32(0xe000e104)=1u<<(37-32);
    for(unsigned pin=6;pin<=7;pin++){sda(1);scl(1);R32(GPIOB+4)|=1u<<pin;gpio_mode(GPIOB,pin,1);R32(GPIOB+0x0c)=(R32(GPIOB+0x0c)&~(3u<<(pin*2)))|(1u<<(pin*2));}
    for(unsigned pin=1;pin<=3;pin++)gpio_mode(GPIOA,pin,3);
    R32(0x40012304)=3u<<16;R32(ADC1+0x10)=(6u<<3)|(6u<<6)|(6u<<9);R32(ADC1+8)=1;
    R32(0xe000e014)=15999;R32(0xe000e018)=0;R32(0xe000e010)=7;
    R32(IWDG)=0x5555;R32(IWDG+4)=0;R32(IWDG+8)=799;R32(IWDG)=0xaaaa;R32(IWDG)=0xcccc;
}
int main(void){Controller c;Protocol p;Sensors s={0,0,0,25,24,0,0,0,0,0};control_init(&c);protocol_init(&p);init();uint32_t previous=0,status_previous=0;float last_q=0;int first=1;
    for(;;){
        if(rx_overflow){motor_off();for(unsigned i=0;i<PROTOCOL_MAX_LINE+1;i++)protocol_feed(&p,&c,'x',emit,0);protocol_feed(&p,&c,'\n',emit,0);rx_overflow=0;}
        for(unsigned i=0;i<32&&rx_read!=rx_write;i++){unsigned char b=rx_ring[rx_read];rx_read=(rx_read+1)&127;protocol_feed(&p,&c,b,emit,0);}
        uint32_t now=milliseconds;if(now==previous)continue;uint32_t dt=now-previous;previous=now;
        unsigned angle=0,current=0,temp=0,bus=0;int valid=as5600(&angle)&&adc(1,&current)&&adc(2,&temp)&&adc(3,&bus);
        float q=(float)angle*(6.28318530718f/4096.0f);if(q>3.14159265359f)q-=6.28318530718f;
        if(first){last_q=q;s.dq=0;first=0;}else {float v=(q-last_q)/(0.001f*(float)dt);if(v>100||v< -100)valid=0;s.dq+=0.1f*(v-s.dq);}last_q=q;
        s.q=q;s.current=((float)current*3.3f/4095.0f-1.65f)/0.2f;s.temperature=ntc_temperature(temp);s.voltage=(float)bus*3.3f*11.0f/4095.0f;
        s.sensor_ok=valid&&current>5&&current<4090&&temp>5&&temp<4090&&bus>5&&bus<4090;
        s.estop_ok=input_pin(GPIOB,1);s.reset_button=input_pin(GPIOB,2);s.limit_min_ok=input_pin(GPIOB,10);s.limit_max_ok=input_pin(GPIOB,11);
        control_tick(&c,&s,now);
        if(c.enabled&&s.estop_ok&&s.limit_min_ok&&s.limit_max_ok){float duty=c.duty;output_pin(GPIOA,7,duty>=0);if(duty<0)duty=-duty;R32(TIM3+0x34)=(uint32_t)(duty*800.0f);output_pin(GPIOB,0,1);}else motor_off();
        if(now-status_previous>=50){status_previous=now;protocol_status(&c,emit,0);}R32(IWDG)=0xaaaa;
    }
}
