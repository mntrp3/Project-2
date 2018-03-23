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

from flask import Flask, request, jsonify
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
class EarthStations(db.Model):
	__tablename__ = 'earthStations'
	id = db.Column(db.Integer, primary_key=True)
	fullName = db.Column(db.String(255))
	lat = db.Column(db.Float)
	long = db.Column(db.Float)
	currentAccuracy = db.Column(db.Float)
	gridpoint = db.Column(db.String(255))
	def __init__(self, fullName,lat,long,currentAccuracy,gridpoint):
		self.fullName = fullName
		self.lat=lat 
		self.long = long
		self.currentAccuracy= currentAccuracy
		self.gridpoint=gridpoint 
	
	

class EarthStationObservations(db.Model):
	__tablename__ = 'earthStationObservations'
	id = db.Column(db.Integer, primary_key=True)
	esTag = db.Column(db.String(255))
	dayAndHour = db.Column(db.String(255))
	observedTemp = db.Column(db.Float)
	accuracy = db.Column(db.Float)
	def __init__(self, esTag, dayAndHour, observedTemp, accuracy):
		self.esTag = esTag
		self.dayAndHour =dayAndHour
		self.observedTemp =observedTemp
		self.accuracy =accuracy 

class Forecast(db.Model):
	__tablename__ = 'forecast'
	id = db.Column(db.Integer, primary_key=True)
	gridId = db.Column(db.String(255))
	dayAndHour = db.Column(db.String(255))
	hoursForward = db.Column(db.Integer)
	daysHoursForecasted = db.Column(db.String(255))
	temperature = db.Column(db.Float)
	icon = db.Column(db.Integer)
	shortCast = db.Column(db.String(255))
	windSpeed = db.Column(db.String(255))
	windDirection = db.Column(db.String(255))
	def __init__(self, gridId, dayAndHour, hoursForward, daysHoursForecasted, temperature, icon, shortCast, windSpeed, windDirection):
		self.gridId = gridId
		self.dayAndHour =dayAndHour
		self.hoursForward = hoursForward 
		self.daysHoursForecasted = daysHoursForecasted 
		self.temperature =temperature 
		self.icon =icon 
		self.shortCast =shortCast
		self.windSpeed =windSpeed
		self.windDirection = windDirection

class GridStations(db.Model):
	__tablename__ = 'gridStations'
	id = db.Column(db.Integer, primary_key=True)
	gridPoint = db.Column(db.String(255))
	def __init__(self, gridPoint):
		self.gridPoint = gridPoint

class Icons(db.Model):
	__tablename__ = 'icons'
	id = db.Column(db.Integer, primary_key=True)
	icon = db.Column(db.String(255))
	def __init__(self, icon):
		self.icon = icon

class Locations(db.Model):
	__tablename__ = 'locations'
	id = db.Column(db.Integer, primary_key=True)
	lat = db.Column(db.Float)
	long = db.Column(db.Float)
	esTag = db.Column(db.String(255))
	def __init__(self, lat,long,esTag):
		self.lat = lat
		self.long=long
		self.esTag = esTag 


#do initialization tasks: setting and checking the locations (if necessary), prep the hourly web reqs, any additional web service needed.
def init():
	global app, init_complete
	getLocs()
	init_complete = True
	initScheduler()
	checkWeather()
	app.run(debug=False)
	
@app.route('/status')
def checkLive():
	print("status checked")
	return "Status: OK", 200, {'Content-Type': 'text/plain; charset=utf-8'}

