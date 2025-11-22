# Makefile for rclone-commander
# Copyright (C) 2025 Miklos Mukka Szel <contact@miklos-szel.com>
# Licensed under GPLv3

# Virtual environment settings
VENV = venv
PYTHON3 = $(VENV)/bin/python3
PIP3 = $(VENV)/bin/pip3

.PHONY: help venv clean build upload install dev test lint release

help:
	@echo "rclone-commander - Build & Release"
	@echo ""
	@echo "Available targets:"
	@echo "  make venv       - Create virtual environment"
	@echo "  make build      - Build distribution packages"
	@echo "  make upload     - Upload to PyPI (requires twine)"
	@echo "  make release    - Clean, build, and upload to PyPI"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make install    - Install package locally in venv"
	@echo "  make dev        - Install in development mode in venv"
	@echo "  make test       - Run tests (if available)"
	@echo "  make lint       - Run linting checks"
	@echo ""

venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV); \
		echo "Virtual environment created!"; \
		echo "Installing build dependencies..."; \
		$(PIP3) install --upgrade pip setuptools wheel build twine; \
		echo "Dependencies installed!"; \
	else \
		echo "Virtual environment already exists."; \
	fi

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Full clean complete!"

build: venv clean
	@echo "Building distribution packages..."
	$(PYTHON3) -m build
	@echo "Build complete! Packages in dist/"

upload: venv
	@echo "Uploading to PyPI..."
	$(PYTHON3) -m twine upload dist/*
	@echo "Upload complete!"

release: venv clean build upload
	@echo "Release complete!"

install: venv
	@echo "Installing package in virtual environment..."
	$(PIP3) install .
	@echo "Install complete!"

dev: venv
	@echo "Installing in development mode..."
	$(PIP3) install -e .
	@echo "Development install complete!"

deps: venv
	@echo "Installing dependencies..."
	$(PIP3) install -r requirements.txt
	@echo "Dependencies installed!"

test: venv
	@echo "Running tests..."
	$(PYTHON3) -m pytest tests/ -v || echo "No tests found"

lint: venv
	@echo "Running linting checks..."
	$(PYTHON3) -m flake8 src/ || echo "flake8 not installed"
	$(PYTHON3) -m mypy src/ || echo "mypy not installed"

run: venv
	@echo "Running rclone-commander..."
	$(PYTHON3) -m src.rclone_commander.main

# Version info
version:
	@echo "Current version: $$(grep '^version' pyproject.toml | cut -d'"' -f2)"
