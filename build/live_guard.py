#!/usr/bin/env python3
"""Stop a deploy when the live site was not deployed by this workflow.

    npx wrangler deployments list --name fort-web --json | python3 build/live_guard.py

Every deploy from fort-site carries the message "fort-site <sha> + fort <sha>".
If the newest live deployment has another message (a manual deploy, a rollback,
or the first deploy after the move from web-pages), the live site may hold
something that is not in git. The deploy then waits until someone has compared
dist/ with the live site (verify_live.py --report) and reruns the workflow with
live_version_reviewed set to the live version id this script prints.
"""
import json
import os
import sys

PREFIX = 'fort-site '


def main():
    deployments = json.load(sys.stdin)
    if not deployments:
        sys.exit('no deployments listed for fort-web')
    latest = max(deployments, key=lambda d: d['created_on'])
    versions = [v['version_id'] for v in latest.get('versions', [])]
    message = latest.get('annotations', {}).get('workers/message', '')
    reviewed = os.environ.get('LIVE_VERSION_REVIEWED', '').strip()
    print(f'live: versions {", ".join(versions)} from {latest["created_on"]}, message {message!r}')
    if message.startswith(PREFIX) and len(versions) == 1:
        print('live site was deployed by fort-site: deploying')
        return
    if reviewed and versions == [reviewed]:
        print(f'live version {reviewed} was compared and reviewed: deploying')
        return
    sys.exit(f'live version {", ".join(versions)} was not deployed by fort-site. Compare the build '
             f'with the live site (the "Compare with live" step above), then run this workflow on '
             f'main with live_version_reviewed={versions[0] if versions else "?"}.')


if __name__ == '__main__':
    main()
