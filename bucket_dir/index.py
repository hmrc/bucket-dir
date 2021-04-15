# -*- coding: utf-8 -*-
import urllib

import humanize


class Index:
    def __init__(self, path, files, subdirectories, excluded_items=None):
        self.path = path
        self.files = files
        self.subdirectories = subdirectories
        self.excluded_items = excluded_items if excluded_items else []

    def should_exclude(self, file_name):
        return file_name in self.excluded_items

    def render(self, site_name, template_environment):
        template = template_environment.get_template("index.html.j2")

        index_items = []
        for item in self.files:
            file_name = item["Key"].split("/")[-1]

            if self.should_exclude(file_name):
                continue

            index_items.append(self.file_index_item(file_name, item))

        for folder in self.subdirectories:
            folder_name = folder.split("/")[-2] + "/"
            index_items.append(
                self.folder_index_item(
                    folder_name,
                )
            )

        return template.render(
            page_name=f"{site_name}/{self.path}",
            index_items=index_items,
            not_root=self.path != "",
        )

    def folder_index_item(self, folder_name):
        return {
            "encoded_name": urllib.parse.quote(folder_name),
            "name": folder_name,
            "modified": "-",
            "size": "-",
        }

    def file_index_item(
        self,
        file_name,
        item,
    ):
        return {
            "encoded_name": urllib.parse.quote(file_name),
            "name": file_name,
            "modified": item["LastModified"].strftime("%d-%b-%Y %H:%M"),
            "size": humanize.naturalsize(item["Size"]),
        }
