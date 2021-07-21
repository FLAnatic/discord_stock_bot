#!/usr/bin/env python3
# bot.py
from asyncio.windows_events import NULL
import os
import discord
from discord.ext import commands, tasks
import http.client
import re
import json
from typing import List,Dict
import math
from sys import exit
import schedule
import time
import datetime
import pandas as pd
import mplfinance as mpf
import random
import numpy as np

testing = False

help_text = """

**Commands**
    ! is the prefix for all bot commands.
    !movers
    !chart
    !random
    !help
**Inline Features**
    The bot looks at every message in the chat room it is in for stock symbols. Symbols start with a
    `$` followed by the stock symbol. For example: $gme will return data for Gamestop Corp.
    Market data is provided by [Yahoo! Finance](https://rapidapi.com/apidojo/api/yahoo-finance1)
    """

# Get token for discord
try:
    tokenFile = open("token.txt", 'r')
except OSError:
    print("Could not open/read token file.")
    exit()

with tokenFile:
    TOKEN = tokenFile.readline()

# Get rapid api key to access yahoo finance api
try:
    rapidapikeyFile = open('rapidapikey.txt', 'r')
except OSError:
    print("Could not open/read Raid API key file.")
    sys.exit()

with rapidapikeyFile:
    RAPIDAPIKEY = rapidapikeyFile.readline()

# Get whale api key to access yahoo finance api
WHALEALERTAPIKEY = None
try:
    whalealertapikeyFile = open('whalealertapikey.txt', 'r')
    with whalealertapikeyFile:
        WHALEALERTAPIKEY = whalealertapikeyFile.readline()
except OSError:
    print("Could not open/read Whale alert API key file. Whale Alert functionality disable.")


# headers used for all rapid api yahoo finance connection requests
headers = {
    'x-rapidapi-key': RAPIDAPIKEY,
    'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com"
}

waHeaders = {
    'x-wa-api-key': WHALEALERTAPIKEY,
    #'x-wa-api-host': "api.whale-alert.io"
}

# create folders for stored images
chartsFolder = r'charts' 
if not os.path.exists(chartsFolder):
    os.makedirs(chartsFolder)

imagesFolder = r'images' 
if not os.path.exists(imagesFolder):
    os.makedirs(imagesFolder)

# Load list of stock symbols used for !rand command
# file generated here : https://www.nasdaq.com/market-activity/stocks/screener
stockListFileName = 'nasdaq_screener.csv'
try:
    stocks = pd.read_csv('nasdaq_screener.csv', index_col=0)
    stockListLen = len(stocks.index)
except:
    stockListLen = 0
    print("Could not open/read stock list csv file.")

def fetchSymbolData(symbol):
    """ make a stock symbol query request to yahoo finance and return entire contents of message returned """
    conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
    url = f"/stock/v2/get-summary?symbol={symbol}&region=US"
    try:
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
    except:
        message = f"An error occured trying to retrive information for ${symbol}. Could not get a response from the remote server."
        return None
  
    if(res.code == 200):
        return res.read()
    else:
        return None

def find_symbols(text: str) -> List[str]:
    """ find all potential stock symbols starting with $ as a list."""
    SYMBOL_REGEX = "[$]([a-zA-Z0-9.=-]{1,9})"
    return list(set(re.findall(SYMBOL_REGEX, text)))

