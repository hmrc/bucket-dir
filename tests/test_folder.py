# -*- coding: utf-8 -*-
from bucket_dir.folder import Folder


class TestFolder:
    def test_folder_object(self):
        folder = Folder(
            "foo", subdirectories=["foo/bar", "foo/baz"], files=[{"Key": "foo/myfile.jar"}]
        )

        assert folder.prefix == "foo"
        assert folder.subdirectories == ["foo/bar", "foo/baz"]
        assert folder.files == [{"Key": "foo/myfile.jar"}]

    def test_get_index_hash(self):
        folder = Folder(
            "foo/",
            subdirectories=["foo/bar", "foo/baz"],
            files=[{"Key": "foo/myfile.jar"}, {"Key": "foo/index.html", "ETag": '"12345"'}],
        )

        assert folder.get_index_hash() == "12345"

    def test_folder_is_empty(self):
        folder = Folder(
            "foo/",
            subdirectories=[],
            files=[],
        )
        assert folder.is_empty()

    def test_folder_not_empty_has_subdirectories(self):
        folder = Folder(
            "foo/",
            subdirectories=["foo/bar", "foo/baz"],
            files=[],
        )
        assert not folder.is_empty()

    def test_folder_not_empty_has_files(self):
        folder = Folder(
            "foo/",
            subdirectories=[],
            files=[{"Key": "foo/myfile.jar"}, {"Key": "foo/index.html", "ETag": '"12345"'}],
        )
        assert not folder.is_empty()

    def test_folder_not_empty_with_excluded_files(self):
        folder = Folder(
            "foo/",
            subdirectories=[],
            files=[{"Key": "foo/index.html", "ETag": '"12345"'}],
        )
        assert folder.is_empty(excluded_files=["index.html"])
