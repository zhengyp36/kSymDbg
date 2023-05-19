#include <linux/fs.h>
#include <linux/init.h>
#include <linux/sysfs.h>
#include <linux/string.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/device.h>
#include "../ksym.h"

KVAR_IMPORT(int, last_add_result);
KVAR_IMPORT(int, last_sub_result);

KFUN_IMPORT(int, demo_add, (int, int));
KFUN_IMPORT(int, demo_sub, (int, int));

KVAR_IMPORT(void*, undef_var);
KFUN_IMPORT(void, undef_fun, (void));

static int
imported(void)
{
	return (KSYM_NAME(last_add_result) &&
	    KSYM_NAME(last_sub_result) &&
	    KSYM_NAME(demo_add) &&
	    KSYM_NAME(demo_sub));
}

static void
call_add(void)
{
	if (imported()) {
		int last = KSYM_REF(last_add_result);
		int curr = KSYM_REF(demo_add)(3, 2);
		printk(KERN_INFO "Debug: Call Add: last=%d, %d + %d = %d\n",
		   last, 3, 2, curr);
	} else {
		printk(KERN_ERR "Debug: Add not imported\n");
	}
}

static void
call_sub(void)
{
	if (imported()) {
		int last = KSYM_REF(last_sub_result);
		int curr = KSYM_REF(demo_sub)(5, 3);
		printk(KERN_INFO "Debug: Call Sub: last=%d, %d - %d = %d\n",
		   last, 5, 3, curr);
	} else {
		printk(KERN_ERR "Debug: Sub not imported\n");
	}
}

static char debug_buffer[1024] = "init";

static ssize_t
debug_show(struct device *dev, struct device_attribute *attr, char *buf)
{
	return sprintf(buf, "%s\n", debug_buffer);
}

static ssize_t
debug_store(struct device *dev, struct device_attribute *attr,
    const char *buf, size_t count)
{
	if (!strncmp(buf, "+", 1)) {
		call_add();
		sprintf(debug_buffer, "3 + 2 = 5");
	} else if (!strncmp(buf, "-", 1)) {
		call_sub();
		sprintf(debug_buffer, "5 - 3 = 2");
	} else
		sprintf(debug_buffer, "Wrong");
	return count;
}

static DEVICE_ATTR(debug, 0644, debug_show, debug_store);

static int debug_major;
static struct class *debug_class;

static struct file_operations debug_fops = {
	.owner = THIS_MODULE,
};

static int __init
debug_init(void)
{
	int ret;
	struct device *debug_device;

	debug_major = register_chrdev(0, "debug", &debug_fops);
	if (debug_major < 0) {
		printk(KERN_ERR "Debug: register char-dev error %d\n",
		    debug_major);
		return (debug_major);
	}

	debug_class = class_create(THIS_MODULE, "debug");
	if (IS_ERR(debug_class)) {
		unregister_chrdev(debug_major, "debug");
		printk(KERN_ERR "Debug: create class error\n");
		return (-EBUSY);
	}

	debug_device = device_create(debug_class, NULL, MKDEV(debug_major,0),
	    NULL, "debug");
	if (IS_ERR(debug_device)) {
		class_destroy(debug_class);
		unregister_chrdev(debug_major, "debug");
		printk(KERN_ERR "Debug: create device error\n");
		return (-EBUSY);
	}

	ret = sysfs_create_file(&debug_device->kobj, &dev_attr_debug.attr);
	if (ret < 0) {
		device_destroy(debug_class, MKDEV(debug_major, 0));
		class_destroy(debug_class);
		unregister_chrdev(debug_major, "debug");
		printk(KERN_ERR "Debug: create sysfs error, ret %d\n", ret);
	} else
		printk(KERN_INFO "Debug init done.\n");

	return (ret);
}

static void __exit
debug_exit(void)
{
	device_destroy(debug_class, MKDEV(debug_major, 0));
	class_destroy(debug_class);
	unregister_chrdev(debug_major, "debug");
	printk(KERN_INFO "Debug exit.\n");
}

module_init(debug_init);
module_exit(debug_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("CeresData");
MODULE_DESCRIPTION("Kernel Symbol Access Debug");
MODULE_VERSION("1.0.0");
