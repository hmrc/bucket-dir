# -*- coding: utf-8 -*-
from bucket_dir import BucketDirGenerator
from bucket_dir.s3 import Folder


def test_generate_ascending_prefixes():
    prefixes = BucketDirGenerator.generate_ascending_prefixes("/foo/bar/baz/")

    assert prefixes == [
        "foo/bar/baz/",
        "foo/bar/",
        "foo/",
        "",
    ]


def test_generate_ascending_prefixes_when_using_slash_for_root():
    prefixes = BucketDirGenerator.generate_ascending_prefixes("/")

    assert prefixes == [""]


class FakeS3:
    def fetch_folder_content(self, folder_key):
        return Folder(prefix=folder_key, files=[], subdirectories=[])


def test_build_ascending_folders():
    generator = BucketDirGenerator()
    ascending_folders = generator.build_ascending_folders(s3=FakeS3(), target_path="foo/baz/")
    assert len(ascending_folders) == 3

    assert ascending_folders[""].prefix == ""
    assert ascending_folders["foo/"].prefix == "foo/"
    assert ascending_folders["foo/baz/"].prefix == "foo/baz/"
