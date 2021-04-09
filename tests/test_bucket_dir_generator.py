# -*- coding: utf-8 -*-
from bucket_dir import BucketDirGenerator


def test_generate_ascending_prefixes():
    full_file_key = "/foo/bar/baz/"

    prefixes = BucketDirGenerator.generate_ascending_prefixes(full_file_key)

    assert prefixes == [
        "foo/bar/baz/",
        "foo/bar/",
        "foo/",
        "",
    ]
