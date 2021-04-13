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
        folder_lengths = list(map(len, self.folders))
        file_lengths = [len(item["Key"]) for item in self.items]
        longest_name_length = max(folder_lengths + file_lengths + [5])

        longest_modified_length = max(
            [len(str(item["LastModified"])) for item in self.items] + [14]
        )

        column_padding = 3
        table_headers = f"{'Name'.ljust(longest_name_length + column_padding)}{'Last modified'.ljust(longest_modified_length + column_padding)}Size"

        index_items = []
        for item in self.items:
            file_name = item["Key"].split("/")[-1]

            if self.should_exclude(file_name):
                continue

            index_items.append(
                self.file_index_item(
                    column_padding, file_name, item, longest_modified_length, longest_name_length
                )
            )

        for folder in self.folders:
            folder_name = folder.split("/")[-2] + "/"
            index_items.append(
                self.folder_index_item(
                    column_padding,
                    folder,
                    folder_name,
                    longest_modified_length,
                    longest_name_length,
                )
            )

        return template.render(
            page_name=f"{site_name}/{self.path}",
            table_headers=table_headers,
            index_items=index_items,
            not_root=self.path != "",
        )

    def folder_index_item(
        self, column_padding, folder, folder_name, longest_modified_length, longest_name_length
    ):
        return {
            "encoded_name": urllib.parse.quote(folder_name),
            "name": folder_name,
            "name_padding": " ".ljust(longest_name_length - len(folder) + column_padding),
            "modified": "-".ljust(longest_modified_length + column_padding),
            "size": "-",
        }

    def file_index_item(
        self, column_padding, file_name, item, longest_modified_length, longest_name_length
    ):
        return {
            "encoded_name": urllib.parse.quote(file_name),
            "name": file_name,
            "name_padding": " ".ljust(longest_name_length - len(item["Key"]) + column_padding),
            "modified": item["LastModified"]
            .strftime("%d-%b-%Y %H:%M")
            .ljust(longest_modified_length + column_padding),
            "size": humanize.naturalsize(item["Size"]),
        }
