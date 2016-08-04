# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 10:56:10 2016

@author: Tak
"""

import falcon
import json
import logging
from lib import evLoad
from lib import houseLoad as house
from lib import Week4_Monthly_Cost as cost
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
        Ls_App = map(int, req.get_param_as_list('Ls_App') or [0]*6)
        Cust_Monthly_Cost = req.get_param_as_int('Monthly_Cost') or 0
        Cust_Monthly_KWh = req.get_param_as_int('Monthly_KWh') or 0

        try:
            Cust_Total_Profile, Cust_Profile, Deferred_Matrix = house.get_household_load_profile(N_room, N_day, N_night, Ls_App, Cust_Monthly_Cost, Cust_Monthly_KWh)
            result = {
                'Cust_Total_Profile':Cust_Total_Profile.tolist(),
                'Cust_Profile':Cust_Profile.tolist(),
                'Deferred_Matrix':Deferred_Matrix.tolist()
            }
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

class EnergyCost:
    def __init__(self):
        self.logger = logging.getLogger('evapp.' + __name__)
        
    def on_get(self, req, resp):
        distance = req.get_param_as_int('distance') or 0
        maker = req.get_param('maker') or ''
        model = req.get_param('model') or ''
        year = req.get_param_as_int('year') or 2016
        charger = req.get_param_as_int('charger') or 0
        N_room = req.get_param_as_int('N_room') or 0
        N_day = req.get_param_as_int('N_day') or 0
        N_night = req.get_param_as_int('N_night') or 0
        Ls_App = map(int, req.get_param_as_list('Ls_App') or [0]*6)
        Cust_Monthly_Cost = req.get_param_as_int('Monthly_Cost') or 0
        Cust_Monthly_KWh = req.get_param_as_int('Monthly_KWh') or 0
        conn_time = map(int, req.get_param_as_list('time') or [0]*4)
        allowance = req.get_param_as_int('allowance') or 350

        try:
            Cust_Total_Profile, Cust_Profile, Deferred_Matrix = house.get_household_load_profile(N_room, N_day, N_night, Ls_App, Cust_Monthly_Cost, Cust_Monthly_KWh, conn_time[:3])
#            house_data = house.get_household_load_profile(N_room, N_day, N_night, Ls_App, Cust_Monthly_Cost, Cust_Monthly_KWh, conn_time[:3])
            ev_data = ev.get_load_profile(distance, maker, model, year, charger, conn_time[3])
            result_cost = cost.get_cost(
                Household_Total=Cust_Total_Profile,
                Household=Cust_Profile,
                Def_Load=Deferred_Matrix,
                Monthly_allowance=allowance,
                EV_Load=ev_data['load_profile'],
                No_EV=5,
                No_Def=2)
        except Exception as ex:
            self.logger.error(ex)
            description = ('Aliens have attacked our base! We will '
                           'be back as soon as we fight them off. '
                           'We appreciate your patience.')

            raise falcon.HTTPServiceUnavailable(
                'Service Outage',
                description,
                30)

        resp.body = json.dumps(result_cost)

app = falcon.API()
ev_load_profile = EvLoadProfile()
house_load_profile = HouseLoadProfile()
energy_cost = EnergyCost()

app.add_route('/ev/load', ev_load_profile)
app.add_route('/house/load', house_load_profile)
app.add_route('/cost', energy_cost)
