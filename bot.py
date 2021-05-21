# bot.py
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

# headers used for all rapid api yahoo finance connection requests
headers = {
    'x-rapidapi-key': RAPIDAPIKEY,
    'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com"
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
        return NULL
  
    if(res.code == 200):
        return res.read()
    else:
        return None

def find_symbols(text: str) -> List[str]:
    """ find all potential stock symbols starting with $ as a list."""
    SYMBOL_REGEX = "[$]([a-zA-Z-]{1,8})"
    return list(set(re.findall(SYMBOL_REGEX, text)))

def Do_Equity_Reply(jsonData):
    """ formulate a reply specifically for an equity quote type """
    try:
        quoteType = jsonData["quoteType"]["quoteType"]
        shortName = jsonData["quoteType"]["shortName"]
        try:
            longName = jsonData["quoteType"]["longName"]
        except:
            longName = shortName
        symbol = jsonData["quoteType"]["symbol"]
        marketState = jsonData["price"]["marketState"]
        price = jsonData["price"]["regularMarketPrice"]["fmt"]
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
        insiderHolding = (f"% Held by Insiders: {insiderPercentHeld}.\r\n" +
                            f"% Held by Institutions: {institutionPercentHeld}.\r\n" +
                            f"Short % of Float: {shortPercentOfFloat}.\r\n"
                            f"http://www.openinsider.com/{symbol}")

        print(longName, price)
        emojiIndicator = ""
        if regularMarketDayChangePctRaw > 0.05:
            emojiIndicator = ":rocket:"
        elif regularMarketDayChangePctRaw < -0.05:
            emojiIndicator = ":skull:"

        description = f"**${price}** ({regularMarketDayChange},{regularMarketDayChangePct}) {emojiIndicator}"
        if marketState == "POST":
            description += f"\r\n\r\n*Post-market: ${postMarketPrice} ({postMarketChange},{postMarketChangePct})*"
        elif marketState == "PRE":
            description += f"\r\n\r\n*Pre-market: ${preMarketPrice} ({preMarketChange},{preMarketChangePct})*"
        message = discord.Embed(title=str(longName).upper() + f" ({symbol})", url=f"https://finance.yahoo.com/quote/{symbol}",
                                description=description,
                                color=0xFF5733)
        message.add_field(name="Quote Type",
                            value=quoteType, inline=True)
        message.add_field(name="Industry", value=industry, inline=True)
        message.add_field(name="Sector", value=sector, inline=True)
        message.add_field(name="Market Cap",
                            value=marketCap, inline=True)
        message.add_field(name="Regular Market Day Range",
                            value=regMktDayRng, inline=True)
        message.add_field(name="Last 52 Week Range",
                            value=fiftyTwoWeekRange, inline=True)
        message.add_field(name="PE Ratio (TTM)",
                            value=trailingPE, inline=True)
        message.add_field(name="PEG Ratio",
                            value=pegRatio, inline=True)
        message.add_field(name="Price to Book",
                            value=priceToBook, inline=True)
        message.add_field(name="Price to Sales",
                            value=priceToSales, inline=True)
        message.add_field(name="EV/EBITDA",
                            value=enterpriseToEbitda, inline=True)
        message.add_field(name="beta", value=beta, inline=True)

        rateAndYield = str(dividendRate) + \
                            " (" + str(dividendYield) + ")"
        message.add_field(name="Dividend Rate and Yield",
                            value=rateAndYield, inline=True)

        message.add_field(name="Share Statistics",
                            value=insiderHolding, inline=False)
        message.add_field(name="MorningStar Key Ratios",
                            value=f"http://financials.morningstar.com/ratios/r.html?t={symbol}", inline=False)
    except:
        message = f"Could not find information for ${symbol}. Perhaps it is not an EQUITY or maybe I'm parsing the data poorly...."
    
    return message

def Do_ETF_Reply(jsonData: dict):
    """ formulate a reply specifically for an ETF quote type """
    try:
        quoteType = jsonData["quoteType"]["quoteType"]
        shortName = jsonData["quoteType"]["shortName"]
        try:
            longName = jsonData["quoteType"]["longName"]
        except:
            longName = shortName
        symbol = jsonData["quoteType"]["symbol"]
        marketState = jsonData["price"]["marketState"]
        price = jsonData["price"]["regularMarketPrice"]["fmt"]
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
            elif regularMarketDayChangePctRaw < -0.05:
                emojiIndicator = ":skull:"
        except:
            emojiIndicator = ""

        description = f"**${price}** ({regularMarketDayChange},{regularMarketDayChangePct}) {emojiIndicator}"
        if marketState == "POST":
            description += f"\r\n\r\n*Post-market: ${postMarketPrice} ({postMarketChange},{postMarketChangePct})*"
        elif marketState == "PRE":
            description += f"\r\n\r\n*Pre-market: ${preMarketPrice} ({preMarketChange},{preMarketChangePct})*"
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

        message.add_field(name="MorningStar ETF Performance",
                            value=f"https://www.morningstar.com/etfs/arcx/{symbol}/performance", inline=False)
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
                    embed.set_footer(text="Stock info requested by: {}".format(ctx.author.display_name))
                    await ctx.send(embed = embed)
                #await message.channel.send(reply[1])
            return

def CleanUpSavedCharts():
    """delete all saved charts """
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
    """ execute getmovers and clean up charts on schedule """
    schedule.run_pending()
    global doGetMoversUpdate
    if doGetMoversUpdate is True:
        doGetMoversUpdate = False
        movers = get_movers()
        channels = bot.get_all_channels()
        for channel in channels:
            if (channel.name == "testing") and (testing == True) :
                try:
                    await channel.send(embed = movers)
                except:
                    continue
            elif testing is True:
                continue
            else:
                try:
                    await channel.send(embed = movers)
                except:
                    continue

        CleanUpSavedCharts()

def fetchChartData(symbol,intervalIn,rangeIn):
    """ makes yahoo finance chart query for provided symbol interval and range """
    conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
    url = f"/stock/v2/get-chart?interval={intervalIn}&symbol={symbol}&range={rangeIn}&region=US"
    try:
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
    except:
        message = f"An error occured trying to retrive chart information for ${symbol}. Could not get a response from the remote server."
        return NULL
  
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

@bot.command()
async def chart(ctx, sym: str):
    """Generate 3 month chart for request stock."""
    async with ctx.typing():
        try:
            symbol = find_symbols(sym)[0]
        except:
            message = f"Could not find a valid symbol to look up."
            return
        filename = str(symbol).lower() +".png"
        filePath = chartsFolder + '/' + filename
        if os.path.isfile(filePath):
            await ctx.send(file=discord.File(filePath))
            return
        else:
            #build the chart and save it
            chartData = fetchChartData(symbol,"1d","3mo")
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
                exp8 = df['Close'].ewm(span=8, adjust=False).mean()
                exp17 = df['Close'].ewm(span=17, adjust=False).mean()
                macd = exp8 - exp17
                signal    = macd.ewm(span=9, adjust=False).mean()
                histogram = macd - signal
                macdPlot = [mpf.make_addplot(histogram,type='bar',width=0.7,panel=1,color='dimgray',alpha=1,secondary_y=False,ylabel='MACD(8,17,9)'),
                            mpf.make_addplot(macd,panel=1,color='fuchsia',secondary_y=True),
                            mpf.make_addplot(signal,panel=1,color='b',secondary_y=True),
                ]
            
                mpf.plot(
                    df,
                    type="candle",
                    addplot=macdPlot,
                    mav=10,
                    title=f"\n{symbol.upper()}",
                    volume=True,
                    volume_panel=2,
                    panel_ratios=(4,2,1),
                    style="default",
                    figscale=1.1,
                    figratio=(8,5),
                    savefig=dict(fname=filePath, dpi=400, bbox_inches="tight")
                )
                await ctx.send(file=discord.File(filePath))
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

bot.run(TOKEN)
