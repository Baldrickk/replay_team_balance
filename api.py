from utils import one_line_string
import itertools
import json
import requests

class API:
  def __init__(self, application_id):
    self.application_id = application_id
    
  def json_from_url(self, url):
    return json.loads(requests.get(url).text)
  
  def get_tank_tiers(self):
    ols = one_line_string()
    url_str = 'https://api.worldoftanks.eu/wot/encyclopedia/vehicles/?application_id={}&fields=type,short_name,tier,tag&page_no={}'
    page_number = 1
    page_count = 1
    tank_db = {}
    while page_number <= page_count:
      url = url_str.format(self.application_id, page_number)
      json_data = json.loads(requests.get(url).text)
      if not json_data.get('status') == 'ok':
        break
      page_count = json_data.get('meta').get('count')
      ols.print(f'Getting tank tiers, page {page_number}/{page_count}')
      page_number += 1
      tank_dict = {tank_data.get('tag'):tank_data for tank_data in json_data.get('data').values()}
      tank_db.update(tank_dict)
    return tank_db

  def id_from_name(self, ols, idx, count, name):
    print(name)
    ols.print(f'Getting player ID: {idx}/{count}:{name}')
    url = ('https://api.worldoftanks.eu/wot/account/list/?type=exact'
                             f'&application_id={self.application_id}'
                             f'&search={name}')
    data = self.json_from_url(url)
    ok = (data.get('status') == 'ok' and 
          data.get('meta').get('count') > 0)
    id = data.get('data')[0].get('account_id') if ok else 0
    return id
  
  def ids_from_names(self, name_iter):
    print('Getting player IDs')
    print(','.join(str(i)+str(v) for i, v in enumerate(name_iter)))
    with one_line_string() as ols:
      ids = (self.id_from_name(ols, idx+1, len(name_iter), name) 
            for idx, name in enumerate(name_iter))
    return ids
    
  def grouper(self, iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)
         
  def player_ratings_from_ids(self, id_iter):
    ratings = []
    for i, group in enumerate(self.grouper(id_iter, 2, '')):
      players = {}
      ids = ','.join(str(id) for id in group)
      url = f'https://api.worldoftanks.eu/wot/account/info/?application_id={self.application_id}&account_id={ids}&fields=global_rating,nickname'
      data = self.json_from_url(url)
      if not data.get('status') == 'ok':
        continue
      else:
        for player in data.get('data').values():
          yield player


