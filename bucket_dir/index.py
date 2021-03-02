# -*- coding: utf-8 -*-
class Index:
    def __init__(self, path):
        self.path = path
        self.items = []

    def add_item(self, item):
        existing_item = [i for i in self.items if i.name == item.name]
        if not existing_item:
            self.items.append(item)

    def render(self, site_name, template_environment):
        template = template_environment.get_template("index.html.j2")
        longest_name_length = max(max([len(item.name) for item in self.items], default=0), 5)
        longest_modified_length = max(
            max([len(item.modified) for item in self.items], default=0), 14
        )
        column_padding = 3
        table_headers = f"{'Name'.ljust(longest_name_length + column_padding)}{'Last modified'.ljust(longest_modified_length + column_padding)}Size"
        index_items = [
            item.get_justified_attributes(
                name_length=longest_name_length,
                modified_length=longest_modified_length,
                column_padding=column_padding,
            )
            for item in self.items
        ]
        return template.render(
            page_name=f"{site_name}{self.path}",
            table_headers=table_headers,
            index_items=index_items,
            not_root=self.path != "/",
        )