#begin background code
def getLocs():
	global listOfPrimeGeoLocs, allGeoLocsWeatherLocs, allWeatherLocs, weatherEndpoint, allStationSets
	
	#check config file
	# if not os.path.exists("config.json"):
		# # get initial core locations
		# counter = 0
		# stop = False
		# while(not stop):
			# initLat= input("latitude of location "+str(counter)+"? ('fin' to stop) ")
			# if(initLat=='fin'):
				# stop = True
				# break
			# initLon = input("longitude of location "+str(counter)+"? (-180 < lon <= 180) ")
			# doubleLat = -91
			# doubleLon = -181
			# try:
				# doubleLat = float(initLat)
				# doubleLon = float(initLon)
			# except:
				# logging.exception("error on input, values must be a valid float")
				# continue
			# if(doubleLat<90 and doubleLat > -90 and doubleLon>-180 and doubleLon<=180):
				# listOfPrimeGeoLocs.append((doubleLon,doubleLat))
				# counter+=1
			# else:
				# logging.exception("error on input, values must be within normal Earth range")
				# continue
			
			# counter+=1
		
		# outputDict = {"primaryGeoLocations":listOfPrimeGeoLocs}
		# # try:
			# # with open('config.json', 'w') as configFileOut:
				# # json.dump(outputDict, configFileOut)
		
		# # except:
			# # print("error writing config file, now exiting")
			# # sys.exit(1)
	# # load config file
	# configData = {}	
	# configChanged = True
	# with open('config.json', 'r') as configFileIn:
		 # configData = json.load(configFileIn)
	
	# print(configData)
	
	listOfPrimeGeoLocs =  [[-77.116171, 38.881543]]#configData["primaryGeoLocations"]
	
	#if(not ("geoWeatherLocMap" in configData)):
	allGeoLocsWeatherLocs = getAllGeoWeatherLocMappings()
	print("greater geo weather loc mappings:")
	#print(allGeoLocsWeatherLocs)
	#	configData["geoWeatherLocMap"]=allGeoLocsWeatherLocs
	#	configChanged = True
	#else:
	#	allGeoLocsWeatherLocs = configData['geoWeatherLocMap']
	
	#if(not ("weatherLocs" in configData)):
	##allWeatherLocs = numpy.unique(allGeoLocsWeatherLocs.values(), axis=0)
	allWeatherLocs = allGeoLocsWeatherLocs.values()
	print("greater office grid mappings:")
	#print(allWeatherLocs)
		#configData["weatherLocs"]=allWeatherLocs
		#configChanged = True
	#else:
		#allWeatherLocs = configData["weatherLocs"]
	#write to config file if any data changed
	# if(configChanged):
		# try:
			# with open('config.json', 'w') as configFileOut:
				# json.dump(configData, configFileOut)
		# except:
			# print("error modifying config file, now continuing")
			
	print("location initialization and update complete.")
	
	#sys.exit(0)
	
	
#check api.weather.gov for the office and region for all the locations we gonna check.
def getAllGeoWeatherLocMappings():
	listOfPrimeGeoLocs = [[-77.116171, 38.881543]]
	fullSet = [(round(loc[0],2),round(loc[1],2)) for loc in listOfPrimeGeoLocs]
	locSet = []
	retDict = {}
	
	highOffset = 0.1
	lowOffset = 0.5
	stepLow = 0.1
	stepHigh = 0.01
	# highOffset = 0.1
	# lowOffset = 0.2
	# stepLow = 0.1
	# stepHigh = 0.05
	for loc in fullSet:
		curLon = loc[0]
		curLat = loc[1]
		#pattern is +/-0.1 deg at 0.02 deg step (121 points), and +/- 0.4 deg at 0.2 step (24 points) for a total of 145 maximum points of interest / major location
		lonMinLow =  curLon-lowOffset
		lonMinHigh = curLon-highOffset
		lonMaxLow = curLon+lowOffset+stepLow
		lonMaxHigh =curLon + highOffset + stepHigh
		latMinLow =  curLat-lowOffset
		latMinHigh = curLat-highOffset
		latMaxLow = curLat+lowOffset+stepLow
		latMaxHigh =curLat + highOffset + stepHigh
		#high res
		for lon in numpy.arange(lonMinHigh,lonMaxHigh, stepHigh):
			for lat in numpy.arange(latMinHigh,latMaxHigh, stepHigh):
				locSet.append((lon,lat))
				
		
		for lon in numpy.arange(lonMinLow,lonMaxLow, stepLow):
			for lat in numpy.arange(latMinLow,latMaxLow, stepLow):
				locSet.append((lon,lat))
		
		
	#locSet = numpy.unique(locSet, axis=0)
	
	print("locset before apiCalls")
	return locSet
	
