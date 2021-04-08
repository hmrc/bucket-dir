# -*- coding: utf-8 -*-
import os
import re
import sys
from unittest import mock

import httpretty
import pytest

import bucket_dir


def body_formatted_correctly(body):
    item_link_line_lengths = []
    for line in body.split("\n"):
        if 'class="item_link"' in line:
            capture_groups = re.findall(
                r'item_link">(.+)<\/a>(\s+[A-Za-z0-9-]+\s[\d\s:]{5}\s+)', line
            )
            item_link_line_lengths.append(sum([len(cg) for cg in capture_groups[0]]))
    if len(set(item_link_line_lengths)) <= 1:
        return True


def index_created_correctly(items, page_name, root_index=False):
    regular_expressions = [
        f"<title>Index of {re.escape(page_name)}</title>",
        f"<h1>Index of {re.escape(page_name)}</h1>",
        '<address style="font-size:small;">Generated by <a href="https://github.com/hmrc/bucket-dir">bucket-dir</a>.</address>',
    ]
    if not root_index:
        regular_expressions.append('<a href="\.\.\/" class="parent_link">\.\.\/<\/a><\/br>')
    for item in items:
        encoded_name = item.get("encoded_name", item["name"])
        regular_expressions.append(
            f"<a href=\"{re.escape(encoded_name)}\" class=\"item_link\">{re.escape(item['name'])}<\/a>\s+{item['last_modified']}\s+{item['size']}"
        )
    put_requests = [request for request in httpretty.latest_requests() if request.method == "PUT"]
    for captured_request in put_requests:
        body = captured_request.body.decode()
        regular_expressions_checklist = {
            regular_expression: False for regular_expression in regular_expressions
        }
        for regular_expression in regular_expressions:
            if re.search(regular_expression, body):
                regular_expressions_checklist[regular_expression] = True
        if all(regular_expressions_checklist.values()):
            if len(items) == body.count('class="item_link"'):
                if body_formatted_correctly(body):
                    return True
    return False


