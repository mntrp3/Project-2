import time
import atexit
import os
import csv
import requests
import json
import numpy
import datetime
import zipfile
import sys
import logging
import socket
import sqlalchemy

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger





app = Flask(__name__)
#variable to prevent a LOT of processing that google'd do.
debug_deployment = True
listOfPrimeGeoLocs = []
allGeoLocsWeatherLocs = {}
allWeatherLocs = []
allStationSets = {}
weatherEndpoint = "https://api.weather.gov/"


#do initialization tasks: setting and checking the locations (if necessary), prep the hourly web reqs, any additional web service needed.
def init():
	global app
	getLocs()
	
	initScheduler()
	checkWeather()
	app.run(debug=False)

def getLocs():
	global listOfPrimeGeoLocs, allGeoLocsWeatherLocs, allWeatherLocs, weatherEndpoint
	
	#check config file
	if not os.path.exists("config.json"):
		#get initial core locations
		counter = 0
		stop = False
		while(not stop):
			initLat= input("latitude of location "+str(counter)+"? ('fin' to stop) ")
			if(initLat=='fin'):
				stop = True
				break
			initLon = input("longitude of location "+str(counter)+"? (-180 < lon <= 180) ")
			doubleLat = -91
			doubleLon = -181
			try:
				doubleLat = float(initLat)
				doubleLon = float(initLon)
			except:
				print("error on input, values must be a valid float")
				continue
			if(doubleLat<90 and doubleLat > -90 and doubleLon>-180 and doubleLon<=180):
				listOfPrimeGeoLocs.append((doubleLon,doubleLat))
				counter+=1
			else:
				print("error on input, values must be within normal Earth range")
				continue
			
			counter+=1
		
		outputDict = {"primaryGeoLocations":listOfPrimeGeoLocs}
		# try:
			# with open('config.json', 'w') as configFileOut:
				# json.dump(outputDict, configFileOut)
		
		# except:
			# print("error writing config file, now exiting")
			# sys.exit(1)
	#load config file
	configData = {}	
	configChanged = True
	with open('config.json', 'r') as configFileIn:
		 configData = json.load(configFileIn)
	
	print(configData)
	
	listOfPrimeGeoLocs = configData["primaryGeoLocations"]
	
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
	global listOfPrimeGeoLocs, allGeoLocsWeatherLocs, allWeatherLocs, weatherEndpoint
	#get a resolution of full locations to 0.02 degrees spacing lat/lon, so approximate distance between points is ~ 0.15 mi (i.e. over a thousand feet)
	#fullSet = [(2*round(loc[0]/2.0,2),2*round(loc[1]/2.0,2)) for loc in listOfPrimeGeoLocs]
	#going with finer resolution since 0.02 was a little bit too low, and we cut out excess gridpoints later anyways.
	fullSet = [(round(loc[0],2),round(loc[1],2)) for loc in listOfPrimeGeoLocs]
	locSet = []
	retDict = {}
	
	# highOffset = 0.1
	# lowOffset = 0.5
	# stepLow = 0.1
	# stepHigh = 0.01
	highOffset = 0.1
	lowOffset = 0.2
	stepLow = 0.1
	stepHigh = 0.05
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
	#print(locSet)
	
	visitedUniqueLocs = {}
	#the part where we call the weather api for its locations
	#'https://api.weather.gov/points/lat,lon
	for uniqueLocation in locSet:
		if(str(uniqueLocation) in visitedUniqueLocs):
			continue
		#print(str(uniqueLocation))
		visitedUniqueLocs[str(uniqueLocation)]=1
		
		try:
			response = requests.get(weatherEndpoint+"points/"+str(uniqueLocation[1])+","+str(uniqueLocation[0]))
			properties = response.json()["properties"]
			valueAnswer =	(properties["cwa"],properties["gridX"],properties["gridY"])
			retDict[uniqueLocation]=valueAnswer
		except:
			continue
	return retDict
	
