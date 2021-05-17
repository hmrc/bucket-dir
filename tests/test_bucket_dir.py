# -*- coding: utf-8 -*-
import os
import re
import sys
from unittest import mock

import httpretty
import pytest

import bucket_dir
from tests.test_s3 import simulate_s3_folder


def assert_index_deleted(path):
    delete_requests = [
        request
        for request in httpretty.latest_requests()
        if request.method == "DELETE" and request.path == f"{path}index.html"
    ]
    assert len(delete_requests) == 1


def assert_index_created_correctly(
    items, path, site_name="foo-bucket", title=None, root_index=False
):
    if not title:
        title = path
    regular_expressions = [
        f"<title>Index of {re.escape(site_name)}{re.escape(title)}</title>",
        f"<h1>Index of {re.escape(site_name)}{re.escape(title)}</h1>",
        '<address style="font-size:small;">Generated by <a href="https://github.com/hmrc/bucket-dir">bucket-dir</a>.</address>',
    ]
    if not root_index:
        regular_expressions.append(
            '<tr>\n*\s*<td><a href="\.\.\/" class="parent_link">\.\.\/<\/a><\/td>\n*\s*<td><\/td>\n*\s*<td><\/td>\n*\s*<\/tr>'
        )
    for item in items:
        encoded_name = item.get("encoded_name", item["name"])
        regular_expressions.append(
            f"<tr>\n*\s*<td><a href=\"{re.escape(encoded_name)}\" class=\"item_link\">{re.escape(item['name'])}<\/a><\/td>\n*\s*<td>{item['last_modified']}<\/td>\n*\s*<td>{item['size']}<\/td>\n*\s*<\/tr>"
        )
    put_requests = [
        request
        for request in httpretty.latest_requests()
        if request.method == "PUT" and request.path == f"{path}index.html"
    ]
    assert len(put_requests) == 1
    captured_request = put_requests[0]
    body = captured_request.body.decode()
    for regular_expression in regular_expressions:
        assert re.search(
            regular_expression, body, flags=re.MULTILINE
        ), f"{regular_expression} != {body}"
    assert len(items) == body.count(
        'class="item_link"'
    ), f"number of items in index file did not match expected {body}"


def simulate_s3_big_bucket():
    simulate_s3_folder(
        prefix="",
        subdirectories=[
            "big-folder-1/",
            "big-folder-2/",
        ],
        files=[],
    )

    big_folder_1_prefixes = []
    big_folder_2_prefixes = []
    for n in range(500):
        key1 = f"big-folder-1/{n}/"
        key2 = f"big-folder-2/{n}/"
        big_folder_1_prefixes.append(key1)
        big_folder_2_prefixes.append(key2)
        simulate_s3_folder(
            prefix=key1,
            subdirectories=[],
            files=[
                {
                    "name": "object-two.bar",
                    "last_modified": "2021-02-22T10:23:11.000Z",
                    "size": 26921,
                }
            ],
        )
        simulate_s3_folder(
            prefix=key2,
            subdirectories=[],
            files=[
                {
                    "name": "object-two.bar",
                    "last_modified": "2021-02-22T10:23:11.000Z",
                    "size": 26921,
                }
            ],
        )
    simulate_s3_folder(
        prefix="big-folder-1/",
        subdirectories=big_folder_1_prefixes,
        files=[],
    )
    simulate_s3_folder(
        prefix="big-folder-2/",
        subdirectories=big_folder_2_prefixes,
        files=[],
    )


