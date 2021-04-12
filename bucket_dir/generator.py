# -*- coding: utf-8 -*-
import concurrent.futures
import hashlib
import logging

import boto3
from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape

from .index import Index
from .s3 import S3


class BucketDirGenerator:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger("bucket_dir")
        self.template_environment = Environment(
            loader=PackageLoader("bucket_dir", "templates"),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @staticmethod
    def generate_ascending_prefixes(directory_key):
        parts = directory_key.split("/")
        parts = list(filter(len, parts))
        paths = []
        for index in range(len(parts)):
            level = "/".join(parts[:index])
            if (not level.endswith("/")) and (level != ""):
                level += "/"
            paths.append(level)
        paths.reverse()
        return paths

    def generate(
        self, bucket, site_name, exclude_objects=None, single_threaded=False, target_path=""
    ):
        # todo make single_threaded actually do something
        self.s3_gateway = S3(bucket_name=bucket)  # todo move this to init

        if target_path.startswith("/"):
            target_path = target_path[1:]

        if not target_path.endswith("/"):
            last_slash = target_path.rfind("/")
            target_path = target_path[: last_slash + 1]

        work_queue = [target_path]
        while len(work_queue) > 0:
            prefix = work_queue.pop()
            prefixes = self.render_and_upload_index_document_to_s3(
                bucket, site_name, prefix, exclude_objects, None
            )
            work_queue.extend(prefixes)

        for prefix in self.generate_ascending_prefixes(target_path):
            self.render_and_upload_index_document_to_s3(
                bucket, site_name, prefix, exclude_objects, None
            )
        self.logger.info(f"Finished indexing {bucket} bucket.")

    def render_and_upload_index_document_to_s3(
        self, bucket, site_name, prefix, extra_excluded_items, index_hashes
    ):
        self.logger.debug(f"Rendering index for {prefix}.")
        folder = self.s3_gateway.fetch_folder_content(prefix)
        index = Index(prefix, extra_excluded_items)
        index.items.extend(folder.files)
        index.folders.extend(folder.subdirectories)

        index_document = index.render(
            site_name=site_name, template_environment=self.template_environment
        ).encode("utf-8")

        key = f"{prefix}index.html"

        new_hash = hashlib.md5(  # nosec # skip bandit check as this is not used for encryption
            index_document
        ).hexdigest()
        old_hash = folder.get_index_hash()
        self.logger.info(f"{key} comparing existing hash: {old_hash} to new hash: {new_hash}")
        if old_hash == new_hash:
            self.logger.info(f"Skipping unchanged index for {key}")
        else:
            self.logger.info(f"Uploading index for {key}")

            self.s3_gateway.s3_client.put_object(
                Body=index_document,
                Bucket=bucket,
                CacheControl="max-age=0",
                ContentType="text/html",
                Key=key,
            )

        return folder.subdirectories
