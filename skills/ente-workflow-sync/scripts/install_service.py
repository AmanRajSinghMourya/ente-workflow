#!/usr/bin/env python3
"""Install this user's five-minute workflow file sync after a successful manual run."""

import argparse
import os
from pathlib import Path
import plistlib
import subprocess
import sys

from sync import DEFAULT_ROOT, SyncError, read_config, validate_repository

LABEL = 'com.aman.ente-workflow-sync'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        validate_repository(root, read_config(root))
        status = root / '.workflow/sync-status.json'
        import json
        if not status.is_file() or json.loads(status.read_text()).get('status') != 'ok':
            raise SyncError('Run and verify manual sync before installing the service')
        script = root / 'skills/ente-workflow-sync/scripts/sync.py'
        definition = {
            'Label': LABEL,
            'ProgramArguments': [sys.executable, '-B', str(script), '--root', str(root), 'sync'],
            'WorkingDirectory': str(root),
            'StartInterval': 300,
            'RunAtLoad': True,
            'ProcessType': 'Background',
            'EnvironmentVariables': {
                'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
                'PYTHONDONTWRITEBYTECODE': '1',
            },
        }
        path = Path.home() / 'Library/LaunchAgents' / (LABEL + '.plist')
        if path.exists():
            old = plistlib.loads(path.read_bytes())
            if old.get('Label') != LABEL or old.get('WorkingDirectory') != str(root):
                raise SyncError('Existing service belongs to a different workflow; left unchanged')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(plistlib.dumps(definition))
        subprocess.run(['plutil', '-lint', str(path)], check=True, capture_output=True)
        domain = 'gui/' + str(os.getuid())
        running = subprocess.run(['launchctl', 'print', domain + '/' + LABEL], capture_output=True)
        if running.returncode == 0:
            subprocess.run(['launchctl', 'bootout', domain + '/' + LABEL], check=True, capture_output=True)
        subprocess.run(['launchctl', 'bootstrap', domain, str(path)], check=True, capture_output=True)
        subprocess.run(['launchctl', 'print', domain + '/' + LABEL], check=True, capture_output=True)
        print('Installed workflow sync every five minutes while this user is logged in.')
        return 0
    except (SyncError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print('Service setup stopped: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
