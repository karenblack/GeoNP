# Author: Karen Black
# Last Modified: May 30, 2021
# Description: Server-side processing for GeoNP webapp

from flask import Flask, render_template, jsonify, request
from bs4 import BeautifulSoup
import requests
import re
import json
import urllib

app = Flask(__name__)

@app.route("/")
def home():
	return render_template("index.html")


# to render compare.html page
@app.route('/compare', methods = ['POST', 'GET'])
def compare():

	# to store data for each park to render in compare page
	image_urls=[]					# to store image urls
	geol = []					    # to store geology paragraph text
	estab = []						# to store infobox text - Established
	visitors = []					# to store infobox text - Park visitors
	maps = []						# to store map coordinates
	headers = []					# headers for comparison page
	nps_web = []					# NPS websites
	states=[]						# state for hiking map
	hikes = []						# hiking titles

	# get the park names submitted for comparison
	if request.method == 'POST':
		titles_all = request.form.getlist('parkToggle')
	
	for item in titles_all:
		title_list = item.split(",")
		title= title_list[0]
		state = title_list[1]

	
		# **** GEOLOGY PARAGRAPHS (text-scraper) *****
		text = geology_text(title)
		geol.append(text)

		# **** INFOBOX QUERY FOR TITLES (text-scraper) ****
		park_title = park_titles(title)
		headers.append(park_title)

		# *** INFOBOX SCRAPING (my API) ****
		infobox_data = infobox(title)
		estab.append(infobox_data[0])
		visitors.append(infobox_data[1])
		nps_web.append(infobox_data[2])

		# **** GPS COORDINATES (text scraper) ****
		park_coords=coords(title)
		maps.append(park_coords)

		# **** IMAGES (image-scraper) *****
		url=images(title)
		image_urls.append(url)

		# ***** HIKING (widget) ********
		modified_title = hiking(title)
		hikes.append(modified_title)
		if state == 'american-samoa' or state == 'us-virgin-islands':
			states.append(state)
		else:
			states.append('us/' + state)

	#render the webpage
	if len(titles_all) == 2:
		return render_template("compareTwo.html", urls=image_urls, title=headers, web=nps_web, vis=visitors, est=estab, geo=geol, map=maps, hike=hikes, state=states)
	else:
		return render_template("compare.html", urls=image_urls, title=headers, web=nps_web, vis=visitors, est=estab, geo=geol, map=maps, hike=hikes, state=states)


def park_titles(title):
	"""Accepts a park title and formats appropriately for display in 'comparison' page"""
	try:
		infobox = requests.get('https://wiki-text-scraper.herokuapp.com/wiki/' + title + '/infobox')
		info_json = infobox.json()
	except:
		info_json = [title]

	# get park Name		
	parkName = info_json[0]
	tags = ['National Park of','National Park and Preserve', 'National Park']
	for tag in tags:
		if tag in parkName:
			parkName = parkName.replace(tag, '')
	return parkName

def geology_text(title):
	"""Accepts a part title and calls the Wikipedia Text Scraper microservice for text from 'Geology' section"""
	try:
		geo = requests.get('https://wiki-text-scraper.herokuapp.com/wiki/' + title + '/Geology')
		print("****GEO*****", title)
		geo_json = geo.json()
		geo = geo_json["Geology"]
		geo_text = geo.replace('\n', '<br> </br>')
	except:
		try:
			error = "<i> No distinct Geology Section available. Please refer to the National Park Service Website or the Park and Other Resources Menu.</i><br> </br> <b>Geography</b><br>"
			geo = requests.get('https://wiki-text-scraper.herokuapp.com/wiki/' + title + '/Geography')
			geo_json = geo.json()
			geo = geo_json["Geography"]
			geo_clean = geo.replace('\n', '<br> </br>')
			geo_text = error + geo_clean
		except:
			error = "<i> No distinct Geology Section available. Please refer to the National Park Service Website or the Park and Other Resources Menu.</i><br> </br> <b>About</b><br>"
			geo = requests.get('https://wiki-text-scraper.herokuapp.com/wiki/' + title + '/Intro')
			geo_json = geo.json()
			geo = geo_json["Intro"]
			geo_clean = geo.replace('\n', '<br> </br>')
			geo_text = error + geo_clean
	return geo_text

def infobox(title):
	"""Accepts a park title and calls the Wikipedia infobox scraper API to obtain specific Park information"""
	# get estabilished date
	try:
		resp = requests.get('https://wiki-image-scraper.herokuapp.com/api/infobox/?title=' + title + '&fld=est')
		resp_json = resp.json()
		estab_date=resp_json["infobox"]
	except:
		estab_date='Not Provided'

	# get park visitors
	try:
		resp = requests.get('https://wiki-image-scraper.herokuapp.com/api/infobox/?title=' + title + '&fld=vis')
		resp_json = resp.json()
		visit=resp_json["infobox"]
	except:
		visit='Not Provided'
	
	# get NPS websites
	try:
		resp = requests.get('https://wiki-image-scraper.herokuapp.com/api/infobox/?title=' + title + '&fld=web')
		resp_json = resp.json()
		nps_url=resp_json["infobox"]
	except:
		nps_url='Not Provided'

	return [estab_date, visit, nps_url]

def coords(title):
	"""Accepts a park title and call Wikipedia text scraper microservice to retrieve GPS coordinates"""

	resp = requests.get('https://wiki-text-scraper.herokuapp.com/wiki/' + title + '/coords')
	resp_json = resp.json()
	coords = [float(resp_json["lat"]), float(resp_json["lon"])]
	return coords

def images(title):
	"""Accepts a park title and requests an image from the Wikipedia image scraping microservice"""
	image= requests.get('https://wiki-image-scraper.herokuapp.com/api/images/?title=' + title + '&ct=main')
	image_json = image.json()
	image_url = {'url': image_json["images"]}
	transform_url = 'https://create-a-map.herokuapp.com/api/picture?ht=400&wid=400&fit=crop&' + urllib.parse.urlencode(image_url)	# image transformer
	return transform_url

def hiking(title):
	"""Accepts a park title and formats the title for use in the All Trails widget"""
	hiking_title = title.lower()
	hiking_title=hiking_title.replace('_', '-')
	return hiking_title


if __name__ == "__main__":
	app.run(debug=True)