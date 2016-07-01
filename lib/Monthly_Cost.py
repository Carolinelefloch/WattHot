import pandas as pd
import numpy as np
import copy
import sqlite3
'''
	Input Paras:
		Daily Loading: numpy array
			Energy Daily Electricity Loading Profile(KWh) with 15mins time interval of the Household 

	Returns
		TOUA_Cost:	2 elements list
			Estimated TOU-A plan monthly cost($) for summer/winter
		TOUB_Cost:	2 elements list
			Estimated TOU-B plan monthly cost($) for summer/winter
		EV_Cost:	2 elements list
			Estimated EV plan monthly cost($) for summer/winter
		E1:		Int
			Estimated E1 plan monthly cost($) 


'''
#######Peak Hours for each plan##############
TOUA_peak=[15,16,17,18,19,20]
TOUB_peak=[16,16,17,18,19,21]
EV_Peak_wd=[14,15,16,17,18,19,20,21]
EV_Peak_we=[15,16,17,18,19]
EV_Partial_Peak_wd=[7,8,9,10,11,12,13,21,22,23]
#############################################

conn=sqlite3.connect('Household_15mins.db')
cur = conn.cursor()
Tariff_TOU=pd.read_sql('SELECT * FROM Tariff_TOU',conn)
Tariff_EV=pd.read_sql('SELECT * FROM Tariff_EV',conn)


def Monthly_Cost(Daily_Loading):
	E1=0;TOUA_Cost=[0,0];TOUB_Cost=[0,0];EV_Cost=[0,0];
	TOUA_wd=[0,0];TOUA_we=[0,0];TOUB_wd=[0,0];TOUB_we=[0,0];EV_wd=[0,0];EV_we=[0,0]
	#Calculate TOU-A,TOU-B Tariff Cost
	Total_Daily_Com=sum(Daily_Loading)/float(4)			#Summation of daily consumption based on the 15mins loading profiles
#Weekday Daily Cost for all three plans	
	for i in range(24):

		#Calculat TOU_A summer/winter cost
		if i not in TOUA_peak:
			if Total_Daily_Com>int(Tariff_TOU[Tariff_TOU['Paras']=='Allowance']['TOUA_summer']):
				Cost_summer=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak']['TOUA_summer'])
				Cost_winter=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak']['TOUA_winter'])
			else:
				Cost_summer=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak Baseline']['TOUA_summer'])
				Cost_winter=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak Baseline']['TOUA_winter'])
		else:
			if Total_Daily_Com>int(Tariff_TOU[Tariff_TOU['Paras']=='Allowance']['TOUA_summer']):
				Cost_summer=float(Tariff_TOU[Tariff_TOU['Paras']=='Peak']['TOUA_summer'])
				Cost_winter=float(Tariff_TOU[Tariff_TOU['Paras']=='Peak']['TOUA_winter'])
			else:
				Cost_summer=float(Tariff_TOU[Tariff_TOU['Paras']=='Peak Baseline']['TOUA_summer'])
				Cost_winter=float(Tariff_TOU[Tariff_TOU['Paras']=='Peak Baseline']['TOUA_winter'])

		TOUA_wd[0]+=Daily_Loading[4*i]*Cost_summer
		TOUA_wd[1]+=Daily_Loading[4*i]*Cost_winter
		#Calculate TOU_B summer/winter cost
		if i not in TOUB_peak:
			Cost_summer=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak']['TOUB_summer'])
			Cost_winter=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak']['TOUB_winter'])

		else:
			Cost_summer=float(Tariff_TOU[Tariff_TOU['Paras']=='Peak']['TOUB_summer'])
			Cost_winter=float(Tariff_TOU[Tariff_TOU['Paras']=='Peak']['TOUB_winter'])
		TOUB_wd[0]+=Daily_Loading[4*i]*Cost_summer
		TOUB_wd[1]+=Daily_Loading[4*i]*Cost_winter
		#Calculate EV summer/winter cost
		if i in EV_Peak_wd:
			Cost_summer=float(Tariff_EV[Tariff_EV['Paras']=='Peak']['EV_summer'])
			Cost_winter=float(Tariff_EV[Tariff_EV['Paras']=='Peak']['EV_winter'])
		elif i in EV_Partial_Peak_wd:
			Cost_summer=float(Tariff_EV[Tariff_EV['Paras']=='Partial_Peak']['EV_summer'])
			Cost_winter=float(Tariff_EV[Tariff_EV['Paras']=='Partial_Peak']['EV_winter'])
		else:
			Cost_summer=float(Tariff_EV[Tariff_EV['Paras']=='Off_Peak']['EV_summer'])
			Cost_winter=float(Tariff_EV[Tariff_EV['Paras']=='Off_Peak']['EV_winter'])
		EV_wd[0]+=Daily_Loading[4*i]*Cost_summer
		EV_wd[1]+=Daily_Loading[4*i]*Cost_winter
