import csv


class PlayerCache:
    def __init__(self, filename, field_names):
        self.filename = filename
        self.data = {}
        self.cache_handle = None
        self.key = field_names[0]
        self.field_names = field_names
        try:
            with open(self.filename, 'r') as file:
                for row in csv.DictReader(file, self.field_names):
                    self.add_to_cache(row)
        except FileNotFoundError:
            # there is no cache file, no problem.
            pass
        self.cache_handle = open(self.filename, 'a', newline='')
        self.writer = csv.DictWriter(self.cache_handle, self.field_names)
        self.cache_handle.flush()
        print(f'{len(self.data)} players loaded')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_cache()

    def add_to_cache(self, record):
        existing = self.data.get(record.get(self.key),{})
        a = all(str(existing.get(i)) == str(record.get(i)) for i in self.field_names)
        if not a:
            if self.cache_handle is not None:
                self.writer.writerow(record)
            self.data[record.get(self.key)] = record

    def cached_record(self, name):
        return self.data.get(name)

    def close_cache(self):
        self.cache_handle.close()
        self._write_clean_cache()

    def _write_clean_cache(self):
        with open(self.filename, 'w', newline='') as self.cache_handle:
            self.writer = csv.DictWriter(self.cache_handle, self.field_names)
            for record in self.data.items():
                self.writer.writerow(record)
