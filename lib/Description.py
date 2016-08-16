'''
Created on Aug 16 2016
@author: David

Description module:		Return the Hash of the rate name and its description for the given utility name


'''

import sqlite3

class Description:
	def __init__(self, path1):
		# Connect the EV and Household model databese
		conn1 = sqlite3.connect(path1)
		self.c1 = conn1.cursor()

	def Get_Descrip(self,utilityName):
		command=(
					'''
					SELECT Description from Rate_Description
					INNER JOIN Utility_Rate_Name
					ON Rate_Description.Rate_id == Utility_Rate_Name.Rate_id
					WHERE Utility_Name=? 
					'''
					)
		Description=self.c1.execute(command,(utilityName,)).fetchall()
		command=(
					'''
					SELECT Rate_Name	 from Utility_Rate_Name
					WHERE Utility_Name=? 
					
					'''
				)
		Rate_Names=self.c1.execute(command,(utilityName,)).fetchall()
		result={}
		for index in range(len(Description)):
			result[Rate_Names[index][0]]=Description[index]
		return result
		
		