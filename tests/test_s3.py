# -*- coding: utf-8 -*-
import urllib

import httpretty

from bucket_dir.s3_gateway import S3Gateway


@httpretty.activate(allow_net_connect=False)
def test_fetch_folder_content(aws_creds):
    simulate_s3_folder(
        prefix="foo/",
        files=[{"name": "index.html"}, {"name": "otherfile.jar"}],
        subdirectories=[
            "/foo/bar/",
            "/foo/baz/",
        ],
    )
    s3 = S3Gateway(bucket_name="foo-bucket")
    folder = s3.fetch_folder_content(folder_key="foo/")

    assert len(httpretty.latest_requests()) == 2

    assert folder.prefix == "foo/"
    assert folder.subdirectories == ["/foo/bar/", "/foo/baz/"]
    assert len(folder.files) == 2
    assert folder.files[0]["Key"] == "foo/index.html"
    assert folder.files[1]["Key"] == "foo/otherfile.jar"


def put_object_request_callback(request, uri, response_headers):
    status = 100
    if len(request.body) > 0:
        status = 200
    return [status, {}, "".encode()]


def simulate_s3_folder(prefix, files, subdirectories, mock_upload=True, mock_delete=False):
    if mock_delete:
        httpretty.register_uri(
            httpretty.DELETE,
            f"https://foo-bucket.s3.eu-west-1.amazonaws.com/{prefix}index.html",
            body="",
        )
    if mock_upload:
        httpretty.register_uri(
            httpretty.PUT,
            f"https://foo-bucket.s3.eu-west-1.amazonaws.com/{prefix}index.html",
            body=put_object_request_callback,
        )

    url_prefix = urllib.parse.quote_plus(prefix)

    contents = ""
    for file in files:
        contents += f"""<Contents>
                            <Key>{prefix}{file["name"]}</Key>
                            <LastModified>{file.get("last_modified", "22-Feb-2021 10:23")}</LastModified>
                            <ETag>&quot;{file.get("etag", "fakeETag")}&quot;</ETag>
                            <Size>{file.get("size", "1234")}</Size>
                            <StorageClass>STANDARD</StorageClass>
                        </Contents>"""

    commonprefixes = ""
    for folders in subdirectories:
        commonprefixes += f"<CommonPrefixes><Prefix>{folders}</Prefix></CommonPrefixes>"

    httpretty.register_uri(
        httpretty.GET,
        f"https://foo-bucket.s3.eu-west-1.amazonaws.com/?list-type=2&prefix={url_prefix}&delimiter=%2F&encoding-type=url",
        match_querystring=True,
        body=f"""<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <Name>foo-bucket</Name>
    <Prefix>{url_prefix}</Prefix>
    <NextContinuationToken>foo-continuation-token</NextContinuationToken>
    <KeyCount>{len(contents)}</KeyCount>
    <MaxKeys>{len(contents)}</MaxKeys>
    <Delimiter>{urllib.parse.quote_plus("/")}</Delimiter>
    <EncodingType>url</EncodingType>
    <IsTruncated>true</IsTruncated>
    </ListBucketResult>""",
    )
    httpretty.register_uri(
        httpretty.GET,
        f"https://foo-bucket.s3.eu-west-1.amazonaws.com/?list-type=2&prefix={url_prefix}&delimiter=%2F&continuation-token=foo-continuation-token&encoding-type=url",
        match_querystring=True,
        body=f"""<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <Name>foo-bucket</Name>
    <Prefix></Prefix>
    <KeyCount>{len(contents)}</KeyCount>
    <MaxKeys>{len(contents)}</MaxKeys>
    <Delimiter>/</Delimiter>
    <EncodingType>url</EncodingType>
    <IsTruncated>false</IsTruncated>
    {contents}
    {commonprefixes}
</ListBucketResult>""",
    )