#init the scheduler for periodically checking weather.api.gov
def initScheduler():
	global listOfPrimeGeoLocs, allGeoLocsWeatherLocs, allWeatherLocs, weatherEndpoint, allStationSets
	
	# scheduler = BackgroundScheduler()
	# scheduler.start()
	# scheduler.add_job(
		# func=checkWeather,
		# trigger=IntervalTrigger(seconds=3600),
		# id='weather_pull',
		# name='Call Weather API every hour',
		# replace_existing=True)
	# # Shut down the scheduler when exiting the app
	# atexit.register(lambda: scheduler.shutdown())

dbLocSet=[]

@app.route('/update')
def checkWeather():
	global weatherEndpoint, init_complete, dbLocSet
	
	
	#print time.strftime("%A, %d. %B %Y %I:%M:%S %p")
	try:
		if not init_complete:
			dbLocSet = getDBLocs()
			init_complete = True
		
		# visitedSet = {}
		hackTime = datetime.now()
		strTime = hackTime.strftime("%y_%m_%d_%H")
		accessTime = hackTime.strftime("%Y%m%d%H")
		
		#database maintenance
		killTime1 = (hackTime-timedelta(days=4)).strftime("%Y%m%d%H")
		killTime2 = (hackTime-timedelta(days=1)).strftime("%Y%m%d%H")
		
		Forecast.query.filter(and_(hoursForward!=24,hoursForward!=72)).delete()
		Forecast.query.filter(dayAndHour<killTime1).delete()
		EarthStationObservations.query.filter(dayAndHour<killTime2).delete()
		
		
		
		#end maintenance
		
		weatherIcons = {}
		for item in dbLocSet:
		
			gridPointString = item
			splitString = gridPointString.split("_")
			office = splitString[0]
			gridX = splitString[1]
			gridY = splitString[2]
			dataDir = "data/"
			dirPath = office+"/"+str(gridX)+"_"+str(gridY)
			curGridId = gridPointString
			# if not(os.path.isdir(dataDir)):
				# try:
					# os.makedirs(dataDir)
				# except Exception as e:
					# print("Error: could not create required directory.")
					# print(e)
					# sys.exit(1)
			# """
			# "forecast": "https://api.weather.gov/gridpoints/IND/27,26/forecast",
			# "forecastHourly": "https://api.weather.gov/gridpoints/IND/27,26/forecast/hourly",
			# "forecastGridData": "https://api.weather.gov/gridpoints/IND/27,26",
			# "observationStations": "https://api.weather.gov/gridpoints/IND/27,26/stations",
			# "stationOfInterest": "https://api.weather.gov/stations/%%%%/observations/current"
			# """
			writeBlob = {}
			#forecastGridData
			gridDataEndpoint = weatherEndpoint+"gridpoints/"+office+"/"+str(gridX)+","+str(gridY)
			#forecast
			forecastEnpoint=gridDataEndpoint +"/forecast"
			#forecastHourly
			hourlyEndpoint = forecastEnpoint +"/hourly"
			#endpoint1:
			
			#stationDataEndpoint = weatherEndpoint+"stations/"+allStationSets[str(item)]+"/observations/current"
			
			# try:
				# #the endpoints
				# writeBlob["gridData"] = requests.get(gridDataEndpoint).json()
			# except Exception as e:
				# print("Warning: "+str(item)+" failed on grid data weather request.")
				# print(e)
				# #time.sleep(5)
				# #continue
				
			try:
				#the endpoints
				writeBlob["hourlyData"] = requests.get(hourlyEndpoint).json()
			except Exception as e:
				logging.exception("Warning: "+str(item)+" failed on hourly forecast weather request.")
				logging.exception(e)
				print("weather api req failed")
			
			try:
				for currentForecastBlob in writeBlob["hourlyData"]["properties"]["periods"]:
					currentHour = currentForecastBlob["number"]
					if currentHour > 72:
						continue
					timeString = datetime.strptime(currentForecastBlob["endTime"][:13], '%Y-%m-%dT%H').strftime("%Y%m%d%H")
					
					iconString = currentForecastBlob['icon']
					if(iconString in weatherIcons):
						idNum = weatherIcons[iconString]
					else:
						try:
							idNum = Icons.query.filter_by(icon=iconString).first().id
						except NoResultFound as e:
							ico = Icons(iconString)
							db.session.add(ico)
							db.session.commit()
							idNum = ico
							# Deal with that as well
						weatherIcons[iconString]=idNum
					
					forecast = Forecast(
						gridId = curGridId,
						dayAndHour = accessTime,
						hoursForward = int(currentHour),
						daysHoursForecasted = timeString,
						temperature = float(currentForecastBlob['temperature']),
						icon = idNum,
						shortCast = currentForecastBlob["shortForecast"],
						windSpeed =currentForecastBlob["windSpeed"],
						windDirection = currentForecastBlob["windDirection"]
					)
					db.session.add(forecast)
					db.session.commit()

			except:
				logging.exception("error writing data file "+ str(item)+", moving to next item")
				print("internal db add record failed")
				continue
				
		
		EarthStationVisits = EarthStations.query.all()
		
		for item in EarthStationVisits:
			
			ESName = item.fullName

			# "stationOfInterest": "https://api.weather.gov/stations/%%%%/observations/current"
			writeBlob = {}

			#endpoint1:
			
			stationDataEndpoint = weatherEndpoint+"stations/"+ESName+"/observations/current"
			

				
			try:
				#the endpoints
				writeBlob = requests.get(stationDataEndpoint).json()
			except Exception as e:
				logging.exception("Warning: "+ESName+" failed on station obvs weather request.")
				logging.exception(e)
				print("weather api stations req failed")

			
			try:
				timeString = datetime.strptime(writeBlob["properties"]['timestamp'][:13], '%Y-%m-%dT%H').strftime("%Y%m%d%H")
				if item.currentAccuracy == Null or item.currentAccuracy <1.0:
					item.currentAccuracy = 90.0
				
				curTemp =float(writeBlob['properties']['temperature']['value'])*1.8+32.0
				
				eso = EarthStationObservations(
					esTag = ESName,
					dayAndHour = timeString,
					observedTemp = curTemp,
					accuracy = getAccNum(timeString, curTemp,  item.currentAccuracy, item.gridpoint)
				)
				db.session.add(eso)
				
				item.currentAccuracy = eso.accuracy
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

