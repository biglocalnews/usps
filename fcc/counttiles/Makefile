CC      = gcc
CFLAGS  = -Wall -Wextra -g -pedantic
LDFLAGS = -shared
TARGET  = counttiles.so
SOURCES = counttiles.c
OBJECTS = $(SOURCES:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) $(OBJECTS) -o $@ $(LDFLAGS)

clean:
	rm $(TARGET)
	rm $(OBJECTS)
