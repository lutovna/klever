from core.avtg.emg.common.signature import import_signature, setup_collection


__grammar_tests = [
    'union {   void *arg;   struct kparam_string const *str;   struct kparam_array const *arr; }',
    'union {   s64 lock;    } arch_rwlock_t',
    'union {   s64 lock;   struct   {     u32 read;     s32 write;   }; } arch_rwlock_t',
    'struct { short unsigned int size; short unsigned int byte_cnt; short unsigned int threshold; } SR9800_BULKIN_SIZE[8U]',
    'unsigned char disable_hub_initiated_lpm : 1',
    'int a',
    'int a;',
    'int a:1',
    'int a:1;',
    'int a[6U]',
    'int int_a',
    'static int a',
    'static const int a',
    'static int const a',
    'int * a',
    'int ** a',
    'int * const a',
    'int * const * a',
    'int * const ** a',
    'int ** const ** a',
    'struct usb a',
    'const struct usb a',
    'const struct usb * a',
    'struct usb * const a',
    'union usb * const a',
    'mytypedef * a',
    'int a []',
    'int a [1]',
    'int a [const 1]',
    'int a [*]',
    'int a [const *]',
    'int a [const *][1]',
    'int a [const *][1][]',
    'static struct usb ** a [const 1][2][*]',
    'int (a)',
    'int *(*a)',
    'int *(**a)',
    'int *(* const a [])',
    'int *(* const a) []',
    'int *(* const a []) [*]',
    'int *(*(a))',
    'int (*(*(a) [])) []',
    'int (*(*(*(a) []))) []',
    'int a(int)',
    'int a(int, int)',
    'int a(void)',
    'void a(void)',
    'void a(int, ...)',
    'void (*a) (int, ...)',
    "int func(int, void (*)(void))",
    "int func(void (*)(void), int)",
    "int func(int, int (*)(int))",
    "int func(int, void (*)(void *))",
    "int func(int *, void (*)(void))",
    "int func(int, int (*)(int))",
    "int func(int *, int (*)(int, int))",
    "int func(int *, int (*)(int, int), ...)",
    "int (*f)(int *)",
    "int (*f)(int *, int *)",
    "int func(struct nvme_dev *, void *)",
    "int (*f)(struct nvme_dev *, void *)",
    "void (**a)(struct nvme_dev *, void *)",
    "void (**a)",
    "void func(struct nvme_dev *, void *, struct nvme_completion *)",
    "void (**a)(void)",
    "void (**a)(struct nvme_dev * a)",
    "void (**a)(struct nvme_dev * a, int)",
    "void (**a)(struct nvme_dev * a, void * a)",
    "void (**a)(struct nvme_dev *, void *)",
    "void (**a)(struct nvme_dev *, void *, struct nvme_completion *)",
    "void (**a)(struct nvme_dev *, void *, int (*)(void))",
    "int func(int (*)(int))",
    "int func(int (*)(int *), ...)",
    "int func(int (*)(int, ...))",
    "int func(int (*)(int, ...), ...)",
    "int (*a)(int (*)(int, ...), ...)",
    'void (*((*a)(int, ...)) []) (void) []',
    '%usb.driver%',
    '$ my_function($, %usb.driver%, int)',
    '%usb.driver% function(int, void *)',
    '%usb.driver% function(int, $, %usb.driver%)'
]

setup_collection({}, {})
for test in __grammar_tests:
    print(test)
    object = import_signature(test)
    #print(object.pretty_name)
    print(object.identifier)
    print(object.to_string('a'))