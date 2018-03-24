import time
import atexit
import os
import csv
import requests
import json
import numpy
import datetime
from datetime import datetime, timedelta
import sys
import logging
import socket
import sqlalchemy

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy





app = Flask(__name__)
#variable to prevent a LOT of processing that google'd do.
debug_deployment = True
listOfPrimeGeoLocs = []
allGeoLocsWeatherLocs = {}
allWeatherLocs = []
allStationSets = {}
init_complete = False
weatherEndpoint = "https://api.weather.gov/"

# Environment variables are defined in app.yaml .
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Creates Classes which will serve as the anchor points for our Tables
class EarthStation(db.Model):
	__tablename__ = 'earthStations'
	id = db.Column(db.Integer, primary_key=True)
	esTag = db.Column(db.String(255))
	esName = db.Column(db.String(255))
	lat = db.Column(db.Float)
	long = db.Column(db.Float)
	gridPoint = db.Column(db.String(255))
	accuracy = db.column(db.Float)
	def __init__(self, esTag,esName,lat,long,gridPoint, accuracy):
		self.esTag = esTag
		self.esName = esName
		self.lat=lat 
		self.long = long
		self.gridPoint=gridPoint 
		self.accuracy = accuracy

class EarthStationObservation(db.Model):
	__tablename__ = 'earthStationObservations'
	id = db.Column(db.Integer, primary_key=True)
	esTag = db.Column(db.String(255))
	dayAndHour = db.Column(db.String(255))
	dayForwards = db.Column(db.String(255))
	observedTemp = db.Column(db.Float)
	forecastTemp = db.Column(db.Float)
	def __init__(self, esTag, dayAndHour, dayForwards, observedTemp, forecastTemp):
		self.esTag = esTag
		self.dayAndHour =dayAndHour
		self.dayForwards =dayForwards
		self.observedTemp =observedTemp
		self.forecastTemp =forecastTemp

######END DATABASE DECLARATION AND VAR INITIALIZATION

#####CLIENT SERVING FUNCTIONS

@app.route('/')
def weather():
	return render_template('index.html')
	
@app.route('/index.html')
def weatherReroute():
	return weather()

@app.route('/index2.html')
def weathermap():
	return render_template('index2.html')

@app.route('/index3.html')
def yearweather():
	return render_template('index3.html')

@app.route('/status')
def checkLive():
	print("status checked")
	return "Status: OK", 200, {'Content-Type': 'text/plain; charset=utf-8'}
@app.route('/ESSet')
def getEarthStationNames():
	retArr = []
	for ES in EarthStation.query.all():
		retArr.append({'name':ES.esName,'tag':ES.esTag})
	return jsonify(retArr)


@app.route('/recentTempTrend/')
def GetRecentTempHistoryBase():
	return GetRecentTempHistory("")
	
