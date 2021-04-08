# -*- coding: utf-8 -*-
from bucket_dir import BucketDirGenerator


def test_get_index_hashes():
    contents = [
        {"Key": "/foo/index.html", "ETag": "34ih5ip34h534"},
        {"Key": "/foo/somthing-else", "ETag": "34ih5ip34h534"},
        {"Key": "/foo/bar/index.html", "ETag": "34534535345"},
    ]

    index_hashes = BucketDirGenerator.generate_index_hash(contents)
    assert index_hashes["/foo/index.html"] == "34ih5ip34h534"
    assert index_hashes["/foo/bar/index.html"] == "34534535345"

    assert index_hashes.get("/foo/somthing-else") is None
