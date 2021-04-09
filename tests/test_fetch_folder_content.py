# -*- coding: utf-8 -*-
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
        files=["/foo/index.html", "/foo/otherfile.jar"],
        subdirectories=[
            "/foo/bar/",
            "/foo/baz/",
        ],
    )
    s3 = S3(bucket_name="foo-bucket")
    folder = s3.fetch_folder_content(folder_key="foo")

    assert folder.prefix == "foo"
    assert folder.subdirectories == ["/foo/bar/", "/foo/baz/"]
    assert len(folder.files) == 2
    assert folder.files[0]["Key"] == "/foo/index.html"
    assert folder.files[1]["Key"] == "/foo/otherfile.jar"


def simulate_s3_folder(files, subdirectories):
    httpretty.enable(allow_net_connect=False)
    httpretty.reset()

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
        "https://foo-bucket.s3.eu-west-1.amazonaws.com/?list-type=2&max-keys=5&continuation-token=foo-continuation-token&encoding-type=url",
        match_query_string=True,
        body=f"""<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <Name>foo-bucket</Name>
    <Prefix></Prefix>
    <ContinuationToken>foo-continuation-token</ContinuationToken>
    <KeyCount>1</KeyCount>
    <MaxKeys>1000</MaxKeys>
    <Delimiter>/</Delimiter>
    <EncodingType>url</EncodingType>
    <IsTruncated>false</IsTruncated>
    {commonprefixes}
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
    <KeyCount>1</KeyCount>
    <MaxKeys>1000</MaxKeys>
    <Delimiter>/</Delimiter>
    <EncodingType>url</EncodingType>
    <IsTruncated>true</IsTruncated>
    {contents}
</ListBucketResult>""",
    )
