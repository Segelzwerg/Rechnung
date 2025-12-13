set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

_default:
    @just --list

fmt:
    uv run ruff check --select I --fix
    uv run ruff format

lint:
    uv run ruff format --check
    uv run ruff check

lint-fix: fmt
    uv run ruff check --fix
