from cffi import FFI

ffi = FFI()

################################################################################
# config.h                                                                     #
################################################################################
ffi.cdef("""
        #define QCGC_ARENA_SIZE_EXP 20	// Between 16 (64kB) and 20 (1MB)
        #define QCGC_MARK_LIST_SEGMENT_SIZE 64
        #define QCGC_INC_MARK_MIN 64	// TODO: Tune for performance
        """)

################################################################################
# object                                                                       #
################################################################################
ffi.cdef("""
        #define QCGC_GRAY_FLAG 0x01

        typedef struct object_s {
                uint32_t flags;
        } object_t;
        """)

################################################################################
# gray_stack                                                                   #
################################################################################
ffi.cdef("""
        typedef struct gray_stack_s {
                size_t index;
                size_t size;
                object_t *items[];
        } gray_stack_t;

        gray_stack_t *qcgc_gray_stack_create(size_t size);

        gray_stack_t *qcgc_gray_stack_push(gray_stack_t *stack, object_t *item);
        object_t *qcgc_gray_stack_top(gray_stack_t *stack);
        gray_stack_t *qcgc_gray_stack_pop(gray_stack_t *stack);
        """)

################################################################################
# bag                                                                          #
################################################################################
ffi.cdef("""
        typedef struct bag_s {
            size_t size;
            size_t count;
            void *items[];
        } bag_t;

        bag_t *qcgc_bag_create(size_t size);

        bag_t *qcgc_bag_add(bag_t *bag, void *item);
        bag_t *qcgc_bag_remove(bag_t *bag, void *item);
        bag_t *qcgc_bag_remove_index(bag_t *bag, size_t index);
        """)

################################################################################
# arena                                                                        #
################################################################################
ffi.cdef(""" const size_t qcgc_arena_size;
        const size_t qcgc_arena_bitmap_size;
        const size_t qcgc_arena_cells_count;
        const size_t qcgc_arena_first_cell_index;

        typedef uint8_t cell_t[16];

        typedef union arena_u arena_t;

        typedef enum blocktype {
                BLOCK_EXTENT,
                BLOCK_FREE,
                BLOCK_WHITE,
                BLOCK_BLACK,
        } blocktype_t;

        cell_t *arena_cells(arena_t *arena);
        uint8_t *arena_mark_bitmap(arena_t *arena);
        uint8_t *arena_block_bitmap(arena_t *arena);
        gray_stack_t *arena_gray_stack(arena_t *arena);

        arena_t *qcgc_arena_create(void);
        void qcgc_arena_destroy(arena_t *arena);

        arena_t *qcgc_arena_addr(cell_t *);
        size_t qcgc_arena_cell_index(cell_t *);
        bool qcgc_arena_get_bitmap_entry(uint8_t *, size_t);
        void qcgc_arena_set_bitmap_entry(uint8_t *, size_t, bool);

        void qcgc_arena_mark_allocated(cell_t *ptr, size_t cells);
        void qcgc_arena_mark_free(cell_t *ptr);

        blocktype_t qcgc_arena_get_blocktype(cell_t *ptr);
        void qcgc_arena_set_blocktype(cell_t *ptr, blocktype_t type);

        bool qcgc_arena_is_empty(arena_t *arena);
        bool qcgc_arena_is_coalesced(arena_t *arena);
        size_t qcgc_arena_free_blocks(arena_t *arena);
        size_t qcgc_arena_white_blocks(arena_t *arena);
        size_t qcgc_arena_black_blocks(arena_t *arena);

        bool qcgc_arena_sweep(arena_t *arena);

        size_t qcgc_arena_sizeof(void);
        """)

################################################################################
# gc_state                                                                     #
################################################################################
ffi.cdef("""
        typedef enum gc_state {
                GC_PAUSE,
                GC_MARK,
                GC_COLLECT,
        } gc_state_t;

        struct qcgc_state {
                object_t **shadow_stack;
                object_t **shadow_stack_base;
                bag_t *arenas;
                size_t current_cell_index;
                size_t gray_stack_size;
                gc_state_t state;
        } qcgc_state;

        """)

################################################################################
# bump_allocator                                                               #
################################################################################
ffi.cdef("""
        struct qcgc_balloc_state {
            cell_t *bump_ptr;
            size_t remaining_cells;
        } qcgc_balloc_state;

        void qcgc_balloc_assign(cell_t *bump_ptr, size_t cells);
        void *qcgc_balloc_allocate(size_t cells);
        bool qcgc_balloc_can_allocate(size_t cells);
        """)

