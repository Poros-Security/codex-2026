#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAX_LEN 256
#define NOTE_BUF_SIZE 64

void debug_dump_notes(void) {
    printf("=== NOTES DEBUG DUMP ===\n");
}

__attribute__((naked))
void note_flags_helper(void) {
    asm volatile ("pop %rdi\n\tret\n\t");
}

void internal_admin(unsigned long token) {
    if (token != 0x1337C0DEUL) {
        printf("access denied\n");
        return;
    }
    FILE *f = fopen("/flag.txt", "r");
    if (!f) { printf("flag file missing\n"); return; }
    char flagbuf[256];
    size_t n = fread(flagbuf, 1, sizeof(flagbuf) - 1, f);
    flagbuf[n] = '\0';
    fclose(f);
    printf("%s", flagbuf);
    fflush(stdout);
}

static ssize_t read_full(int fd, void *buf, size_t n) {
    size_t off = 0;
    while (off < n) {
        ssize_t r = read(fd, (char *)buf + off, n - off);
        if (r <= 0) return r;
        off += (size_t)r;
    }
    return (ssize_t)off;
}

void handle_set_note(unsigned short len) {
    char note[NOTE_BUF_SIZE];
    if (read_full(0, note, len) <= 0) exit(1);
    system("echo note saved");
}

void handle_delete_note(unsigned short len) {
    char *buf = malloc(len);
    if (!buf) exit(1);
    if (read_full(0, buf, len) <= 0) { free(buf); exit(1); }
    free(buf);
    printf("note deleted\n");
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    while (1) {
        unsigned char opcode;
        unsigned char lenbytes[2];
        if (read_full(0, &opcode, 1) <= 0) break;
        if (read_full(0, lenbytes, 2) <= 0) break;
        unsigned short len = (unsigned short)(lenbytes[0] | (lenbytes[1] << 8));
        if (len > MAX_LEN) { printf("length too large\n"); continue; }
        switch (opcode) {
            case 0x01: handle_set_note(len); break;
            case 0x02: handle_delete_note(len); break;
            default: printf("unknown opcode\n"); break;
        }
    }
    return 0;
}