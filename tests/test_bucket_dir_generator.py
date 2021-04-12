# -*- coding: utf-8 -*-
from bucket_dir import BucketDirGenerator
from bucket_dir.s3 import Folder


def test_generate_ascending_prefixes():
    prefixes = BucketDirGenerator.generate_ascending_prefixes("foo/bar/baz/")

    assert prefixes == [
        "foo/bar/",
        "foo/",
        "",
    ]


def test_generate_ascending_prefixes_returns_nothing_when_at_top():
    prefixes = BucketDirGenerator.generate_ascending_prefixes("")

    assert prefixes == []
