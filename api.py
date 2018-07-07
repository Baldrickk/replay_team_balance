import itertools
import json
import requests
from time import sleep
from random import randint
from concurrent.futures import as_completed as as_comp
from concurrent.futures import ThreadPoolExecutor as tpe


class API:
    def __init__(self, application_id, over_writer):
        self.application_id = application_id
        self.ow = over_writer

    @staticmethod
    def requests_retry_session(retries=10,
                               backoff_factor_min=10,
                               backoff_factor_max=20,
                               status_forcelist=(500, 502, 504),
                               session=None):
        session = session or requests.Session()
        retry = requests.packages.urllib3.util.retry.Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=randint(backoff_factor_min, backoff_factor_max),
            status_forcelist=status_forcelist,
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def json_from_url(self, url):
        return json.loads(self.requests_retry_session().get(url).text)

    def tank_tiers(self):
        with open('missingtanks.json') as missing:
            tank_db = json.load(missing)
        url_str = ('https://api.worldoftanks.eu/wot/encyclopedia/vehicles/?'
                   'application_id={}&'
                   'fields=type,short_name,tier,tag&'
                   'page_no={}')
        page_number = 1
        page_count = page_number + 1
        while page_number <= page_count:
            url = url_str.format(self.application_id, page_number)
            json_data = json.loads(self.requests_retry_session().get(url).text)
            if not json_data.get('status') == 'ok':
                break
            page_count = json_data.get('meta').get('page_total')
            page_number = json_data.get('meta').get('page')
            self.ow.print(f'Getting tank tiers, page {page_number}/{page_count}')
            page_number += 1
            tank_dict = {tank_data.get('tag'): tank_data for tank_data in json_data.get('data').values()}
            tank_db.update(tank_dict)
        return tank_db

    def id_from_name(self, idx, count, name):
        # print (f'{idx} - {count} - {name}')
        self.ow.print(f'Getting player ID: {idx}/{count}:{name}')
        # We are probably going to run into a load of REQUEST_LIMIT_EXCEDED errors now that
        # the rate has increased  Need to handle that.
        retry = True
        while retry:
            url = ('https://api.worldoftanks.eu/wot/account/list/?type=exact'
                   f'&application_id={self.application_id}'
                   f'&search={name}')
            data = self.json_from_url(url)
            if data.get('status') == 'ok':
                if data.get('meta').get('count') > 0:
                    return data.get('data')[0].get('account_id')
            elif data.get('status') == 'error' and data.get('error').get('code') == 407:
                sleep(0.5)
            else:
                # we haven't found our player, and we have run into a different error.
                # return an empty player
                print (data)
                return 0

    def ids_from_names_generator(self, names):
        for i, name in enumerate(names):
            p_id = self.id_from_name(i+1, len(names), name)
            if p_id:
                yield p_id
                
    def ids_from_names_generator_2(self, names):
        with tpe() as executor:
            future_to_id = {executor.submit(self.id_from_name, i+1, len(names), name): (i+1, name) for (i, name) in enumerate(names)}
            for future in as_comp(future_to_id):
                i, name = future_to_id[future]
                try:
                    id = future.result()
                except Exception as exc:
                    print(f'ID-ing {name} generated an exception: {exc}, retrying')
                    # future_to_id[executor.submit(self.id_from_name, i, len(names), name)] = (i, name)
                else:
                    yield id

    def ids_from_names(self, name_iter):
        return self.ids_from_names_generator_2(name_iter)

    @staticmethod
    def grouper(iterable, n, fillvalue=None):
        """Collect data into fixed-length chunks or blocks
        grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"""
        args = [iter(iterable)] * n
        return itertools.zip_longest(*args, fillvalue=fillvalue)

    def ratings_from_ids(self, id_iter):
        count = 0
        for i, group in enumerate(self.grouper(id_iter, 100, '')):
            ids = ','.join(str(player_id) for player_id in group)
            url = ('https://api.worldoftanks.eu/wot/account/info/?'
                   f'application_id={self.application_id}&'
                   f'account_id={ids}&'
                   'fields=global_rating,nickname')
            count += 1
            self.ow.print(f'Getting Player ratings - {count*100}')
            data = self.json_from_url(url)
            if not data.get('status') == 'ok':
                continue
            else:
                for player_id, player in data.get('data').items():
                    if not player:
                        continue
                    player['id'] = player_id
                    yield player

    def r_from_id_url(self, group):
        url = ('https://api.worldoftanks.eu/wot/account/info/?'
               f'application_id={self.application_id}&'
               f'account_id={",".join(str(player_id) for player_id in group)}'
               '&fields=global_rating,nickname')
        return url
    
    def ratings_from_ids_2(self, id_iter):
        with tpe() as executor:
            future_to_rate = {executor.submit(self.json_from_url, self.r_from_id_url(group)): 
                              (i+1, group) for (i, group) in enumerate(self.grouper(id_iter, 100, ''))}
            for future in as_comp(future_to_rate):
                i, group = future_to_rate[future]
                self.ow.print(f'Getting Player ratings - {i*100}')
                try:
                    ratings = future.result()
                    if not ratings.get('status') == 'ok':
                        print(ratings)
                except Exception as exc:
                    print(f'rating-ing group {i} generated an exception: {exc}')
                else:
                    r_data = ratings.get('data')
                    if r_data is not None:
                        for player_id, player in r_data.items():
                            if not player:
                                continue
                            player['id'] = player_id
                            yield player

