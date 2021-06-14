#Quelle für Scrapper als Basis: https://github.com/gustafvh/Apartment-ML-Predictor-Stockholm_-with-WebScraper-and-Data-Insights
#Anpassungen durch Gruppe, damit es wieder funktioniert -> Scrapper für Hemnet und API Yelp. 

import pandas as pd
import numpy as np

from WebScraper.WebScraper import *
from ProcessData import cleanAndConvertToNum, removeOutliers, removeWrongCoordinates, addPricePerSizeColumn
from YelpApi import updateDfWithYelpDetails

import time

#Webscraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#Yelp API 
from yelpapi import YelpAPI

#Functions

def getRowsFromHnet(driver, numberOfPages):
    # One page is 50 rows
    # driver = initCrawler(20, 25)

    apData = pd.DataFrame()
    apData = getMultiplePages(driver, numberOfPages)

    return apData


def writeToCsv(dataframe):
    dataframe.to_csv('hnetData.csv', index=False)


def getAllSegments():
    apData = pd.DataFrame()
    segments = [90, 95, 100]
    #segments = [91, 92]

    for i in range(0, (len(segments)-1)):
        driver = initCrawler(segments[i], segments[i+1])
        apDataNew = getRowsFromHnet(driver, 50)
        apData = apData.append(apDataNew, ignore_index=True)
        
    apData.to_csv('./Data/hnetData.csv', index=False)
    
    return apData

def initCrawler(minSize, maxSize):

    minSize = str(minSize)
    maxSize = str(maxSize)

    options = Options()
    #options.add_argument("--incognito")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(executable_path="chromedriver.exe", options=options)

    # url = "https://www.hemnet.se/salda/bostader?housing_form_groups%5B%5D=apartments&location_ids%5B%5D=18031&page=1"

    url = "https://www.hemnet.se/salda/bostader?location_ids%5B%5D=18031&item_types%5B%5D=bostadsratt&rooms_min=3.5&rooms_max=4.5&living_area_min=" + \
        minSize + "&living_area_max=" + maxSize + "&sold_age=all"
      
    driver.get(url)
    #driver.implicitly_wait(10)
    time.sleep(5) 
    #driver.find_element_by_xpath("//*[contains(text(), 'Jag samtycker')]").click()
    
    #css=.consent__button-wrapper > .hcl-button--primary |
    #self.driver.find_element(By.CSS_SELECTOR, ".consent__button-wrapper > .hcl-button--primary").click()
    # Click Privacy Policy pop-up
    consentButton = driver.find_elements_by_css_selector(".consent__button-wrapper > .hcl-button--primary")
       
    consentButton[0].click()

    return driver


def getAllApartmentsInPage(driver):

    # Get all listings-objects on page
    apListings = driver.find_elements_by_css_selector(
        ".sold-property-listing")

    apDate, apAdress, apSize, apRooms, apBroker, apRent, apPrice = [], [], [], [], [], [], []

    for i, listing in enumerate(apListings):

        # SalesDate
        date = listing.find_elements_by_css_selector(
            ".sold-property-listing__sold-date")
        apDate.append('Unknown') if len(
            date) == 0 else apDate.append(date[0].text.replace('Såld ', '').strip())

        # Adress
        adress = listing.find_elements_by_css_selector(
            ".item-result-meta-attribute-is-bold")
        apAdress.append('Unknown') if len(
            adress) == 0 else apAdress.append(adress[0].text.strip())

        # Size & Rooms
        both = listing.find_elements_by_css_selector(
            ".sold-property-listing__subheading")
        both = both[0].text.split('  ')
        size = both[0][:-3]

        # If rooms field wasn't found
        if both[1]:
            room = both[1][1].replace(' rum', '')
        else:
            room = 'Unknown'

        apSize.append('Unknown') if len(
            size) == 0 else apSize.append(size)
        apRooms.append('Unknown') if len(
            room) == 0 else apRooms.append(room)

        # Realtor
        broker = listing.find_elements_by_css_selector(
            ".sold-property-listing__broker")
        apBroker.append('Unknown') if len(
            broker) == 0 else apBroker.append(broker[0].text.strip())

        # Charge / Operations Costs
        rent = listing.find_elements_by_css_selector(
            ".sold-property-listing__fee")
        apRent.append('Unknown') if len(
            rent) == 0 else apRent.append(rent[0].text.replace(' kr/mån', '').replace(' ', ''))

        # Price
        price = listing.find_elements_by_css_selector(
            ".sold-property-listing__subheading")
        # price = price[0].text.split('\n')[0]
        if len(price) == 0 or len(price) == 1:
            apPrice.append('Unknown')
        else:
            apPrice.append(price[1].text.replace(
                'Slutpris ', '').replace('kr', '').replace(' ', ''))

    totalData = [apDate, apAdress,
                 apSize, apRooms, apBroker, apRent, apPrice]

    print(totalData)

    totalDataFrame = createDataframe(totalData)

    return totalDataFrame