def Do_Equity_Reply(jsonData):
    """ formulate a reply specifically for an equity quote type """
    try:
        quoteType = jsonData["quoteType"]["quoteType"]
        symbol = jsonData["quoteType"]["symbol"]
        marketState = jsonData["price"]["marketState"]
        price = jsonData["price"]["regularMarketPrice"]["fmt"]
        currency = jsonData["price"]["currency"]
        currencySymbol = jsonData["price"]["currencySymbol"]
        exchange = jsonData["price"]["exchangeName"]
        try:
            shortName = jsonData["quoteType"]["shortName"]
        except:
            shortName = symbol
        try:
            longName = jsonData["quoteType"]["longName"]
        except:
            longName = shortName
        print("Equity Reply: ",longName, price)
        try:
            preMarketPrice = jsonData["price"]["preMarketPrice"]["fmt"]
            preMarketChangeRaw = jsonData["price"]["preMarketChange"]["raw"]
            preMarketChange = jsonData["price"]["preMarketChange"]["fmt"]
            preMarketChangePct = jsonData["price"]["preMarketChangePercent"]["fmt"]
            preMarketGain = False
            if preMarketChangeRaw >= 0:
                preMarketChange = "+" + preMarketChange
                preMarketChangePct = "+" + preMarketChangePct
                preMarketGain = True
        except:
            preMarketPrice = price
            preMarketChange = "N/A"
            preMarketChangePct = "N/A"
        try:
            postMarketPrice = jsonData["price"]["postMarketPrice"]["fmt"]
            postMarketChangeRaw = jsonData["price"]["postMarketChange"]["raw"]
            postMarketChange = jsonData["price"]["postMarketChange"]["fmt"]
            postMarketChangePct = jsonData["price"]["postMarketChangePercent"]["fmt"]
            postMarketGain = False
            if postMarketChangeRaw >= 0:
                postMarketChange = "+" + postMarketChange
                postMarketChangePct = "+" + postMarketChangePct
                postMarketGain = True

        except:
            postMarketPrice = price
            postMarketChange = "N/A"
            postMarketChangePct = "N/A"
        try:
            industry = jsonData["summaryProfile"]["industry"]
            sector = jsonData["summaryProfile"]["sector"]
        except:
            industry = "N/A"
            sector = "N/A"
        try:
            regularMarketDayLow = jsonData["price"]["regularMarketDayLow"]["fmt"]
            regularMarketDayHigh = jsonData["price"]["regularMarketDayHigh"]["fmt"]
            regMktDayRng = str(regularMarketDayLow) + \
                                " - " + str(regularMarketDayHigh)
            regularMarketDayChange = jsonData["price"]["regularMarketChange"]["fmt"]
            regularMarketDayChangeRaw = jsonData["price"]["regularMarketChange"]["raw"]
            regularMarketDayChangePct = jsonData["price"]["regularMarketChangePercent"]["fmt"]
            regularMarketDayChangePctRaw = jsonData["price"]["regularMarketChangePercent"]["raw"]
            regularMarketDayGain = False
            if regularMarketDayChangeRaw >= 0:
                regularMarketDayChange = "+" + regularMarketDayChange
                regularMarketDayChangePct = "+" + regularMarketDayChangePct
                regularMarketDayGain = True
        except:
            regMktDayRng = "N/A"
            regularMarketDayChange = "N/A"
            regularMarketDayChangePct = "N/A"

        try:
            fiftyTwoWeekLow = jsonData["summaryDetail"]["fiftyTwoWeekLow"]["fmt"]
            fiftyTwoWeekHigh = jsonData["summaryDetail"]["fiftyTwoWeekHigh"]["fmt"]
            fiftyTwoWeekRange = str(
                fiftyTwoWeekLow) + " - " + str(fiftyTwoWeekHigh)
        except:
            fiftyTwoWeekRange = "N/A"
        try:
            enterpriseToEbitda = jsonData["defaultKeyStatistics"]["enterpriseToEbitda"]["fmt"]
        except:
            enterpriseToEbitda = "N/A"
        try:
            marketCap = jsonData["price"]["marketCap"]["fmt"]
        except:
            marketCap = "N/A"
        try:
            trailingPERaw = jsonData["summaryDetail"]["trailingPE"]["raw"]
            trailingPEFmt = jsonData["summaryDetail"]["trailingPE"]["fmt"]
            if 0 <= trailingPERaw <= 15:
                peColor = ':green_circle:'
            elif trailingPERaw < 0 or trailingPERaw > 50:
                peColor = ':red_circle:'
            else:
                peColor = ':yellow_circle:'
            trailingPE = trailingPEFmt + peColor
        except:
            trailingPE = "N/A"
        try:
            pegRatioRaw = jsonData["defaultKeyStatistics"]["pegRatio"]["raw"]
            pegRatioFmt = jsonData["defaultKeyStatistics"]["pegRatio"]["fmt"]
            if 0 <= pegRatioRaw <= 1:
                pegColor = ':green_circle:'
            elif pegRatioRaw < 0 or pegRatioRaw > 2:
                    pegColor = ':red_circle:'
            else:
                pegColor = ':yellow_circle:'
            pegRatio = pegRatioFmt + pegColor
        except:
            pegRatio = "N/A"
        try:
            priceToBookRaw = jsonData["defaultKeyStatistics"]["priceToBook"]["raw"]
            priceToBookFmt = jsonData["defaultKeyStatistics"]["priceToBook"]["fmt"]
            if 0 <= priceToBookRaw <= 2:
                priceToBookColor = ':green_circle:'
            elif priceToBookRaw < 0 or priceToBookRaw > 5:
                priceToBookColor = ':red_circle:'
            else:
                priceToBookColor = ':yellow_circle:'
            priceToBook = priceToBookFmt + priceToBookColor
        except:
            priceToBook = "N/A"
        try:

            priceToSalesRaw = jsonData["summaryDetail"]["priceToSalesTrailing12Months"]["raw"]
            priceToSalesFmt = jsonData["summaryDetail"]["priceToSalesTrailing12Months"]["fmt"]
            if 0 <= priceToSalesRaw <= 2:
                priceToSalesColor = ':green_circle:'
            elif priceToSalesRaw < 0 or priceToSalesRaw > 10:
                priceToSalesColor = ':red_circle:'
            else:
                priceToSalesColor = ':yellow_circle:'
            priceToSales = priceToSalesFmt + priceToSalesColor
        except:
            priceToSales = "N/A"
        try:
            dividendRate = jsonData["summaryDetail"]["dividendRate"]["fmt"]
            dividendYield = jsonData["summaryDetail"]["dividendYield"]["fmt"]
        except:
            dividendRate = "N/A"
            dividendYield = "N/A"
        try:
            beta = jsonData["summaryDetail"]["beta"]["fmt"]
        except:
            beta = "N/A"

        insiderPurchases = "N/A"
        try:
            buyInfoShares = jsonData["netSharePurchaseActivity"]["buyInfoShares"]["fmt"]
        except:
            buyInfoShares = "N/A"
        try:
            buyInfoCount = jsonData["netSharePurchaseActivity"]["buyInfoCount"]["fmt"]
        except:
            buyInfoCount = "N/A"
        try:
            sellInfoShares = jsonData["netSharePurchaseActivity"]["sellInfoShares"]["fmt"]
        except:
            sellInfoShares = "N/A"
        try:
            sellInfoCount = jsonData["netSharePurchaseActivity"]["sellInfoCount"]["fmt"]
        except:
            sellInfoCount = "N/A"
        try:
            insiderPercentHeld = jsonData["majorHoldersBreakdown"]["insidersPercentHeld"]["fmt"]
        except:
            insiderPercentHeld = "N/A"
        try:
            institutionPercentHeld = jsonData["majorHoldersBreakdown"]["institutionsPercentHeld"]["fmt"]
        except:
            institutionPercentHeld = "N/A"
        try:
            shortPercentOfFloat = jsonData["defaultKeyStatistics"]["shortPercentOfFloat"]["fmt"]
        except:
            shortPercentOfFloat = "N/A"

        insiderPurchases = (f"Purchases: {buyInfoShares} shares in {buyInfoCount} transactions.\r\n" +
                            f"Sales: {sellInfoShares} shares in {sellInfoCount} transactions.")
                        
        insiderSymbol = symbol.replace('-','')
        insiderHolding = (f"% Held by Insiders: {insiderPercentHeld}.\r\n" +
                            f"% Held by Institutions: {institutionPercentHeld}.\r\n" +
                            f"Short % of Float: {shortPercentOfFloat}.\r\n"
                            f"http://www.openinsider.com/{insiderSymbol}")

        emojiIndicator = ""
        try:
            if regularMarketDayChangePctRaw > 0.05:
                emojiIndicator = ":rocket:"
            if regularMarketDayChangePctRaw > 0.25:
                emojiIndicator += ":full_moon:"
            if regularMarketDayChangePctRaw < -0.05:
                emojiIndicator = ":skull:"
            if regularMarketDayChangePctRaw < -0.25:
                emojiIndicator += ":skull:"
        except:
            emojiIndicator = ""

        description = f"**{currencySymbol}{price}** ({regularMarketDayChange},{regularMarketDayChangePct}) {emojiIndicator}"
        if marketState == "POST":
            description += f"\n*Post-market: {currencySymbol}{postMarketPrice} ({postMarketChange},{postMarketChangePct})*"
        elif marketState == "PRE":
            description += f"\n*Pre-market: {currencySymbol}{preMarketPrice} ({preMarketChange},{preMarketChangePct})*"
        description += f"\nExhange: {exchange}\nCurrency: {currency}"

        message = discord.Embed(title=str(longName).upper() + f" ({symbol})", url=f"https://finance.yahoo.com/quote/{symbol}",
                                description=description,
                                color=0xFF5733)
        message.add_field(name="Quote Type",
                            value=quoteType, inline=True)
        if industry != "N/A":
            message.add_field(name="Industry", value=industry, inline=True)
        if sector != "N/A":
            message.add_field(name="Sector", value=sector, inline=True)
        if marketCap != "N/A":
            message.add_field(name="Market Cap", value=marketCap, inline=True)
        if regMktDayRng != "N/A":
            message.add_field(name="Regular Market Day Range", value=regMktDayRng, inline=True)
        if fiftyTwoWeekRange != "N/A":
            message.add_field(name="Last 52 Week Range", value=fiftyTwoWeekRange, inline=True)
        if trailingPE != "N/A":
            message.add_field(name="PE Ratio (TTM)", value=trailingPE, inline=True)
        if pegRatio != "N/A":
            message.add_field(name="PEG Ratio", value=pegRatio, inline=True)
        if priceToBook != "N/A":
            message.add_field(name="Price to Book", value=priceToBook, inline=True)
        if priceToSales != "N/A":
            message.add_field(name="Price to Sales", value=priceToSales, inline=True)
        if enterpriseToEbitda != "N/A":
            message.add_field(name="EV/EBITDA", value=enterpriseToEbitda, inline=True)
        if beta != "N/A":
            message.add_field(name="beta", value=beta, inline=True)

        if quoteType != "CURRENCY" and quoteType != "CRYPTOCURRENCY":
            rateAndYield = str(dividendRate) + \
                                " (" + str(dividendYield) + ")"
            message.add_field(name="Dividend Rate and Yield",
                                value=rateAndYield, inline=True)

            message.add_field(name="Share Statistics",
                                value=insiderHolding, inline=False)
            morningstarSymbol = symbol.replace('-','.')
            message.add_field(name="MorningStar Key Ratios",
                                value=f"http://financials.morningstar.com/ratios/r.html?t={morningstarSymbol}", inline=False)
    except:
        message = f"Could not find information for ${symbol}. Perhaps it is not an EQUITY or maybe I'm parsing the data poorly...."
    
    return message

