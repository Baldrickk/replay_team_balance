import itertools
import json
import requests


class API:
    def __init__(self, application_id, over_writer):
        self.application_id = application_id
        self.ow = over_writer

    @staticmethod
    def json_from_url(url):
        return json.loads(requests.get(url).text)

    def tank_tiers(self):
        url_str = ('https://api.worldoftanks.eu/wot/encyclopedia/vehicles/?'
                   'application_id={}&'
                   'fields=type,short_name,tier,tag&'
                   'page_no={}')
        page_number = 1
        page_count = 1
        tank_db = {}
        while page_number <= page_count:
            url = url_str.format(self.application_id, page_number)
            json_data = json.loads(requests.get(url).text)
            if not json_data.get('status') == 'ok':
                break
            page_count = json_data.get('meta').get('count')
            self.ow.print(f'Getting tank tiers, page {page_number}/{page_count}')
            page_number += 1
            tank_dict = {tank_data.get('tag'):tank_data for tank_data in json_data.get('data').values()}
            tank_db.update(tank_dict)
        return tank_db

    def id_from_name(self, idx, count, name):
        self.ow.print(f'Getting player ID: {idx}/{count}:{name}')
        url = ('https://api.worldoftanks.eu/wot/account/list/?type=exact'
               f'&application_id={self.application_id}'
               f'&search={name}')
        data = self.json_from_url(url)
        ok = (data.get('status') == 'ok' and
              data.get('meta').get('count') > 0)
        acc_id = data.get('data')[0].get('account_id') if ok else 0
        return acc_id

    def ids_from_names(self, name_iter):
        ids = (self.id_from_name(idx+1, len(name_iter), name)
               for idx, name in enumerate(name_iter))
        return ids

    @staticmethod
    def grouper(iterable, n, fillvalue=None):
        """Collect data into fixed-length chunks or blocks
        grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"""
        args = [iter(iterable)] * n
        return itertools.zip_longest(*args, fillvalue=fillvalue)

    def ratings_from_ids(self, id_iter):
        for i, group in enumerate(self.grouper(id_iter, 100, '')):
            ids = ','.join(str(player_id) for player_id in group)
            url = ('https://api.worldoftanks.eu/wot/account/info/?'
                   f'application_id={self.application_id}&'
                   f'account_id={ids}&'
                   'fields=global_rating,nickname')
            data = self.json_from_url(url)
            if not data.get('status') == 'ok':
                continue
            else:
                for player_id, player in data.get('data').items():
                    player['id'] = player_id
                    yield player


