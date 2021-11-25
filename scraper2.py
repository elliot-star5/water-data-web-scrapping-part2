#!/usr/bin/env	python3


import time
from selenium import webdriver				# import webdriver to communicate with web browser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re									# extract with regular expression selection
from bs4 import BeautifulSoup				# to extract data with help of css selector
import csv									# to write csv file and do operation related to it.
import numpy as np							# to fastup process of array manipulation

# page hidden inside of site
secrete_page = None

# to search location
location_searcher = None

# searching location wrapper class
class getMeLocation:
	def __init__(self):
		# webbrowser driver
		self.driver = None
		# address of place 
		self.address = None

	def getwebbrowser(self):
		options = webdriver.ChromeOptions()
		# options.add_argument("--headless")
		self.driver = webdriver.Chrome(options=options)
		self.driver.get("https://www.gps-coordinates.net/")		# from which website we have to scrap data
		self.driver.execute_script("window.scrollBy(0,1700)")

	def setAddress(self, address):
		self.address = address		# set the address from where we have to get latitude and longitude
		self.driver.execute_script(f"document.getElementById('address').value = '{self.address}'")		# set city name 
		self.driver.execute_script("document.getElementsByClassName('btn btn-primary')[0].click()")		# click the Get GPS coordinate button

	def fetchLatitude(self):
		return self.driver.execute_script("return document.getElementById('latitude').value")		# to return latitude from javascript

	def fetchLongitude(self):
		return self.driver.execute_script("return document.getElementById('longitude').value")		# to return longitude from javascript


	def close(self):
		# close driver
		self.driver.close()



# secrete page 
class SecretePage:
	def __init__(self, driver):
		self.driver = driver
		self.file = open("output.csv", 'w', newline='')
		self.csvfile = csv.writer(self.file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		self.wait = WebDriverWait(self.driver, 100)

	# checked contaminants and clicks show
	def show_Contaminants_separately(self):
		self.driver.execute_script("document.getElementById('ContentPlaceHolder_chkAll').checked = true;" +
							"document.getElementById('ContentPlaceHolder_btnGO').click();")
		self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 
					"table.SNewFontReportTable th:nth-of-type(33)")))	
												# wait till 33 table data is loaded

	# pages before entrpy
	def pages_before_entry(self):
		time.sleep(4)
		length = int(self.driver.execute_script("return document.getElementById('tableReportTable').children[1].childElementCount;"))

		for out in range(length - 1):
			string_data = "ContentPlaceHolder_rpt_lnkSamples_" + str(out)
			self.wait.until(
				 EC.element_to_be_clickable((By.ID, string_data)))
			self.driver.execute_script(f"document.getElementById('{string_data}').click()")
			self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ContentPlaceHolder_chkAll")))
			self.show_Contaminants_separately()
			self.next_page()
 
	# check for clicked element is fully loaded 
	def sanity_check(self, data):
		while (True):
			color = self.driver.execute_script(f"return document.getElementById('ContentPlaceHolder_repIndex_lnkPages_{data}').style.color")
			if color != "red":
				time.sleep(2)
				continue
			break
		
	# cleaning up data for storing in csv format
	def clean_up(self):
		output = ''
		soup = BeautifulSoup(self.driver.page_source, 'html.parser')

		for data in soup.select('table.SNewFontReportTable tr td'):
			output += re.sub(' {2,}', '', BeautifulSoup.get_text(data)) + '|'
									# removes 2 or more space from data
		output = np.array(output[:-1].split('|'))
		output = output.reshape(len(output) // 33, 33)[:, 1:]


		# array to store latitude and longitude of cities
		new_array = []
		for searching_input in output:
			location_searcher.setAddress(searching_input[4])
			time.sleep(1)
			new_array.append(np.r_[output, np.array(location_searcher.fetchLatitude()), np.array(location_searcher.fetchLongitude())])
		return new_array



	# writes output into csvfile and traverse through number of page in secretepage
	def next_page(self):
		self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 
								"table.SNewFontReportTable th:nth-of-type(33)"))) # wait until table have 33 th
		length = int(self.driver.execute_script("return document.getElementsByClassName('lnkPages').length"))

		self.csvfile.writerows(self.clean_up())

		for data in range(1, length):
			self.driver.execute_script(f"document.getElementById('ContentPlaceHolder_repIndex_lnkPages_{data}').click()")
			self.sanity_check(data)
			self.csvfile.writerows(self.clean_up())

		self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
							 "table.SNewFontReportTable th:nth-of-type(33)")))				
														# wait till 33 table data is loaded
		self.driver.back()
		self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 
							"table.OuterReportTable")))	# wait till table.OuterReportTable loaded

	# close file before exit
	def close(self):
		self.driver.close()
		self.file.close()



# Get webbrowser with options
def get_webbrowser():
	url = "https://ejalshakti.gov.in/IMISReports/Reports/WaterQuality/rpt_WQM_SampleTesting_S.aspx?Rep=0&RP=Y"
	options = webdriver.ChromeOptions()
	options.add_argument('--incognito')
	#options.add_argument('--proxy-server="socks5://127.0.0.1:8080"')		# for proxy options
	#options.add_argument('--headless')		# to start in command line interface
	driver = webdriver.Chrome(options=options)
	driver.get(url)
	return driver


# get total number of element with given id
def get_length_from_id(driver, id_d):
	try:
		length = int(driver.execute_script("return document.getElementById('" + id_d + "').length"))
	except:
		driver.back()
		length = int(driver.execute_script("return document.getElementById('" + id_d + "').length"))
	return length

# selects elements by id and click it.
def get_data(id_d, id_num):
	return "document.getElementById('" + id_d  + "').selectedIndex = " + str(id_num) + ';' + "document.getElementById('ContentPlaceHolder_btnGO').click();" 
# clicks tested samples by id
def get_tested_samples_by_id(id_num):
	return f"document.getElementById('ContentPlaceHolder_rpt_lnkSamples_{id_num}').click()"





# parsing state by id
def get_state_district(driver):
	return parser(driver, "ContentPlaceHolder_ddState")


# parser parses through data 
def parser(driver, id_d):
	global secrete_page
	length = get_length_from_id(driver, id_d)

	# loop through states
	for data in range(1, length):
		driver.execute_script(get_data(id_d, data))
		secrete_page.pages_before_entry()
		time.sleep(4)
	

def main():
	try:
		# get webdriver
		driver = get_webbrowser()
		global secrete_page	
		secrete_page = SecretePage(driver)

		# create a location_searcher 
		location_searcher = getMeLocation()

		# start web browser for searcher window
		location_searcher.getwebbrowser()

		# traverse through whole options
		get_state_district(driver)

		# close driver and csv file
		secrete_page.close()
	# closes opened file
	finally:
		secrete_page.file.close()
		

if __name__ == '__main__':
	main()
