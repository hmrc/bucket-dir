# -*- coding: utf-8 -*-
import boto3

from .folder import Folder


class S3:
    def __init__(self, bucket_name):
        self.s3_client = boto3.client("s3")
        self.bucket_name = bucket_name

    def fetch_folder_content(self, folder_key):
        paginator = self.s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self.bucket_name, Prefix=folder_key, Delimiter="/"
        )
        files = []
        subdirectories = []
        for page in page_iterator:
            files.extend(page.get("Contents", []))
            subdirectories.extend(page.get("CommonPrefixes", []))

        subdirectories = list(map(lambda data: data["Prefix"], subdirectories))

        return Folder(prefix=folder_key, subdirectories=subdirectories, files=files)

    def put_object(self, body, key):
        self.s3_client.put_object(
            Body=body,
            Bucket=self.bucket_name,
            CacheControl="max-age=0",
            ContentType="text/html",
            Key=key,
        )