def simulate_s3(folders_to_be_indexed):
    httpretty.enable(allow_net_connect=False)
    httpretty.reset()
    httpretty.register_uri(
        httpretty.GET,
        "https://foo-bucket.s3.eu-west-1.amazonaws.com/?list-type=2&max-keys=5&continuation-token=foo-continuation-token&encoding-type=url",
        match_query_string=True,
        body=f"""<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <Name>foo-bucket</Name>
    <Prefix></Prefix>
    <ContinuationToken>foo-continuation-token</ContinuationToken>
    <KeyCount>6</KeyCount>
    <MaxKeys>6</MaxKeys>
    <EncodingType>url</EncodingType>
    <IsTruncated>false</IsTruncated>
    <Contents>
        <Key>deep-folder/i/ii/iii/index.html</Key>
        <LastModified>2021-02-22T10:28:13.000Z</LastModified>
        <ETag>&quot;2a191461baaeb6a9f0add33ac9187ea4&quot;</ETag>
        <Size>26921</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
    <Contents>
        <Key>deep-folder/i/ii/iii/deep-object</Key>
        <LastModified>2021-02-22T10:26:36.000Z</LastModified>
        <ETag>&quot;ccdab8fb019e23387203c06c157d302f-2&quot;</ETag>
        <Size>16524288</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
    <Contents>
        <Key>empty-folder/</Key>
        <LastModified>2021-02-22T10:23:25.000Z</LastModified>
        <ETag>&quot;d41d8cd98f00b204e9800998ecf8427e&quot;</ETag>
        <Size>0</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
    <Contents>
        <Key>folder+with+spaces/an+object+with+spaces</Key>
        <LastModified>2021-02-22T10:24:37.000Z</LastModified>
        <ETag>&quot;11490e1fc1376b0c209d05cf1190843f-4&quot;</ETag>
        <Size>32993280</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
    <Contents>
        <Key>FOLDER_With_UnUsUaL_n4m3/it%5C%27gets*even.%28weirder%29/see%21</Key>
        <LastModified>2021-02-22T10:26:16.000Z</LastModified>
        <ETag>&quot;3e4b4b8018db93caccae34dc2fecc8d0&quot;</ETag>
        <Size>22749</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
    <Contents>
        <Key>favicon.ico</Key>
        <LastModified>2021-04-07T09:19:44.000Z</LastModified>
        <ETag>&quot;18f190bd12aa40e3e7199c665e8fcc9c&quot;</ETag>
        <Size>12345</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
</ListBucketResult>""",
    )
    httpretty.register_uri(
        httpretty.GET,
        "https://foo-bucket.s3.eu-west-1.amazonaws.com/?list-type=2&max-keys=5&encoding-type=url",
        match_query_string=True,
        body=f"""<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <Name>foo-bucket</Name>
    <Prefix></Prefix>
    <NextContinuationToken>foo-continuation-token</NextContinuationToken>
    <KeyCount>5</KeyCount>
    <MaxKeys>5</MaxKeys>
    <EncodingType>url</EncodingType>
    <IsTruncated>true</IsTruncated>
    <Contents>
        <Key>root-one</Key>
        <LastModified>2021-02-22T10:23:44.000Z</LastModified>
        <ETag>&quot;18f190bd12aa40e3e7199c665e8fcc9c&quot;</ETag>
        <Size>30087</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
    <Contents>
        <Key>root-two</Key>
        <LastModified>2021-02-22T10:24:21.000Z</LastModified>
        <ETag>&quot;5b111fddb5257c3a2ddcb1d34deb455b&quot;</ETag>
        <Size>10801</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
    <Contents>
        <Key>regular-folder/object-one.foo</Key>
        <LastModified>2021-02-22T10:22:36.000Z</LastModified>
        <ETag>&quot;ccdab8fb019e23387203c06c157d302f-2&quot;</ETag>
        <Size>16524288</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
    <Contents>
        <Key>regular-folder/object-two.bar</Key>
        <LastModified>2021-02-22T10:23:11.000Z</LastModified>
        <ETag>&quot;13fa4f75b40ae3fbcb1bc1afb870fc0c&quot;</ETag>
        <Size>26921</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
    <Contents>
        <Key>regular-folder/index.html</Key>
        <LastModified>2021-02-22T10:28:13.000Z</LastModified>
        <ETag>&quot;13fa4f75b40ae3fbcb1bc1afb870fc0c&quot;</ETag>
        <Size>26921</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>
</ListBucketResult>""",
    )
    for folder in folders_to_be_indexed:
        httpretty.register_uri(
            httpretty.PUT,
            f"https://foo-bucket.s3.eu-west-1.amazonaws.com{folder}index.html",
            body=put_object_request_callback,
        )


def simulate_s3_big_bucket():
    httpretty.enable(allow_net_connect=False)
    httpretty.reset()
    contents = ""
    for folder_number in range(1000):
        contents += f"""<Contents>
        <Key>folder-{folder_number}/foo-object</Key>
        <LastModified>2021-02-22T10:23:44.000Z</LastModified>
        <ETag>&quot;18f190bd12aa40e3e7199c665e8fcc9c&quot;</ETag>
        <Size>30087</Size>
        <StorageClass>STANDARD</StorageClass>
    </Contents>"""
    body = f"""<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <Name>foo-bucket</Name>
    <Prefix></Prefix>
    <KeyCount>1000</KeyCount>
    <MaxKeys>1000</MaxKeys>
    <EncodingType>url</EncodingType>
    <IsTruncated>false</IsTruncated>
    {contents}
</ListBucketResult>"""
    httpretty.register_uri(
        httpretty.GET,
        "https://foo-bucket.s3.eu-west-1.amazonaws.com/?list-type=2&max-keys=1000&encoding-type=url",
        match_query_string=True,
        body=body,
    )
    httpretty.register_uri(
        httpretty.PUT,
        f"https://foo-bucket.s3.eu-west-1.amazonaws.com/index.html",
        body=put_object_request_callback,
    )
    for folder_number in range(1000):
        httpretty.register_uri(
            httpretty.PUT,
            f"https://foo-bucket.s3.eu-west-1.amazonaws.com/folder-{folder_number}/index.html",
            body=put_object_request_callback,
        )


