import csv


class PlayerCache:
    def __init__(self, filename, field_names):
        self.filename = filename
        self.data = {}
        self.names_to_id = set()
        self.ids_to_stat = set()
        self.cache_handle = None
        self.key = field_names[0]
        self.field_names = field_names
        try:
            with open(filename, 'r') as file:
                for row in csv.DictReader(file, field_names):
                    self.add_to_cache(row)
        except FileNotFoundError:
            # there is no cache file, no problem.
            pass
        self.cache_handle = open(filename, 'a', newline='')
        self.writer = csv.DictWriter(self.cache_handle, field_names)
        self.cache_handle.flush()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_cache()

    def add_to_cache(self, record):
        if self.cache_handle and self.data.get(record.get(self.key)) is None:
            self.writer.writerow(record)
        self.data[record.get(self.key)] = record

    def cached_record(self, name):
        return self.data.get(name)

    def close_cache(self):
        self.cache_handle.close()

