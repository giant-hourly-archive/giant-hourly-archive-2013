#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) AboutCode and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://aboutcode.org for more information about nexB OSS projects.
#

usage = """
Rerun all failed workflows of a repo. Must set GITHUB_TOKEN

Usage example: python rerun.py foo/bar
"""

import os
import sys
import time

import requests


def rerun_failed_workflows(repo:str, headers:str, delay:int=30):
    """
    Rerun all failed workflows in ``repo`` waiting ``delay`` seconds between
    each call.
    """
    while True:
        failed_runs_url = f"https://api.github.com/repos/{repo}/actions/runs?status=failure&per_page=50"
        response = requests.get(failed_runs_url, headers=headers)
        response.raise_for_status()

        failed_runs = response.json().get("workflow_runs", [])
        if not failed_runs:
            print(f"No more failed failed_runs.")
            break

        for failed_run in failed_runs:
            rerun_url = failed_run.get("rerun_url")
            # this is our tag "2026-07-27"
            tag = failed_run.get("head_branch")
            html_url = failed_run.get("html_url")
            print(f"Rerunning failed run for {tag} at {html_url}")
            rerun_response = requests.post(rerun_url, headers=headers)
            rerun_response.raise_for_status()
            time.sleep(delay)


if __name__ == "__main__":

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10"
    }

    args = sys.argv[1:]
    if not len(args) == 1:
        print(usage)
        sys.exit(1)

    repo = args[0]

    print(f"Rerunning failed workflows for {repo}")
    rerun_failed_workflows(repo=repo, headers=headers)
    print(f"Done")

