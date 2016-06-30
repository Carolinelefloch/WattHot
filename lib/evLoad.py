# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 15:20:11 2016

@author: ODA
"""

import math
import sqlite3

class EV:
    def __init__(self, path):
        # Connect the EV model databese
        conn = sqlite3.connect(path)
        self.cur = conn.cursor()


    """ Get 24-hour load profile for EV charging
    
        Parameters
        ----------
        distance : float
            Daily driving distance in mile
        ev_maker : string
            Maker of EV
        ev_model : string
            Model of EV
        ev_year : int
            Year of EV        
        charger_type : int
            Type of charger
            -level 1 : 0
            -level 2 (25amp): 1
            -level 2 (40amp): 2
            -level 2 (50amp): 3
    
        Returns
        ----------
        load_profile : list
            24-hour load profile when charging is requested
        charging_time : float
            24-hour load profile when charging is requested
        depletion : float
            24-hour load profile when charging is requested
    """
    charging_load_data = [1.4, 4.8, 7.2, 9.6] #kW


    def get_load_profile(self, distance, ev_maker, ev_model,  ev_year, charger_type):
        self.cur.execute('SELECT combE, range, acceptanceR FROM spec WHERE make = ? AND model = ? AND year = ? LIMIT 1', (ev_maker, ev_model, ev_year))
        data = self.cur.fetchone()
        if data is None:
            print('There is no model matching to %s, %s, %d in the database' %(ev_maker, ev_model,  ev_year))
            return  
        consumption_rate, range_mile, acceptance_load = data
    
        # check if the distance exceeds the maximum range
        if  distance > range_mile:
            distance = range_mile
        depletion = float(distance) / range_mile
        
        # choose the smaller load from charger load and acceptance load
        charging_load = min(self.charging_load_data[charger_type], acceptance_load)
    
        # compute charging time
        charging_time = consumption_rate * distance / 100 / charging_load
        if charging_time < 48:
            t = int(math.ceil(charging_time*2))  # round up the time
            load_profile = [charging_load]*t + [0]*(48-t)
        else:
            load_profile = [charging_load]*48
            
        return {'load_profile' : load_profile, 'charging_time' : charging_time, 'depletion' : depletion}
        