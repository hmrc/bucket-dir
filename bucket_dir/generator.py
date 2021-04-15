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

    def generate(self, extra_exclude_objects=None, single_threaded=False, target_path=""):
        if target_path.startswith("/"):
            target_path = target_path[1:]

        if not target_path.endswith("/"):
            last_slash = target_path.rfind("/")
            target_path = target_path[: last_slash + 1]

        excluded_objects = ["favicon.ico", "index.html"]
        if extra_exclude_objects:
            excluded_objects.extend(extra_exclude_objects)

        max_workers = 1 if single_threaded else None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            self.logger.info(
                f"Generating indexes for {self.s3_gateway.bucket_name} across {executor._max_workers} worker threads."
            )
            folder_dictionary = {}
            futures = deque([])
            self.enqueue_folder_discovery(executor, folder_dictionary, futures, target_path)

            self.wait_for_all_futures_recursively(futures)

            for prefix, folder in folder_dictionary.items():
                futures.append(executor.submit(self.update_index, prefix, folder, excluded_objects))

            self.wait_for_all_futures(futures)

        self.logger.info(f"Finished generation.")

    def enqueue_folder_discovery(self, executor, folder_dictionary, futures, target_path):
        futures.append(
            executor.submit(
                self.discover_folder,
                folder_dictionary,
                target_path,
                executor,
            )
        )
        for prefix in self.generate_ascending_prefixes(target_path):
            futures.append(executor.submit(self.discover_folder, folder_dictionary, prefix))

    def wait_for_all_futures(self, futures):
        self.logger.debug(f"Waiting for all futures to finish.")
        while len(futures) > 0:
            futures.popleft().result()

    def wait_for_all_futures_recursively(self, futures):
        self.logger.debug(f"Waiting for all futures to finish.")
        while len(futures) > 0:
            sub_futures_array = futures.popleft().result()
            futures.extend(sub_futures_array)

    def discover_folder(self, folder_dictionary, prefix, executor=None):
        self.logger.debug(f"Rendering index for prefix: '{prefix}'.")
        folder = self.s3_gateway.fetch_folder_content(prefix)
        folder_dictionary[prefix] = folder

        futures = []
        if executor is not None:
            for subdirectory in folder.subdirectories:
                futures.append(
                    executor.submit(
                        self.discover_folder,
                        folder_dictionary,
                        subdirectory,
                        executor,
                    )
                )

        return futures

    def update_index(self, prefix, folder, excluded_objects):
        key = f"{prefix}index.html"
        if folder.is_empty(excluded_objects):
            self.logger.debug(f"Skipping empty folder {key}.")
            return

        index = Index(prefix, folder.files, folder.subdirectories, excluded_objects)
        index_document = index.render(
            site_name=self.site_name, template_environment=self.template_environment
        ).encode("utf-8")

        new_hash = hashlib.md5(  # nosec # skip bandit check as this is not used for encryption
            index_document
        ).hexdigest()
        old_hash = folder.get_index_hash()
        self.logger.debug(f"{key} comparing existing hash: {old_hash} to new hash: {new_hash}.")
        if old_hash == new_hash:
            self.logger.debug(f"Skipping unchanged index for {key}.")
        else:
            self.logger.info(f"Uploading index for {key}.")
            self.s3_gateway.put_object(
                body=index_document,
                key=key,
            )
