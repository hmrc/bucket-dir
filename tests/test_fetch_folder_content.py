# -*- coding: utf-8 -*-
import urllib

from httpretty import httpretty

from bucket_dir.s3 import Folder
from bucket_dir.s3 import S3


def test_folder_object():
    folder = Folder(
        "foo", subdirectories=["foo/bar", "foo/baz"], files=[{"name": "foo/myfile.jar"}]
    )

    assert folder.prefix == "foo"
    assert folder.subdirectories == ["foo/bar", "foo/baz"]
    assert folder.files == [{"name": "foo/myfile.jar"}]


def test_fetch_folder_content(aws_creds):
    simulate_s3_folder(
        prefix="foo/",
        files=["/foo/index.html", "/foo/otherfile.jar"],
        subdirectories=[
            "/foo/bar/",
            "/foo/baz/",
        ],
    )
    s3 = S3(bucket_name="foo-bucket")
    folder = s3.fetch_folder_content(folder_key="foo/")

    assert len(httpretty.latest_requests) == 2

    assert folder.prefix == "foo/"
    assert folder.subdirectories == ["/foo/bar/", "/foo/baz/"]
    assert len(folder.files) == 2
    assert folder.files[0]["Key"] == "/foo/index.html"
    assert folder.files[1]["Key"] == "/foo/otherfile.jar"


def simulate_s3_folder(prefix, files, subdirectories):
    httpretty.enable(allow_net_connect=False)
    httpretty.reset()

    url_prefix = urllib.parse.quote_plus(prefix)

    contents = ""
    for file in files:
        contents += f"""<Contents>
                            <Key>{file}</Key>
                            <LastModified>2021-02-22T10:28:13.000Z</LastModified>
                            <ETag>&quot;2a191461baaeb6a9f0add33ac9187ea4&quot;</ETag>
                            <Size>26921</Size>
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
    <KeyCount>{len(file)}</KeyCount>
    <MaxKeys>{len(file)}</MaxKeys>
    <Delimiter>{urllib.parse.quote_plus("/")}</Delimiter>
    <EncodingType>url</EncodingType>
    <IsTruncated>true</IsTruncated>
    </ListBucketResult>""",
    )
    httpretty.register_uri(
        httpretty.GET,
        f"https://foo-bucket.s3.eu-west-1.amazonaws.com/?list-type=2&prefix=foo%2F&delimiter=%2F&continuation-token=foo-continuation-token&encoding-type=url",
        match_querystring=True,
        body=f"""<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <Name>foo-bucket</Name>
    <Prefix></Prefix>
    <KeyCount>{len(file)}</KeyCount>
    <MaxKeys>{len(file)}</MaxKeys>
    <Delimiter>/</Delimiter>
    <EncodingType>url</EncodingType>
    <IsTruncated>false</IsTruncated>
    {contents}
    {commonprefixes}
</ListBucketResult>""",
    )
