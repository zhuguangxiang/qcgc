CFLAGS=-Wall -Wextra -std=gnu11 -Wmissing-declarations -Wmissing-prototypes -g -O0
SRC=qcgc.c arena.c allocator.c bag.c event_logger.c gray_stack.c shadow_stack.c hugeblocktable.c
LDFLAGS=-lrt

lib: $(SRC)
	$(CC) $(CFLAGS) -fpic -shared -o qcgc.so $^ $(LDFLAGS)

support:
	cd test && make $@

demo: lib
	$(CC) $(CFLAGS) -o demo/demo_list -I. demo/demo_list.c -L. -l:qcgc.so

.PHONY: test
test:
	cd test && make $@

.PHONY: doc
doc:
	doxygen Doxyfile

.PHONY: clean
clean:
	$(RM) -f *.so *.o *.gcov *.gcda *.gcno
	$(RM) -rf doc
	$(RM) perf.data*
	find . -name "qcgc_events.log" -type f -delete
	cd test && make $@