@mock.patch.object(sys, "argv", ["bucket-dir", "foo-bucket"])
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir_no_creds(delete_aws_creds):
    httpretty.register_uri(
        httpretty.PUT,
        "http://169.254.169.254/latest/api/token",
        status=404,
    )
    httpretty.register_uri(
        httpretty.GET,
        "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
        status=404,
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 1


@mock.patch.object(
    sys,
    "argv",
    ["bucket-dir", "foo-bucket", "--single-threaded"],
)
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir(aws_creds):
    simulate_s3_folder(
        prefix="",
        subdirectories=[
            "deep-folder/",
            "empty-folder/",
            "folder with spaces/",
            "regular-folder/",
            "FOLDER_With_UnUsUaL_n4m3/",
        ],
        files=[
            {"name": "root-one", "last_modified": "22-Feb-2021 10:23", "size": "30100"},
            {"name": "root-two", "last_modified": "22-Feb-2021 10:24", "size": "10800"},
        ],
    )
    simulate_s3_folder(
        prefix="empty-folder/",
        subdirectories=[],
        files=[],
        mock_upload=False,
    )
    simulate_s3_folder(
        prefix="folder with spaces/", subdirectories=[], files=[{"name": "an+object+with+spaces"}]
    )
    simulate_s3_folder(
        prefix="regular-folder/",
        subdirectories=[],
        files=[
            {
                "name": "object-one.foo",
                "last_modified": "2021-02-22T10:22:36.000Z",
                "size": 16524288,
            },
            {"name": "object-two.bar", "last_modified": "2021-02-22T10:23:11.000Z", "size": 26921},
        ],
    )
    simulate_s3_folder(
        prefix="deep-folder/",
        subdirectories=[
            "deep-folder/i/",
        ],
        files=[],
    )
    simulate_s3_folder(
        prefix="deep-folder/i/",
        subdirectories=[
            "deep-folder/i/ii/",
        ],
        files=[],
    )
    simulate_s3_folder(
        prefix="deep-folder/i/ii/",
        subdirectories=[
            "deep-folder/i/ii/iii/",
        ],
        files=[],
    )
    simulate_s3_folder(
        prefix="deep-folder/i/ii/iii/",
        subdirectories=[],
        files=[
            {"name": "index.html", "etag": "164b668c016a3b64086d3326850209b9"},
            {"name": "deep-object"},
        ],
        mock_upload=False,
    )
    simulate_s3_folder(
        prefix="FOLDER_With_UnUsUaL_n4m3/",
        subdirectories=["FOLDER_With_UnUsUaL_n4m3/it\\'gets*even.(weirder)/"],
        files=[
            {"name": "index.html", "last_modified": "22-Feb-2021 10:23"},
        ],
    )
    simulate_s3_folder(
        prefix="FOLDER_With_UnUsUaL_n4m3/it\\'gets*even.(weirder)/",
        subdirectories=[],
        files=[
            {"name": "see!", "last_modified": "22-Feb-2021 10:23"},
        ],
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0

    assert_index_created_correctly(
        items=[
            {"name": "deep-folder/", "last_modified": "-", "size": "-"},
            {
                "name": "folder with spaces/",
                "last_modified": "-",
                "size": "-",
                "encoded_name": "folder%20with%20spaces/",
            },
            {"name": "FOLDER_With_UnUsUaL_n4m3/", "last_modified": "-", "size": "-"},
            {"name": "regular-folder/", "last_modified": "-", "size": "-"},
            {"name": "root-one", "last_modified": "22-Feb-2021 10:23", "size": "30.1 kB"},
            {"name": "root-two", "last_modified": "22-Feb-2021 10:24", "size": "10.8 kB"},
        ],
        path="/",
        site_name="foo-bucket",
        root_index=True,
    )
    assert_index_created_correctly(
        items=[
            {"name": "object-one.foo", "last_modified": "22-Feb-2021 10:22", "size": "16.5 MB"},
            {"name": "object-two.bar", "last_modified": "22-Feb-2021 10:23", "size": "26.9 kB"},
        ],
        path="/regular-folder/",
        site_name="foo-bucket",
    )
    assert_index_created_correctly(
        items=[{"name": "i/", "last_modified": "-", "size": "-"}],
        path="/deep-folder/",
        site_name="foo-bucket",
    )
    assert_index_created_correctly(
        items=[{"name": "ii/", "last_modified": "-", "size": "-"}],
        path="/deep-folder/i/",
        site_name="foo-bucket",
    )
    assert_index_created_correctly(
        items=[{"name": "iii/", "last_modified": "-", "size": "-"}],
        path="/deep-folder/i/ii/",
        site_name="foo-bucket",
    )
    assert_index_created_correctly(
        items=[
            {
                "name": "an object with spaces",
                "last_modified": "22-Feb-2021 10:23",
                "size": "1.2 kB",
                "encoded_name": "an%20object%20with%20spaces",
            },
        ],
        path="/folder%20with%20spaces/",
        title="/folder with spaces/",
        site_name="foo-bucket",
    )
    assert_index_created_correctly(
        items=[
            {
                "name": "it\\'gets*even.(weirder)/",
                "last_modified": "-",
                "size": "-",
                "encoded_name": "it%5C%27gets%2Aeven.%28weirder%29/",
            },
        ],
        path="/FOLDER_With_UnUsUaL_n4m3/",
        site_name="foo-bucket",
    )
    assert_index_created_correctly(
        items=[
            {
                "name": "see!",
                "last_modified": "22-Feb-2021 10:23",
                "size": "1.2 kB",
                "encoded_name": "see%21",
            },
        ],
        path="/FOLDER_With_UnUsUaL_n4m3/it%5C%27gets%2Aeven.%28weirder%29/",
        title="/FOLDER_With_UnUsUaL_n4m3/it\\'gets*even.(weirder)/",
        site_name="foo-bucket",
    )


@pytest.mark.parametrize(
    "target_path",
    [
        "/deep-folder/i/ii/",
        "/deep-folder/i/ii/blah",
        "deep-folder/i/ii/",
        "deep-folder/i/ii/blah",
    ],
)
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir_with_target_path(aws_creds, mocker, target_path):
    mocker.patch.object(
        sys,
        "argv",
        [
            "bucket-dir",
            "foo-bucket",
            "--target-path",
            target_path,
            "--single-threaded",
        ],
    )
    simulate_s3_folder(
        prefix="",
        subdirectories=[
            "deep-folder/",
            "empty-folder/",
        ],
        files=[
            {"name": "root-one", "last_modified": "22-Feb-2021 10:23", "size": "30100"},
            {"name": "root-two", "last_modified": "22-Feb-2021 10:24", "size": "10800"},
        ],
    )
    simulate_s3_folder(
        prefix="deep-folder/",
        subdirectories=[
            "deep-folder/i/",
        ],
        files=[],
    )
    simulate_s3_folder(
        prefix="deep-folder/i/",
        subdirectories=[
            "deep-folder/i/ii/",
        ],
        files=[],
    )
    simulate_s3_folder(
        prefix="deep-folder/i/ii/",
        subdirectories=[
            "deep-folder/i/ii/iii/",
        ],
        files=[],
    )
    simulate_s3_folder(
        prefix="deep-folder/i/ii/folderthatisnotthere/",
        subdirectories=[],
        files=[],
        mock_upload=False,
    )
    simulate_s3_folder(
        prefix="deep-folder/i/ii/iii/",
        subdirectories=[],
        files=[
            {"name": "deep-object"},
        ],
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0
    assert_index_created_correctly(
        items=[
            {"name": "deep-folder/", "last_modified": "-", "size": "-"},
            {"name": "empty-folder/", "last_modified": "-", "size": "-"},
            {"name": "root-one", "last_modified": "22-Feb-2021 10:23", "size": "30.1 kB"},
            {"name": "root-two", "last_modified": "22-Feb-2021 10:24", "size": "10.8 kB"},
        ],
        path="/",
        site_name="foo-bucket",
        root_index=True,
    )
    assert_index_created_correctly(
        items=[{"name": "i/", "last_modified": "-", "size": "-"}],
        path="/deep-folder/",
        site_name="foo-bucket",
    )
    assert_index_created_correctly(
        items=[{"name": "ii/", "last_modified": "-", "size": "-"}],
        path="/deep-folder/i/",
        site_name="foo-bucket",
    )
    assert_index_created_correctly(
        items=[{"name": "iii/", "last_modified": "-", "size": "-"}],
        path="/deep-folder/i/ii/",
        site_name="foo-bucket",
    )


@mock.patch.object(
    sys,
    "argv",
    ["bucket-dir", "foo-bucket", "--site-name", "test-site-name"],
)
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir_with_site_name(aws_creds):
    simulate_s3_folder(
        prefix="",
        subdirectories=[],
        files=[
            {"name": "a-file", "last_modified": "22-Feb-2021 10:23"},
        ],
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0
    assert_index_created_correctly(
        items=[
            {
                "name": "a-file",
                "last_modified": "22-Feb-2021 10:23",
                "size": "1.2 kB",
            },
        ],
        path="/",
        site_name="test-site-name",
        root_index=True,
    )


@mock.patch.object(
    sys,
    "argv",
    [
        "bucket-dir",
        "foo-bucket",
        "--exclude-object",
        "root-one",
        "--exclude-object",
        "object-two.bar",
        "--single-threaded",
    ],
)
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir_with_excluded_objects(aws_creds):
    simulate_s3_folder(
        prefix="",
        subdirectories=[],
        files=[
            {"name": "the-not-excluded-thing", "last_modified": "22-Feb-2021 10:23"},
            {"name": "root-one"},
            {"name": "object-two.bar"},
            {"name": "favicon.ico"},
            {"name": "index.html"},
        ],
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0
    assert_index_created_correctly(
        items=[
            {
                "name": "the-not-excluded-thing",
                "last_modified": "22-Feb-2021 10:23",
                "size": "1.2 kB",
            },
        ],
        path="/",
        site_name="foo-bucket",
        root_index=True,
    )


@mock.patch.object(
    sys,
    "argv",
    [
        "bucket-dir",
        "foo-bucket",
        "--exclude-object",
        "excluded-object.zip",
        "--single-threaded",
    ],
)
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir_does_not_list_empty_folders(aws_creds):
    simulate_s3_folder(
        prefix="",
        subdirectories=["folder-with-only-excluded/", "folder-we-like/"],
        files=[],
    )
    simulate_s3_folder(
        prefix="folder-with-only-excluded/",
        subdirectories=[],
        files=[{"name": "excluded-object.zip"}],
        mock_upload=False,
    )
    simulate_s3_folder(
        prefix="folder-we-like/",
        subdirectories=[],
        files=[{"name": "the-not-excluded-thing"}, {"name": "excluded-object.zip"}],
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0
    assert_index_created_correctly(
        items=[
            {
                "name": "folder-we-like/",
                "last_modified": "-",
                "size": "-",
            },
        ],
        path="/",
        site_name="foo-bucket",
        root_index=True,
    )
    assert_index_created_correctly(
        items=[
            {
                "name": "the-not-excluded-thing",
                "last_modified": "22-Feb-2021 10:23",
                "size": "1.2 kB",
            },
        ],
        path="/folder-we-like/",
        site_name="foo-bucket",
    )


@mock.patch.object(
    sys,
    "argv",
    [
        "bucket-dir",
        "foo-bucket",
        "--single-threaded",
    ],
)
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_deletes_old_index_files(aws_creds):
    simulate_s3_folder(
        prefix="",
        subdirectories=["folder-that-is-basically-empty/"],
        files=[{"name": "foo.html"}],
    )
    simulate_s3_folder(
        prefix="folder-that-is-basically-empty/",
        subdirectories=[],
        files=[{"name": "index.html"}],
        mock_upload=False,
        mock_delete=True,
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0

    assert_index_created_correctly(
        items=[
            {
                "name": "foo.html",
                "last_modified": "22-Feb-2021 10:23",
                "size": "1.2 kB",
            },
        ],
        path="/",
        site_name="foo-bucket",
        root_index=True,
    )
    assert_index_deleted(path="/folder-that-is-basically-empty/")


@mock.patch.object(
    sys,
    "argv",
    [
        "bucket-dir",
        "foo-bucket",
    ],
)
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir_multithreaded_smoke(aws_creds):
    """We cannot use httpretty when multithreading, see:

    https://github.com/gabrielfalcao/HTTPretty/issues/186
    https://github.com/gabrielfalcao/HTTPretty/issues/209

    Most of the testing value is thus performed with --single-threaded.

    This test ensures that mulithreading itself basically works.
    """
    simulate_s3_folder(
        prefix="",
        subdirectories=[
            "deep-folder/",
            "empty-folder/",
            "folder with spaces/",
            "regular-folder/",
            "FOLDER_With_UnUsUaL_n4m3/",
        ],
        files=[
            {"name": "root-one", "last_modified": "22-Feb-2021 10:23", "size": "30100"},
            {"name": "root-two", "last_modified": "22-Feb-2021 10:24", "size": "10800"},
        ],
    )
    simulate_s3_folder(
        prefix="empty-folder/",
        subdirectories=[],
        files=[],
    )
    simulate_s3_folder(
        prefix="folder with spaces/", subdirectories=[], files=[{"name": "an+object+with+spaces"}]
    )
    simulate_s3_folder(
        prefix="regular-folder/",
        subdirectories=[],
        files=[
            {
                "name": "object-one.foo",
                "last_modified": "2021-02-22T10:22:36.000Z",
                "size": 16524288,
            },
            {"name": "object-two.bar", "last_modified": "2021-02-22T10:23:11.000Z", "size": 26921},
        ],
    )
    simulate_s3_folder(
        prefix="folder+with+spaces/",
        subdirectories=[],
        files=[
            {"name": "an+object+with+spaces"},
        ],
    )
    simulate_s3_folder(
        prefix="deep-folder/",
        subdirectories=[
            "deep-folder/i/",
        ],
        files=[],
    )
    simulate_s3_folder(
        prefix="deep-folder/i/",
        subdirectories=[
            "deep-folder/i/ii/",
        ],
        files=[],
    )
    simulate_s3_folder(
        prefix="deep-folder/i/ii/",
        subdirectories=[
            "deep-folder/i/ii/iii/",
        ],
        files=[],
    )
    simulate_s3_folder(
        prefix="deep-folder/i/ii/iii/",
        subdirectories=[],
        files=[
            {"name": "index.html", "etag": "164b668c016a3b64086d3326850209b9"},
            {"name": "deep-object"},
        ],
        mock_upload=False,
    )
    simulate_s3_folder(
        prefix="FOLDER_With_UnUsUaL_n4m3/",
        subdirectories=["FOLDER_With_UnUsUaL_n4m3/it\\'gets*even.(weirder)/"],
        files=[
            {"name": "index.html", "last_modified": "22-Feb-2021 10:23"},
        ],
    )
    simulate_s3_folder(
        prefix="FOLDER_With_UnUsUaL_n4m3/it\\'gets*even.(weirder)/",
        subdirectories=[],
        files=[
            {"name": "see!", "last_modified": "22-Feb-2021 10:23"},
        ],
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0


@mock.patch.object(
    sys,
    "argv",
    [
        "bucket-dir",
        "foo-bucket",
    ],
)
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir_multithreaded_no_list_permissions(aws_creds, caplog):
    httpretty.register_uri(
        httpretty.GET,
        "https://foo-bucket.s3.eu-west-1.amazonaws.com/?list-type=2&delimiter=%2F&prefix=&encoding-type=url",
        status=403,
        body="""<?xml version="1.0" encoding="UTF-8"?>
        <Error>
            <Code>AccessDenied</Code>
            <Message>Access Denied</Message>
            <RequestId>foo-request-id</RequestId>
            <HostId>foo-host-id</HostId>
        </Error>""",
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 1
    assert (
        "Access denied when making a ListObjectsV2 call. Please ensure appropriate AWS permissions are set."
        in caplog.messages
    )


@mock.patch.object(
    sys,
    "argv",
    [
        "bucket-dir",
        "foo-bucket",
    ],
)
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir_multithreaded_unhandled_client_error(aws_creds, caplog):
    httpretty.register_uri(
        httpretty.GET,
        "https://foo-bucket.s3.eu-west-1.amazonaws.com/?list-type=2&delimiter=%2F&prefix=&encoding-type=url",
        status=403,
        body="""<?xml version="1.0" encoding="UTF-8"?>
        <Error>
            <Code>WeirdError</Code>
            <Message>Something funky happened</Message>
            <RequestId>foo-request-id</RequestId>
            <HostId>foo-host-id</HostId>
        </Error>""",
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 1
    assert (
        "An unhandled ClientError occured when interacting with AWS: 'An error occurred (WeirdError) when calling the ListObjectsV2 operation: Something funky happened'."
        in caplog.messages
    )


@mock.patch.object(
    sys,
    "argv",
    [
        "bucket-dir",
        "foo-bucket",
    ],
)
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir_multithreaded_no_put_permissions(aws_creds, caplog):

    # This is a workaround for https://github.com/gabrielfalcao/HTTPretty/issues/416
    # TODO: The above has now been marked as resolved so this could potentially be refactored to align it better with actual behaviours of the S3 API
    def put_object_failed_request_callback(request, uri, response_headers):
        status = 100
        body = ""
        if len(request.body) > 0:
            status = 403
            body = """<?xml version="1.0" encoding="UTF-8"?>
            <Error>
                <Code>AccessDenied</Code>
                <Message>Access Denied</Message>
                <RequestId>GEW5C7J1JCY4GVPC</RequestId>
                <HostId>NaxEi4Nqz+XdWRxTZf0ww+oHsNl11xyauaaJaIy6SUhhF8waL4B/5vxRDGEWwcCQPW6UIb0yuHk=</HostId>
            </Error>"""
        return [status, {}, body.encode()]

    simulate_s3_folder(
        prefix="",
        subdirectories=[],
        files=[
            {"name": "an-object", "last_modified": "22-Feb-2021 10:23", "size": "30100"},
        ],
        mock_upload=False,
    )
    httpretty.register_uri(
        httpretty.PUT,
        "https://foo-bucket.s3.eu-west-1.amazonaws.com/index.html",
        body=put_object_failed_request_callback,
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 1
    assert (
        "Access denied when making a PutObject call. Please ensure appropriate AWS permissions are set."
        in caplog.messages
    )


@pytest.mark.skipif(
    not os.getenv("BUCKET_DIR_PROFILE_TEST"),
    reason="Performance test, run explicitly for benchmarking.",
)
@mock.patch.object(sys, "argv", ["bucket-dir", "foo-bucket"])
@httpretty.activate(allow_net_connect=False)
def test_generate_bucket_dir_big_bucket(aws_creds):
    simulate_s3_big_bucket()
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0