################################################################################
# mark_list                                                                    #
################################################################################
ffi.cdef("""
        typedef struct mark_list_s {
                size_t head;
                size_t tail;
                size_t length;
                size_t count;
                size_t insert_index;
                object_t **segments[];
        } mark_list_t;

        mark_list_t *qcgc_mark_list_create(size_t initial_size);
        void qcgc_mark_list_destroy(mark_list_t *list);

        mark_list_t *qcgc_mark_list_push(mark_list_t *list, object_t *object);
        mark_list_t *qcgc_mark_list_push_all(mark_list_t *list,
                        object_t **objects, size_t count);

        object_t **qcgc_mark_list_get_head_segment(mark_list_t *list);
        mark_list_t *qcgc_mark_list_drop_head_segment(mark_list_t *list);
        """)


################################################################################
# qcgc                                                                         #
################################################################################
ffi.cdef("""
        typedef enum mark_color {
                MARK_COLOR_WHITE,
                MARK_COLOR_LIGHT_GRAY,
                MARK_COLOR_DARK_GRAY,
                MARK_COLOR_BLACK,
        } mark_color_t;

        void qcgc_initialize(void);
        void qcgc_destroy(void);
        void qcgc_write(object_t *object);
        object_t *qcgc_allocate(size_t size);
        void qcgc_collect(void);
        mark_color_t qcgc_get_mark_color(object_t *object);

        // qcgc.c
        object_t *qcgc_bump_allocate(size_t size);
        void qcgc_mark(void);
        void qcgc_mark_all(void);
        void qcgc_mark_incremental(void);
        void qcgc_sweep(void);
        """)

################################################################################
# utilities                                                                    #
################################################################################

ffi.cdef("""
        // object
        typedef struct {
            object_t hdr;
            uint32_t type_id;
        } myobject_t;

        void _set_type_id(object_t *obj, uint32_t id);
        uint32_t _get_type_id(object_t *obj);
        """)

################################################################################
# set_source                                                                   #
################################################################################

ffi.set_source("support",
        """
        #include "../config.h"
        #include "../object.h"
        #include "../qcgc.h"
        #include "../arena.h"
        #include "../bump_allocator.h"
        #include "../mark_list.h"
        #include "../gray_stack.h"
        #include "../bag.h"

        // arena.h - Macro replacements
        const size_t qcgc_arena_size = QCGC_ARENA_SIZE;

        const size_t qcgc_arena_bitmap_size = QCGC_ARENA_BITMAP_SIZE;
        const size_t qcgc_arena_cells_count = QCGC_ARENA_CELLS_COUNT;
        const size_t qcgc_arena_first_cell_index = QCGC_ARENA_FIRST_CELL_INDEX;

        // qcgc.c prototoypes
        object_t *qcgc_bump_allocate(size_t size);
        void qcgc_mark(void);
        void qcgc_mark_all(void);
        void qcgc_mark_incremental(void);
        void qcgc_sweep(void);

        cell_t *arena_cells(arena_t *arena) {
            return arena->cells;
        }

        uint8_t *arena_mark_bitmap(arena_t *arena) {
            return arena->mark_bitmap;
        }

        uint8_t *arena_block_bitmap(arena_t *arena) {
            return arena->block_bitmap;
        }

        gray_stack_t *arena_gray_stack(arena_t *arena) {
            return arena->gray_stack;
        }

        size_t qcgc_arena_sizeof(void) {
            return sizeof(arena_t);
        }

        // Utilites
        typedef struct {
            object_t hdr;
            uint32_t type_id;
        } myobject_t;

        void _set_type_id(object_t *obj, uint32_t id);
        uint32_t _get_type_id(object_t *obj);

        void _set_type_id(object_t *object, uint32_t id) {
            ((myobject_t *) object)->type_id = id;
        }

        uint32_t _get_type_id(object_t *object) {
            return ((myobject_t *) object)->type_id;
        }

        void qcgc_trace_cb(object_t *object, void (*visit)(object_t *)) {
            myobject_t *o = (myobject_t *) object;
            if (o->type_id < 1<<16) {
                // Default object, no references
                return;
            } else {
                // Object containing only references
                object_t **members = (object_t **) o + 1;
                size_t fields = o->type_id - (1<<16);
                for (size_t i = 0; i < fields; i++) {
                    object_t *ref = members[i];
                    visit(ref);
                }
            }
        }

        """, sources=['../qcgc.c', '../arena.c', '../bump_allocator.c',
                '../mark_list.c', '../gray_stack.c', '../bag.c'],
        extra_compile_args=['--coverage','-std=gnu99', '-UNDEBUG', '-O0'],
        extra_link_args=['--coverage'])

if __name__ == "__main__":
    ffi.compile()