#Weekend Daily Cost for all three plans
	#TOU-A summer/winter daily cost
	if Total_Daily_Com>int(Tariff_TOU[Tariff_TOU['Paras']=='Allowance']['TOUA_summer']):
		Cost_summer=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak']['TOUA_summer'])
		Cost_winter=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak']['TOUA_winter'])
	else:
		Cost_summer=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak Baseline']['TOUA_summer'])
		Cost_winter=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak Baseline']['TOUA_winter'])
	for i in range(24):
		TOUA_we[0]+=Daily_Loading[4*i]*Cost_summer
		TOUA_we[1]+=Daily_Loading[4*i]*Cost_winter
	#TOU-B summer/winter daily cost
	Cost_summer=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak']['TOUB_summer'])
	Cost_winter=float(Tariff_TOU[Tariff_TOU['Paras']=='Off Peak']['TOUB_winter'])
	for i in range(24):
		TOUB_we[0]+=Daily_Loading[4*i]*Cost_summer
		TOUB_we[1]+=Daily_Loading[4*i]*Cost_winter
	#EV summer/winter daily cost
	for i in range(24):
		if i in EV_Peak_we:
			Cost_summer=float(Tariff_EV[Tariff_EV['Paras']=='Peak']['EV_summer'])
			Cost_winter=float(Tariff_EV[Tariff_EV['Paras']=='Peak']['EV_winter'])
		else:
			Cost_summer=float(Tariff_EV[Tariff_EV['Paras']=='Off_Peak']['EV_summer'])
			Cost_winter=float(Tariff_EV[Tariff_EV['Paras']=='Off_Peak']['EV_winter'])
		EV_we[0]+=Daily_Loading[4*i]*Cost_summer
		EV_we[1]+=Daily_Loading[4*i]*Cost_winter
	#Calculate the E1 Plan
	E1_allowance=10										#Assume the allowance is 10	
	if Total_Daily_Com<E1_allowance:
		E1+=Total_Daily_Com*0.18212
	elif Total_Daily_Com>E1_allowance and Total_Daily_Com<20:
		E1+=(Total_Daily_Com-10)*0.2409+0.18212*10
	else:
		E1+=0.18212*10+0.2409*10+(Total_Daily_Com-20)*0.4
	E1*=30											#Convert Daily Cost Estimation to Monthly Cost Estimation
	#Calculate Monthly Results based on the Daily Results: 22Weekday,8Weekend day eavh month

	TOUA_Cost[0]=22*TOUA_wd[0]+8*TOUA_we[0]
	TOUA_Cost[1]=22*TOUA_wd[1]+8*TOUA_we[1]
	TOUB_Cost[0]=22*TOUB_wd[0]+8*TOUB_we[0]
	TOUB_Cost[1]=22*TOUB_wd[1]+8*TOUB_we[1]
	EV_Cost[0]=22*EV_wd[0]+8*EV_we[0]
	EV_Cost[1]=22*EV_wd[1]+8*EV_we[1]

	return TOUA_Cost,TOUB_Cost,EV_Cost,E1
