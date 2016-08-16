# -*- coding: utf-8 -*-
'''
Created on Aug 3 2016
@author: David


Design the Cost class to integrate the consumption prediction and cost calculation function.

Convert the Input Cost to the consumption to the Cost

Assumption:
	1. For Tier and TOU and Tier Type(TOU 1,1,0 type) Rate Calculation. Tier Arrangement based on the customer's cost
        	No.Tier 1=30 cost <70
			No.Tier 1=20;No.Tier 2=10 if cost>70 and cost<120
			No.Tier 1=15;No.Tier 2=15 if cost>120
	2. Monthly Allowance retrieve directly from the Tariff book database(Not related to the Zip Code)
	3.Assuming the season of the customer cost input is average of Summer Cost and Winter Cost to Estimate the Monthly electricity consumption

'''

import pandas as pd
import numpy as np
import json
import copy
import sqlite3

class Cost:
	def __init__(self, path1,path2):
		# Connect the EV and Household model databese
		conn1 = sqlite3.connect(path1)
		conn2 = sqlite3.connect(path2)
		self.c1 = conn1.cursor()
		self.c2 = conn2.cursor()
		self.Def_Load=pd.read_sql('SELECT * FROM Deferred_Load',conn2)
		self.Profile=pd.read_sql('SELECT * FROM Profile',conn2)
		self.Ave_Input=pd.read_sql('SELECT * FROM Pred_Monthly_Cost',conn2).as_matrix()
	
	Week_day=[1,1,1,1,1,0,0]                                                        #1 represents weekday,0 represents weekend
	Week_day=Week_day+Week_day+Week_day+Week_day+[1,1]
	'''
	Input Paras
		1. Utility Name 																str
			Utility Name of the input utility			
		2. Rate Name 																	str
			Rate Name of the Customer's Cost
		3. EV Load 																		list
			EV Load calculation results from the EV function
		4. Cost for the input rate plan
		5.N_room:                														int
			Number of rooms
		6.N_day:                														int
			Number of people stay in day
		7.N_night:            															int
			Number of people stay in night
		8.Ls_App:                														list
			List of appliances; 														1/0:Yes/No
			List Element:[Stove,Dishwasher,Clothes Washer,Dryer,Swimming Pool,HVAC]
		9.Charging_Outside:																int
			EV charging outside:1
			EV doesn't Charging outside:0
		10.No.EV=5																		int
			Number of day the EV used
		11.No.Def=2																		int
			Number of day the deferred load used



	Function:
				Get_EV_Def_Cost:			Return cost of EV load, water pump load, and HVAC load.

				Get_Monthly_Consumption:	Convet the Cost to Monthly Consumption	
				Return the monthly electricity consumption based on the input monthly cost

				Get_Cost:					Convert the Consumption to Cost
				Return the overall cost,ev cost,deferred cost,household cost of all rate given the name of the utility
	'''
	def Get_Allowance(self,Input_Name):
		command=(
					'''
					SELECT Allowance from Rate_Information
					INNER JOIN Utility_Rate_Name
					ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? AND Rate_Name=?
					'''
					)
		Allowance=self.c1.execute(command,Input_Name).fetchall()[0]
		Allowance=Allowance[0]
				
		if Allowance=='Na':
			Allowance=[10000000]
			N_Tier=1
		else:
			Allowance=json.loads(Allowance)
			N_Tier=len(Allowance)+1
		return Allowance,N_Tier

	def Get_Tier_Rate(self,Input_Name):
		command=(
					'''
					SELECT Tier_Rate	 from Rate_Information
					INNER JOIN Utility_Rate_Name
					ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? AND Rate_Name=?	
					'''
						)
		Tier_Tariff=self.c1.execute(command,Input_Name).fetchall()[0][0]		
		Tier_Tariff=json.loads(Tier_Tariff)
		return Tier_Tariff
	def Get_Hourly_Rate(self,Input):
		command=(
					'''
					SELECT * from Hourly_Rate
					INNER JOIN Utility_Rate_Name
					ON Hourly_Rate.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? AND Rate_Name=? And Tier=? and Week_day=? and Season=?
					'''
				)
		Rate_Vector=self.c1.execute(command,Input).fetchall()
		try:
			Rate_Vector=Rate_Vector[0][5:102]
		except TypeError:
			print 'Type Error for Query Results'
		return Rate_Vector

	def Get_EV_Def_Cost(self,Charging_Outside,Utility_Name,Rate_Name,EV_Load,Ls_App,No_EV=5,Cost=0):
		###################################################################
		#######If Charging the EV outside the home,half the EV Load########
		###################################################################
		Input_Name=(Utility_Name,Rate_Name)
		if Charging_Outside==1:														
			EV_Load=map(lambda x:x/float(2),EV_Load)
		if Ls_App[4]==0 and Ls_App[5]==0 and np.unique(EV_Load).tolist()==[0]:
			return 0
		Adj_EV_Load=map(lambda x:x/float(5)*No_EV,EV_Load)							
		#Calibrate the EV_Load based on No.of day EV used
		if Ls_App[4]==1:
			Adj_EV_Load=map(lambda x:x+1.12,Adj_EV_Load)
		if Ls_App[5]==1:
			Adj_EV_Load=map(lambda x:x+0.356,Adj_EV_Load)

		command=(
					'''
					SELECT TIER_Type from Rate_Information
					INNER JOIN Utility_Rate_Name
					ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? AND Rate_Name=?
					'''
				)

		Tier_Type=self.c1.execute(command,Input_Name).fetchall()[0]
		Tier_Type=Tier_Type[0]
		
		Allowance,N_Tier=self.Get_Allowance(Input_Name)
		Daily_Cost=Cost/float(30)

		def Get_Tier_Array(Daily_Cost,Allowance_Cost):
			Acc_Cost=0;Tier=[]

			for day in range(30):
				Acc_Cost+=Daily_Cost
				
				for i in range(len(Allowance_Cost)):
					if Acc_Cost<Allowance_Cost[i]:
						Tier.append(i)
						break
					if Acc_Cost>Allowance_Cost[-1]:
						Tier.append(len(Allowance_Cost))
			return Tier

		if Tier_Type==0:
			Tier=[];[Tier.append(0) for i in range(30)]							
		elif Tier_Type==1 and N_Tier==1:
			Tier=[];[Tier.append(0) for i in range(30)]							
		else:
			Tier_Tariff=self.Get_Tier_Rate(Input_Name)
			Allowance_Cost=[];[Allowance_Cost.append(Allowance[i]*Tier_Tariff[i]) for i in range(len(Allowance))]
			Tier=Get_Tier_Array(Daily_Cost,Allowance_Cost)

		EV_Cost_Summer=0;EV_Cost_Winter=0;Season=['summer','winter']
		for S in Season:
			for index in range(30):
				T=Tier[index];W=self.Week_day[index]
				Input=(Utility_Name,Rate_Name,T,W,S)
				
				Rate_Vector=self.Get_Hourly_Rate(Input)
				if S=='summer':
					EV_Cost_Summer+=sum(np.multiply(Adj_EV_Load,Rate_Vector))/float(4)
				else:
					EV_Cost_Winter+=sum(np.multiply(Adj_EV_Load,Rate_Vector))/float(4)
		EV_Cost=(EV_Cost_Winter)#+EV_Cost_Summer)/2
		if EV_Cost<Cost:
			return EV_Cost
		else: 
			return Cost

	def Get_Consumption_Without_Cost(self,N_room, N_day, N_night):
		N_people=N_day+N_night
		if N_people==0:
			N_people+=1
		N_people-=1;N_room-=1   #Index Shifting                                        
		return self.Ave_Input[(N_people,N_room)]

	def Matching(self,Input_List):
		if Input_List[0]<=1 and Input_List[1]<=1:
			return self.Profile['Profile 3']
		if Input_List[0]>1 and Input_List[1]<=3:
			return self.Profile['Profile 4']
		if Input_List[0]>1 and Input_List[1]>3:
			return self.Profile['Profile 1']
		if Input_List[0]==0:
			if Input_List[2][5]==0 and Input_List[2][1]==0 and Input_List[1]<=3:
				return self.Profile['Profile 3']
			else:
				return self.Profile['Profile 2']
	
	def Get_Monthly_Consumption(self,Charging_Outside,Utility_Name,Rate_Name,N_room, N_day,N_night,Ls_App,EV_Load,Cost,No_EV=5):
	#Put three input(number of day/night/room) to a List
		def Input_Ls(N_day=None,N_night=None,Ls_App=[]):                
			return [N_day,N_night,Ls_App]

		Input_List=Input_Ls(N_day,N_night,Ls_App)

		if Cost==0:
			Monthly_Consumption=self.Get_Consumption_Without_Cost(N_room,N_day,N_night)
			return Monthly_Consumption
		else:
			Def_EV_Cost=self.Get_EV_Def_Cost(Charging_Outside,Utility_Name,Rate_Name,EV_Load,Ls_App,No_EV,Cost)
			if Def_EV_Cost>Cost:
				return 'Wrong Number of Input Cost'
			else:
				Cost-=Def_EV_Cost

			Input_Name=(Utility_Name,Rate_Name)

			###Deduction of monthly fixed rate
			command=(
					'''
					SELECT Fixed_Fee from Rate_Information
					INNER JOIN Utility_Rate_Name
					ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? AND Rate_Name=?
					'''
					)
			Monthly_Fixed_Fee=self.c1.execute(command,Input_Name).fetchall()[0][0]
			Cost=max(0,Cost-Monthly_Fixed_Fee)

			###Predicting thr consumption based on the rate type
			command=(
					'''
					SELECT Rate_Type from Rate_Information
					INNER JOIN Utility_Rate_Name
					ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? AND Rate_Name=?
					
					'''
					)
			Cust_Rate_type=self.c1.execute(command,Input_Name).fetchall()[0]
			Cust_Rate_type=Cust_Rate_type[0]
			#############################################
			#####Calculating the TIER type consumption###
			#############################################
			if Cust_Rate_type=='TIER':

				Allowance,N_Tier=self.Get_Allowance(Input_Name)

				Tier_Tariff=self.Get_Tier_Rate(Input_Name)
				
				'''
				Initial the results

				Converting the Tier Plan cost to the Tier Plan Daily Consumption

				Recursively calculating the approximate monthly consumption
				'''
				Tier_Result=0;T=0
				def Get_Comsuption_Tier(Cost,T,Tier_Result):
					Tier_Consumption=Cost/Tier_Tariff[T]
					if T<(N_Tier-1):
						if (Tier_Result+Tier_Consumption)<=Allowance[T]:
							Tier_Result+=Tier_Consumption
							return Tier_Result
						else:
							if T==0:
								Cost-=Allowance[T]*Tier_Tariff[T]
							else:
								Cost-=(Allowance[T]-Allowance[T-1])*Tier_Tariff[T]
							Tier_Result=Allowance[T];T+=1
							return Get_Comsuption_Tier(Cost,T,Tier_Result)
					else:
						Tier_Consumption=Cost/Tier_Tariff[-1]
						Tier_Result+=Tier_Consumption
						return Tier_Result

				Monthly_Consumption=Get_Comsuption_Tier(Cost,T,Tier_Result)
				return Monthly_Consumption
			##############################################
			#####Calculating the TOU type consumption#####
			##############################################
			elif Cust_Rate_type=='TOU':

				command=(
					'''
					SELECT TOU_Type,TIER_Type,DEMAND_Type from Rate_Information
					INNER JOIN Utility_Rate_Name
					ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? AND Rate_Name=?
					
					'''
					)
				TOU_Type=self.c1.execute(command,Input_Name).fetchall()[0]     					
				#TOU_Type:Three element Tuple (1,0,0)
				
				####TOU type and TOU Demand Type, No Tier Type Rate

				if TOU_Type==(1,0,0) or TOU_Type==(1,0,1):
					command=(
					'''
					SELECT Summer_Demand_Rate	 from Rate_Information
					INNER JOIN Utility_Rate_Name
					ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? AND Rate_Name=?
					
					'''
					)
					Demand_Rate=self.c1.execute(command,Input_Name).fetchall()[0][0]
					Cust_Profile=copy.copy(self.Matching(Input_List))
					#Cust_Profile=map(lambda x:x/sum(Cust_Profile)*4,Cust_Profile)
					
					Cust_Demand=float(max(Cust_Profile))
					Cust_Demand/=float(30)   ##Convert Monthly consumption to Daily Consumption
					
					Demand_Cost=Cust_Demand*Demand_Rate

					Tier=[];[Tier.append(0) for i in range(30)];
					TOU_Cost_Summer=0;TOU_Cost_Winter=0;Season=['summer','winter']
					for S in Season:		
						for index in range(30):
							T=Tier[index];W=self.Week_day[index]
							Input=(Utility_Name,Rate_Name,T,W,S)
					
							Rate_Vector=self.Get_Hourly_Rate(Input)
							if S=='summer':
								TOU_Cost_Summer+=sum(np.multiply(Cust_Profile,Rate_Vector))/float(4)
							elif S=='winter':
								TOU_Cost_Winter+=sum(np.multiply(Cust_Profile,Rate_Vector))/float(4)
					'''
					Aug 15 2016 Revision:

					Assume the Input Cost is the winter cost insterd of average cost of summer and winter

					'''
					TOU_Cost=(TOU_Cost_Winter)#+TOU_Cost_Summer)/2
					return round(Cost/(TOU_Cost+Demand_Cost),2)
				elif TOU_Type==(1,1,0) or TOU_Type==(1,1,1):
					command=(
					'''
					SELECT Summer_Demand_Rate	 from Rate_Information
					INNER JOIN Utility_Rate_Name
					ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? AND Rate_Name=?
					
					'''
					)
					Demand_Rate=self.c1.execute(command,Input_Name).fetchall()[0][0]

					Cust_Profile=copy.copy(self.Matching(Input_List))
					Cust_Demand=float(max(Cust_Profile))
					Cust_Demand/=float(30)   														
					#Convert Monthly consumption to Daily Consumption
					Demand_Cost=Cust_Demand*Demand_Rate
									
					if Cost<=70:
						Tier=[];[Tier.append(0) for i in range(30)];TOU_Cost=0						
					elif Cost>70 and Cost<120:																			
						Tier=[];[Tier.append(0) for i in range(20)];[Tier.append(1) for i in range(10)];
					else:																			
						Tier=[];[Tier.append(0) for i in range(15)];[Tier.append(1) for i in range(15)];
					
					#Tier=np.zeros(30).tolist()
					TOU_Cost_Summer=0;TOU_Cost_Winter=0;Season=['summer','winter']
					for S in Season:
						for index in range(30):
							T=Tier[index];W=self.Week_day[index]
							Input=(Utility_Name,Rate_Name,T,W,S)
							
							Rate_Vector=self.Get_Hourly_Rate(Input)
							if S=='summer':
								TOU_Cost_Summer+=sum(np.multiply(Cust_Profile,Rate_Vector))/float(4)
							else:
								TOU_Cost_Winter+=sum(np.multiply(Cust_Profile,Rate_Vector))/float(4)
					
					TOU_Cost=(TOU_Cost_Winter)#+TOU_Cost_Summer)/2
					return round(Cost/(TOU_Cost+Demand_Cost),2)
				
	def Get_Cost(self,Utility_Name,Household_Total,Household, Def_Load,EV_Load,Charging_Outside,No_EV=5,No_Def=2):
		if Charging_Outside==1:
			EV_Load=map(lambda x:x/float(2),EV_Load)
		DT_house=sum(Household_Total)/4
		DT_EV=sum(EV_Load)/4
		DT_EV=DT_EV/float(5)*float(No_EV)                                                	
		#Deduction of number of day EV used
		EV_Load_Adj=[i/float(5)*float(No_EV) for i in EV_Load]
		Def_Load_Adj=[]
		for i in range(3):                                                                	
			#Deduction of number of day Deferred Load used
			Def_Load_Adj.append([j/float(7)*float(No_Def) for j in Def_Load[i]])

		'''
		Calculate the Tier for each of the day.
		Assume four weeks and two weekdays every month

		return: 30 list vector
		Tier for each day of the month
		'''
		command=(
					'''
					SELECT Allowance	 from Rate_Information
					INNER JOIN Utility_Rate_Name
					ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? 
					
					'''
				)
		Monthly_Allowance=self.c1.execute(command,(Utility_Name,)).fetchall()
		No_Rate=len(Monthly_Allowance)

		def Get_Tier_Array(DT_house,DT_EV,Allowance):
			Cost=0;Tier=[]

			if Allowance[0]=='Na':
				[Tier.append(0) for i in range(30)]
				return Tier
			Allowance=json.loads(Allowance[0])
			for day in range(30):
				if self.Week_day[day]==1:
					Cost=Cost+DT_house+DT_EV
				else:
					Cost=Cost+DT_house
				for i in range(len(Allowance)):
					if Cost<Allowance[i]:
						Tier.append(i)
						break
					if Cost>Allowance[-1]:
						Tier.append(len(Allowance))
			return Tier
		
		#######Initial Output Vector#########
		Household_Cost_Summer=np.zeros(No_Rate)                                                
		Household_Cost_Winter=np.zeros(No_Rate)
		Deferred_Cost_Summer=np.zeros(No_Rate)
		Deferred_Cost_Winter=np.zeros(No_Rate)
		EV_Cost_Summer=np.zeros(No_Rate)
		EV_Cost_Winter=np.zeros(No_Rate)
		Season=['summer','winter']
		command=(
					'''
					SELECT Rate_Name	 from Utility_Rate_Name
					WHERE Utility_Name=? 
					
					'''
				)
		Rate_Names=self.c1.execute(command,(Utility_Name,)).fetchall()

		for P in range(No_Rate):
			Rate_Name=Rate_Names[P][0]
			Cust_Tier=Get_Tier_Array(DT_house,DT_EV,Monthly_Allowance[P])
			#if P is 0:
			
			for S in Season:
				Max_Demand=0
				for day in range(30):
					T=Cust_Tier[day];D=self.Week_day[day]
					Input=(Utility_Name,Rate_Name,T,D,S)
					
					R=self.Get_Hourly_Rate(Input)
					if max(R)>Max_Demand:
						Max_Demand=max(R)
					if S=='summer':
						Household_Cost_Summer[P]+=round(sum(np.multiply(R,Household))/4,2)    
						#Divide four to convert 15mins time interval to one hour time interval
						Deferred_Cost_Summer[P]+=round(sum(sum(np.multiply(R,Def_Load_Adj)))/4,2)
						#Only has EV Load During WeekDay
						if D==1:                                                        
							EV_Cost_Summer[P]+=round(sum(np.multiply(R,EV_Load_Adj))/4,2)
					else:
						Household_Cost_Winter[P]+=round(sum(np.multiply(R,Household))/4,2)
						Deferred_Cost_Winter[P]+=round(sum(sum(np.multiply(R,Def_Load_Adj)))/4,2)
						if D==1:
							EV_Cost_Winter[P]+=round(sum(np.multiply(R,EV_Load_Adj))/4,2)
				Input=(Utility_Name,Rate_Name)
				command=(
						'''
						SELECT Fixed_Fee from Rate_Information
						INNER JOIN Utility_Rate_Name
						ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
						WHERE Utility_Name=? AND Rate_Name=?	
						'''
						)
				Monthly_Fixed_Fee=self.c1.execute(command,Input).fetchall()[0][0]
				command=(
						'''
						SELECT Summer_Demand_Rate, Winter_Demand_Rate from Rate_Information
						INNER JOIN Utility_Rate_Name
						ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
						WHERE Utility_Name=? AND Rate_Name=?	
						'''
						)
				Demand_Fee=self.c1.execute(command,Input).fetchall()[0]
				
				if S=='summer':
					Household_Cost_Summer[P]+=Monthly_Fixed_Fee
					Household_Cost_Summer[P]+=Demand_Fee[0]*Max_Demand
				else:
					Household_Cost_Winter[P]+=Monthly_Fixed_Fee
					Household_Cost_Summer[P]+=Demand_Fee[1]*Max_Demand
		
		Total_Cost_Summer=[x+y+z for x,y,z in zip(Household_Cost_Summer,Deferred_Cost_Summer,EV_Cost_Summer)]
		Total_Cost_Summer=[round(i,2) for i in Total_Cost_Summer]
		Total_Cost_Winter=[x+y+z for x,y,z in zip(Household_Cost_Winter,Deferred_Cost_Winter,EV_Cost_Winter)]
		Total_Cost_Winter=[round(i,2) for i in Total_Cost_Winter]

		Plan_Cost_Summer=[Household_Cost_Summer,Deferred_Cost_Summer,EV_Cost_Summer,Total_Cost_Summer]
		Plan_Cost_Winter=[Household_Cost_Winter,Deferred_Cost_Winter,EV_Cost_Winter,Total_Cost_Winter]

		Plan_Cost={'Plan_Name':Rate_Names,'House_S':Household_Cost_Summer.tolist(),'Def_S':Deferred_Cost_Summer.tolist(),'EV_S':EV_Cost_Summer.tolist(),'Total_S':Total_Cost_Summer,
        'House_W':Household_Cost_Winter.tolist(),'Def_W':Deferred_Cost_Winter.tolist(),'EV_W':EV_Cost_Winter.tolist(),'Total_W':Total_Cost_Winter}
		return Plan_Cost