def getMultiplePages(driver, numberOfPages):
    apD = pd.DataFrame()
    for i in range(0, numberOfPages):

        # Get all apartments at this page
        newApData = getAllApartmentsInPage(driver)

        apD = apD.append(newApData, ignore_index=True)

        # Scroll to bottom of page
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        # Click Next Page Button
        nextButton = driver.find_elements_by_css_selector(
            ".next_page")
        nextButton[0].click()

    return apD


def createDataframe(apColumns):

    apColumns = {
        'Date': apColumns[0],
        'Adress': apColumns[1],
        'Size': apColumns[2],
        'Rooms': apColumns[3],
        'Broker': apColumns[4],
        'Rent': apColumns[5],
        'Price': apColumns[6],
    }

    apDf = pd.DataFrame(data=apColumns)

    return apDf


def getDetailsFromAdress(adress):
    adress = adress + " stockholm"
    yelp_api = YelpAPI(
        "7s_bYIDTC8bIvaZ1GarIhtAsBULdpE4Y4ShtkgYHQFTo9eezCauxrP56dk9VJGzEDqQUaMAWMdEvhG-ygssGQh3-7tTHW6R7jIh4EWcgw-QkLX5UMpe_HL73fqvEYHYx")
    response = yelp_api.search_query(cc='se', location=adress, radius=2000, limit=1)
    #print(response)
    if 'error' in response: # Check if there is a key called "error"
        #return ('0.0', '0.0', '0.0')
        if response['error'].get('code') != 'LOCATION_NOT_FOUND':
        # A different code, should probably log this.
            print('Location error on row ', i)
            return ('0', '0', '0')

    else:
        latitude = response['region']['center']['latitude']
        longitude = response['region']['center']['longitude']
        pointsOfInterestsNearby = response['total']
        return (latitude, longitude, pointsOfInterestsNearby)


def updateDfWithYelpDetails(df, fromRow, toRow):

    # Add columns for NearbyPOIs, Latitude and Longitude
    df['NearbyPOIs'] = 0.0
    df['Latitude'] = 0.0
    df['Longitude'] = 0.0
    
    #Name anpassen
    name = './Data/'+'yelpData' + str('1') + "-" + str(toRow) + ".csv"

    df = df.reset_index(drop=True)

    for i in range(fromRow, toRow):
        df.to_csv(name, index=False)
        adress = df.at[i, 'Adress']
        print('Getting Yelp details for', adress, 'on row', i)

        yelpResponse = getDetailsFromAdress(adress)

        df.at[i, 'Latitude'] = yelpResponse[0]
        df.at[i, 'Longitude'] = yelpResponse[1]
        df.at[i, 'NearbyPOIs'] = yelpResponse[2]

    df['NearbyPOIs'] = df['NearbyPOIs'].astype('float')


def cleanData():
    apData = pd.read_csv('./Data/hnetData.csv')

    apData = cleanAndConvertToNum(apData)

    apData.to_csv('./Data/CleanHnetData.csv', index=False)


def GetData():
    # Step 1.1 - Get all data from hNet
    getAllSegments()

    # Step 1.2 - Clean data with formatting and output to new csv file
    cleanData()

    # Step 1.3 - Read CSV and make import and add Yelp Data
    apData = pd.read_csv('./Data/CleanHnetData.csv')
    apData = updateDfWithYelpDetails(apData, 0, 4927)
    
    # Step 1.4 Save Final clean File
    apData.to_csv('./Data/ScrappedDataClean.csv', index=False)

    
#Start with GetData()
def main():

    # main step - Run preProcess who gets, cleans, and processes data used. Outputs file
    GetData()

main()