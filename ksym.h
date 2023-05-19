#ifndef __KSYM_H__
#define __KSYM_H__

#define KSYM_NAME(name) ___KSYM_IMPORT_ADDR_3578___##name##___2904___
#define KVAR_IMPORT(type,name) type * KSYM_NAME(name)
#define KFUN_IMPORT(type,name,proto) type (*KSYM_NAME(name)) proto
#define KSYM_REF(name) (*KSYM_NAME(name))

#endif // __KSYM_H__
