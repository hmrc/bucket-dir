# -*- coding: utf-8 -*-
import humanize


class Item:
    def __init__(self, name, modified=None, size=None):
        self.name = name
        self.modified = modified.strftime("%d-%b-%Y %H:%M") if modified else "-"
        self.size = humanize.naturalsize(size) if size else "-"

    def get_justified_attributes(self, name_length, modified_length, column_padding):
        return {
            "name": self.name,
            "name_padding": " ".ljust(name_length - len(self.name) + column_padding),
            "modified": self.modified.ljust(modified_length + column_padding),
            "size": self.size,
        }
