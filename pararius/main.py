# Library Imports
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import pandas as pd
import os
import json

# List of request headers, extracted & filtered from chrome dev tools
HEADERS = {}

######################################################################################################################
# Description: Returns an array of strings with the required URLs to scrape, with all filters applied & 
#              with a parameter specifying the total number of pages that need to be traversed.  
# Parameters:
#   baseUrl -> string: Its the base URL with the filters applied, such as min & max budget, interior types etc.
#   pageCount -> int: Total number of pages you want the scraper to traverse and get the results from.
# Returns: An array of strings with the required URLs which can be directly called. 
######################################################################################################################
def UrlList(baseUrl: str, pageCount: int, header=HEADERS) -> list[str]:
    # Try fetching URL and return an empty array if the response is not successful
    try:
        print("Fetching URL: ", baseUrl)
        response = requests.get(baseUrl, headers=header, allow_redirects=True)
        response.raise_for_status
    except:
        print("Error fetching URL: ", baseUrl)
        return []

    # Initializing my soup, nomnom
    siteHTML = BeautifulSoup(response.text, 'html.parser')

    # Get the inner string from 2nd last <li> element within a <ul> with class=pagination__list and convert it into an int
    maxPageCount = int(siteHTML.find_all("ul", class_="pagination__list")[0].find_all("li")[-2].a.string)

    if(pageCount > maxPageCount):
        print("There are only", maxPageCount, "pages of data available.")
        pageCount = maxPageCount # max number of pages to avoid duplicates

    urlList = []
    for i in range(pageCount):
        if i == 0:
            urlList.append(baseUrl)
            continue
        url = baseUrl + "/page-" + str(i+1)
        urlList.append(url)

    return urlList

######################################################################################################################
# Description: Fetches the HTML data from pararius.com with all the filters applied, page by page and parses
#              the different rental property listings and returns a 2D array with all the parsed info.
# Parameters:
#   city -> string: Name of the city where you want to search your rental properties in.
#   minPrice -> int: Minimum rental price for the properties you're interested in.
#   maxPrice -> int: Maximum rental price for the properties you're interested in.
#   interior -> string: The type of interior you want in your property i.e. Shell/Upholstered/Furnished
#   newPref  -> bool: The user preference if they only want new listings i.e. True if yes, otherwise False
# Returns: Returns a 2D array with all the parsed info in its appropriate format
######################################################################################################################
def fetchData(city="amsterdam", minPrice=0, maxPrice=60000,interior="", newPref=False, header=HEADERS):
    baseUrl = "https://www.pararius.com/apartments/" + city + "/" + str(minPrice) + "-" + str(maxPrice)
    
    if(len(interior) != 0):
        baseUrl += "/" + interior

    pageCount = 1 

    urlList = UrlList(baseUrl, pageCount, header=header)

    excelData = []
    for url in urlList:
        try:
            print("Fetching URL: ", url)
            response = requests.get(url, headers=header)
            response.raise_for_status
        except:
            print("Error fetching URL: ", baseUrl)
            continue
        
        # Initializing my soup, nomnom
        responseHTML = BeautifulSoup(response.text, 'html.parser')
        listingsSection = responseHTML.find_all("li", class_="search-list__item search-list__item--listing")

        for listing in listingsSection:
            # Extracting listing's name
            listingName = (listing.section.h2.a.string).strip()
            # Extracting listing's status (New/Highlighted/Rented Under Options ...)
            listingLabelHTML = listing.section.find("div", class_="listing-search-item__label")
            listingStatus = ( (listingLabelHTML.span.string).strip() if listingLabelHTML != None else "")
            # If listing is not new and user is only interested in new listings then skip this listing!
            if("new" not in listingStatus.lower() and newPref):
                continue

            # Extracting listing's rent amount, removing commas, "per month" keyword and € sign to get just the number
            listingRentAmount = int((listing.section.find("div", class_="listing-search-item__price").string).strip().split("per")[0].split("€")[1].strip().replace(",",""))

            # Extracting listing's surface area, number of rooms and interior type
            listingFeatures = listing.section.find("div", class_="listing-search-item__features").ul.find_all("li")
            listingSurfaceArea = (listingFeatures[0].string).strip()
            listingNumberOfRooms = (listingFeatures[1].string).strip()
            listingInterior = (listingFeatures[2].string).strip()

            # Extracting listing's Pin Code and location
            listingLocation = (listing.section.find("div", class_="listing-search-item__sub-title'").string).strip()

            # Extracting listing's pararius link
            listingLink = "https://www.pararius.com" + listing.section.h2.a["href"]

            # Extracting listing's estate agent details, name and agent link
            listingEstateAgent = listing.section.find("div", class_="listing-search-item__info").a
            listingEstateAgentName = (listingEstateAgent.string).strip()
            listingEstateAgentLink = "https://www.pararius.com" + listingEstateAgent["href"]

            listingData = [listingName, listingStatus, listingRentAmount, listingSurfaceArea, listingNumberOfRooms, listingInterior, listingLocation, listingLink, listingEstateAgentName, listingEstateAgentLink]
            excelData.append(listingData)

    if(len(urlList) >= 5):
        print("Phew! that was a lot of scraping. I'll need a coffee after this':)")

    return excelData