def Do_ETF_Reply(jsonData: dict):
    """ formulate a reply specifically for an ETF quote type """
    try:
        quoteType = jsonData["quoteType"]["quoteType"]
        symbol = jsonData["quoteType"]["symbol"]
        marketState = jsonData["price"]["marketState"]
        price = jsonData["price"]["regularMarketPrice"]["fmt"]
        currency = jsonData["price"]["currency"]
        currencySymbol = jsonData["price"]["currencySymbol"]
        exchange = jsonData["price"]["exchangeName"]
        try:
            shortName = jsonData["quoteType"]["shortName"]
        except:
            shortName = symbol
        try:
            longName = jsonData["quoteType"]["longName"]
        except:
            longName = shortName
        print("ETF Reply: ",longName, price)
        try:
            preMarketPrice = jsonData["price"]["preMarketPrice"]["fmt"]
            preMarketChangeRaw = jsonData["price"]["preMarketChange"]["raw"]
            preMarketChange = jsonData["price"]["preMarketChange"]["fmt"]
            preMarketChangePct = jsonData["price"]["preMarketChangePercent"]["fmt"]
            preMarketGain = False
            if preMarketChangeRaw >= 0:
                preMarketChange = "+" + preMarketChange
                preMarketChangePct = "+" + preMarketChangePct
                preMarketGain = True
        except:
            preMarketPrice = price
            preMarketChange = "N/A"
            preMarketChangePct = "N/A"
        try:
            postMarketPrice = jsonData["price"]["postMarketPrice"]["fmt"]
            postMarketChangeRaw = jsonData["price"]["postMarketChange"]["raw"]
            postMarketChange = jsonData["price"]["postMarketChange"]["fmt"]
            postMarketChangePct = jsonData["price"]["postMarketChangePercent"]["fmt"]
            postMarketGain = False
            if postMarketChangeRaw >= 0:
                postMarketChange = "+" + postMarketChange
                postMarketChangePct = "+" + postMarketChangePct
                postMarketGain = True
        except:
            postMarketPrice = price
            postMarketChange = "N/A"
            postMarketChangePct = "N/A"

        try:
            regularMarketDayLow = jsonData["price"]["regularMarketDayLow"]["fmt"]
            regularMarketDayHigh = jsonData["price"]["regularMarketDayHigh"]["fmt"]
            regMktDayRng = str(regularMarketDayLow) + \
                                " - " + str(regularMarketDayHigh)
            regularMarketDayChange = jsonData["price"]["regularMarketChange"]["fmt"]
            regularMarketDayChangeRaw = jsonData["price"]["regularMarketChange"]["raw"]
            regularMarketDayChangePct = jsonData["price"]["regularMarketChangePercent"]["fmt"]
            regularMarketDayChangePctRaw = jsonData["price"]["regularMarketChangePercent"]["raw"]
            regularMarketDayGain = False
            if regularMarketDayChangeRaw >= 0:
                regularMarketDayChange = "+" + regularMarketDayChange
                regularMarketDayChangePct = "+" + regularMarketDayChangePct
                regularMarketDayGain = True
        except:
            regMktDayRng = "N/A"
            regularMarketDayChange = "N/A"
            regularMarketDayChangePct = "N/A"

        try:
            fiftyTwoWeekLow = jsonData["summaryDetail"]["fiftyTwoWeekLow"]["fmt"]
            fiftyTwoWeekHigh = jsonData["summaryDetail"]["fiftyTwoWeekHigh"]["fmt"]
            fiftyTwoWeekRange = str(
                fiftyTwoWeekLow) + " - " + str(fiftyTwoWeekHigh)
        except:
            fiftyTwoWeekRange = "N/A"

        try:
            marketCap = jsonData["price"]["marketCap"]["fmt"]
        except:
            marketCap = "N/A"

        try:
            beta = jsonData["defaultKeyStatistics"]["beta3Year"]["fmt"]
        except:
            beta = "N/A"
        try:
            fundInceptionDate = jsonData["defaultKeyStatistics"]["fundInceptionDate"]["fmt"]
        except:
            fundInceptionDate = "N/A"
        try:
            fundFamily = jsonData["fundProfile"]["family"]
        except:
            fundFamily = "N/A"
        try:
            totalAssets = jsonData["defaultKeyStatistics"]["totalAssets"]["fmt"]
        except:
            totalAssets = "N/A"
        try:
            fundYield = jsonData["summaryDetail"]["yield"]["fmt"]
        except:
            fundYield = "N/A"
        try:
            ytdReturn = "N/A"
            if jsonData["fundPerformance"]["trailingReturns"]["ytd"]["raw"]:
                ytdReturn = jsonData["fundPerformance"]["trailingReturns"]["ytd"]["fmt"]
        except:
            ytdReturn = "N/A"
        try:
            oneYearAverageReturn = "N/A"
            if jsonData["fundPerformance"]["trailingReturns"]["oneYear"]["raw"]:
                oneYearAverageReturn = jsonData["fundPerformance"]["trailingReturns"]["oneYear"]["fmt"]
        except:
            oneYearAverageReturn = "N/A"
        try:
            threeYearAverageReturn = "N/A"
            if jsonData["fundPerformance"]["trailingReturns"]["threeYear"]["raw"]:
                threeYearAverageReturn = jsonData["fundPerformance"]["trailingReturns"]["threeYear"]["fmt"]
        except:
            threeYearAverageReturn = "N/A"
        try:
            fiveYearAverageReturn = "N/A"
            if jsonData["fundPerformance"]["trailingReturns"]["fiveYear"]["raw"]:
                fiveYearAverageReturn = jsonData["fundPerformance"]["trailingReturns"]["fiveYear"]["fmt"]
        except:
            fiveYearAverageReturn = "N/A"
        try:
            tenYearAverageReturn = "N/A"
            if jsonData["fundPerformance"]["trailingReturns"]["tenYear"]["raw"]:
                tenYearAverageReturn = jsonData["fundPerformance"]["trailingReturns"]["tenYear"]["fmt"]
        except:
            tenYearAverageReturn = "N/A"
        try:
            styleBox = jsonData["fundProfile"]["styleBoxUrl"]
        except:
            styleBox = ""
        try:
            expenses = jsonData["fundProfile"]["feesExpensesInvestment"]["annualReportExpenseRatio"]["fmt"]
        except:
            expenses = "N/A"

        compositionString = "N/A" 
        try:
            stockPosition = jsonData["topHoldings"]["stockPosition"]["fmt"]
            if jsonData["topHoldings"]["stockPosition"]["raw"]:
                compositionString = "Stocks: " + stockPosition
        except:
            stockPosition = "N/A"
        try:
            bondPosition = jsonData["topHoldings"]["bondPosition"]["fmt"]
            if jsonData["topHoldings"]["bondPosition"]["raw"]:
                compositionString += "\r\nBonds: " + bondPosition
        except:
            bondPosition = "N/A"

        try:
            preferredPosition = jsonData["topHoldings"]["preferredPosition"]["fmt"]
            if jsonData["topHoldings"]["preferredPosition"]["raw"]:
                compositionString += "\r\nPreferred: " + preferredPosition
        except:
            preferredPosition = "N/A"
        try:
            convertiblePosition = jsonData["topHoldings"]["convertiblePosition"]["fmt"]
            if jsonData["topHoldings"]["convertiblePosition"]["raw"]:
                compositionString += "\r\nConvertible: " + convertiblePosition
        except:
            convertiblePosition = "N/A"
        try:
            cashPosition = jsonData["topHoldings"]["cashPosition"]["fmt"]
            if jsonData["topHoldings"]["cashPosition"]["raw"]:
                compositionString += "\r\nCash: " + cashPosition
        except:
            cashPosition = "N/A"
        try:
            otherPosition = jsonData["topHoldings"]["otherPosition"]["fmt"]
            if jsonData["topHoldings"]["otherPosition"]["raw"]:
                compositionString += "\r\nOther: " + otherPosition
        except:
            otherPosition = "N/A"

            
        try:
            sectorWeightings = jsonData["topHoldings"]["sectorWeightings"]
            sectorWeightingsString = ""
            for sector in sectorWeightings:
                keys = sector.keys()
                for key in keys:
                    if sector[key]["raw"] == 0:
                        continue
                    else:
                        sectorWeightingsString += key + ": " + sector[key]["fmt"] + "\r\n"
            if sectorWeightingsString == "":
                sectorWeightingsString = "N/A"
        except:
            sectorWeightingsString = "N/A"
        try:
            topHoldingTotalPct = 0
            topHoldings = jsonData["topHoldings"]["holdings"]
            topHoldingsString = ""
            for holding in topHoldings:
                symbolString = ""
                if holding["symbol"]:
                    symbolString = " (" + holding["symbol"] + ")"
                topHoldingsString += holding["holdingName"] + symbolString + ": " + holding["holdingPercent"]["fmt"] + "\r\n"
                topHoldingTotalPct += holding["holdingPercent"]["raw"]
        except: 
            topHoldingsString = "N/A"
            topHoldingTotalPct = "N/A"

        print(longName, price)
        emojiIndicator = ""
        try:
            if regularMarketDayChangePctRaw > 0.05:
                emojiIndicator = ":rocket:"
            if regularMarketDayChangePctRaw > 0.25:
                emojiIndicator += ":full_moon:"
            if regularMarketDayChangePctRaw < -0.05:
                emojiIndicator = ":skull:"
            if regularMarketDayChangePctRaw < -0.25:
                emojiIndicator += ":skull:"
        except:
            emojiIndicator = ""

        description = f"**{currencySymbol}{price}** ({regularMarketDayChange},{regularMarketDayChangePct}) {emojiIndicator}"
        if marketState == "POST":
            description += f"\n*Post-market: {currencySymbol}{postMarketPrice} ({postMarketChange},{postMarketChangePct})*"
        elif marketState == "PRE":
            description += f"\n*Pre-market: {currencySymbol}{preMarketPrice} ({preMarketChange},{preMarketChangePct})*"
        description += f"\nExhange: {exchange}\nCurrency: {currency}"
        message = discord.Embed(title=str(longName).upper() + f" ({symbol})", url=f"https://finance.yahoo.com/quote/{symbol}",
                                description=description,
                                color=0xFF5733)
        message.add_field(name="Quote Type",
                            value=quoteType, inline=True)
        message.add_field(name="Fund Family",
                            value=fundFamily, inline=True)
        message.add_field(name="Market Cap",
                            value=marketCap, inline=True)
        message.add_field(name="Total Assets",
                            value=totalAssets, inline=True)
        message.add_field(name="Regular Market Day Range",
                            value=regMktDayRng, inline=True)
        message.add_field(name="Last 52 Week Range",
                            value=fiftyTwoWeekRange, inline=True)
        message.add_field(name="beta", value=beta, inline=True)

        message.add_field(name="Fund Inception Date", value=fundInceptionDate, inline=True)
        
        message.add_field(name="Yield", value=fundYield, inline=True)
        
        message.add_field(name="Expense Ratio", value=expenses, inline=True)

        message.add_field(name="Performance", value="ytd: " + ytdReturn + "\r\n1yr: " + oneYearAverageReturn + "\r\n3yr: " + threeYearAverageReturn 
                                                   + "\r\n5yr: " + fiveYearAverageReturn+ "\r\n10yr: " + tenYearAverageReturn, inline=True)

        message.add_field(name="Composition ", value=compositionString, inline=True)

        message.add_field(name="Sector Weightings", value=sectorWeightingsString, inline=True)

        message.add_field(name="Top Holdings" + " ({:.2%})".format(topHoldingTotalPct), value=topHoldingsString, inline=True)

        message.set_image(url = styleBox)
        
        morningstarSymbol = symbol.replace('-','.')
        message.add_field(name="MorningStar ETF Performance",
                            value=f"https://www.morningstar.com/etfs/arcx/{morningstarSymbol}/performance", inline=False)
    except:
        message = f"Could not find information for ${symbol}. Perhaps it is not an EQUITY or maybe I'm parsing the data poorly...."
    
    return message

