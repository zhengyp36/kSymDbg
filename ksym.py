#!/usr/bin/python

import os
import re
import sys
import random

class KSym(object):
    def __init__(self):
        self.load()
    
    def hookCodes(self, usrConf=[]):
        ok,hookTable = self.hookList(usrConf)
        if not ok or not hookTable:
            return ok,[]
        
        codes = ['\tprintk(KERN_INFO "KSym set hooks now ...\\n");']
        codes.append('')
        
        for sym in hookTable:
            codes.append('\tprintk(KERN_INFO "KSymSet: %s=0x%s.\\n");' % (
                sym, hookTable[sym]))
            codes.append('\t*(void**)0x%sULL = (void*)0x%sULL;' % (
                self.ksymAddr(self.hookName(sym)), hookTable[sym]))
            codes.append('')
        
        return True,codes
    
    def load(self):
        self.symbols = {}
        self.hooks = []
        
        fd = open('/proc/kallsyms')
        print('[KSYM]Load kernel symbols...')
        for line in fd.readlines():
            self.add(line.strip().split())
        print('[KSYM]Load kernel symbols done.')
        fd.close()
    
    def add(self, info):
        info.append('')
        sym = {
            'addr' : info[0],
            'type' : info[1],
            'name' : info[2],
            'mod'  : info[3][1:-1],
        }
        nameArr = [sym['name']]
        
        # Remove suffix for some static symbols
        if not nameArr[0].startswith('.') and '.' in nameArr[0]:
            nameArr.append(nameArr[0].split('.')[0])
        
        for name in nameArr:
            if name not in self.symbols:
                self.symbols[name] = []
                r = re.search(self.hookPattern(),name)
                if r:
                    self.hooks.append(r.groups()[0])
            self.symbols[name].append(sym)
    
    def ksymAddr(self,sym):
        if sym in self.symbols:
            if len(self.symbols[sym]) == 1:
                return self.symbols[sym][0]['addr']
        else:
            return None
    
    def hookList(self, usrConf):
        hookTable,hookError = {},[]
        usrTable = self.loadUsrConf(usrConf)
        
        for sym in self.hooks:
            if sym in usrTable:
                hookTable[sym] = usrTable[sym]
            else:
                addr = self.ksymAddr(sym)
                if addr:
                    hookTable[sym] = addr
                else:
                    hookError.append(sym)
        
        if hookError:
            print('Error: *** Some symbols error: %s.' % ' '.join(hookError))
            return False,{}
        else:
            if not hookTable:
                print('Warning: *** No symbols need to be hooked.')
            return True,hookTable
    
    def loadUsrConf(self, usrConf):
        table = {}
        for conf in usrConf:
            if not os.path.isfile(conf):
                print("Error: *** '%s' does not exist or is not a file." % conf)
                sys.exit(1)
            self.loadOneUsrConf(conf, table)
        return table
    
    def loadOneUsrConf(self, conf, table):
        fd = open(conf)
        for line in fd.readlines():
            r = re.search('(\w+)\s*=\s*(\w+)', line.strip())
            if r:
                var,addr = r.groups()
                table[var] = self.validateAddr(addr)
        fd.close()
    
    def validateAddr(self, addr):
        if addr.startswith('0x') or addr.startswith('0X'):
            return addr[2:]
        else:
            return addr
    
    def hookPattern(self):
        return self.hookName('([a-z,A-Z,_][a-z,A-Z,_,0-9]*)')
    
    def hookName(self, name):
        return '___KSYM_IMPORT_ADDR_3578___%s___2904___' % name

class Hook(object):
    def run(self):
        if len(sys.argv) == 2 and sys.argv[1] in ['help', '--help', '-h']:
            print('Usage: %s [<usrConf> ...]' % os.path.basename(sys.argv[0]))
            sys.exit(0)
        
        ok,codes = KSym().hookCodes(usrConf=sys.argv[1:])
        if not ok:
            sys.exit(1)
        elif not codes:
            sys.exit(0)
        
        workspace = '/tmp/ksym.hook.%s' % self.rand()
        ko = 'ksym_%s' % self.rand('')
        ko_path = '%s/%s.ko' % (workspace, ko)
        
        os.mkdir(workspace)
        print('[KSYM]Generate makefile & source @%s ...' % workspace)
        
        self.write('%s/Makefile' % workspace,
        [
            'obj-m += %s.o' % ko,
            '',
            'modules clean:',
            '\t$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) $@',
            '',
        ])
        
        self.write('%s/%s.c' % (workspace, ko),
        [
            '#include <linux/init.h>',
            '#include <linux/module.h>',
            '#include <linux/kernel.h>',
            '',
            'static int __init',
            'ksym_init(void)',
            '{',
            '\n'.join(codes),
            '\treturn (0);',
            '}',
            '',
            'static void __exit',
            'ksym_exit(void)',
            '{',
            '\tprintk(KERN_INFO "Ksym exit.\\n");',
            '}',
            '',
            'module_init(ksym_init);',
            'module_exit(ksym_exit);',
            '',
            'MODULE_LICENSE("GPL");',
            'MODULE_AUTHOR("CeresData");',
            'MODULE_DESCRIPTION("Kernel Symbol Access");',
            'MODULE_VERSION("1.0.0");',
            '',
        ])
        
        rc = os.system('cd %s && make' % workspace)
        if rc != 0:
            print('Error: *** Fail to make %s.' % ko_path)
            sys.exit(rc)
        
        if not os.path.isfile('%s/%s.ko' % (workspace, ko)):
            print('Error: *** Make success but fail to generate %s.' % ko_path)
            sys.exit(1)
        print('[KSYM]Generate %s success.' % ko_path)
        
        rc = os.system('insmod %s' % ko_path)
        if rc != 0:
            print('Error: *** Fail to insert %s.' % ko_path)
            sys.exit(rc)
        print('[KSYM]Insert %s success which means setup-hooks done.' % ko_path)
        
        rc = os.system('rmmod %s' % ko)
        if rc != 0:
            print('Error: *** Fail to remove %s.' % ko)
            sys.exit(rc)
        print('[KSYM]Remove %s success.' % ko)
        
        rc = os.system('rm -rf %s' % workspace)
        print('[KSYM]Cleanup %s done.' % workspace)
    
    def rand(self, sep='.'):
        return sep.join([str(random.randint(0,999)) for i in range(4)])
    
    def write(self, path, lines):
        fd = open(path, 'w')
        fd.write('\n'.join(lines))
        fd.close()

if __name__ == '__main__':
    Hook().run()