#init the scheduler for periodically checking weather.api.gov
def initScheduler():
	global listOfPrimeGeoLocs, allGeoLocsWeatherLocs, allWeatherLocs, weatherEndpoint
	
	scheduler = BackgroundScheduler()
	scheduler.start()
	scheduler.add_job(
		func=checkWeather,
		trigger=IntervalTrigger(seconds=3600),
		id='weather_pull',
		name='Call Weather API every hour',
		replace_existing=True)
	# Shut down the scheduler when exiting the app
	atexit.register(lambda: scheduler.shutdown())
	
def checkWeather():
	global listOfPrimeGeoLocs, allGeoLocsWeatherLocs, allWeatherLocs, weatherEndpoint
    #print time.strftime("%A, %d. %B %Y %I:%M:%S %p")
	visitedSet = {}
	hackTime = datetime.datetime.now()
	strTime = hackTime.strftime("%y_%m_%d_%H")
	for item in allWeatherLocs:
		if(str(item) in visitedSet):
			continue
		visitedSet[str(item)]=1
		office = item[0]
		gridX = item[1]
		gridY = item[2]
		dataDir = "data/"
		dirPath = office+"/"+str(gridX)+"_"+str(gridY)
		# if not(os.path.isdir(dataDir)):
			# try:
				# os.makedirs(dataDir)
			# except Exception as e:
				# print("Error: could not create required directory.")
				# print(e)
				# sys.exit(1)
			"""
			       "forecast": "https://api.weather.gov/gridpoints/IND/27,26/forecast",
        "forecastHourly": "https://api.weather.gov/gridpoints/IND/27,26/forecast/hourly",
        "forecastGridData": "https://api.weather.gov/gridpoints/IND/27,26",
        "observationStations": "https://api.weather.gov/gridpoints/IND/27,26/stations",
			"""
		writeBlob = {}
		#forecastGridData
		gridDataEndpoint = weatherEndpoint+"gridpoints/"+office+"/"+str(gridX)+","+str(gridY)
		#forecast
		forecastEnpoint=gridDataEndpoint +"/forecast"
		#forecastHourly
		hourlyEndpoint = forecastEnpoint +"/hourly"
		#endpoint1:
			
			
		try:
			#the endpoints
			writeBlob["gridData"] = requests.get(gridDataEndpoint).json()
		except Exception as e:
			print("Warning: "+str(item)+" failed on grid data weather request.")
			print(e)
			#time.sleep(5)
			#continue
			
		try:
			#the endpoints
			writeBlob["hourlyData"] = requests.get(hourlyEndpoint).json()
		except Exception as e:
			print("Warning: "+str(item)+" failed on hourly forecast weather request.")
			print(e)
			#time.sleep(5)
			#continue
			
		try:
			#the endpoints
			writeBlob["forecastData"] = requests.get(forecastEnpoint).json()
		except Exception as e:
			print("Warning: "+str(item)+" failed on forecast weather request.")
			print(e)
			#time.sleep(5)
			#continue
		
		# writingMode = 'w'
		# if(os.path.exists(dataDir) and os.path.isfile(dataDir+'runningArchive.zip')):
			# writingMode = 'a'
		
		#write the data (later to be replaced with db access)
		# try:
			# zf = zipfile.ZipFile(dataDir+'runningArchive.zip', 
								 # mode='a',
								 # compression=zipfile.ZIP_DEFLATED, 
								 # )
			# try:
				# zf.writestr(os.path.join(dirPath,strTime+'.json'), json.dumps(writeBlob))
			# except:
				# print("error zipping data file "+ str(item)+"")
			# finally:
				# zf.close()
			# #with open(os.path.join(dirPath,strTime+'.json'), 'w') as curFileOut:
			# #	json.dump(writeBlob, curFileOut)
		# except:
			# print("error writing data file "+ str(item)+", moving to next item")
			# continue

if __name__ == "__main__":
	init()