def Do_Fund_Reply(jsonData: dict):
    """ formulate a reply specifically for an Mutual Fund quote type """
    return Do_ETF_Reply(jsonData)

def price_reply(symbols: list) -> Dict[str, str]:
    """ for all symbols in provided list query yahoo finance, parse the data and send an embed reponse or an error message in case of failure """
    dataMessages = {}
    for symbol in symbols:
        # throw away anything that just has numerics like $1000
        if symbol.isnumeric():
            continue
        data = fetchSymbolData(symbol)
        if not len(data):
            message = f"Could not find information for ${symbol}."
            dataMessages[symbol] = message
        else:
            jsonData = json.loads(data.decode())
            
            theType = type(jsonData)

            message = {}
            try:
                quoteType = jsonData["quoteType"]["quoteType"]
                if quoteType == "EQUITY":
                    message = Do_Equity_Reply(jsonData)
                elif quoteType == "ETF":
                    message = Do_ETF_Reply(jsonData)
                elif quoteType == "MUTUALFUND":
                    message = Do_Fund_Reply(jsonData)
                elif quoteType == "CRYPTOCURRENCY":
                    message = Do_Equity_Reply(jsonData)
                elif quoteType == "CURRENCY":
                    message = Do_Equity_Reply(jsonData)
                else:
                    message = Do_Equity_Reply(jsonData)
            except:
                message = f"Could not find quote type for ${symbol}."

            dataMessages[symbol] = message

    return dataMessages

