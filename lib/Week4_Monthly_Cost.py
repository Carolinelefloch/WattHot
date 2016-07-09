import pandas as pd
import numpy as np
import copy
import sqlite3

#####Database Reading#####
conn=sqlite3.connect('db/Tariff_Rate.db')
cur = conn.cursor()
rate=pd.read_sql('SELECT * FROM PG_and_E',conn)
##########################

'''
    Function:            get_cost
        Monthly Cost Calculation for EV load,deferred load,and household load

    Input Paras:

        Household_Total:97 size list vector
            15mins time interval 24hours hosehold total loading profile
        Household:        97 size list vector
            15mins time interval 24hours household baseline loading profile
        Def_Load:        3*97 size list matrix
            15mins time interval 24hours deferred load loading profile
        EV_Load:        97 size list vector
            15mins time interval 24hours EV charging loading profile
        Monthly_allowance:    int
            Baseline allowance for tier rate plan
        No_EV:            int
            Number of day EV is used/week
            Default Value:5
        No_Def:            int
            Number of day Deferred loads is used/week
            Dafault Value:2

    Output:
        Plan_Cost_Summer/Winter: 4*4 List for each
            Includes Following Vectors:

            Household_Cost:    4 size vector
                Household baseline loading cost for E1,ETOU-A,ETOU-B,EV-TOU plans
            Deferred_Cost:    4 size vector
                Deferred loading cost for E1,ETOU-A,ETOU-B,EV-TOU plans
                Deferred loading includes washer machine, dryer, dishermachine
            EV_Cost:        4 size vector
                EV loading cost for E1,ETOU-A,ETOU-B,EV-TOU plans
            Total_Cost:        4 size vector
                Total cost for E1,ETOU-A,ETOU-B,EV-TOU plans

'''

def get_cost(Household_Total,Household,Def_Load,Monthly_allowance,EV_Load,No_EV=5,No_Def=2):
    #Calculate Tier for each day of the month
    #Total_load=[x1+x2+x3+x4+x5+x6 for x1,x2,x3,x4,x5,x6]#

    Week_day=[1,1,1,1,1,0,0]                                                        #1 represents weekday,0 represents weekend
    Week_day=Week_day+Week_day+Week_day+Week_day+[1,1]                                #Weekday and Weekend for the month
    DT_house=sum(Household_Total)/4
    DT_EV=sum(EV_Load)/4
    DT_EV=DT_EV/float(5)*float(No_EV)                                                #Deduction of number of day EV used
    EV_Load_Adj=[i/float(5)*float(No_EV) for i in EV_Load]
    Def_Load_Adj=[]
    for i in range(3):                                                                #Deduction of number of day Deferred Load used
        Def_Load_Adj.append([j/float(7)*float(No_Def) for j in Def_Load[i]])

    '''
    Calculate the Tier for each of the day.
    Assume four weeks and two weekdays every month

    return: 30 list vector
        Tier for each day of the month
    '''
                        
    def Tier_arrange(DT_house,DT_EV,Monthly_allowance):
        Cost=0;Tier=[]
        for day in range(30):
            if Week_day[day]==1:
                Cost=Cost+DT_house+DT_EV
            else:
                Cost=Cost+DT_house
            if Cost<=Monthly_allowance:
                Tier.append(0)
            elif Cost>Monthly_allowance and Cost<(2*Monthly_allowance):
                Tier.append(1)
            else:
                Tier.append(2)

        return Tier
    #####dataframe filter shortcut########
    def Filter(df, key, value):
        return df[df[key] == value]
    pd.DataFrame.Filter = Filter
    ######################################

    Cust_Tier=Tier_arrange(DT_house,DT_EV,Monthly_allowance)
    #######Initial Output Vector#########
    Household_Cost_Summer=np.zeros(4)                                                #[ETOU-A,ETOU-B,EV-TOU,E1] Cost
    Household_Cost_Winter=np.zeros(4)
    Deferred_Cost_Summer=np.zeros(4)
    Deferred_Cost_Winter=np.zeros(4)
    EV_Cost_Summer=np.zeros(4)
    EV_Cost_Winter=np.zeros(4)
    #####################################

    #Calculate Four plan Cost
    rate_column=range(6,103)
    Season=['summer','winter']
    Plan=['ETOU-A','ETOU-B','EV','E1']
    #Query Tier and Weekday to get coresponding rate
    for P in range(len(Plan)):
        for S in Season:
            for day in range(30):
                T=Cust_Tier[day];D=Week_day[day]                                    #T:Tier for the day; D: Weekday/end for that day
                if Plan[P]=='ETOU-A':
                    if T==2:            
                        T=1                                                            #ETOU-A plan don't have Tier 2
                    R=rate.Filter('Rate_name',Plan[P]).Filter('Tier',T).Filter('Week_day',D).Filter('Season',S)[rate_column]
                if Plan[P]=='ETOU-B' or Plan[P]=='EV':
                    R=rate.Filter('Rate_name',Plan[P]).Filter('Week_day',D).Filter('Season',S)[rate_column]
                if Plan[P]=='E1':
                    R=rate.Filter('Rate_name',Plan[P]).Filter('Tier',T)[rate_column]
                R=map(list,R.values)[0]
                if S=='summer':
                    Household_Cost_Summer[P]+=round(sum(np.multiply(R,Household))/4,2)    #Divide four to convert 15mins time interval to one hour time interval
                    Deferred_Cost_Summer[P]+=round(sum(sum(np.multiply(R,Def_Load_Adj)))/4,2)
                    if D==1:                                                        #Only has EV Load During WeekDay
                        EV_Cost_Summer[P]+=round(sum(np.multiply(R,EV_Load_Adj))/4,2)
                else:
                    Household_Cost_Winter[P]+=round(sum(np.multiply(R,Household))/4,2)
                    Deferred_Cost_Winter[P]+=round(sum(sum(np.multiply(R,Def_Load_Adj)))/4,2)
                    if D==1:
                        EV_Cost_Winter[P]+=round(sum(np.multiply(R,EV_Load_Adj))/4,2)
    Total_Cost_Summer=[x+y+z for x,y,z in zip(Household_Cost_Summer,Deferred_Cost_Summer,EV_Cost_Summer)]
    Total_Cost_Summer=[round(i,2) for i in Total_Cost_Summer]
    Total_Cost_Winter=[x+y+z for x,y,z in zip(Household_Cost_Winter,Deferred_Cost_Winter,EV_Cost_Winter)]
    Total_Cost_Winter=[round(i,2) for i in Total_Cost_Winter]
#    Plan_Cost_Summer=[Household_Cost_Summer,Deferred_Cost_Summer,EV_Cost_Summer,Total_Cost_Summer]
#    Plan_Cost_Winter=[Household_Cost_Winter,Deferred_Cost_Winter,EV_Cost_Winter,Total_Cost_Winter]
    Plan_Cost={'House_S':Household_Cost_Summer.tolist(),'Def_S':Deferred_Cost_Summer.tolist(),'EV_S':EV_Cost_Summer.tolist(),'Total_S':Total_Cost_Summer,
         'House_W':Household_Cost_Winter.tolist(),'Def_W':Deferred_Cost_Winter.tolist(),'EV_W':EV_Cost_Winter.tolist(),'Total_W':Total_Cost_Winter}

    return Plan_Cost