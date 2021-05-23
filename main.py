# Author: Karen Black
# Last Modified: May 16, 2021
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
	maps = []						# to store map scripts
	headers = []					# headers for comparison page
	nps_web = []					# NPS websites

	# get the values (park names) submitted for comparison
	if request.method == 'POST':
		titles_all = request.form.getlist('parkToggle')
	# 	print("!!!!Title!!!!", titles_all)
	

	# repeat series of calls to microservices for each value (park name)
	for index in range(len(titles_all)):
		title = titles_all[index]
		#print("!!!!Title!!!!", title)
	
		# **** GEOLOGY PARAGRAPHS (text-scraper) *****
		try:
			geo = requests.get('https://wiki-text-scraper.herokuapp.com/wiki/' + title + '/Geology')
			print("****GEO*****", title)
			geo_json = geo.json()
			geo = geo_json["Geology"]
			geo_text = geo.replace('\n', '<br> </br>')
			# geo_text = re.sub(r'\[.*?\]+', '', geo)     #for removing footnotes from text, patrick's scraper now implements
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
		# print("!!!!Geology!!!!", geo_text)
		geol.append(geo_text)


		# **** INFOBOX QUERY FOR TITLES (text-scraper) ****
		try:
			infobox = requests.get('https://wiki-text-scraper.herokuapp.com/wiki/' + title + '/infobox')

			info_json = infobox.json()
		except:
			info_json = [title]

		# get park Name		
		parkName = info_json[0]
		tags = ['National Park and Preserve', 'National Park']
		for tag in tags:
			if tag in parkName:
				parkName = parkName.replace(tag, '')
		headers.append(parkName)

		# *** INFOBOX SCRAPING (my API) ****
		# get estabilished date
		try:
			resp = requests.get('https://wiki-image-scraper.herokuapp.com/api/infobox/?title=' + title + '&fld=est')
			resp_json = resp.json()
			estab.append(resp_json["infobox"])
		except:
			estab.append('Not Provided')
		# print("******", estab)

		# get park visitors
		try:
			resp = requests.get('https://wiki-image-scraper.herokuapp.com/api/infobox/?title=' + title + '&fld=vis')
			resp_json = resp.json()
			visitors.append(resp_json["infobox"])
		except:
			visitors.append('Not Provided')
		# print("******", visitors)
		
		# get NPS websites
		try:
			resp = requests.get('https://wiki-image-scraper.herokuapp.com/api/infobox/?title=' + title + '&fld=web')
			resp_json = resp.json()
			nps_web.append(resp_json["infobox"])
		except:
			nps_web.append('Not Provided')
		# print("******", nps_web)

		# **** GPS COORDINATES (text scraper) ****
		resp = requests.get('https://wiki-text-scraper.herokuapp.com/wiki/' + title + '/coords')
		resp_json = resp.json()
		# coords = {"lat": float(resp_json["lat"]), "lon": float(resp_json["lon"])}

		# **** MAP SCRIPT (mapping service) ****
		# coords = {"lat": float(resp_json["lat"]), "lon": float(resp_json["lon"])}
		# id = "map"+str(index)
		# data = {"key": "gRX53OwxCKxC3v1yQrvE", "id": id, "map": {"title": title, "coordinates": coords}}
		# print("!!!!!!mapData", data)
		# resp = requests.post('https://easy-map-maker.herokuapp.com/', json=data)
		# resp_json = resp.json()
		# # print("***Map", resp_json)
		# maps.append(resp_json["script"])
		# print("*****maps", maps[index])

		# ALTERNATIVE MAP APPROACH
		coords = [float(resp_json["lat"]), float(resp_json["lon"])]
		maps.append(coords)
		# print("*****maps", maps[index])

	# **** IMAGES (image-scraper) *****
		image= requests.get('https://wiki-image-scraper.herokuapp.com/api/images/?title=' + title + '&ct=main')
		image_json = image.json()
		# print("!!!!image_JSON!!!!", image_json)
		image_url = {'url': image_json["images"]}
		transform_url = 'https://create-a-map.herokuapp.com/api/picture?ht=400&wid=400&fit=crop&' + urllib.parse.urlencode(image_url)	# image transformer
		# print("!!!!transform!!!!", transform_url)
		image_urls.append(transform_url)


	#render the webpage
	return render_template("compare.html", urls=image_urls, title=headers, web=nps_web, vis=visitors, est=estab, geo=geol, map=maps)



if __name__ == "__main__":
	app.run(debug=True)