def get_movers():
    """ make market movers request to yahoo finance and rturns the result data"""
    message = {}
    conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
    url = f"/market/v2/get-movers?region=US&lang=en-US&start=0&count=25"
    try:
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
    except:
        message = f"An error occured trying to retrive market movers data. Could not connect to the remote server."
        return message

    data = res.read()
    jsonData = json.loads(data.decode())
    try:
        results = jsonData["finance"]["result"]
    except:
        message = f"An error occured trying to retrive market movers data."
        return message
    
    message=discord.Embed(title="Market Movers")
    for mover in results:
        try:
            title = mover["title"]
            if "gainers" in title.lower():
                title = title + ":chart_with_upwards_trend::rocket:"
            elif "losers" in title.lower():
                title = title + ":chart_with_downwards_trend: "
            description = mover["description"]
            quotes = mover["quotes"]
            symbolList = ""
            for quote in quotes:
                symbol = quote["symbol"]
                symbolList += f"{symbol}, " 
            
            message.add_field(name=title, value=symbolList, inline=False)

        except:
            continue

    return message

client = discord.Client()
bot = commands.Bot(command_prefix="!", description=help_text,)

# setup uthe daily get movers query with the schedule
doGetMoversUpdate = False
def get_movers_schedule():
    global doGetMoversUpdate
    weekno = datetime.datetime.today().weekday()
    if weekno < 5:
        doGetMoversUpdate = True
        
schedule.every().day.at("17:00").do(get_movers_schedule)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    scheduleTask.start()

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        return
    
    if (testing == True) and (message.channel.name != "testing"):
        return
    if (testing == False) and (message.channel.name == "testing"):
        return

    ctx = await bot.get_context(message)
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    if "doge" in message.content.lower():
        file_path = os.path.join(imagesFolder, "dogecoin.png")
        if os.path.isfile(file_path):
            await ctx.reply(file=discord.File(file_path))  

    if "gme" in message.content.lower():
        await ctx.reply("💎🙌")

    if "covid" in message.content.lower():
        await ctx.reply('Please maintain proper social distancing for all stock requests!')

    if "moon" in message.content.lower():
        await ctx.reply(":rocket:")

    if "$" in message.content:
        symbols = find_symbols(message.content)
        if symbols:
            for reply in price_reply(symbols).items():
                if isinstance(reply[1],str):
                    await ctx.send(reply[1])
                else:
                    embed = reply[1]
                    embed.set_footer(text="Info requested by: {}".format(ctx.author.display_name))
                    await ctx.send(embed = embed)
                #await message.channel.send(reply[1])
            return

def CleanUpSavedCharts():
    """delete all saved charts and files """
    for filename in os.listdir(chartsFolder):
        file_path = os.path.join(chartsFolder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))    

@bot.command()
async def movers(ctx):
    """Provides a list of the days top 25 gainers, losers and most active."""
    message = get_movers()
    await ctx.send(embed = message)
    return

@tasks.loop(minutes=1)
async def scheduleTask():
    """ execute periodic work like whale alerts, getmovers and clean up charts on schedule """
    messages = []
    startTime = scheduleTask.prevEndTime
    endTime = int(time.time())
    scheduleTask.prevEndTime = endTime
    if WHALEALERTAPIKEY:
        transactions = getWhaleAlertTransactions(startTime,endTime,10000000)
        if transactions:
            messages = DoWhaleAlertReply(transactions)
    schedule.run_pending()
    global doGetMoversUpdate
    if doGetMoversUpdate is True:
        doGetMoversUpdate = False
        movers = get_movers()
        messages.append(movers)
        CleanUpSavedCharts()
    if not messages:
        return
    for message in messages:
        channels = bot.get_all_channels()
        for channel in channels:
            if (channel.name == "testing") and (testing == True):
                try:
                    await channel.send(embed = message)
                except:
                    continue
            elif (channel.name == "testing") and (testing == False):
                continue
            elif testing is True:
                continue
            else:
                try:
                    await channel.send(embed = message)
                except:
                    continue

