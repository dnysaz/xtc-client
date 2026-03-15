# Makefile for XtermChat (xtc)

PWD=$(shell pwd)
TARGET=/usr/local/bin/xtc
SCRIPT=$(PWD)/xtc.py

.PHONY: install uninstall deps help

help:
	@echo "Usage:"
	@echo "  make install    - Install dependencies + xtc command globally"
	@echo "  make uninstall  - Remove xtc command"
	@echo "  make deps       - Install dependencies only (no symlink)"

# ── Install dependencies only ─────────────────────────────────────────────────
deps:
	@echo "\033[34m[*] Installing Python dependencies...\033[0m"
	@pip3 install --quiet prompt_toolkit requests flask
	@echo "\033[32m[*] Python dependencies installed.\033[0m"

	@# Linux only: install xclip for clipboard support
	@if [ "$$(uname)" = "Linux" ]; then \
		echo "[*] Detected Linux — checking clipboard utility..."; \
		if ! command -v xclip > /dev/null 2>&1 && ! command -v xsel > /dev/null 2>&1; then \
			echo "[*] Installing xclip for clipboard support..."; \
			sudo apt-get install -y xclip > /dev/null 2>&1 || \
			echo "\033[33m[!] Could not install xclip. Install manually: sudo apt install xclip\033[0m"; \
		else \
			echo "\033[32m[*] Clipboard utility already available.\033[0m"; \
		fi \
	fi

	@# macOS: pbcopy is built-in, just confirm
	@if [ "$$(uname)" = "Darwin" ]; then \
		echo "\033[32m[*] macOS detected — pbcopy available (built-in).\033[0m"; \
	fi

# ── Install deps + symlink ────────────────────────────────────────────────────
install: deps
	@if [ -L $(TARGET) ] || [ -f $(TARGET) ]; then \
		echo "\033[33m[!] Aborted: 'xtc' is already installed in $(TARGET).\033[0m"; \
		echo "[*] Use 'make uninstall' first if you want to reinstall."; \
		exit 1; \
	fi
	@echo "[*] Setting execution permission for xtc.py..."
	@chmod +x $(SCRIPT)
	@echo "[*] Creating symbolic link in $(TARGET)..."
	@sudo ln -s $(SCRIPT) $(TARGET)
	@echo ""
	@echo "\033[32m[*] DONE! XtermChat is ready.\033[0m"
	@echo "\033[2m    Run: xtc connect @your-server-ip:8080\033[0m"

# ── Uninstall ─────────────────────────────────────────────────────────────────
uninstall:
	@if [ ! -L $(TARGET) ] && [ ! -f $(TARGET) ]; then \
		echo "\033[31m[!] Error: 'xtc' is not installed.\033[0m"; \
		exit 1; \
	fi
	@echo "[*] Removing $(TARGET)..."
	@sudo rm -f $(TARGET)
	@echo "\033[32m[*] xtc has been uninstalled successfully.\033[0m"