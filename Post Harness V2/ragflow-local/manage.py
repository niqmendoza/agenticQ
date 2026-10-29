#!/usr/bin/env python3
"""Start/inspect/stop only the qa-ragflow-local Compose project."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'stop', 'status', 'logs'])
    args = parser.parse_args()
    action = {'start': ['up', '-d'], 'stop': ['stop'], 'status': ['ps'],
              'logs': ['logs', '--tail', '60', 'ragflow']}[args.action]
    return subprocess.call(['docker', 'compose', '-f', str(ROOT / 'compose.json'), *action], cwd=ROOT)


if __name__ == '__main__':
    raise SystemExit(main())