def put_object_request_callback(request, uri, response_headers):
    status = 100
    if len(request.body) > 0:
        status = 200
    return [status, {}, "".encode()]


@mock.patch.object(sys, "argv", ["bucket-dir", "foo-bucket"])
def test_generate_bucket_dir_no_creds(delete_aws_creds):
    httpretty.enable(allow_net_connect=False)
    httpretty.reset()
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
    [
        "bucket-dir",
        "foo-bucket",
        "--single-threaded",
    ],
)
def test_generate_bucket_dir(aws_creds):
    simulate_s3(
        folders_to_be_indexed=[
            "/",
            "/deep-folder/",
            "/deep-folder/i/",
            "/deep-folder/i/ii/",
            "/empty-folder/",
            "/folder with spaces/",
            "/regular-folder/",
            "/FOLDER_With_UnUsUaL_n4m3/",
            "/FOLDER_With_UnUsUaL_n4m3/it\\'gets*even.(weirder)/",
        ]
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0

    # skipped as it has not changed
    assert not index_created_correctly(
        items=[{"name": "deep-object", "last_modified": "22-Feb-2021 10:26", "size": "16.5 MB"}],
        page_name="foo-bucket/deep-folder/i/ii/iii/",
    )

    assert index_created_correctly(
        items=[
            {"name": "deep-folder/", "last_modified": "-", "size": "-"},
            {"name": "empty-folder/", "last_modified": "-", "size": "-"},
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
        page_name="foo-bucket/",
        root_index=True,
    )
    assert index_created_correctly(
        items=[
            {"name": "object-one.foo", "last_modified": "22-Feb-2021 10:22", "size": "16.5 MB"},
            {"name": "object-two.bar", "last_modified": "22-Feb-2021 10:23", "size": "26.9 kB"},
        ],
        page_name="foo-bucket/regular-folder/",
    )
    assert index_created_correctly(
        items=[{"name": "i/", "last_modified": "-", "size": "-"}],
        page_name="foo-bucket/deep-folder/",
    )
    assert index_created_correctly(
        items=[{"name": "ii/", "last_modified": "-", "size": "-"}],
        page_name="foo-bucket/deep-folder/i/",
    )
    assert index_created_correctly(
        items=[{"name": "iii/", "last_modified": "-", "size": "-"}],
        page_name="foo-bucket/deep-folder/i/ii/",
    )
    assert index_created_correctly(
        items=[],
        page_name="foo-bucket/empty-folder/",
    )
    assert index_created_correctly(
        items=[
            {
                "name": "an object with spaces",
                "last_modified": "22-Feb-2021 10:24",
                "size": "33.0 MB",
                "encoded_name": "an%20object%20with%20spaces",
            },
        ],
        page_name="foo-bucket/folder with spaces/",
    )
    assert index_created_correctly(
        items=[
            {
                "name": "it\\'gets*even.(weirder)/",
                "last_modified": "-",
                "size": "-",
                "encoded_name": "it%5C%27gets%2Aeven.%28weirder%29/",
            },
        ],
        page_name="foo-bucket/FOLDER_With_UnUsUaL_n4m3/",
    )
    assert index_created_correctly(
        items=[
            {
                "name": "see!",
                "last_modified": "22-Feb-2021 10:26",
                "size": "22.7 kB",
                "encoded_name": "see%21",
            },
        ],
        page_name="foo-bucket/FOLDER_With_UnUsUaL_n4m3/it\\'gets*even.(weirder)/",
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
    simulate_s3(
        folders_to_be_indexed=[
            "/",
            "/deep-folder/",
            "/deep-folder/i/",
            "/deep-folder/i/ii/",
            "/deep-folder/i/ii/iii/",
        ]
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0
    assert index_created_correctly(
        items=[
            {"name": "deep-folder/", "last_modified": "-", "size": "-"},
            {"name": "empty-folder/", "last_modified": "-", "size": "-"},
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
        page_name="foo-bucket/",
        root_index=True,
    )
    assert index_created_correctly(
        items=[{"name": "i/", "last_modified": "-", "size": "-"}],
        page_name="foo-bucket/deep-folder/",
    )
    assert index_created_correctly(
        items=[{"name": "ii/", "last_modified": "-", "size": "-"}],
        page_name="foo-bucket/deep-folder/i/",
    )
    assert index_created_correctly(
        items=[{"name": "iii/", "last_modified": "-", "size": "-"}],
        page_name="foo-bucket/deep-folder/i/ii/",
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
def test_generate_bucket_dir_with_excluded_objects(aws_creds):
    simulate_s3(
        folders_to_be_indexed=[
            "/",
            "/deep-folder/",
            "/deep-folder/i/",
            "/deep-folder/i/ii/",
            "/deep-folder/i/ii/iii/",
            "/empty-folder/",
            "/folder with spaces/",
            "/regular-folder/",
            "/FOLDER_With_UnUsUaL_n4m3/",
            "/FOLDER_With_UnUsUaL_n4m3/it\\'gets*even.(weirder)/",
        ]
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0
    assert index_created_correctly(
        items=[
            {"name": "deep-folder/", "last_modified": "-", "size": "-"},
            {"name": "empty-folder/", "last_modified": "-", "size": "-"},
            {
                "name": "folder with spaces/",
                "last_modified": "-",
                "size": "-",
                "encoded_name": "folder%20with%20spaces/",
            },
            {"name": "FOLDER_With_UnUsUaL_n4m3/", "last_modified": "-", "size": "-"},
            {"name": "regular-folder/", "last_modified": "-", "size": "-"},
            {"name": "root-two", "last_modified": "22-Feb-2021 10:24", "size": "10.8 kB"},
        ],
        page_name="foo-bucket/",
        root_index=True,
    )
    assert index_created_correctly(
        items=[
            {"name": "object-one.foo", "last_modified": "22-Feb-2021 10:22", "size": "16.5 MB"},
        ],
        page_name="foo-bucket/regular-folder/",
    )


@mock.patch.object(
    sys,
    "argv",
    [
        "bucket-dir",
        "foo-bucket",
    ],
)
def test_generate_bucket_dir_multithreaded_smoke(aws_creds):
    """We cannot use httpretty when multithreading, see:

    https://github.com/gabrielfalcao/HTTPretty/issues/186
    https://github.com/gabrielfalcao/HTTPretty/issues/209

    Most of the testing value is thus performed with --single-threaded.

    This test ensures that mulithreading itself basically works.
    """
    simulate_s3(
        folders_to_be_indexed=[
            "/",
            "/deep-folder/",
            "/deep-folder/i/",
            "/deep-folder/i/ii/",
            "/deep-folder/i/ii/iii/",
            "/empty-folder/",
            "/folder with spaces/",
            "/regular-folder/",
            "/FOLDER_With_UnUsUaL_n4m3/",
            "/FOLDER_With_UnUsUaL_n4m3/it\\'gets*even.(weirder)/",
        ]
    )
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0


@pytest.mark.skipif(
    not os.getenv("BUCKET_DIR_PROFILE_TEST"),
    reason="Performance test, run explicitly for benchmarking.",
)
@mock.patch.object(sys, "argv", ["bucket-dir", "foo-bucket"])
def test_generate_bucket_dir_big_bucket(aws_creds):
    simulate_s3_big_bucket()
    with pytest.raises(SystemExit) as system_exit:
        bucket_dir.run_cli()
    assert system_exit.value.code == 0
