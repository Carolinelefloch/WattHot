# WattHot
Predict energy consumption and energy costs. Create APIs to be querried by watthot.com
Watthot proposes 3 apis: 1) EV load calculation , 2) Household load calculation , 3) Cost calculation 

<Rest-API>

##  1) EV load calcultation
http://localhost:8000/ev/load/?distance=50&maker=Nissan&model=Leaf&year=2015&charger=2

## 2) Household load calculation
http://localhost:8000/house/load/?N_room=1&N_day=1&N_night=1&Ls_App=1,1,1,1,1,0&Monthly_Cost=0&Monthly_KWh=0

## 3) Cost calculation
http://localhost:8000/cost/?Utility_Name=PG&E&Rate_Name=ETOUA&distance=50&maker=Nissan&model=Leaf&year=2012&charger=0&N_room=2&N_day=3&N_night=0&Ls_App=1,0,1,1,0,0&Monthly_Cost=200&time=0,0,0,0&charging_outside=1

## 4) Description 
http://localhost:8000/des/?Utility_Name=PG&E

## 5) Eligibility
http://localhost:8000/eli/?Utility_Name=PG&E

## 6) Connection Time
http://localhost:8000/cost/conn/?Utility_Name=PG&Rate_Name=E1

<p>Inputs:</p>
<ol>
<li>distance: Daily distnce driven bu the EV (miles)</li>
<li>maker: EV brand</li>
<li>model: EV model</li>
<li>year: EV model year</li>
<li>charger: Type of charger (Level 1/ Level 2 - 25 amp/ Level 2 - 40 amp / Level 2 - 50 amp) </li>
<li> N_room: Nb of rooms in the house (1- 5+)</li>
<li> N_day: Nb of people present in the house during day time (1- 5+)</li>
<li> N_night: Nb of people present in the house during evening and night time  (1- 5+)</li>
<li>Ls_App: Extra appliances: 1/0:Yes/No - List Element:[Stove,Dishwasher,Clothes Washer,Dryer,Swimming Pool,HVAC] </li>
<li> Cust_Monthly_Cost Monthly electricity cost($) of customer; default value: 0 - may not be given by customer </li>
<li> Cust_MOnthly_KWh: Monthly electricity consumption(KWh) of customer; default value:0. May not be given by customer if Cust_Monthly_Cost is given, then Cust_MOnthly_KWh will not be required </li>
<li>Connection time: connection time of household appliances and EV (time step: 15 minutes) - List Element:[house1, house2, house3, EV] </li>
<li>Allowance </li>
</ol>
<p>Ouputs: vector of cost for each utility rate (PG&E: [ETOU-A,ETOU-B,EV-TOU,E1] )</p>
<ol>
<li>Total_W: Total monthly cost during winter</li>
<li>Total_S: Total monthly cost during summer</li>
<li>House_W: Household monthly cost during winter</li>
<li>House_S: Household monthly cost during summer</li>
<li>Def_W: Deferrable loads: monthly cost during winter (Dishwasher,Clothes Washer,Dryer) (</li>
<li>Def_S: Deferrable loads: monthly cost during summer (Dishwasher,Clothes Washer,Dryer) </li>
<li>EV_W: EV monthly cost during winter</li>
<li>EV_S: EV monthly cost during summer</li>
<li>Plan_Name: List of the Utility name and the PG&E plan name</li>
</ol>
