#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>

static int last_add_result;

int
demo_add(int x, int y)
{
	printk("Demo: Call Add: %d + %d = %d\n", x, y, x + y);
	return (last_add_result = x + y);
}

int *
demo_add_result(void)
{
	return (&last_add_result);
}

static int last_sub_result;

int
demo_sub(int x, int y)
{
	printk("Demo: Call Sub: %d - %d = %d\n", x, y, x - y);
	return (last_sub_result = x - y);
}

int *
demo_sub_result(void)
{
	return (&last_sub_result);
}

static int __init
demo_init(void)
{
	printk(KERN_INFO "Demo init.\n");
	return (0);
}

static void __exit
demo_exit(void)
{
	printk(KERN_INFO "Demo exit.\n");
}

module_init(demo_init);
module_exit(demo_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("CeresData");
MODULE_DESCRIPTION("Kernel Symbol Access Demo");
MODULE_VERSION("1.0.0");
