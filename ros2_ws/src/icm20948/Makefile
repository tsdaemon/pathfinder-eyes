CC = gcc
CFLAGS = -Wall -Wextra -fPIC -lm -std=gnu99

icm20948/ICM20948.so: icm20948/ICM20948.c icm20948/ICM20948.h
	$(CC) -shared -o icm20948/ICM20948.so icm20948/ICM20948.c $(CFLAGS)
clean:
	rm -f icm20948/ICM20948.so