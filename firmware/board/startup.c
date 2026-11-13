/* SPDX-License-Identifier: Apache-2.0 */
#include <stdint.h>
extern int main(void);
extern void SysTick_Handler(void),USART1_IRQHandler(void);
extern uint32_t _sidata,_sdata,_edata,_sbss,_ebss,_estack;
static void Default_Handler(void){for(;;){}}
void Reset_Handler(void){uint32_t *src=&_sidata,*dst=&_sdata;while(dst<&_edata)*dst++=*src++;for(dst=&_sbss;dst<&_ebss;dst++)*dst=0;main();for(;;){}}
__attribute__((section(".isr_vector"),used)) const uintptr_t vectors[98]={
    [0]=(uintptr_t)&_estack,[1]=(uintptr_t)Reset_Handler,[2]=(uintptr_t)Default_Handler,[3]=(uintptr_t)Default_Handler,[4]=(uintptr_t)Default_Handler,[5]=(uintptr_t)Default_Handler,[6]=(uintptr_t)Default_Handler,[11]=(uintptr_t)Default_Handler,[12]=(uintptr_t)Default_Handler,[14]=(uintptr_t)Default_Handler,[15]=(uintptr_t)SysTick_Handler,[16+37]=(uintptr_t)USART1_IRQHandler
};
