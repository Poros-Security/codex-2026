#define _GNU_SOURCE
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

struct vault { uint64_t cells[8]; uint64_t seal; void (*hook)(void); };
static void quiet(void) { puts("Nothing happens."); }
static void win(void) {
    char flag[128] = {0}; int fd = open("/flag", O_RDONLY);
    if (fd < 0) _exit(1); ssize_t n = read(fd, flag, sizeof(flag) - 1);
    if (n > 0) write(STDOUT_FILENO, flag, (size_t)n); _exit(0);
}
static void menu(struct vault *v) {
    int choice, index; unsigned long long value;
    for (;;) {
        puts("\n[1] read cell\n[2] write cell\n[3] invoke\n[4] quit");
        printf("> "); if (scanf("%d", &choice) != 1) _exit(0);
        if (choice == 1) {
            printf("index: "); if (scanf("%d", &index) != 1) _exit(0);
            printf("value: 0x%llx\n", (unsigned long long)v->cells[index]);
        } else if (choice == 2) {
            printf("index: "); if (scanf("%d", &index) != 1) _exit(0);
            printf("value: "); if (scanf("%llx", &value) != 1) _exit(0);
            v->cells[index] = value; puts("written");
        } else if (choice == 3) v->hook();
        else if (choice == 4) return;
    }
}
int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    struct vault v = {0}; v.seal = 0xdec0de5eedULL; v.hook = quiet;
    puts("== Blind Vault =="); menu(&v); return 0;
}
