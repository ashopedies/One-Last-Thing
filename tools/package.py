#!/usr/bin/env python3
"""Build install/source ZIPs from an explicit first-party file allowlist."""
import argparse
import hashlib
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent


def build(version, source=False, output=None):
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Version must be MAJOR.MINOR.PATCH')
    for toc in sorted((ROOT/'OneLastThing').glob('*.toc')):
        text = toc.read_text()
        if not re.search(r'^## Version: '+re.escape(version)+r'\s*$', text, re.M):
            raise ValueError(f'Version does not match {toc.relative_to(ROOT)}')
        for entry in text.splitlines():
            entry = entry.strip()
            if entry and not entry.startswith('#') and not (toc.parent/entry).is_file():
                raise ValueError(f'Missing TOC entry: {toc.name}: {entry}')
    core = (ROOT/'OneLastThing/Core.lua').read_text()
    if not re.search(r"A.version\s*=\s*['\"]"+re.escape(version)+r"['\"]", core):
        raise ValueError('Core.lua version mismatch')
    changelog = (ROOT/'CHANGELOG.md').read_text()
    if not changelog.startswith('# Changelog\n\n## '+version+' '):
        raise ValueError('Latest changelog entry does not match version')
    if (ROOT/'OneLastThing/CHANGELOG.md').read_text() != changelog:
        raise ValueError('Root and addon changelogs differ')
    if f'ONE LAST THING — {version}' not in (ROOT/'OneLastThing/README.txt').read_text():
        raise ValueError('Addon README version mismatch')

    # No downloaded addons, game account files, historical archives or machine paths.
    files = []
    for path in sorted((ROOT/'OneLastThing').iterdir()):
        if path.is_file() and path.suffix in {'.lua', '.toc', '.xml', '.md', '.txt'}:
            files.append((path, path.relative_to(ROOT).as_posix()))
    if source:
        for folder in ['tests', 'tools', 'docs', '.github']:
            for path in sorted((ROOT/folder).rglob('*')):
                if path.is_file() and path.suffix in {'.lua', '.toc', '.py', '.md', '.yml', '.yaml'}:
                    files.append((path, path.relative_to(ROOT).as_posix()))
        for name in ['README.md', 'CHANGELOG.md', 'LICENSE', '.gitignore', 'requirements-dev.txt']:
            files.append((ROOT/name, name))
    else:
        files.append((ROOT/'LICENSE', 'OneLastThing/LICENSE'))

    dest = Path(output) if output else ROOT/'dist'
    dest.mkdir(parents=True, exist_ok=True)
    suffix = 'source' if source else 'forever'
    archive = dest/f'OneLastThing-{version}-{suffix}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as out:
        for path, name in files:
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(info, path.read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    section = changelog.split('\n## ', 2)[1]
    notes = section.split('\n', 1)[1].strip()+'\n'
    (dest/'release-notes.md').write_text(notes)
    print(f'{archive.name}: {len(files)} files, {archive.stat().st_size} bytes')
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--source', action='store_true', help='Build a GitHub-ready source archive')
    parser.add_argument('--output', help='Destination folder (default: dist)')
    args = parser.parse_args()
    build(args.version, args.source, args.output)
