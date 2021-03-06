import unittest
from support import lib, ffi
from qcgc_test import QCGCTest

class BumpAllocatorTest(QCGCTest):
    def test_bump_allocator_internals(self):
        arena = lib.qcgc_arena_create()
        first_cell = lib.arena_cells(arena)[lib.qcgc_arena_first_cell_index]
        size = lib.qcgc_arena_cells_count - lib.qcgc_arena_first_cell_index
        lib.bump_allocator_assign(ffi.addressof(first_cell), size)

        self.assertEqual(ffi.addressof(first_cell), lib._qcgc_bump_allocator.ptr)
        self.assertEqual(size, self.bump_remaining_cells())

        p = self.bump_allocate(16)
        self.assertEqual(ffi.addressof(first_cell), p)
        self.assertEqual(size - 1, self.bump_remaining_cells())

        q = self.bump_allocate((2**lib.QCGC_LARGE_ALLOC_THRESHOLD_EXP))
        self.assertEqual(ffi.addressof(lib.arena_cells(arena)[lib.qcgc_arena_first_cell_index + 1]), q)
        self.assertEqual(size - 1 - 2**(lib.QCGC_LARGE_ALLOC_THRESHOLD_EXP - 4), self.bump_remaining_cells())

    def test_alloc_full_arena(self):
        size = 16 * (lib.qcgc_arena_cells_count - lib.qcgc_arena_first_cell_index)
        i = 0
        while (size > 2**lib.QCGC_LARGE_ALLOC_THRESHOLD_EXP):
            i = (i + 16) % (2**lib.QCGC_LARGE_ALLOC_THRESHOLD_EXP)
            if i == 0:
                i += 16
            p = self.bump_allocate(i)
            self.assertNotEqual(p, ffi.NULL)
            size -= i
        self.bump_allocate(size)
        self.bump_allocate(size)

    def test_many_small_allocations(self):
        objects = set()
        p = self.bump_allocate(16)
        arena = lib.qcgc_arena_addr(ffi.cast("cell_t *", p))
        objects.add(p)

        for _ in range(1000):
            p = self.bump_allocate(16)
            objects.add(p)
            self.assertEqual(arena, lib.qcgc_arena_addr(ffi.cast("cell_t *", p)))

        self.assertFalse(ffi.NULL in objects)
        self.assertEqual(len(objects), 1001)

    def test_reuse_old_free_space(self):
        arena = lib.qcgc_arena_create()
        first_cell = lib.arena_cells(arena)[lib.qcgc_arena_first_cell_index]
        size = lib.qcgc_arena_cells_count - lib.qcgc_arena_first_cell_index
        lib.qcgc_fit_allocator_add(ffi.addressof(first_cell), size)

        lib.bump_ptr_reset()
        p = self.bump_allocate(16)
        self.assertEqual(ffi.addressof(first_cell), p)

if __name__ == "__main__":
    unittest.main()

