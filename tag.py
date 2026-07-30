#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) AboutCode and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://aboutcode.org for more information about nexB OSS projects.
#

usage = """
Tag git repositories for each day in a year from a start date.

Usage example: python tag.py 2026-01-01
"""

import subprocess
import sys
import time

from datetime import date
from datetime import timedelta


def make_full_date(iso: str):
    """
    Return an iso date as YYYY-MM-DD given an ``iso`` string input, backfilling
    the month and date to January 1st or 1st of the month if they are missing.
    """
    if len(iso) == 4:
        # plain YYYY, start on 1st day of the year
        iso = f"{iso}-01-01"
    elif len(iso) == 7:
        # plain YYYY-YY, start on 1st day of the month
        iso = f"{iso}-01"
    return iso


def days_in_year_since(start:str, end:str=None):
    """
    Yield all the days in a year since a ``start`` ISO date (including that
    date) or up to an ``end`` date. If no end date is provided, or a
    future year beyond the start year, only ever goes to the end of the start
    year. Accepts a plain year or plain year-month without day too.

    For example::

    >>> list(days_in_year_since("2012-12-25"))
    ['2012-12-25', '2012-12-26', '2012-12-27', '2012-12-28', '2012-12-29', '2012-12-30', '2012-12-31']
    >>> list(days_in_year_since("2010-12-25"))
    ['2010-12-25', '2010-12-26', '2010-12-27', '2010-12-28', '2010-12-29', '2010-12-30', '2010-12-31']
    >>> list(days_in_year_since("2010-12-31"))
    ['2010-12-31']
    >>> len(list(days_in_year_since("2027")))
    365
    >>> len(list(days_in_year_since("2027-01")))
    365
    >>> len(list(days_in_year_since("2024-01")))
    366
    >>> len(list(days_in_year_since("2024-05")))
    245
    >>> len(list(days_in_year_since("2024-05-17")))
    229
    >>> list(days_in_year_since(start="2012-12-25", end="2012-12-28"))
    ['2012-12-25', '2012-12-26', '2012-12-27', '2012-12-28']
    """
    start = make_full_date(start)
    start_date = date.fromisoformat(start)

    if not end:
        end_date = date(start_date.year + 1, 1, 1)
    else:
        end = make_full_date(end)
        end_date = date.fromisoformat(end)
        if end_date.year != start_date.year:
            raise Exception(f"Invalid end date. start: {start} and end:{end} are not in the same year")
        # account for strict inferior test
        end_date += timedelta(days=1)

    current_date = start_date
    while current_date < end_date:
        yield current_date.isoformat()
        current_date += timedelta(days=1)


def tag_and_push(day_tag: str, git_remote:str="ssh", force:bool=False):
    """
    Tag and push a git tag ``day_tag`` using the "ssh" remote in the current
    directory.
    """
    print(f"  Tagging and pushing: {day_tag}")
    try:
        if force:
            cmd = f'git tag -f {day_tag} -m "{day_tag}"'
        else:
            cmd = f"git tag {day_tag}"
        subprocess.run(cmd, shell=True)
    except:
        # ignore if tags already exists
        pass

    if force:
        cmd = f"git push -f {git_remote} {day_tag}"
    else:
        # this has no effect if already pushed
        cmd = f"git push {git_remote} {day_tag}"

    subprocess.run(cmd, shell=True)


def tag_and_push_year(start: str, end: str=None, delay=40, force:bool=False):
    """
    Tag and push a tag for each day of a year from ``start`` date. Wait
    ``delay`` seconds between each.
    """
    for day in days_in_year_since(start=start, end=end):
        tag_and_push(day_tag=day, force=force)
        time.sleep(delay)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not len(args) in (1, 2, 3):
        print(usage)
        sys.exit(1)

    start = args[0]

    end = None
    if len(args) == 2:
        end = args[1]

    force = False
    if len(args) == 3:
        force = bool(args[2])

    print(f"Tagging and pushing from: {start} until: {end}")
    tag_and_push_year(start=start, end=end, force=force)
    print(f"Done")
