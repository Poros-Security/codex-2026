#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netdb.h>

static void setup(void) {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

static void set_result(const char *choice) {
    const char *host = getenv("RESULT_HOST");
    const char *port = getenv("RESULT_PORT");
    const char *key = getenv("RESULT_KEY");

    struct addrinfo hints;
    struct addrinfo *addresses = NULL;
    struct addrinfo *current;
    int sock = -1;
    char request[256];

    if (host == NULL || port == NULL || key == NULL || key[0] == '\0') {
        return;
    }

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(host, port, &hints, &addresses) != 0) {
        return;
    }

    for (current = addresses; current != NULL; current = current->ai_next) {
        sock = socket(
            current->ai_family,
            current->ai_socktype,
            current->ai_protocol
        );

        if (sock < 0) {
            continue;
        }

        if (connect(sock, current->ai_addr, current->ai_addrlen) == 0) {
            break;
        }

        close(sock);
        sock = -1;
    }

    if (sock >= 0) {
        snprintf(
            request,
            sizeof(request),
            "POST /internal/result/%s HTTP/1.1\r\n"
            "Host: unlock-api\r\n"
            "X-Internal-Key: %s\r\n"
            "Content-Length: 0\r\n"
            "Connection: close\r\n\r\n",
            choice,
            key
        );

        send(sock, request, strlen(request), 0);
        close(sock);
    }

    freeaddrinfo(addresses);
}

void i_wish_for_prosperity(void) {
    puts("With this, you can buy anything in the world");
    set_result("money");
    puts("Your result has been updated. Refresh the Result page.");
}

void i_wish_for_longevity(void) {
    puts("With this, you can't possibly die");
    set_result("longevity");
    puts("Your result has been updated. Refresh the Result page.");
}

void i_wish_for_wisdom(void) {
    puts("With this, you will be able to see through");
    set_result("wise_mind");
    puts("Your result has been updated. Refresh the Result page.");
}

void i_wish_for_affection(void) {
    puts("With this, you will be adored");
    set_result("love");
    puts("Your result has been updated. Refresh the Result page.");
}

void i_wish_for_nourishment(void) {
    puts("With this, you will never be hungry");
    set_result("food");
    puts("Your result has been updated. Refresh the Result page.");
}

static void reveal_fate(void) {
    char memory[96];

    printf("Why do you wish to start over? ");
    fgets(memory, sizeof(memory), stdin);

    printf(memory);
    puts("");
}

int main(void) {
    char choice[64];

    setup();

    puts("====================================================================");
    puts("If you can start over life and get an upgrade, what will you choose?");
    puts("====================================================================");

    reveal_fate();
    printf("Input : ");
    fgets(choice, 256, stdin);

    puts("May your choice not lead to your doom");
    return 0;
}
