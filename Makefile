# Makefile for XtermChat (xtc)

PWD=$(shell pwd)
TARGET=/usr/local/bin/xtc
SCRIPT=$(PWD)/xtc.py

.PHONY: install uninstall help

help:
	@echo "Usage:"
	@echo "  make install    - Install xtc command globally"
	@echo "  make uninstall  - Remove xtc command"

install:
	@if [ -L $(TARGET) ] || [ -f $(TARGET) ]; then \
		echo "\033[33m[!] Aborted: 'xtc' is already installed in $(TARGET).\033[0m"; \
		echo "[*] Use 'make uninstall' first if you want to reinstall."; \
		exit 1; \
	fi
	@echo "[*] Setting execution permission for xtc.py..."
	@chmod +x $(SCRIPT)
	@echo "[*] Creating symbolic link in $(TARGET)..."
	@sudo ln -s $(SCRIPT) $(TARGET)
	@echo "\033[32m[*] DONE! You can now use 'xtc' command.\033[0m"

uninstall:
	@if [ ! -L $(TARGET) ] && [ ! -f $(TARGET) ]; then \
		echo "\033[31m[!] Error: 'xtc' is not installed.\033[0m"; \
		exit 1; \
	fi
	@echo "[*] Removing $(TARGET)..."
	@sudo rm -f $(TARGET)
	@echo "\033[32m[*] xtc has been uninstalled successfully.\033[0m"