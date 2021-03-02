# -*- coding: utf-8 -*-
import boto3
from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape
from rich.progress import track

from .index import Index
from .item import Item


class BucketDirGenerator:
    def __init__(self):
        self.template_environment = Environment(
            loader=PackageLoader("bucket_dir", "templates"),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.s3_client = boto3.client("s3")

    def build_indexes(self, contents):
        indexes = {"/": Index("/")}
        for content in contents:
            key_components = content["Key"].split("/")
            item_name = key_components[-1]
            if len(key_components) > 1:
                path_components = key_components[:-1]
                for depth in range(len(path_components)):
                    path = f"/{'/'.join(path_components[:depth + 1])}/"
                    if depth > 0:
                        parent_path = f"/{'/'.join(path_components[:depth])}/"
                    else:
                        parent_path = "/"
                    if path not in indexes:
                        indexes[path] = Index(path)
                    indexes[parent_path].add_item(Item(f"{path_components[depth]}/"))
                full_path = f"/{'/'.join(path_components)}/"
            else:
                full_path = "/"
            if item_name not in ["", "index.html"]:
                indexes[full_path].add_item(
                    Item(name=item_name, modified=content["LastModified"], size=content["Size"])
                )
        return indexes

    def generate(self, bucket, site_name):
        contents = self.get_bucket_contents(bucket)
        indexes = self.build_indexes(contents)
        for path, index in track(indexes.items()):
            index_document = index.render(
                site_name=site_name, template_environment=self.template_environment
            )
            self.upload_index_document_to_s3(bucket, path, index_document)

    def get_bucket_contents(self, bucket):
        # TODO: Support more than 1000 objects in bucket
        response = self.s3_client.list_objects_v2(
            Bucket=bucket,
            MaxKeys=1000,
        )
        return response.get("Contents", [])

    def upload_index_document_to_s3(self, bucket, path, index_document):
        s3_client = boto3.client("s3")
        key = f"{path[1:]}index.html"
        s3_client.put_object(
            Body=index_document.encode(),
            Bucket=bucket,
            CacheControl="max-age=0",
            ContentType="text/html",
            Key=key,
        )
