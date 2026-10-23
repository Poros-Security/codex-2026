#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/miscdevice.h>
#include <linux/ioctl.h>
#include <linux/delay.h>
#include <linux/cred.h>
#include <linux/uaccess.h>
#include <linux/uidgid.h>

#define DEVICE_NAME "locker"

/*
 * Existing IOCTLs
 */
#define LOCKER_OPEN    _IO('L', 1)
#define LOCKER_SYNC    _IO('L', 2)
#define LOCKER_COMMIT  _IO('L', 3)
#define LOCKER_RESET   _IO('L', 4)

/*
 * New IOCTL:
 * Only works after the intended exploit reaches COMMIT.
 */
#define LOCKER_GETFLAG _IOR('L', 5, char[128])

/*
 * State machine
 */
#define STATE_IDLE      0
#define STATE_READY     1
#define STATE_PENDING   2
#define STATE_GRANTED   3


struct locker_object {
    int state;
    int prepared;
    int pending;
    int sequence;
};


static struct locker_object object;

/*
 * This is the important gate.
 *
 * solved == true only after LOCKER_COMMIT succeeds.
 */
static bool solved;


/*
 * Flag is NOT stored as plaintext.
 *
 * Original flag bytes were XORed with 0x5a.
 *
 * This prevents:
 *
 *     strings chall.ko
 *
 * from directly revealing the flag.
 *
 * It is NOT cryptographic protection. A determined
 * reverse engineer can recover it.
 */
static const unsigned char flag_enc[] = {
    0x19, 0x15, 0x1e, 0x1f, 0x02, 0x68, 0x6c,
    0x21, 0x2a, 0x69, 0x28, 0x2e, 0x6e, 0x37,
    0x1b, 0x05, 0x31, 0x6e, 0x36, 0x6b, 0x05,
    0x38, 0x6b, 0x31, 0x6b, 0x05, 0x38, 0x6b,
    0x31, 0x6b, 0x34, 0x05, 0x29, 0x69, 0x36,
    0x3b, 0x6b, 0x34, 0x05, 0x28, 0x69, 0x2e,
    0x68, 0x3c, 0x2f, 0x34, 0x39, 0x05, 0x29,
    0x69, 0x2a, 0x2f, 0x32, 0x05, 0x37, 0x6a,
    0x32, 0x6a, 0x34, 0x05, 0x31, 0x28, 0x6b,
    0x29, 0x6e, 0x28, 0x34, 0x23, 0x6e, 0x27
};

#define FLAG_LEN (sizeof(flag_enc))


/*
 * LOCKER_OPEN
 *
 * First stage of the state machine.
 */
static long locker_open(void)
{
    if (object.state != STATE_IDLE)
        return -EPERM;

    object.state = STATE_READY;
    object.prepared = 1;
    object.pending = 1;
    object.sequence = 0;

    /*
     * Race window.
     *
     * Another thread can call LOCKER_SYNC()
     * while pending == 1.
     */
    msleep(100);

    object.pending = 0;

    /*
     * LOCKER_SYNC() changes sequence to 1.
     * If that happened during the window,
     * transition to GRANTED.
     */
    if (object.sequence == 1)
        object.state = STATE_GRANTED;

    return 0;
}


/*
 * LOCKER_SYNC
 *
 * Intended to be called concurrently with LOCKER_OPEN.
 */
static long locker_sync(void)
{
    if (!object.pending)
        return -EAGAIN;

    if (object.state != STATE_READY)
        return -EPERM;

    object.sequence = 1;
    object.state = STATE_PENDING;

    return 0;
}


/*
 * LOCKER_COMMIT
 *
 * Final stage of the intended exploit.
 *
 * If the race succeeded:
 *
 *     STATE_GRANTED
 *
 * then the process receives root credentials.
 *
 * We also set:
 *
 *     solved = true
 *
 * This becomes the gate for LOCKER_GETFLAG.
 */
static long locker_commit(void)
{
    struct cred *new_cred;

    if (!object.prepared)
        return -EPERM;

    if (object.state != STATE_GRANTED)
        return -EPERM;

    /*
     * Give the calling process root credentials.
     */
    new_cred = prepare_kernel_cred(&init_task);

    if (!new_cred)
        return -ENOMEM;

    commit_creds(new_cred);

    /*
     * IMPORTANT:
     *
     * The challenge is now considered solved.
     */
    solved = true;

    /*
     * Reset the state machine.
     */
    object.state = STATE_IDLE;
    object.prepared = 0;
    object.pending = 0;
    object.sequence = 0;

    return 0;
}


/*
 * LOCKER_GETFLAG
 *
 * The flag does NOT exist as /flag.txt.
 *
 * The only way to obtain it is through this ioctl.
 *
 * Requirements:
 *
 *     1. The intended COMMIT must have succeeded.
 *     2. Current process must have root credentials.
 */
static long locker_getflag(unsigned long arg)
{
    unsigned char flag[FLAG_LEN];
    size_t i;

    /*
     * Exploit has not completed.
     */
    if (!solved)
        return -EPERM;

    /*
     * Require root.
     */
    if (!uid_eq(current_euid(), GLOBAL_ROOT_UID))
        return -EPERM;

    /*
     * Decode the flag only after both checks pass.
     */
    for (i = 0; i < FLAG_LEN; i++)
        flag[i] = flag_enc[i] ^ 0x5a;

    /*
     * Send decoded flag to userspace.
     */
    if (copy_to_user(
            (void __user *)arg,
            flag,
            FLAG_LEN))
        return -EFAULT;

    return FLAG_LEN;
}


/*
 * LOCKER_RESET
 */
static long locker_reset(void)
{
    object.state = STATE_IDLE;
    object.prepared = 0;
    object.pending = 0;
    object.sequence = 0;

    /*
     * Reset the solved state as well.
     */
    solved = false;

    return 0;
}


/*
 * IOCTL dispatcher
 */
static long locker_ioctl(
    struct file *file,
    unsigned int cmd,
    unsigned long arg
)
{
    switch (cmd) {

    case LOCKER_OPEN:
        return locker_open();

    case LOCKER_SYNC:
        return locker_sync();

    case LOCKER_COMMIT:
        return locker_commit();

    case LOCKER_RESET:
        return locker_reset();

    case LOCKER_GETFLAG:
        return locker_getflag(arg);

    default:
        return -EINVAL;
    }
}


/*
 * File operations
 */
static const struct file_operations locker_fops = {
    .owner = THIS_MODULE,
    .unlocked_ioctl = locker_ioctl,
};


/*
 * /dev/locker
 */
static struct miscdevice locker_device = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = DEVICE_NAME,
    .fops = &locker_fops,

    /*
     * Participants can access the device.
     */
    .mode = 0666,
};


/*
 * Module initialization
 */
static int __init locker_init(void)
{
    int ret;

    object.state = STATE_IDLE;
    object.prepared = 0;
    object.pending = 0;
    object.sequence = 0;

    solved = false;

    ret = misc_register(&locker_device);

    if (ret)
        return ret;

    return 0;
}


/*
 * Module cleanup
 */
static void __exit locker_exit(void)
{
    misc_deregister(&locker_device);
}


module_init(locker_init);
module_exit(locker_exit);


MODULE_LICENSE("GPL");
MODULE_AUTHOR("CTF Author");
MODULE_DESCRIPTION("Kernel state-machine challenge");
MODULE_VERSION("2.0");
