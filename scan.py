#!/usr/bin/env python3

import subprocess
import argparse
from pathlib import Path
import shutil
import tempfile
import json
import atexit

# https://semgrep.dev/docs/writing-rules/rule-syntax/#required
SEVERITY_MAP = {
    'INFO': 'INFO',
    'WARNING': 'MINOR',
    'ERROR': 'BLOCKER',
}


def convert_category(category):
    # category is free-format in semgrep
    # only special one (and the one security cares the most) is `security`
    if category == 'security':
        return 'VULNERABILITY'
    return 'CODE_SMELL'


def parser():
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('api_key', metavar='api-key', type=str, help='API key to upload analysis')
    p.add_argument('source', type=Path, help='Path to sources to scan')
    p.add_argument('report', type=Path, help='Path to semgrep report (JSON format)')
    p.add_argument('--scanner-bin', type=Path, default='sonar-scanner', help='Path to sonar-scanner binary (if not in $PATH)')
    p.add_argument('--sonar-host', type=str, default='http://localhost:9000', help='Sonar server URL')
    p.add_argument('--sonar-project', type=str, default='testing', help='Sonar project key')
    p.add_argument('-c', '--convert-only', type=Path, help='Convert JSON report only and save it in this path (both api_key and source arguments ignored)')
    return p


def convert_json(args, destination: Path = None):
    if destination is None:
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        sonar_report = Path(f.name)
        # delete on script exit, after it is used by sonar-scanner
        atexit.register(lambda: sonar_report.unlink())
    else:
        sonar_report = destination

    report = json.loads(args.report.read_text())

    path_prefix = args.source.absolute()
    
    issues = []
    for issue in report['results']:
        _path = Path(issue['path'])
        try:
            # if semgrep was executed with full path, report will have full paths
            # sonar-scanner needs relative paths
            _path = _path.relative_to(path_prefix)
        except ValueError:
            pass

        issues.append({
            'engineId': 'semgrep',
            'ruleId': issue['check_id'],
            'severity': SEVERITY_MAP[issue['extra']['severity']],
            'type': convert_category(issue['extra']['metadata'].get('category')),
            'primaryLocation': {
                'message': issue['extra']['message'],
                'filePath': str(_path),
                'textRange': {
                    'startLine': issue['start']['line'],
                    'endLine': issue['end']['line'],

                    # FIXME: something weird with semgrep line numbering versus sonar...
                    # semgrep is 1-index on the line numbering but import those in sonar:
                    # * for some it's the line after (that would be ok if 0-indexed)
                    # * for others it's the line before....

                    # 'startColumn': issue['start']['col'] - 1,
                    # 'endColumn': issue['end']['col'] - 1,
                }
            },
        })

    sonar_report.write_text(
        json.dumps({
            'issues': issues,
        })
    )
    return sonar_report


def main(argv=None):
    p = parser()
    args, extra_args = p.parse_known_args(argv)
    if not args.convert_only:
        scanner_bin = shutil.which(args.scanner_bin)
        if scanner_bin is None:
            p.error(f'{args.scanner_bin} not found, use --scanner-bin with a valid path')

    sonar_report = convert_json(args, destination=args.convert_only)

    if args.convert_only:
        return

    sonar_argv = [
        scanner_bin,
        f'-Dsonar.projectKey={args.sonar_project}',
        f'-Dsonar.externalIssuesReportPaths={sonar_report.absolute()}',
        f'-Dsonar.host.url={args.sonar_host}',
        f'-Dsonar.login={args.api_key}',
    ]
    sonar_argv.extend(extra_args or [])
    subprocess.check_call(
        sonar_argv,
        cwd=args.source
    )


if __name__ == '__main__':
    main()
