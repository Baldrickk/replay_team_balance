class PlayerCache:
    def __init__(self, filename):
        self.filename = filename
        self.data = {}
        self.names_to_id = set()
        self.ids_to_stat = set()
        self.cache_handle = None
        try:
            with open(filename, 'r') as file:
                for line in file:
                    if line:
                        name, p_id, rating = line.split(',')
                        player = {'nickname': name,
                                  'id': p_id,
                                  'global_rating': rating}
                        self.add_to_cache(player)
        except FileNotFoundError:
            pass
        self.cache_handle = open(filename, 'a')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_cache()

    def add_to_cache(self, player):
        player_name = player.get('nickname')
        player_id = player.get('id')
        player_rating = player.get('global_rating')
        self.data[player_name] = {'name': player_name,
                                  'id': player_id,
                                  'rating': player_rating}
        if self.cache_handle and not self.data.get(player.get('name')):
            self.cache_handle.write(f'{player_name},'
                                    f'{player_id},'
                                    f'{player_rating}\n')

    def cached_player(self, name):
        return self.data.get(name)

    def close_cache(self):
        self.cache_handle.close()