@app.route('/recentTempTrend/<Station>')
def GetRecentTempHistory(Station):
	if Station is None or Station == "":
		Station = 'KDCA'#Reagan
	
	hackTime = datetime.now()
	accessTime = hackTime.strftime("%Y%m%d%H")
	
	#database maintenance
	killTime1 = (hackTime-timedelta(days=1))
	killTime2 = (killTime1).strftime("%Y%m%d%H")
	
	retDict = {}
	curESSet = EarthStation.query.filter_by(esTag = Station).all()
	
	curES = curESSet[0]
	latVal = curES.lat
	#print(latVal)
	lonVal = curES.long
	#print(lonVal)
	accVal = curES.accuracy
	
	
	# if(curES is not None):
		# retDict['data']= {"name":str(curES.esName),"lat":latVal,"lon":lonVal, "acc":accVal}
	
	startingHour = int(accessTime[8:])
	retArr = []
	for i in numpy.arange(0,24):
		curTime = (killTime1+timedelta(hours=int(i))).strftime("%Y%m%d%H")
		currentHour = curTime[8:]+":00"
		
		curPoint = EarthStationObservation.query.filter_by(esTag = curES.esTag).filter_by(dayAndHour=curTime).first()
		if curPoint is None:
			curTemp = 'null'
		else:
			curTemp = curPoint.observedTemp
			
		forPoint = EarthStationObservation.query.filter_by(esTag = curES.esTag).filter_by(dayForwards=curTime).first()
		if forPoint is None:
			forTemp = 'null'
		else:
			forTemp = forPoint.observedTemp
		retArr.append ({"hour": currentHour, 'today':curTemp, 'yesterdayPredict':forTemp})
	
	retDict['chartData']=retArr
	
	# for recordedData in EarthStationObservation.query.filter_by(esTag = curES.esTag).filter(EarthStationObservation.dayForwards>killTime2).order_by(EarthStationObservation.dayForwards).all():
	# #HACK until db read is online
	# retArr = [{"hour":"8:00 AM","today":"60","yesterdayPredict":65,"threeDayPredict":65},{"hour":"9:00 AM","today":"70","yesterdayPredict":40,"threeDayPredict":45},{"hour":"10:00 AM","today":"40","yesterdayPredict":80,"threeDayPredict":82},{"hour":"11:00 AM","today":"60","yesterdayPredict":85,"threeDayPredict":85},{"hour":"12:00 PM","today":"80","yesterdayPredict":80,"threeDayPredict":80},{"hour":"1:00 PM","today":"45","yesterdayPredict":75,"threeDayPredict":75},{"hour":"2:00 PM","today":"50","yesterdayPredict":73,"threeDayPredict":72},{"hour":"3:00 PM","today":"40","yesterdayPredict":70,"threeDayPredict":70},{"hour":"4:00 PM","today":"null","yesterdayPredict":75,"threeDayPredict":75}]
	
	# startTimeStamp = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d%H")
	
	# retArr = [{'hour':'','today':0,'yesterdayPredict':0,'threeDayPredict':0} for i in numpy.arange(0,24)]
	
	return jsonify(retDict)
	
#format for this function:
	# {
# "collectionTime":{"day":1,"hour":25},
# "locations":[{lat,lon,"statID"},...],
# "stations": {"statID":{"gridID",accuracy},...},
# "forecastGrid":{"1":{"gridID":{forecastTemp,icon,shortCast,windSpeed,windDirection}...},"2":...}
# }
@app.route('/curForecastInfo')
def GetRecentForecast():
	return "not yet implemented"
		
#########END CLIENT SERVING FUNCTIONS

#do initialization tasks: setting and checking the locations (if necessary), prep the hourly web reqs, any additional web service needed.
def init():
	global app, init_complete
	#getLocs()
	init_complete = True
	#initScheduler()
	#checkWeather()
	app.run(debug=False)	

#var used exclusively for ease of instanced updates when live
dbLocSet=[]

