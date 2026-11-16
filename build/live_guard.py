#!/usr/bin/env python3
"""Stop a deploy when the live site was not deployed by this workflow.

    npx wrangler deployments list --name fort-web --json | python3 build/live_guard.py

Every deploy from fort-site carries the message "fort-site <sha> + fort <sha>".
If the newest live deployment has another message (a manual deploy, a rollback,
or the first deploy after the move from web-pages), the live site may hold
something that is not in git. The deploy then waits until an admin has compared
dist/ with the live site (the build's "Compare with live" step) and set the live
version id this script prints as the variable LIVE_VERSION_REVIEWED of the
`production` environment, then reruns the workflow.
"""
import json
import os
import sys

PREFIX = 'fort-site '


def decide(deployments, reviewed):
    """Returns (deploy?, explanation) for the newest live deployment."""
    if not deployments:
        return False, 'no deployments listed for fort-web'
    latest = max(deployments, key=lambda d: d['created_on'])
    versions = [v['version_id'] for v in latest.get('versions', [])]
    message = latest.get('annotations', {}).get('workers/message', '')
    live = f'live: versions {", ".join(versions)} from {latest["created_on"]}, message {message!r}'
    if message.startswith(PREFIX) and len(versions) == 1:
        return True, f'{live}\nlive site was deployed by fort-site: deploying'
    if reviewed and versions == [reviewed]:
        return True, f'{live}\nlive version {reviewed} was compared and reviewed: deploying'
    return False, (f'{live}\nlive version {", ".join(versions)} was not deployed by fort-site. Compare '
                   f'the build with the live site (the build job\'s "Compare with live" step), set '
                   f'the production environment variable '
                   f'LIVE_VERSION_REVIEWED={versions[0] if versions else "?"}, and rerun this workflow.')


def main():
    ok, explanation = decide(json.load(sys.stdin), os.environ.get('LIVE_VERSION_REVIEWED', '').strip())
    print(explanation)
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