scheduleTask.prevEndTime = int(time.time())

def fetchChartData(symbol,intervalIn,rangeIn):
    """ makes yahoo finance chart query for provided symbol interval and range """
    conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
    url = f"/stock/v2/get-chart?interval={intervalIn}&symbol={symbol}&range={rangeIn}&region=US"
    try:
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
    except:
        message = f"An error occured trying to retrive chart information for ${symbol}. Could not get a response from the remote server."
        return None
  
    if(res.code == 200):
        return res.read()
    else:
        return None


def parseTimestamp(inputdata):
    """ Convert epoch timestamt into 2021-05-07 04:48:00 format """
    timestamplist = []
    timestamplist.extend(inputdata["chart"]["result"][0]["timestamp"])
  
    calendertime = []
    
    for ts in timestamplist:
        dt = datetime.datetime.fromtimestamp(ts)
        calendertime.append(dt.strftime("%Y-%m-%d %H:%M:%S"))
    
    return calendertime

def macdBuySellMarkers(histogram):
    sigBuy = []
    sigSell = []
    previous = None
    for date, value in histogram.iteritems():
        if previous == None:
            previous = value
            sigBuy.append(np.nan)
            sigSell.append(np.nan)
        else:
            if previous < 0 and value > 0:
                sigBuy.append(value*0.99)
                sigSell.append(np.nan)
            elif previous > 0 and value < 0:
                sigSell.append(value*1.01)
                sigBuy.append(np.nan)
            else:
                sigBuy.append(np.nan)
                sigSell.append(np.nan)
        previous = value
    return sigBuy,sigSell

def movavgBuySellMarkers(priceline,ma):
    sigBuy = []
    sigSell = []
    previousma = None
    previousPrice = None
    for date, value in ma.iteritems():
        if previousma == None:
            previousma = value
            previousPrice = priceline[date]
            sigBuy.append(np.nan)
            sigSell.append(np.nan)
        else:
            price = priceline[date]

            if previousPrice <= previousma and price > value:
                sigBuy.append(ma[date]*.99)
                sigSell.append(np.nan)
            elif previousPrice >= previousma and price < value:
                sigSell.append(ma[date]*1.01)
                sigBuy.append(np.nan)
            else:
                sigBuy.append(np.nan)
                sigSell.append(np.nan)
        previousma = value
        previousPrice = priceline[date]
    return sigBuy,sigSell

def calcStochastics(df,period,kavg,davg):
    kLine = []
    lPeriod = []
    hPeriod = []
    for date,value in df['Close'].iteritems():
        if len(lPeriod) < period:
            lPeriod.append(df['Low'][date])
            hPeriod.append(df['High'][date])
        if len(lPeriod) == period:
            lPeriod.append(df['Low'][date])
            hPeriod.append(df['High'][date])
            kValue = 100 * ( (value - min(lPeriod)) / (max(hPeriod) - min(lPeriod)) )
            kLine.append(kValue)
            lPeriod.pop(0)
            hPeriod.pop(0)
        elif len(lPeriod) < period:
            kLine.append(np.nan)
    
    df['KLine'] = kLine
    stochasticKLine = df['KLine'].rolling(kavg).mean()
    stochasticDLine = stochasticKLine.rolling(davg).mean()
    return stochasticKLine,stochasticDLine

def calcStochasticDLine(df):
    dLine = []
    l3 = []
    h3 = []
    for date,value in df['Close'].iteritems():
        if len(l3) < 3:
            l3.append(df['Low'][date])
            h3.append(df['High'][date])
        if len(l3) == 3:
            l3.append(df['Low'][date])
            h3.append(df['High'][date])
            kValue = 100 * ( (value - min(l3)) / (max(h3) - min(l3)) )
            dLine.append(kValue)
            l3.pop(0)
            h3.pop(0)
        elif len(l3) < 3:
            dLine.append(np.nan)
    return dLine

def stochBuySellMarkers(stochasticKLine,stochasticDLine):
    stochSigBuy = []
    stochSigSell = []
    kPrev = None
    dPrev = None
    for date,kval in stochasticKLine.iteritems():
        dval = stochasticDLine[date]
        if kPrev is None:
            kPrev = kval
            dPrev = dval
            stochSigBuy.append(np.nan)
            stochSigSell.append(np.nan)
        else:
            if (kval > dval) and (kPrev <= dPrev):
                stochSigBuy.append(stochasticKLine[date]-5)
                stochSigSell.append(np.nan)
            elif (kval < dval) and (kPrev >= dPrev):
                stochSigSell.append(stochasticKLine[date]+5)
                stochSigBuy.append(np.nan)
            else:
                stochSigBuy.append(np.nan)
                stochSigSell.append(np.nan) 
        
        kPrev = kval
        dPrev = dval

    return stochSigBuy,stochSigSell

def calcMACD(closeData,fastMAPeriod,slowMAPeriod,signalPeriod):
    expFast = closeData.ewm(span=fastMAPeriod, adjust=False).mean()
    expSlow = closeData.ewm(span=slowMAPeriod, adjust=False).mean()
    macd = expFast - expSlow
    signal = macd.ewm(span=signalPeriod, adjust=False).mean()
    histogram = macd - signal
    return macd,signal,histogram

def calcRSI(closeData):
    delta = closeData.diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up/ema_down
    rsi = (100 - (100/(1 + rs)))
    rsi.iloc[:12] = np.nan
    return rsi

