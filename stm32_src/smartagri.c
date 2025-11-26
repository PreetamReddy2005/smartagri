/* 
 * STM32F072RB SmartAgri Sensor Firmware
 * Bare-metal implementation without HAL dependencies
 */

// Register definitions for STM32F072RB
#define RCC_BASE        0x40021000
#define GPIOA_BASE      0x48000000
#define GPIOB_BASE      0x48000400
#define ADC1_BASE       0x40012400
#define USART2_BASE     0x40004400
#define TIM3_BASE       0x40000400

// RCC Registers
#define RCC_CR          (*(volatile unsigned int *)(RCC_BASE + 0x00))
#define RCC_AHBENR      (*(volatile unsigned int *)(RCC_BASE + 0x14))
#define RCC_APB2ENR     (*(volatile unsigned int *)(RCC_BASE + 0x18))
#define RCC_APB1ENR     (*(volatile unsigned int *)(RCC_BASE + 0x1C))

// GPIO Registers
#define GPIOA_MODER     (*(volatile unsigned int *)(GPIOA_BASE + 0x00))
#define GPIOA_ODR       (*(volatile unsigned int *)(GPIOA_BASE + 0x14))
#define GPIOA_IDR       (*(volatile unsigned int *)(GPIOA_BASE + 0x10))
#define GPIOA_PUPDR     (*(volatile unsigned int *)(GPIOA_BASE + 0x0C))
#define GPIOA_AFR0      (*(volatile unsigned int *)(GPIOA_BASE + 0x20))
#define GPIOA_AFR1      (*(volatile unsigned int *)(GPIOA_BASE + 0x24))

#define GPIOB_MODER     (*(volatile unsigned int *)(GPIOB_BASE + 0x00))
#define GPIOB_ODR       (*(volatile unsigned int *)(GPIOB_BASE + 0x14))

// ADC Registers
#define ADC_ISR         (*(volatile unsigned int *)(ADC1_BASE + 0x00))
#define ADC_CR          (*(volatile unsigned int *)(ADC1_BASE + 0x08))
#define ADC_CHSELR      (*(volatile unsigned int *)(ADC1_BASE + 0x28))
#define ADC_DR          (*(volatile unsigned int *)(ADC1_BASE + 0x40))

// USART2 Registers
#define USART2_CR1      (*(volatile unsigned int *)(USART2_BASE + 0x00))
#define USART2_BRR      (*(volatile unsigned int *)(USART2_BASE + 0x0C))
#define USART2_ISR      (*(volatile unsigned int *)(USART2_BASE + 0x1C))
#define USART2_TDR      (*(volatile unsigned int *)(USART2_BASE + 0x28))

void delay_ms(int ms) {
    for(int i = 0; i < ms; i++) {
        for(volatile int j = 0; j < 8000; j++);
    }
}

void uart_putchar(char c) {
    while(!(USART2_ISR & (1 << 7))); // Wait for TXE
    USART2_TDR = c;
}

void uart_puts(const char *s) {
    while(*s) uart_putchar(*s++);
}

void uart_putnum(int num) {
    char buf[12];
    int i = 0;
    if(num == 0) {
        uart_putchar('0');
        return;
    }
    if(num < 0) {
        uart_putchar('-');
        num = -num;
    }
    while(num > 0) {
        buf[i++] = '0' + (num % 10);
        num /= 10;
    }
    while(i > 0) uart_putchar(buf[--i]);
}

int read_adc(int channel) {
    ADC_CHSELR = (1 << channel);
    ADC_CR |= (1 << 2); // Start conversion
    while(!(ADC_ISR & (1 << 2))); // Wait for EOC
    return ADC_DR;
}

void init_clocks(void) {
    // Enable clocks for GPIOA, GPIOB, ADC, USART2
    RCC_AHBENR |= (1 << 17) | (1 << 18); // GPIOA, GPIOB
    RCC_APB2ENR |= (1 << 9); // ADC
    RCC_APB1ENR |= (1 << 17); // USART2
}

void init_gpio(void) {
    // PA0, PA1 as Analog (for ADC)
    GPIOA_MODER |= (3 << 0) | (3 << 2);
    
    // PA2, PA3 as Alternate Function (USART2)
    GPIOA_MODER &= ~((3 << 4) | (3 << 6));
    GPIOA_MODER |= (2 << 4) | (2 << 6);
    GPIOA_AFR0 |= (1 << 8) | (1 << 12); // AF1 for USART2
    
    // PA5 as Output (LED)
    GPIOA_MODER &= ~(3 << 10);
    GPIOA_MODER |= (1 << 10);
    
    // PA4 as Input with pullup (Rain sensor)
    GPIOA_MODER &= ~(3 << 8);
    GPIOA_PUPDR |= (1 << 8);
}

void init_usart(void) {
    // 115200 baud @ 8MHz clock
    USART2_BRR = 69; // 8000000 / 115200
    USART2_CR1 |= (1 << 0) | (1 << 3) | (1 << 2); // UE, TE, RE
}

void init_adc(void) {
    ADC_CR |= (1 << 31); // ADCAL - Start calibration
    while(ADC_CR & (1 << 31)); // Wait for calibration
    ADC_CR |= (1 << 0); // ADEN - Enable ADC
    while(!(ADC_ISR & (1 << 0))); // Wait for ADRDY
}

void send_json(int moisture, int temp, int ph, int rain, int water_level) {
    uart_puts("{\"moisture\":");
    uart_putnum(moisture);
    uart_puts(",\"temp\":");
    uart_putnum(temp);
    uart_puts(",\"ph\":");
    uart_putnum(ph);
    uart_puts(",\"rain\":");
    uart_putnum(rain);
    uart_puts(",\"water_level\":");
    uart_putnum(water_level);
    uart_puts("}\r\n");
}

int main(void) {
    init_clocks();
    init_gpio();
    init_usart();
    init_adc();
    
    delay_ms(1000);
    uart_puts("STM32F072RB SmartAgri Started\r\n");
    
    while(1) {
        // Read sensors
        int moisture_raw = read_adc(0); // PA0
        int ph_raw = read_adc(1);       // PA1
        int rain = (GPIOA_IDR & (1 << 4)) ? 0 : 1;
        
        // Convert to percentages (simplified)
        int moisture = (moisture_raw * 100) / 4095;
        int temp = 25; // Dummy
        int ph = 7;    // Dummy (needs calibration)
        int water_level = 75; // Dummy
        
        send_json(moisture, temp, ph, rain, water_level);
        
        // Blink LED
        GPIOA_ODR ^= (1 << 5);
        
        delay_ms(500);
    }
}
