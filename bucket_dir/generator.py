# -*- coding: utf-8 -*-
import hashlib
import logging
from collections import deque
from concurrent.futures.thread import ThreadPoolExecutor

import boto3
from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape

from .index import Index
from .s3 import S3


class BucketDirGenerator:
    def __init__(
        self,
        bucket_name,
        site_name,
        logger=None,
    ):
        self.logger = logger or logging.getLogger("bucket_dir")
        self.template_environment = Environment(
            loader=PackageLoader("bucket_dir", "templates"),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.site_name = site_name
        self.s3_gateway = S3(bucket_name=bucket_name)

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

    def generate(self, exclude_objects=None, single_threaded=False, target_path=""):
        if target_path.startswith("/"):
            target_path = target_path[1:]

        if not target_path.endswith("/"):
            last_slash = target_path.rfind("/")
            target_path = target_path[: last_slash + 1]

        max_workers = 1 if single_threaded else None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = deque([])
            futures.append(
                executor.submit(
                    self.render_and_upload_index_document_to_s3,
                    target_path,
                    exclude_objects,
                    executor,
                )
            )

            for prefix in self.generate_ascending_prefixes(target_path):
                futures.append(
                    executor.submit(
                        self.render_and_upload_index_document_to_s3,
                        prefix,
                        exclude_objects,
                    )
                )

            self.wait_for_all_futures_recursively(futures)

    def wait_for_all_futures_recursively(self, futures):
        self.logger.info(f"waiting for all futures to finish")
        while len(futures) > 0:
            sub_futures_array = futures.popleft().result()
            futures.extend(sub_futures_array)

    def render_and_upload_index_document_to_s3(self, prefix, extra_excluded_items, executor=None):
        self.logger.info(f"Rendering index for {prefix}.")
        folder = self.s3_gateway.fetch_folder_content(prefix)

        futures = []
        if executor is not None:
            for subdirectory in folder.subdirectories:
                self.logger.info(f"{prefix} job submitting job for {subdirectory}")
                futures.append(
                    executor.submit(
                        self.render_and_upload_index_document_to_s3,
                        subdirectory,
                        extra_excluded_items,
                        executor,
                    )
                )

        index = Index(prefix, extra_excluded_items)
        index.items.extend(folder.files)
        index.folders.extend(folder.subdirectories)

        index_document = index.render(
            site_name=self.site_name, template_environment=self.template_environment
        ).encode("utf-8")

        key = f"{prefix}index.html"

        new_hash = hashlib.md5(  # nosec # skip bandit check as this is not used for encryption
            index_document
        ).hexdigest()
        old_hash = folder.get_index_hash()
        self.logger.debug(f"{key} comparing existing hash: {old_hash} to new hash: {new_hash}")
        if old_hash == new_hash:
            self.logger.info(f"Skipping unchanged index for {key}")
        else:
            self.logger.info(f"Uploading index for {key}")
            self.s3_gateway.put_object(
                body=index_document,
                key=key,
            )

        return futures