@app.route('/update')
def checkWeather():	
	try:
		
		# visitedSet = {}
		hackTime = datetime.now()
		strTime = hackTime.strftime("%y_%m_%d_%H")
		accessTime = hackTime.strftime("%Y%m%d%H")
		
		#database maintenance
		#killTime1 = (hackTime-timedelta(days=4)).strftime("%Y%m%d%H")
		#killTime2 = (hackTime-timedelta(days=1)).strftime("%Y%m%d%H")
		
		#Forecast.query.filter(and_(hoursForward!=24,hoursForward!=72)).delete()
		#Forecast.query.filter(dayAndHour<killTime1).delete()
		#EarthStationObservations.query.filter(dayAndHour<killTime2).delete()
		#end maintenance
		ESSet = EarthStation.query.all()
		#weatherIcons = {}
		for item in ESSet:
			
			# "forecastHourly": "https://api.weather.gov/gridpoints/IND/27,26/forecast/hourly",
			
			writeBlob = {}
			#forecastGridData
			gridDataEndpoint = weatherEndpoint+"gridpoints/"+item.gridPoint
			#forecast
			forecastEnpoint=gridDataEndpoint +"/forecast"
			#forecastHourly
			hourlyEndpoint = forecastEnpoint +"/hourly"
			#endpoint1:
			
				
			try:
				#the endpoints
				writeBlob["hourlyData"] = requests.get(hourlyEndpoint).json()
			except Exception as e:
				logging.exception("Warning: "+str(item)+" failed on hourly forecast weather request.")
				logging.exception(e)
				print("weather api req failed")
			
			try:
				writeBlob["obvs"] = requests.get(weatherEndpoint+"stations/"+item.esTag+"/observations/current").json()
			except Exception as e:
				logging.exception("Warning: "+str(item)+" failed on ES weather request.")
				logging.exception(e)
				print("weather api req failed")
			
			
			try:
				currentForecastBlob = writeBlob["hourlyData"]["properties"]["periods"][23]
				currentHour = currentForecastBlob["number"]
				timeString = datetime.strptime(currentForecastBlob["endTime"][:13], '%Y-%m-%dT%H').strftime("%Y%m%d%H")
				curTemp = writeBlob['obvs']['properties']['temperature']['value']
				if curTemp is None:
					obvTemps = None
				else:
					obvTemps = curTemp*1.8+32.0
				
				nextESO = EarthStationObservation(item.esTag, accessTime, timeString, obvTemps, currentForecastBlob['temperature'])
				
				item.accuracy = getAccNum(accessTime,obvTemps, item.accuracy, item.esTag)
		
				db.session.add(nextESO)
				db.session.commit()

			except:
				logging.exception("error writing data file "+ str(item)+", moving to next item")
				print("internal db add record failed")
				continue
		
		print("weather api pull succeeded")
		return "api pull complete", 200, {'Content-Type': 'text/plain; charset=utf-8'}
	except	Exception as e:
		logging.exception("Warning: "+str(item)+" failed on hourly forecast weather request.")
		logging.exception(e)
		print("weather update failed")
		print(str(e))
		return "api pull failed", 500, {'Content-Type': 'text/plain; charset=utf-8'}

def getAccNum(accessTime, obvTemp, curAcc, esAbbrev):
	#can do weighted based on time later
	accs=[]
	for casts in EarthStationObservation.query.filter_by(dayForwards = accessTime, esTag = esAbbrev):
		accs.append(getTempAcc(obvTemp,casts.forecastTemp))
	if len(accs)>0:
		return getTempDiffAcc(numpy.average(accs),curAcc)
	else:
		return curAcc

def getTempAcc(obvTemp, estTemp):
	return  100.0-min(max(abs(obvTemp-estTemp)-1.0,0.0),20.0)*5.0
	
def getTempDiffAcc(relAcc, curAcc):
	return curAcc*0.999+relAcc*0.001
#############end background code



#####################configuration, setup, and maintenance code: DO NOT CALL except when needed/using live server to interact with database.
@app.route('/initDatabase')
def InsertTables():
	db.create_all()
	return "tables created!", 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/initEarthStations')
def InsertEarthStations():
	print('es add started')
	ESInitJson = json.load(open("AllStationsWithLocTag.json"))
	print('json loaded')
	for row in ESInitJson:
		print('looping!')
		respoJson = requests.get("https://api.weather.gov/stations/"+row['abbrev']).json()
		lat = respoJson['geometry']['coordinates'][1]
		lon = respoJson['geometry']['coordinates'][0]
		
		
		newEarthStation = EarthStation(row['abbrev'],row['name'],lat,lon,row['LocTag'],80.0)
		db.session.add(newEarthStation)
		db.session.commit()
	
	return "ES added!", 200, {'Content-Type': 'text/plain; charset=utf-8'}
#######END CONFIGURATION CODE

	
if __name__ == "__main__":
	#sys.exit(0)
	init()

