from support import lib,ffi
from qcgc_test import QCGCTest
import unittest

class ObjectTestCase(QCGCTest):
    def test_write_barrier(self):
        o = self.allocate(16)
        self.push_root(o)
        arena = lib.qcgc_arena_addr(ffi.cast("cell_t *", o))
        o.hdr.flags = o.hdr.flags & ~lib.QCGC_GRAY_FLAG
        self.assertEqual(ffi.cast("object_t *", o).flags & lib.QCGC_GRAY_FLAG, 0)
        lib.qcgc_write(ffi.cast("object_t *", o))
        self.assertEqual(ffi.cast("object_t *", o).flags & lib.QCGC_GRAY_FLAG, lib.QCGC_GRAY_FLAG)

        lib.qcgc_state.phase = lib.GC_MARK
        o = self.allocate(16)
        self.push_root(o)
        arena = lib.qcgc_arena_addr(ffi.cast("cell_t *", o))
        o.hdr.flags = o.hdr.flags & ~lib.QCGC_GRAY_FLAG
        self.assertEqual(ffi.cast("object_t *", o).flags & lib.QCGC_GRAY_FLAG, 0)
        self.set_blocktype(ffi.cast("cell_t *", o), lib.BLOCK_BLACK)
        lib.qcgc_state.phase = lib.GC_MARK
        lib.qcgc_write(ffi.cast("object_t *", o))
        self.assertEqual(ffi.cast("object_t *", o).flags & lib.QCGC_GRAY_FLAG, lib.QCGC_GRAY_FLAG)
        self.assertEqual(lib.arena_gray_stack(arena).count, 1)
        self.assertEqual(lib.arena_gray_stack(arena).items[0], o)

if __name__ == "__main__":
    unittest.main()
