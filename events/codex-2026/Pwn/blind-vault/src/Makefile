CC := gcc
CFLAGS := -O0 -fno-stack-protector -fPIE -pie
LDFLAGS := -Wl,-z,relro,-z,now -Wl,-z,noexecstack

.PHONY: all clean checksec
TARGET := ../dist/vault

all: $(TARGET)

$(TARGET): challenge.c | ../dist
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)
	strip --strip-all $@

../dist:
	mkdir -p $@

clean:
	rm -f $(TARGET)

checksec: $(TARGET)
	@file $(TARGET)