def generateChartBuySellMessage(priceData,macdSigBuy,macdSigSell,stochSigBuy,stochSigSell,movavgSigBuy,movavgSigSell,rsi,stochasticLine,chartMsgPath):
    retMsg = ""
    Sell = -1
    Buy = 1
    macdState = None
    stochState = None
    maState = None
    lastSignal = None
    buySellSignal = []
    index = 0
    for date,value in priceData.iteritems():
        val =  macdSigBuy[index]
        if not np.isnan(macdSigBuy[index]):
            macdState = Buy
        elif not np.isnan(macdSigSell[index]):
            macdState = Sell
        if not np.isnan(stochSigBuy[index]):
            stochState = Buy
        elif not np.isnan(stochSigSell[index]):
            stochState = Sell
        if not np.isnan(movavgSigBuy[index]):
            maState = Buy
        elif not np.isnan(movavgSigSell[index]):
            maState = Sell
        if macdState == Buy and stochState == Buy and maState == Buy and lastSignal != Buy:
            buySellSignal.append((":green_circle::chart_with_upwards_trend:Buy",date,value))
            macdState = None
            stochState = None
            lastSignal = None
            lastSignal = Buy
        elif macdState == Sell and stochState == Sell and maState == Sell and lastSignal != Sell:
            buySellSignal.append((":red_circle::chart_with_downwards_trend:Sell",date,value))
            macdState = None
            stochState = None
            lastSignal = None
            lastSignal = Sell
        index += 1
                

    for buySellstring,date,value in buySellSignal:
        overBoughtSoldStr = ""
        rsiStr = ""
        stochStr = ""
        rsiVal = rsi[date]
        stochasticVal = stochasticLine[date]
        if rsiVal >= 70 or stochasticVal >= 80:
            if rsiVal >= 70:
                rsiStr = "*rsi*"
            if stochasticVal >= 80:
                if len(rsiStr):
                    stochStr = " *+ stoch*"
                else:
                    stochStr = "*stoch*"
            overBoughtSoldStr = rsiStr + stochStr + " *overbought*"
        elif rsiVal <= 30 or stochasticVal <= 20:
            if rsiVal <= 30:
                    rsiStr = "*rsi*"
            if stochasticVal <= 20:
                if len(rsiStr):
                    stochStr = " *+ stoch*"
                else:
                    stochStr = "*stoch*"
            overBoughtSoldStr = rsiStr + stochStr + " *oversold*"
        date = date.strftime("%m-%d")
        price = "${:.2f}".format(value)
        retMsg += f"{buySellstring} on {date} @ {price} {overBoughtSoldStr}\n"
    try:
        F=open(chartMsgPath,"w")
        F.write(retMsg)
        F.close()
    except:
        pass
    return retMsg

