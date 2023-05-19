obj-m += demo.o
obj-m += debug.o

modules clean:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) $@
