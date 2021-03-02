# -*- coding: utf-8 -*-
import re

import boto3
import humanize
from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape
from rich.progress import track


class BucketDirGenerator:
    def __init__(self, console):
        self.console = console
        self.env = Environment(
            loader=PackageLoader("bucket_dir", "templates"),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.s3_client = boto3.client("s3")

    def generate(self, bucket, site_name):
        contents = self.get_bucket_contents(bucket)
        folders = self.get_bucket_folders(contents)
        for folder in track(folders, description="Processing index documents:"):
            index_document = self.render_index_document(folder, folders, contents, site_name)
            self.upload_index_document_to_s3(bucket, folder, index_document)

    def get_bucket_contents(self, bucket):
        # TODO: Support more than 1000 objects in bucket
        response = self.s3_client.list_objects_v2(
            Bucket=bucket,
            MaxKeys=1000,
        )
        return response.get("Contents", [])

    def get_bucket_folders(self, contents):
        folders = {""}
        keys = [content["Key"] for content in contents]
        for key in keys:
            path = key.split("/")[:-1]
            for depth in range(len(path)):
                folders.add("/".join(path[: depth + 1]))
        self.console.log(f"Folders in bucket: {folders}")
        return list(folders)

    def render_index_document(self, folder, folders, contents, site_name):
        # TODO: There be much sillyness here
        template = self.env.get_template("index.html.j2")
        index_items = []
        longest_name_length = 5
        longest_modified_length = 14
        column_padding = 3
        not_root = folder != ""
        matching_contents = []
        if folder == "":
            matching_contents.extend(
                [
                    content
                    for content in contents
                    if re.match("^[a-z0-9A-Z!\-_.*'()\s]+\/?$", content["Key"])
                ]
            )
        else:
            matching_contents.extend(
                [
                    content
                    for content in contents
                    if re.match(f"^{folder}\/[a-z0-9A-Z!\-_.*'()\s]+/?$", content["Key"])
                ]
            )
        for matching_content in matching_contents:
            name = (
                matching_content["Key"].split("/")[-1]
                or f"{matching_content['Key'].split('/')[-2]}/"
            )
            if name == "index.html":
                continue
            modified = matching_content["LastModified"].strftime("%d-%b-%Y %H:%M")
            if len(name) > longest_name_length:
                longest_name_length = len(name)
            if len(modified) > longest_modified_length:
                longest_modified_length = len(modified)
            if matching_content["Size"]:
                index_items.append(
                    {
                        "name": name,
                        "modified": modified,
                        "size": humanize.naturalsize(matching_content["Size"]),
                    }
                )
        if folder == "":
            matching_subfolders = [
                subfolder
                for subfolder in folders
                if re.match(f"^[a-z0-9A-Z!\-_.*'()\s]+$", subfolder)
            ]
        else:
            matching_subfolders = [
                subfolder
                for subfolder in folders
                if re.match(f"^{folder}\/[a-z0-9A-Z!\-_.*'()]+\/?$", subfolder)
            ]
        for matching_subfolder in matching_subfolders:
            name = f"{matching_subfolder.split('/')[-1]}/"
            if len(name) > longest_name_length:
                longest_name_length = len(name)
            index_items.append(
                {
                    "name": name,
                    "modified": "-",
                    "size": "-",
                }
            )
        for index_item in index_items:
            index_item["padding"] = " ".ljust(
                longest_name_length - len(index_item["name"]) + column_padding
            )
            index_item["modified"] = index_item["modified"].ljust(
                longest_modified_length + column_padding
            )
        table_headers = f"{'Name'.ljust(longest_name_length + column_padding)}{'Last modified'.ljust(longest_modified_length + column_padding)}Size"
        page_name = f"{site_name}/{folder}"
        if not page_name.endswith("/"):
            page_name = f"{page_name}/"
        return template.render(
            page_name=page_name,
            table_headers=table_headers,
            index_items=index_items,
            not_root=not_root,
        )

    def upload_index_document_to_s3(self, bucket, folder, index_document):
        s3_client = boto3.client("s3")
        key = "index.html"
        if folder != "":
            key = f"{folder}/index.html"
        s3_client.put_object(
            Body=index_document.encode(),
            Bucket=bucket,
            CacheControl="max-age=0",
            ContentType="text/html",
            Key=key,
        )
