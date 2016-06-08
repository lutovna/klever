#include <linux/module.h>
#include <linux/tty.h>
#include <linux/tty_driver.h>
#include <linux/emg/test_model.h>
#include <verifier/nondet.h>

int flip_a_coin;
struct tty_driver *driver;
struct tty_port port;
struct device *device;
unsigned int lines;
unsigned int index;

int ldv_open(struct tty_struct * tty, struct file * filp)
{
    ldv_invoke_callback();
    return 0;
}

void ldv_close(struct tty_struct * tty, struct file * filp)
{
    ldv_invoke_callback();
}

static struct tty_operations ldv_tty_ops = {
    .open = ldv_open,
    .close = ldv_close
};

static int ldv_activate(struct tty_port *tport, struct tty_struct *tty)
{
	/* pass */
    return 0;
}

static void ldv_shutdown(struct tty_port *tport)
{
	/* pass */
}

static const struct tty_port_operations ldv_tty_port_ops = {
	.activate = ldv_activate,
	.shutdown = ldv_shutdown,
};

static int __init ldv_init(void)
{
	int res;

	flip_a_coin = ldv_undef_int();
    if (flip_a_coin) {
        driver = alloc_tty_driver(lines);
        if (driver) {
            tty_set_operations(driver, &ldv_tty_ops);
            ldv_register();
            res = tty_register_driver(driver);
            if (res) {
                put_tty_driver(driver);
                return res;
            }
            else {
                tty_port_init(& port);
                port.ops = & ldv_tty_port_ops;
                tty_port_register_device(& port, driver, ldv_undef_int(), device);
            }
        }
    }
    return 0;
}

static void __exit ldv_exit(void)
{
	if (flip_a_coin) {
        tty_unregister_device(driver, index);
        tty_port_destroy(&port);
        tty_unregister_driver(driver);
        put_tty_driver(driver);
        ldv_deregister();
    }
}

module_init(ldv_init);
module_exit(ldv_exit);
