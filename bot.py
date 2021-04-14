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

help_text = """

**Commands**
    - !movers - Returns the top 25 gainers,losers and volume stocks of the day.
    - !help   - Display this help message you are reading
**Inline Features**
    The bot looks at every message in the chat room it is in for stock symbols. Symbols start with a
    `$` followed by the stock symbol. For example: $gme will return data for Gamestop Corp.
    Market data is provided by [Yahoo! Finance](https://rapidapi.com/apidojo/api/yahoo-finance1)
    """



try:
    tokenFile = open("token.txt", 'r')
except OSError:
    print("Could not open/read token file.")
    exit()

with tokenFile:
    TOKEN = tokenFile.readline()

try:
    rapidapikeyFile = open('rapidapikey.txt', 'r')
except OSError:
    print("Could not open/read Raid API key file.")
    sys.exit()

with rapidapikeyFile:
    RAPIDAPIKEY = rapidapikeyFile.readline()

headers = {
    'x-rapidapi-key': RAPIDAPIKEY,
    'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com"
}

millnames = ['','Thousand','M',' B',' T']

def millify(n):
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])

def fetchSymbolData(symbol):
    conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': RAPIDAPIKEY,
        'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com"
        }
    #url = f"/market/v2/get-quotes?region=US&symbols={symbol}"
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
    SYMBOL_REGEX = "[$]([a-zA-Z-]{1,8})"
    return list(set(re.findall(SYMBOL_REGEX, text)))

def price_reply(symbols: list) -> Dict[str, str]:
    dataMessages = {}
    for symbol in symbols:
        data = fetchSymbolData(symbol)
        if not len(data):
            message = f"Could not find information for ${symbol}."
            dataMessages[symbol] = message
        else:
            jsonData = json.loads(data.decode())
            message = {}
            try:
                shortName = jsonData["quoteType"]["shortName"]
                try:
                    longName = jsonData["quoteType"]["longName"]
                except:
                    longName = shortName
                quoteType = jsonData["quoteType"]["quoteType"]
                symbol = jsonData["quoteType"]["symbol"]
                marketState =  jsonData["price"]["marketState"]
                price = jsonData["price"]["regularMarketPrice"]["fmt"]
                try:
                    postMarketPrice = jsonData["price"]["postMarketPrice"]["fmt"]
                    preMarketPrice = jsonData["price"]["preMarketPrice"]["fmt"]
                except:
                    postMarketPrice = price
                    preMarketPrice = price
                try:
                    industry = jsonData["summaryProfile"]["industry"]
                    sector = jsonData["summaryProfile"]["sector"]
                except:
                    industry = "N/A"
                    sector = "N/A"
                try:
                    regularMarketDayLow = jsonData["price"]["regularMarketDayLow"]["fmt"]
                    regularMarketDayHigh = jsonData["price"]["regularMarketDayHigh"]["fmt"]
                    regMktDayRng = str(regularMarketDayLow) + " - " + str(regularMarketDayHigh)
                except:
                    regMktDayRng = "N/A"
                
                try:
                    fiftyTwoWeekLow = jsonData["summaryDetail"]["fiftyTwoWeekLow"]["fmt"]
                    fiftyTwoWeekHigh = jsonData["summaryDetail"]["fiftyTwoWeekHigh"]["fmt"]
                    fiftyTwoWeekRange = str(fiftyTwoWeekLow) + " - " + str(fiftyTwoWeekHigh)
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
                    else:
                        priceToBookColor = ':yellow_circle:'
                    priceToBook = priceToBookFmt + priceToBookColor
                except:
                    priceToBook = "N/A"
                try:
                    
                    priceToSalesRaw = jsonData["summaryDetail"]["priceToSalesTrailing12Months"]["raw"]
                    priceToSalesFmt = jsonData["summaryDetail"]["priceToSalesTrailing12Months"]["fmt"]
                    if priceToSalesRaw <= 4:
                        priceToSalesColor = ':green_circle:'
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
                    buyInfoCount = jsonData["netSharePurchaseActivity"]["buyInfoCount"]["fmt"]
                    sellInfoShares = jsonData["netSharePurchaseActivity"]["sellInfoShares"]["fmt"]
                    sellInfoCount = jsonData["netSharePurchaseActivity"]["sellInfoCount"]["fmt"]
                    insiderPurchases = (f"Purchases: {buyInfoShares} shares in {buyInfoCount} transactions.\r\n" +
                                       f"Sales: {sellInfoShares} shares in {sellInfoCount} transactions.")
                except:
                    buyInfoShares = "N/A"
                    buyInfoCount = "N/A"
                    sellInfoShares = "N/A"
                    sellInfoCount = "N/A"

                print(longName, price)
                description = f"The market price of {symbol} is ${price}"
                if marketState == "POST":
                    description = f"The post-market price of {symbol} is ${postMarketPrice}"
                elif marketState == "PRE":
                    description = f"The pre-market price of {symbol} is ${preMarketPrice}"
                message = discord.Embed(title=str(longName).upper(), url=f"https://finance.yahoo.com/quote/{symbol}",
                                        description=description,
                                        color=0xFF5733)
                message.add_field(name="Quote Type", value=quoteType, inline=True)
                message.add_field(name="Industry", value=industry, inline=True)
                message.add_field(name="Sector", value=sector, inline=True)
                message.add_field(name="Market Cap", value=marketCap, inline=True)
                message.add_field(name="Regular Market Day Range", value=regMktDayRng, inline=True)
                message.add_field(name="Last 52 Week Range", value=fiftyTwoWeekRange, inline=True)
                message.add_field(name="PE Ratio (TTM)", value=trailingPE, inline=True)
                message.add_field(name="PEG Ratio", value=pegRatio, inline=True)
                message.add_field(name="Price to Book", value=priceToBook, inline=True)
                message.add_field(name="Price to Sales", value=priceToSales, inline=True)
                message.add_field(name="Enterprise Value/EBITDA",value=enterpriseToEbitda, inline=True)
                message.add_field(name="beta",value=beta, inline=True)

                rateAndYield = str(dividendRate) + " (" + str(dividendYield) + ")"
                message.add_field(name="Dividend Rate and Yield", value=rateAndYield, inline=True)

                message.add_field(name="Insider info",value=f"http://www.openinsider.com/{symbol}", inline=False)
                message.add_field(name="MorningStar Key Ratios", value=f"http://financials.morningstar.com/ratios/r.html?t={symbol}", inline=False)
            except:
                message = f"Could not find information for ${symbol}. Perhaps it is not an EQUITY or maybe I'm parsing the data poorly...."

            dataMessages[symbol] = message

    return dataMessages

def get_movers():
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

doGetMoversUpdate = False
def get_movers_schedule():
    global doGetMoversUpdate
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
    
    ctx = await bot.get_context(message)
    if message.content[0] == "!":
        await bot.process_commands(message)
        return


    if "gme" in message.content:
        await ctx.reply("💎🙌")

    if "covid" in message.content:
        await ctx.reply('Please maintain proper social distancing for all stock requests!')

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

@bot.command()
async def movers(ctx):
    message = get_movers()
    await ctx.send(embed = message)
    return

@tasks.loop(minutes=1)
async def scheduleTask():
    schedule.run_pending()
    global doGetMoversUpdate
    if doGetMoversUpdate is True:
        doGetMoversUpdate = False
        weekno = datetime.datetime.today().weekday()
        if weekno < 5:
            movers = get_movers()
            channels = bot.get_all_channels()
            for channel in channels:
                try:
                    await channel.send(embed = movers)
                except:
                    continue
 
bot.run(TOKEN)
