"""Portable project-hook entrypoint; no network calls or optional imports."""
import sys
from slack_bridge.hooks import main

if __name__ == '__main__':
    main(sys.argv[1])
