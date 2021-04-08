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
        subdirectories=[
            "/foo/bar/",
            "/foo/baz/",
        ]
    )
    s3 = S3(bucket_name="foo-bucket")
    folder = s3.fetch_folder_content(folder_key="foo")

    assert folder.prefix == "foo"
    assert folder.subdirectories == ["/foo/bar/", "/foo/baz/"]


def simulate_s3_folder(subdirectories):
    httpretty.enable(allow_net_connect=False)
    httpretty.reset()

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
</ListBucketResult>""",
    )
    # for folder in folders_to_be_indexed:
    #     httpretty.register_uri(
    #         httpretty.PUT,
    #         f"https://foo-bucket.s3.eu-west-1.amazonaws.com{folder}index.html",
    #         body=put_object_request_callback,
    #     )