def getAccNum(dayAndHour, obvTemp, curAcc, gridPoint):
	#can do weighted based on time later
	accs=[]
	for casts in Forecast.query.filter_by(daysHoursForecasted = dayAndHour, gridId = gridPoint):
		accs.append(getTempAcc(obvTemp,casts.temperature))
	if len(accs)>0:
		return getTempDiffAcc(numpy.average(accs),curAcc)
	else:
		return curAcc

def getTempAcc(obvTemp, estTemp):
	return  100.0-min(max(abs(obvTemp-estTemp)-1.0,0.0),20.0)*5.0
	
def getTempDiffAcc(relAcc, curAcc):
	return curAcc*0.999+relAcc*0.001

def getDBLocs():
	retArr = []
	gridPointVisits = GridStations.query.all()
	for curGridPoint in gridPointVisits:
		retArr.append(curGridPoint.gridPoint)
	return retArr
#end background code

@app.route('/recentTempTrend')
def GetRecentTempHistory():
	#HACK until db read is online
	retArr = [{"hour":"8:00 AM","today":"60","yesterdayPredict":65,"threeDayPredict":65},{"hour":"9:00 AM","today":"70","yesterdayPredict":40,"threeDayPredict":45},{"hour":"10:00 AM","today":"40","yesterdayPredict":80,"threeDayPredict":82},{"hour":"11:00 AM","today":"60","yesterdayPredict":85,"threeDayPredict":85},{"hour":"12:00 PM","today":"80","yesterdayPredict":80,"threeDayPredict":80},{"hour":"1:00 PM","today":"45","yesterdayPredict":75,"threeDayPredict":75},{"hour":"2:00 PM","today":"50","yesterdayPredict":73,"threeDayPredict":72},{"hour":"3:00 PM","today":"40","yesterdayPredict":70,"threeDayPredict":70},{"hour":"4:00 PM","today":"null","yesterdayPredict":75,"threeDayPredict":75}]
	
	# startTimeStamp = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d%H")
	
	# retArr = [{'hour':'','today':0,'yesterdayPredict':0,'threeDayPredict':0} for i in numpy.arange(0,24)]
	
	return jsonify(retArr)
	
	
	
	

	# {
