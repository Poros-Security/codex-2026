#include <stdio.h>
#include <stdlib.h>

int main(void) {
    FILE *f = fopen("/flag", "r");
    if (!f) { perror("open"); return 1; }
    char buf[512];
    while (fgets(buf, sizeof buf, f)) fputs(buf, stdout);
    fclose(f);
    return 0;
}