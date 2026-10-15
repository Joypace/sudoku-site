#!/usr/bin/env python3
"""Read-only website review check against an explicitly selected App revision."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    'Touch controls, boards, history, hints and Help': (
        'lib/widgets/tips/', 'lib/widgets/pause_tips.dart', 'lib/widgets/board',
        'lib/widgets/tray', 'lib/widgets/panel', 'lib/widgets/overlay',
        'lib/widgets/note', 'lib/widgets/reveal', 'lib/widgets/play',
        'lib/engine/play_', 'lib/widgets/options/assist', 'lib/widgets/theme',
        'docs/ued/tips/'),
    'Journey': ('lib/widgets/journey/', 'lib/model/journey/'),
    'Library': ('lib/widgets/library/', 'lib/engine/library_'),
    'Create, import and share': ('lib/widgets/mine/', 'lib/widgets/sharing/',
        'lib/engine/sharing', 'lib/engine/incoming_'),
    'Element assistants': ('lib/widgets/elements/',),
    'All wording and feature claims': ('lib/l10n/', 'assets/rules/',),
    'App identity, opening links, privacy and platform support': (
        'ios/Runner/', 'ios/Runner.xcodeproj/', 'android/app/build.gradle',
        'android/app/src/main/AndroidManifest.xml', 'lib/engine/ads/'),
    'All rendered sections': ('lib/widgets/chrome_palette', 'lib/main.dart',
        'lib/widgets/screen_skeleton', 'lib/widgets/app_header'),
}


def sections_for(paths):
    sections = set()
    for path in paths:
        matched = False
        for section, prefixes in GROUPS.items():
            if path.startswith(prefixes):
                sections.add(section)
                matched = True
        if path.startswith('assets/') and path != 'assets/content' and not matched:
            sections.add('Other shipped artwork, fonts and effects: review rendered sections')
        if not matched and path.startswith(('lib/', 'pubspec.')):
            sections.add('Other App behavior/dependencies: check website claims and privacy')
    return sorted(sections)


def git(app, *args):
    return subprocess.check_output(['git', '-C', str(app), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--ref', required=True, help='Exact locally available verified App revision/ref; no fetch is performed')
    args = parser.parse_args()
    source = json.loads((ROOT / 'app-source.json').read_text())
    target = git(args.app, 'rev-parse', '--verify', args.ref + '^{commit}')
    paths = git(args.app, 'diff', '--name-only', source['reviewedApp'], target).splitlines()
    sections = sections_for(paths)
    content = git(args.app, 'rev-parse', target + ':assets/content')
    if content != source['reviewedContent']:
        sections.append('Bundled artwork, catalogue and tip scenarios: review content diff')
    print('Reviewed App:', source['reviewedApp'])
    print('Candidate App:', target)
    if sections:
        print('Website review required:')
        for section in sorted(set(sections)):
            print(' -', section)
        print('Review relevant changes; regenerate affected captures and run local website checks before publication.')
        return 2
    print('No website review triggered by the changed paths/content. Nothing was built or published.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