# "collectionTime":{"day":1,"hour":25},
# "locations":[{lat,lon,"statID"},...],
# "stations": {"statID":{"gridID",accuracy},...},
# "forecastGrid":{"1":{"gridID":{forecastTemp,icon,shortCast,windSpeed,windDirection}...},"2":...}
# }
@app.route('/curForecastInfo')
def GetRecentForecast():
	return "not yet implemented"

#configuration, setup, and maintenance code: do not call except when needed.
@app.route('/initDatabase')
def InsertTables():
	db.create_all()
	return "tables created!", 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/buildLocSet')
def GenerateLoc():
	global weatherEndpoint
	print ("writing locs to db")
	try:
		startingLocSet = getAllGeoWeatherLocMappings()
	except:
		return "failed to generate all points", 500, {'Content-Type': 'text/plain; charset=utf-8'}
	print("locs generated")
	visitedUniqueLocs = {}
	visitedGridPoints={}
	visitedES = {}
	#the part where we call the weather api for its locations
	#'https://api.weather.gov/points/lat,lon
	for uniqueLocation in startingLocSet:
		if(str(uniqueLocation) in visitedUniqueLocs):
			continue
		#print(str(uniqueLocation))
		visitedUniqueLocs[str(uniqueLocation)]=1
		try:
			response = requests.get(weatherEndpoint+"points/"+str(uniqueLocation[1])+","+str(uniqueLocation[0]))
			properties = response.json()["properties"]
			gridPointString = str(properties["cwa"])+"_"+str(properties["gridX"])+"_"+str(properties["gridY"])
			
			secondResponse = requests.get(weatherEndpoint+"points/"+str(uniqueLocation[1])+","+str(uniqueLocation[0])+"/stations")
			curPointStationSet = secondResponse.json()["features"]
			#later: get closest ES to point of investigation
			#HACK: should return/compute this bit separately.
			firstStation = curPointStationSet[0]
			stationName = firstStation['properties']['stationIdentifier']
		except Exception as e:
			#sys.exit(0)
			print("Error has occurred:" +str(sys.exc_info()[-1].tb_lineno))
			print(str(e))
			continue
		try:
			newLoc = Locations(uniqueLocation[1],uniqueLocation[0],stationName)
			db.session.add(newLoc)
			
			if(stationName in visitedES):
				continue
			
			newES = EarthStations(stationName, firstStation['geometry']['coordinates'][1], firstStation['geometry']['coordinates'][0],90.0, gridPointString)
			db.session.add(newES)
			visitedES[stationName]=1
			
			if( gridPointString in visitedGridPoints):
				continue
			
			newGridPoint = GridStations(gridPointString)
			db.session.add(newGridPoint)
			visitedGridPoints[gridPointString]=1
		except Exception as e:
			print ("failed db adds")
			print(str(e))
			return "failed to add to db", 500, {'Content-Type': 'text/plain; charset=utf-8'}
	db.session.commit()
	# try:
		# with open('allStations.json', 'w') as stationDataOut:
			# json.dump(allStationSets, stationDataOut)
	# except:
		# print("error modifying config file, now continuing")
	print("locations found and written to db")
	# sys.exit(0)
	return "successful loc prep!", 200, {'Content-Type': 'text/plain; charset=utf-8'}

	
if __name__ == "__main__":
	#sys.exit(0)
	init()

