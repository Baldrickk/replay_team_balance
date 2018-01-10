from utils import one_line_string
import json
import requests

class API:
  def __init__(self, application_id):
    self.application_id = application_id
    
  def json_from_url(self, url):
    return json.loads(requests.get(url).text)
  
  def get_tank_tiers():
    url = f'https://api.worldoftanks.eu/wot/account/list/?application_id={self.application_id}&search={name}&type=exact'
    tank_db = json.loads(requests.get(url).text)
    tanks = tanks_db.get('data')
    return tankdata
    for i, tank in tanks.items():
      name = tank.get('tag')
      tier = tank.get('tier')
      nation = tank.get('nation')
      tankdata[name] = (name, tier, nation)
    return tankdata

  def id_from_name(self, ols, idx, count, name):
    ols.print(f'{idx}/{count}:{name}')
    url = ('https://api.worldoftanks.eu/wot/account/list/?type=exact'
                             f'&application_id={self.application_id}'
                             f'&search={name}')
    print (url)
    data = self.json_from_url(url)
    ok = (data.get('status') == 'ok' and 
          data.get('meta').get('count') > 0)
    id = data.get('data')[0].get('account_id') if ok else 0
    return id
  
  def ids_from_names(self, name_iter):
    print('Getting player IDs')
    ols = one_line_string()
    ids = [self.id_from_name(ols, idx, len(name_iter), name) 
                        for idx, name in enumerate(name_iter)]
    return ids
      
  def player_ratings_from_ids(self, id_iter):
    ratings = []
    for i, group in enumerate(self.grouper(id_iter, 100)):
      ids = ','.join(group)
      url = f'https://api.worldoftanks.eu/wot/account/info/?application_id={self.application_id}&account_id={ids}&fields=global_rating,nickname'
      data = self.json_from_url(url)
