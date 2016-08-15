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
from lib import Cost as C
ev = evLoad.EV('db/ev_model.db')
COST=C.Cost('db/Tariff_Rate_New.db','db/Household_15mins.db')
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
        cust_monthly_cost = req.get_param_as_int('Monthly_Cost') or 0
        #Cust_Monthly_KWh = req.get_param_as_int('Monthly_KWh') or 0

        try:
            Cust_Total_Profile, Cust_Profile, Deferred_Matrix = house.get_household_load_profile(N_room, N_day, N_night, Ls_App, cust_monthly_cost, Cust_Monthly_KWh)
            #Cust_Total_Profile, Cust_Profile1, Deferred_Matrix = house.get_household_load_profile(Consumption_Case2,N_room, N_day,N_night,Ls_App,connection_time=[0, 0, 0])
            #get_household_load_profile(Consumption,N_room, N_day,N_night,Ls_App,connection_time=[0, 0, 0])
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
        Utility_Name = req.get_param('Utility_Name') 
        if Utility_Name=='PG':
            Utility_Name='PG&E'
        if Utility_Name=="I don't know":
        	Utility_Name='PG&E'

        Rate_Name = req.get_param('Rate_Name') 
        if Rate_Name == "I don't know":
        	if Utility_Name=='PG&E':
        		Rate_Name='E1'
        	elif Utility_Name=='Duke Energy North Carolina':
        		Rate_Name='Residential Service Rate'
        	elif Utility_Name=='Duke Energy South Carolina':
        		Rate_name='Residential Service'
        	elif Utility_Name=='Duke Energy Indiana':
        		Rate_Name='Residential and Farm Service'
        	elif Utility_Name=='Duke Energy Kentucky':
        		Rate_Name='Residential Service'
        	elif Utility_Name=='Duke Energy Ohio':
        		Rate_Name='Residential Service'
        	elif Utility_Name=='Duke Energy Florida':
        		Rate_Name='Residential Service'
        distance = req.get_param_as_int('distance') or 0
        maker = req.get_param('maker') or ''
        model = req.get_param('model') or ''
        year = req.get_param_as_int('year') or 2016
        charger = req.get_param_as_int('charger') or 0
        N_room = req.get_param_as_int('N_room') or 0
        N_day = req.get_param_as_int('N_day') or 0
        N_night = req.get_param_as_int('N_night') or 0
        Ls_App = map(int, req.get_param_as_list('Ls_App') or [0]*6)
        cust_monthly_cost = req.get_param_as_int('Monthly_Cost') or 0
        #Cust_Monthly_KWh = req.get_param_as_int('Monthly_KWh') or 0
        conn_time = map(int, req.get_param_as_list('time') or [0]*4)
        #allowance = req.get_param_as_int('allowance') or 350
        charging_outside=req.get_param_as_int('Charging_outside') or 0

        try:
            ev_data = ev.get_load_profile(distance, maker, model, year, charger, conn_time[3])['load_profile']
            #EV_Cost=COST.Get_EV_Def_Cost(Charging_Outside,Utility_Name,Rate_Name,EV_data,Ls_App,No_EV,cust_monthly_cost)
            Consumption=COST.Get_Monthly_Consumption(charging_outside,Utility_Name,Rate_Name,N_room, N_day,N_night,Ls_App,ev_data,cust_monthly_cost,No_EV=5)
            Cust_Total_Profile, Cust_Profile, Deferred_Matrix = house.get_household_load_profile(Consumption,N_room, N_day, N_night, Ls_App, conn_time[:3])
            #house_data = house.get_household_load_profile(N_room, N_day, N_night, Ls_App, cust_monthly_cost, Cust_Monthly_KWh, conn_time[:3])
            #ev_data = ev.get_load_profile(distance, maker, model, year, charger, conn_time[3])
            result_cost = COST.Get_Cost(
                Utility_Name=Utility_Name,
                Household_Total=Cust_Total_Profile,
                Household=Cust_Profile,
                Def_Load=Deferred_Matrix,
                EV_Load=ev_data,
                Charging_Outside=charging_outside,
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
        #resp.body=Utility_Name
app = falcon.API()
ev_load_profile = EvLoadProfile()
house_load_profile = HouseLoadProfile()
energy_cost = EnergyCost()

app.add_route('/ev/load', ev_load_profile)
app.add_route('/house/load', house_load_profile)
app.add_route('/cost', energy_cost)
