'''
Created on Aug 16 2016
@author: David

Description module:     Return the Hash of the rate name and its description for the given utility name


'''

import sqlite3
import json

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
        print Description[0]
        #for i in range(len(Description)):
            #Description[i]=str(Description[i])

        command=(
                    '''
                    SELECT Eligibility from Rate_Description
                    INNER JOIN Utility_Rate_Name
                    ON Rate_Description.Rate_id == Utility_Rate_Name.Rate_id
                    WHERE Utility_Name=? 
                    '''
                    )
        elig=self.c1.execute(command,(utilityName,)).fetchall()

        #for i in range(len(elig)):
            #elig[i]=str(elig[i])

        command=(
                    '''
                    SELECT Rate_Name     from Utility_Rate_Name
                    WHERE Utility_Name=? 
                    
                    '''
                )
        Rate_Names=self.c1.execute(command,(utilityName,)).fetchall()
        for i in range(len(Rate_Names)):
            Rate_Names[i]=str(Rate_Names[i][0])
        
        result={'Rate Name': Rate_Names,'Description':Description,'Eligibility':elig}
        return result

    def Get_ConnTime(self,utilityName):

        command=(
                    '''
                    SELECT Summer_Peak_End from Rate_Information
                    INNER JOIN Utility_Rate_Name
                    ON Rate_Information.Rate_id == Utility_Rate_Name.Rate_id
                    WHERE Utility_Name=? 
                    '''
                    )
        
        connTime=self.c1.execute(command,(utilityName,)).fetchall()
        for index in range(len(connTime)):
            if connTime[index][0] is None:
                connTime[index]='charge when you perfer'
            else:
                connTime[index]=json.loads(connTime[index][0])[0]
        
        command=(
                    '''
                    SELECT Rate_Name     from Utility_Rate_Name
                    WHERE Utility_Name=? 
                    
                    '''
                )
        Rate_Names=self.c1.execute(command,(utilityName,)).fetchall()
        for i in range(len(Rate_Names)):
            Rate_Names[i]=str(Rate_Names[i][0])

        result={'Rate Name': Rate_Names,'conn Time':connTime}
        return result
        
    def Get_imageName(self,utilityName):
        command=(
                    '''
                    SELECT Image_Name from Image
                    INNER JOIN Utility_Rate_Name
                    ON Image.Rate_id == Utility_Rate_Name.Rate_id
                    WHERE Utility_Name=? 
                    '''
                    )
        imageName=self.c1.execute(command,(utilityName,)).fetchall()
        for index in range(len(imageName)):
            imageName[index]=imageName[index][0]

        command=(
                    '''
                    SELECT Rate_Name     from Utility_Rate_Name
                    WHERE Utility_Name=? 
                    
                    '''
                )
        Rate_Names=self.c1.execute(command,(utilityName,)).fetchall()
        for i in range(len(Rate_Names)):
            Rate_Names[i]=str(Rate_Names[i][0])

        result={'Rate Name': Rate_Names,'Image Name':imageName}
        return result
