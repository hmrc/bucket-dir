# -*- coding: utf-8 -*-
import concurrent.futures
import hashlib
import logging

import boto3
from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape

from .index import Index
from .item import Item


class BucketDirGenerator:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger("bucket_dir")
        self.template_environment = Environment(
            loader=PackageLoader("bucket_dir", "templates"),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.s3_client = boto3.client("s3")

    @staticmethod
    def build_indexes(contents, exclude_objects):
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
            if not exclude_objects:
                exclude_objects = []
            exclude_objects.extend(["", "favicon.ico", "index.html"])
            if item_name not in exclude_objects:
                indexes[full_path].add_item(
                    Item(name=item_name, modified=content["LastModified"], size=content["Size"])
                )
        return indexes

    @staticmethod
    def generate_index_hash(content_list):
        index_hash = {}
        for content in content_list:
            if content["Key"].endswith("index.html"):
                index_hash[content["Key"]] = content["ETag"].replace('"', "")
        return index_hash

    def generate(
        self, bucket, site_name, exclude_objects=None, single_threaded=False, target_path="/"
    ):
        contents = self.get_bucket_contents(bucket)
        self.logger.info(f"Building indexes for {bucket}.")
        indexes = self.build_indexes(contents, exclude_objects)
        index_hashes = self.generate_index_hash(contents)

        self.logger.info(f"Built {len(indexes)} indexes for {bucket}.")
        if not target_path.startswith("/"):
            target_path = f"/{target_path}"
        descending_indexes = {
            path: index for path, index in indexes.items() if path.startswith(target_path)
        }
        ascending_indexes = {
            path: index for path, index in indexes.items() if target_path.startswith(path)
        }
        target_indexes = {**descending_indexes, **ascending_indexes}
        if single_threaded:
            for path, index in target_indexes.items():
                self.render_and_upload_index_document_to_s3(
                    bucket, site_name, path, index, index_hashes
                )
        else:
            futures = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for path, index in target_indexes.items():
                    futures.append(
                        executor.submit(
                            self.render_and_upload_index_document_to_s3,
                            bucket,
                            site_name,
                            path,
                            index,
                            index_hashes,
                        )
                    )
            for future in futures:
                future.result()
        self.logger.info(f"Finished indexing {bucket} bucket.")

    def get_bucket_contents(self, bucket):
        paginator = self.s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket)
        self.logger.info(f"Listing objects in the {bucket} bucket.")
        contents = [content for page in page_iterator for content in page["Contents"]]
        self.logger.info(f"Found {len(contents)} objects in the {bucket} bucket.")
        return contents

    def render_and_upload_index_document_to_s3(self, bucket, site_name, path, index, index_hashes):
        self.logger.debug(f"Rendering index for {path}.")
        index_document = index.render(
            site_name=site_name, template_environment=self.template_environment
        ).encode("utf-8")

        key = f"{path[1:]}index.html"

        new_hash = hashlib.md5(  # nosec # skip bandit check as this is not used for encryption
            index_document
        ).hexdigest()
        self.logger.debug(
            f"{key} comparing existing hash: {index_hashes.get(key)} to new hash: {new_hash}"
        )
        if index_hashes.get(key) == new_hash:
            self.logger.info(f"Skipping unchanged index for {key}")
        else:
            self.logger.info(f"Uploading index for {key}")

            self.s3_client.put_object(
                Body=index_document,
                Bucket=bucket,
                CacheControl="max-age=0",
                ContentType="text/html",
                Key=key,
            )
