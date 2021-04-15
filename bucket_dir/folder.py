# -*- coding: utf-8 -*-
class Folder:
    def __init__(self, prefix, files, subdirectories):
        self.prefix = prefix
        self.files = files
        self.subdirectories = subdirectories

    def get_index_hash(self):
        for file in self.files:
            if file["Key"] == f"{self.prefix}index.html":
                return file["ETag"].replace('"', "")
        return None

    def is_empty(self, excluded_files=None):
        if excluded_files:
            for file in self.files:
                if not file["Key"].endswith(tuple(excluded_files)):
                    return False
            return not self.subdirectories
        else:
            return not (self.subdirectories or self.files)
