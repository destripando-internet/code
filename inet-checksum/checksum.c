#include <stdio.h>
#include <stdint.h>

uint16_t ip_checksum(const uint8_t *data, int length) {
    uint32_t sum = 0;

    while (length > 1) {
        uint16_t word = (data[0] << 8) | data[1];
        sum += word;
        data += 2;
        length -= 2;
    }

    // If there's a leftover byte
    if (length == 1)
        sum += data[0] << 8;

    // Fold 32-bit sum to 16 bits
    while (sum >> 16)
        sum = (sum & 0xFFFF) + (sum >> 16);

    return (uint16_t)(~sum);
}

uint16_t sum16(const uint8_t *data, int length) {
    int count = length;
    uint32_t sum = 0;
    const uint8_t *addr = (const uint8_t *)data;

    while (count > 1) {
        sum += *(const uint16_t *)addr;
        addr += 2;
        count -= 2;
    }

    if (count > 0) {
        sum += *(const uint8_t *)addr;
    }

    return sum;
}

int main() {
    uint8_t ip_header[] = {
        0x45, 0x00,
        0x00, 0x54,
        0x00, 0x00,
        0x40, 0x00,
        0x40, 0x01,
        0x00, 0x00,             // checksum field set to 0
        0xC0, 0xA8, 0x00, 0x01,
        0xC0, 0xA8, 0x00, 0xC7,
        0x10
    };

    uint8_t test1[] = {
        0x11, 0x22,
        0x33, 0x44,
        0x55
    };

    uint16_t checksum = ip_checksum(ip_header, sizeof(ip_header));
    printf("Checksum: 0x%04X\n", checksum);

    uint16_t test_sum16 = sum16(test1, sizeof(test1));
    printf("Test sum: %04d\n", test_sum16);

    return 0;
}
