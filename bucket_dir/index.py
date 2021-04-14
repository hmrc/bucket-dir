# -*- coding: utf-8 -*-
import urllib

import humanize


class Index:
    def __init__(self, path, extra_excluded_items=None):
        self.path = path
        self.items = []
        self.folders = []
        self.excluded_items = ["favicon.ico", "index.html"]
        if extra_excluded_items:
            self.excluded_items.extend(extra_excluded_items)

    def should_exclude(self, file_name):
        return file_name in self.excluded_items

    def render(self, site_name, template_environment):
        template = template_environment.get_template("index.html.j2")

        index_items = []
        for item in self.items:
            file_name = item["Key"].split("/")[-1]

            if self.should_exclude(file_name):
                continue

            index_items.append(self.file_index_item(file_name, item))

        for folder in self.folders:
            folder_name = folder.split("/")[-2] + "/"
            index_items.append(
                self.folder_index_item(
                    folder,
                    folder_name,
                )
            )

        return template.render(
            page_name=f"{site_name}/{self.path}",
            index_items=index_items,
            not_root=self.path != "",
        )

    def folder_index_item(self, folder, folder_name):
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
