import pandas as pd
import numpy as np
from itertools import groupby
import operator
from operator import itemgetter
import copy
import sqlite3

conn=sqlite3.connect('db/Household_15mins.db')
Def_Load=pd.read_sql('SELECT * FROM Deferred_Load',conn)
Profile=pd.read_sql('SELECT * FROM Profile',conn)
Ave_Input=pd.read_sql('SELECT * FROM Pred_Monthly_Cost',conn).as_matrix()

'''
    Input Reference Data:
        Ave_Input:  numpy matrix
            Predicted Average Daily Consumption(KWh) based on No.room, No. people
        Profile:    pandas DataFrame
            Four Cluster of customer's profile
            Normolazing for Monthly Electricity Consumption
            Sum of Profile should around 1/30(0.03333)
        Def_Load:   Pandas DataFrame
            List of Deferred Load Average Daily Consumption
'''

'''
    Get 24-hour load profile for Household consumption
    Paras:
        N_room:                int
            Number of rooms
        N_day:                int
            Number of people stay in day
        N_night:            int
            Number of people stay in night
        Ls_App:                list
            List of appliances; 1/0:Yes/No
            List Element:[Stove,Dishwasher,Clothes Washer,Dryer,Swimming Pool,HVAC]
        Cust_Monthly_Cost:    int
            Monthly electricity cost($) of customer; default value:0
            may not be given by customer
        Cust_MOnthly_KWh:    int
            Monthly electricity consumption(KWh) of customer; default value:0
            may not be given by customer
            if Cust_Monthly_Cost is given, then Cust_MOnthly_KWh will not be required
    Return:
        Cust_profile:        numpy Vector
            24 hour profile for baseline model
        Deferred_Matrix:    3*97 numpy matrix
            Possible Deferred Loading and its Duration During the day
'''
################# Example Modeling Input####################
#N_day=2;N_night=4;N_room=1;Ls_App=[1,0,1,1,1,0]   

#The Input here shouble be achieved from Website

############################################################
def get_household_load_profile(Consumption,N_room, N_day,N_night,Ls_App,connection_time=[0, 0, 0]):


    #Put three input(number of day/night/room) to a List
    def Input_Ls(N_day=None,N_night=None,Ls_App=[]):                
        return [N_day,N_night,Ls_App]

    # profile Matching based on the Input_List

        '''
        Input Paras:
            Input_List: List
                List that contains all coustomer's input
        
        Return:
            Profile:    Single Column Pandas DataFrame
                A 24 length single column DataFrame
        '''
    def Matching(Input_List):
        if Input_List[0]<=1 and Input_List[1]<=1:
            return Profile['Profile 3']
        if Input_List[0]>1 and Input_List[1]<=3:
            return Profile['Profile 4']
        if Input_List[0]>1 and Input_List[1]>3:
            return Profile['Profile 1']
        if Input_List[0]==0:
            if Input_List[2][5]==0 and Input_List[2][1]==0 and Input_List[1]<=3:
                return Profile['Profile 3']
            else:
                return Profile['Profile 2']
    #Total Comsumption Calculation
  
    Input_List=Input_Ls(N_day,N_night,Ls_App)
    '''
    Week 6 Revision:

        Remove the Consumption input argument
        Adding the Consumption Prediction function given the cost

    '''
    Cust_Profile=copy.copy(Matching(Input_List))

    Cust_Profile=map(lambda x:x*Consumption,Cust_Profile)                         
    #Resulted 24 vector Total consumption
    
    #Adding Swimming Pump Consumption and HVAC Consumption
    if Ls_App[4]==1:                                                              
        Cust_Profile=map(lambda x:x+1.12,Cust_Profile)
    if Ls_App[5]==1:                                                              
        Cust_Profile=map(lambda x:x+0.356,Cust_Profile)
    Cust_Total_Profile=copy.copy(Cust_Profile)

    #Calculating Baseline and Deferred Loading
    '''
        Paras:  
            Def_Load_Index: int
                all 0 elements' Index in the Appliance List
            Cust_Def: Pandas Dataframe
                Deferred Loading Daily Consumption of Customer's Appliances List
    '''
    #Find the index that appliance element==1
    def find_number_in_list(lst, Num):
        return [i for i, x in enumerate(lst) if x==Num]
    Def_Load_Index=find_number_in_list(Ls_App[1:4],1)#Only [1:4]
    #Index Shifting since the List start from 1
    Def_Load_Index = [x+1 for x in Def_Load_Index]                                
    Cust_Def=Def_Load.iloc[Def_Load_Index]

    #Find possible hours' index of the duration in the deferred loading
    def Baseline(lst, num):
        result=[i for i, x in enumerate(lst) if x>=num ]
        #filter off-peak Hour; Assume 15:00-21:00 is Peak Hour
        result=filter(lambda x:x>=15*4 and x<=21*4,result)                       
        return result
    #find the possible deferred load time interval that in the peak profile 
    def Def_Load_Interval(lst,Profile):
        Time_Interval=[]
        index, value = max(enumerate(Profile[60:85]), key=operator.itemgetter(1))
        #Index Shifting
        index+=60                                                                 
        if index in lst:
            Time_Interval.append(index)
            Time_Interval.append(index+1)
            Time_Interval.append(index+2)
            Time_Interval.append(index+3)
        return Time_Interval    
        
    #Generate three vectors for each deferred load and the resulted baseline profile
    '''
        Paras:
            Deferred_Matrix: numpy matrix
                3*25 size matrix of the corresponse deferred consumption for each of the three appliances
            Def_duration: List
                Starting and Ending time of the deferred Load during the peak Hours.
                The Starting and Ending time is the first two hour in the possible duration
        Return:
            Cust_Profile: numpy vector
                Baseline model of the customer
            Deferred_Matrix: numpy matrix
                Time of each deferred load could happen in one day.


    '''

    Deferred_Matrix=np.zeros((3,97))         #Initialize Matrix

    for Def_Item in Def_Load_Index:
        Def_Loading=Cust_Def['Average Daily Consumption(KWh)'][Def_Item]
        Def_Duration=Baseline(Cust_Profile,Def_Loading)
        Def_Duration=Def_Load_Interval(Def_Duration,Cust_Profile)
        if Def_Duration !=None:
            if len(Def_Duration)>1:
                Deferred_Matrix[(Def_Item-1,Def_Duration[0])]=Def_Loading
                Deferred_Matrix[(Def_Item-1,Def_Duration[1])]=Def_Loading
                Deferred_Matrix[(Def_Item-1,Def_Duration[2])]=Def_Loading 
                Deferred_Matrix[(Def_Item-1,Def_Duration[3])]=Def_Loading         #Resulted Deferred Loading Plot
        Cust_Profile-=Deferred_Matrix[Def_Item-1]                                 #Index Shifting
    
    for i in range(3):
        t = connection_time[i]
        if t > 0:
            Deferred_Matrix[i,:] = np.pad(Deferred_Matrix[i,:-t], (t,0), 'constant')

    return Cust_Total_Profile, Cust_Profile, Deferred_Matrix
#    return {
#        'Cust_Total_Profile':Cust_Total_Profile.tolist(),
#        'Cust_Profile':Cust_Profile.tolist(),
#        'Deferred_Matrix':Deferred_Matrix.tolist()
#        }
# Dishwasher, Clothes Washed, and Dryer
