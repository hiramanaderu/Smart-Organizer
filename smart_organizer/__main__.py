"""CLI / interactive entry point."""
import sys
from .cli import run_cli
from .tui import run_tui

def main():
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_tui()

if __name__ == "__main__":
    main()
