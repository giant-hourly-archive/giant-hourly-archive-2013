#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) AboutCode and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://aboutcode.org for more information about nexB OSS projects.
#

usage = """
Fetches the gharchive.org data files released for a day, verify their integrity
and computes a checksum file.

Usage example: python fetch.py 2026-01-01 dist/

This will fetch the 24 data files published on 2026-01-01 in the dist/ directory
"""

import hashlib
import re
import sys

from pathlib import Path
from xml.etree import ElementTree as ET

import requests

GHARCHIVE_URL = "https://data.gharchive.org"
NAMESPACE = {"s3": "http://doc.s3.amazonaws.com/2006-03-01"}


def get_files_for_prefix(prefix: str):
    """
    Yield tuples of (file name, MD5 hash) for all the gharchive files
    with a name start with ``prefix``.

    The files are store in an S3-like bucket, so we can use that API for filtering
    """
    # check the prefix is one daay
    assert re.match(pattern=r"\d{4}-\d{2}-\d{2}", string=prefix)
    # one day is 24 hours: we fetch only one day at a time hence no more than 24 keys
    max_keys: str = 24
    response = requests.get(f"{GHARCHIVE_URL}?prefix={prefix}&max-keys={max_keys}")
    response.raise_for_status()
    root = ET.fromstring(response.content)
    for contents in root.findall("s3:Contents", NAMESPACE):
        file_name = contents.find("s3:Key", NAMESPACE).text
        size = int(contents.find("s3:Size", NAMESPACE).text)
        md5 = contents.find("s3:ETag", NAMESPACE).text.strip('"')
        print(f"Listing: {file_name}, size: {size}")
        yield file_name, size, md5


def fetch_and_save_archive(file_name: str, size: str, md5: str, target_dir: Path):
    """
    Fetch and saves the gharchive ``file_name`` in ``target_dir``.
    Check that its ``size and ``md5`` are correct or fail.
    Also compute and return its sha256.
    """
    file_url = f"{GHARCHIVE_URL}/{file_name}"
    print(f"  Downloading from: {file_url}")

    response = requests.get(file_url)
    response.raise_for_status()
    content = response.content

    size_fetched = len(content)
    md5_fetched = hashlib.md5(content, usedforsecurity=False).hexdigest()
    if size_fetched != size or md5_fetched != md5:
        raise Exception(f"Failed to fetch: {file_name}")

    file = target_dir / file_name
    file.write_bytes(content)

    return hashlib.sha256(content, usedforsecurity=True).hexdigest()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not len(args) ==2:
        print(usage)
        sys.exit(1)
    prefix = args[0]
    target_dir = Path(args[1])
    target_dir.mkdir(exist_ok=True)

    print(f"Listing {GHARCHIVE_URL}/{prefix}*")
    files = list(get_files_for_prefix(prefix=prefix))
    print(f"Fetching to: {target_dir}")
    checksums = []
    for file_name, size, md5 in files:
        print(f"Fetching: {file_name}")
        sha256 = fetch_and_save_archive(
            file_name=file_name,
            size=size,
            md5=md5,
            target_dir=target_dir,
        )
        checksums.append(f"{sha256} {file_name}")
    checksums_file = target_dir / "sha256sums.txt"
    checksums_file.write_text(data="\n".join(checksums))
    print(f"Done")