@bot.command()
async def chart(ctx, sym: str):
    """Generate 3 month chart for request stock."""
    async with ctx.typing():
        try:
            symbol = find_symbols(sym)[0]
        except:
            message = f"Could not find a valid symbol to look up."
            return
        print("Chart: ",symbol)
        chartName = str(symbol).lower() +".png"
        chartImgPath = chartsFolder + '/' + chartName
        chartMsgName = str(symbol).lower() +".txt"
        chartMsgPath = chartsFolder + '/' + chartMsgName
        if os.path.isfile(chartImgPath) and os.path.isfile(chartMsgPath):
            try:
                F=open(chartMsgPath,"r")
                chartMsg = F.read()
                F.close()
            except:
                chartMsg = "" 
            await ctx.send(file=discord.File(chartImgPath))
            await ctx.send(chartMsg)
            return
        else:
            chartData = None
            if testing is True:
                try:
                    F=open("chart.dat","rb")
                    chartData = F.read()
                    F.close()
                except:
                   chartData = None 
            #build the chart and save it
            if chartData is None:
                chartData = fetchChartData(symbol,"1d","3mo")
                if testing is True:
                    F=open("chart.dat","wb")
                    F.write(chartData)
                    F.close()
            try:
                if not len(chartData):
                    message = f"Could not find chart information for ${symbol}."
                    await ctx.send(message)
                    return
            except:
                message = f"Something went wrong retrieving chart data for ${symbol}."
                await ctx.send(message)
                return
            
            try:
                chartData = json.loads(chartData.decode())
            except:
                message = f"Could not decode json chart data for ${symbol}."
                await ctx.send(message)
                return

            inputdata = {}
            if not chartData["chart"]["result"]:
                message = f"Could not find chart information for ${symbol}."
                await ctx.send(message)
                return

            try:
                regularMarketPrice = chartData["chart"]["result"][0]["meta"]["regularMarketPrice"]  
                regularMarketTime = chartData["chart"]["result"][0]["meta"]["regularMarketTime"]
                regularMarketTime = datetime.datetime.fromtimestamp(regularMarketTime)
                regularMarketTime = regularMarketTime.strftime("%y-%m-%d %H:%M:%S")
                inputdata["DateTime"] = parseTimestamp(chartData)
                inputdata["Open"] = chartData["chart"]["result"][0]["indicators"]["quote"][0]["open"]
                inputdata["Close"] = chartData["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                inputdata["Volume"] = chartData["chart"]["result"][0]["indicators"]["quote"][0]["volume"]
                inputdata["High"] = chartData["chart"]["result"][0]["indicators"]["quote"][0]["high"]
                inputdata["Low"] = chartData["chart"]["result"][0]["indicators"]["quote"][0]["low"]
                inputdata["Adj Close"] = chartData["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"]

                df = pd.DataFrame(inputdata)
                df['Datetime'] = pd.to_datetime(inputdata["DateTime"], format='%Y-%m-%d %H:%M:%S')
                df = df.set_index(pd.DatetimeIndex(df['Datetime']))
                closeData = df['Close']
                # 10 day moving average for price chart
                ma = closeData.rolling(10).mean()
                #generate MACD chart data
                macd,signal,histogram = calcMACD(closeData,8,17,9)
                macdSigBuy,macdSigSell = macdBuySellMarkers(histogram)
                movavgSigBuy,movavgSigSell = movavgBuySellMarkers(closeData,ma)    
                # generate stochastics chart data            
                stochasticKLine,stochasticDLine = calcStochastics(df,14,3,3)
                stochSigBuy,stochSigSell = stochBuySellMarkers(stochasticKLine,stochasticDLine)
                stochasticOverboughtLine = [80] * len(stochasticKLine)
                stochasticUnderboughtLine = [20] * len(stochasticKLine)
                # generate RSI chart
                rsi = calcRSI(closeData)
                rsiOverboughtLine = [70] * len(rsi)
                rsiUnderboughtLine = [30] * len(rsi)
                chartBuySellMessage = generateChartBuySellMessage(ma,macdSigBuy,macdSigSell,stochSigBuy,stochSigSell,movavgSigBuy,movavgSigSell,rsi,stochasticKLine,chartMsgPath)
                addPlots = [mpf.make_addplot(histogram,type='bar',width=0.7,panel=1,color='dimgray',alpha=1,secondary_y=False,ylabel='MACD'),
                            mpf.make_addplot(macd,panel=1,color='fuchsia',secondary_y=True,width=0.5),
                            mpf.make_addplot(signal,panel=1,color='b',secondary_y=True,width=0.5),
                            mpf.make_addplot(macdSigBuy,panel=1,color='g',type='scatter',markersize=50,marker='^'),
                            mpf.make_addplot(macdSigSell,panel=1,color='r',type='scatter',markersize=50,marker='v'),
                            mpf.make_addplot(ma,panel=0,color='c',width=0.5),
                            mpf.make_addplot(closeData,panel=0,color='black',width=0.2),
                            mpf.make_addplot(movavgSigBuy,panel=0,color='g',type='scatter',markersize=50,marker='^'),
                            mpf.make_addplot(movavgSigSell,panel=0,color='r',type='scatter',markersize=50,marker='v'),
                            mpf.make_addplot(stochasticKLine,panel=2,color='black',width=0.5,ylabel='Stoch'),
                            mpf.make_addplot(stochasticDLine,panel=2,color='red',width=0.5,secondary_y=False),
                            mpf.make_addplot(stochasticOverboughtLine,panel=2,secondary_y=False,color='grey',width=0.4),
                            mpf.make_addplot(stochasticUnderboughtLine,panel=2,secondary_y=False,color='grey',width=0.4),
                            mpf.make_addplot(stochSigBuy,panel=2,color='g',type='scatter',markersize=50,marker='^',secondary_y=False),
                            mpf.make_addplot(stochSigSell,panel=2,color='r',type='scatter',markersize=50,marker='v',secondary_y=False),
                            mpf.make_addplot(rsi,panel=3,color='red',width=0.5,secondary_y=False,ylabel='RSI'),
                            mpf.make_addplot(rsiOverboughtLine,panel=3,secondary_y=False,color='grey',width=0.4),
                            mpf.make_addplot(rsiUnderboughtLine,panel=3,secondary_y=False,color='grey',width=0.4),
                ]
            
                mpf.plot(
                    df,
                    type="candle",
                    addplot=addPlots,
                    title=f"{symbol.upper()} (${regularMarketPrice} @ {regularMarketTime})",
                    volume=True,
                    volume_panel=4,
                    panel_ratios=(4,2,2,2,1),
                    style="default",
                    figscale=1.1,
                    figratio=(8,5),
                    savefig=dict(fname=chartImgPath, dpi=400, bbox_inches="tight")
                )
                await ctx.send(file=discord.File(chartImgPath))
                await ctx.send(chartBuySellMessage)

            except:
                message = f"Failed to generate chart data for ${symbol}."
                await ctx.send(message)
    return

@bot.command()
async def rand(ctx):
    """Get a random stock ticker."""
    if not stockListLen:
        message = f"I don't have a list of stocks to pick at random.  Make sure I have a .csv from available to read from: https://www.nasdaq.com/market-activity/stocks/screener"
        return
    try:   
        while True:
            randomPick = random.randint(0, stockListLen-1)
            symbol = stocks.iloc[randomPick].name
            if '^' in symbol:
                continue
            else:
                break
    except:
        message = f"I had a problem getting a random stock from the list."
        return  
    try: 
        symbol = stocks.iloc[randomPick].name
        for reply in price_reply([symbol]).items():
            if isinstance(reply[1],str):
                await ctx.send(reply[1])
            else:
                embed = reply[1]
                embed.set_footer(text="Random stock picked for: {}. Chosen from a list of {} symbols.".format(ctx.author.display_name,stockListLen))
                await ctx.send(embed = embed)
    except:
        message = f"I wasn't able to get a symbol name from my list."
        return


def getWhaleAlertTransactions(startTime, endTime, minValue):
    """Get whale alert transactions between startTime and endTIme with specified min value."""
    conn = http.client.HTTPSConnection("api.whale-alert.io")
    url = f"/v1/transactions?start={startTime}&end={endTime}&min_value={minValue}"
    try:
        conn.request("GET", url, headers=waHeaders)
        res = conn.getresponse()
    except:
        message = f"An error occured trying to retrive whale alert data. Could not connect to the remote server."
        return message
    if(res.code == 200):
        ret = res.read()
        ret = json.loads(ret.decode())
        return ret
    else:
        return None

def DoWhaleAlertReply(jsonData):
    messages = []
    if len(jsonData):
        try:
            result = jsonData["result"]
            cursor = jsonData["cursor"]
            count = jsonData["count"]
        except:
            return None
    if count:
        print(f"Detected {count} whale alert transactions.")
    if result == 'success' and count > 0:
        try:
            transactions = jsonData["transactions"]
            for transaction in transactions:
                blockchain = transaction["blockchain"]
                symbol = transaction["symbol"]
                id = transaction["id"]
                transactionType = transaction["transaction_type"]
                hash = transaction["hash"]
                transactionFrom = transaction["from"]
                fromAddress = transactionFrom["address"]
                fromOwnerType = transactionFrom["owner_type"]
                try:
                    fromOwner = transactionFrom["owner"]
                except:
                    fromOwner = "unknown wallet"

                transactionTo = transaction["to"]
                toAddress = transactionTo["address"]
                toOwnerType = transactionTo["owner_type"]
                try:
                    toOwner = transactionTo["owner"]
                except:
                    toOwner = "unknown wallet"
                timeStamp = transaction["timestamp"]
                amount = transaction["amount"]
                amount_usd = transaction["amount_usd"]
                transaction_count = transaction["transaction_count"]
                readableTimeStamp = datetime.datetime.fromtimestamp(timeStamp)
                readableTimeStamp = readableTimeStamp.strftime("%y-%m-%d %H:%M:%S")
                symbol = symbol.upper()
                amount = "{:,}".format(int(amount))
                amount_usd = "{:,}".format(int(amount_usd))
                blockchain = blockchain.upper()
                message=discord.Embed(title=f"{blockchain}",url=f"https://whale-alert.io/transaction/{blockchain}/{hash}",color=0xFF5733)
                message.add_field(name="Transaction Type", value=transactionType, inline=False)
                message.add_field(name="Amount", value=f"{amount} **{symbol}** (${amount_usd})", inline=False)
                message.add_field(name="Timestamp", value=f"{readableTimeStamp} ({timeStamp})", inline=False)
                message.add_field(name="Hash", value=hash, inline=False)
                message.add_field(name="From", value=f"{fromOwner} ({fromOwnerType})\r\n{fromAddress}", inline=False)
                message.add_field(name="To", value=f"{toOwner} ({toOwnerType})\r\n{toAddress}", inline=False)

                messages.append(message)
                return messages
        except:
            return None

        
bot.run(TOKEN)
