import csv


class PlayerCache:
    def __init__(self, filename):
        self.filename = filename
        self.data = {}
        self.names_to_id = set()
        self.ids_to_stat = set()
        self.cache_handle = None
        field_names = ['nickname', 'id', 'global_rating']
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

    def add_to_cache(self, player):
        if self.cache_handle and self.data.get(player.get('nickname')) is None:
            self.writer.writerow(player)
        self.data[player.get('nickname')] = player

    def cached_player(self, name):
        return self.data.get(name)

    def close_cache(self):
        self.cache_handle.close()

