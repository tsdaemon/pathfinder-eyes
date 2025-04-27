-include .env

PORT ?= COM6

.PHONY: flash
flash:
	mpremote connect $(PORT) fs cp *.py :
	make reset

.PHONY: reset
reset:
	mpremote connect $(PORT) reset

.PHONY: test-uart
test-uart:
	mpremote connect $(PORT) fs cp test_uart.py :main.py
	make reset

repl:
	mpremote connect $(PORT) repl
