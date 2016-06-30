# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 10:56:10 2016

@author: Tak

Test URL:
http://localhost:8000/ev/load/?distance=50&maker=Nissan&model=Leaf&year=2015&charger=2
http://localhost:8000/house/load/?N_room=1&N_day=1&N_night=1&Ls_App=[1,1,1,1,1,0]
"""

import falcon
import json
import logging
from lib import evLoad
from lib import houseLoad as house
ev = evLoad.EV('db/ev_model.db')

class EvLoadProfile:
    def __init__(self):
        self.logger = logging.getLogger('evapp.' + __name__)
        
    def on_get(self, req, resp):
        distance = req.get_param_as_int('distance') or 0
        maker = req.get_param('maker') or ''
        model = req.get_param('model') or ''
        year = req.get_param_as_int('year') or 2016
        charger = req.get_param_as_int('charger') or 0
        
        try:
            result = ev.get_load_profile(distance, maker, model, year, charger)
        except Exception as ex:
            self.logger.error(ex)
            description = ('Aliens have attacked our base! We will '
                           'be back as soon as we fight them off. '
                           'We appreciate your patience.')

            raise falcon.HTTPServiceUnavailable(
                'Service Outage',
                description,
                30)
        resp.body = json.dumps(result)

class HouseLoadProfile:
    def __init__(self):
        self.logger = logging.getLogger('houseapp.' + __name__)
        
    def on_get(self, req, resp):
        N_room = req.get_param_as_int('N_room') or 0
        N_day = req.get_param_as_int('N_day') or 0
        N_night = req.get_param_as_int('N_night') or 0
        Ls_App = req.get_param_as_list('Ls_App') or []

        try:
            result = house.get_household_load_profile(N_room, N_day, N_night, Ls_App)
        except Exception as ex:
            self.logger.error(ex)
            description = ('Aliens have attacked our base! We will '
                           'be back as soon as we fight them off. '
                           'We appreciate your patience.')

            raise falcon.HTTPServiceUnavailable(
                'Service Outage',
                description,
                30)
        resp.body = json.dumps(result)
 
app = falcon.API()
ev_load_profile = EvLoadProfile()
house_load_profile = HouseLoadProfile()

app.add_route('/ev/load', ev_load_profile)
app.add_route('/house/load', house_load_profile)