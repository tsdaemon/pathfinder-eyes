CC = gcc
CFLAGS = -Wall -Wextra -fPIC -lm -std=gnu99

ICM20948.so: ICM20948.c ICM20948.h
	$(CC) -shared -o ICM20948.so ICM20948.c $(CFLAGS)
clean:
	rm -f ICM20948.so