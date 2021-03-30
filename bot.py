# bot.py
import os
import discord
from discord.ext import commands
import http.client
import re
import json
from typing import List,Dict
import math
from sys import exit

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

def find_symbols(text: str) -> List[str]:
    SYMBOL_REGEX = "[$]([a-zA-Z-]{1,7})"
    return list(set(re.findall(SYMBOL_REGEX, text)))

def price_reply(symbols: list) -> Dict[str, str]:
    dataMessages = {}
    for symbol in symbols:
        conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
        headers = {
            'x-rapidapi-key': RAPIDAPIKEY,
            'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com"
            }
        url = f"/market/v2/get-quotes?region=US&symbols={symbol}"
        #url = f"/stock/v2/get-summary?symbol={symbol}&region=US"
        try:
            conn.request("GET", url, headers=headers)
            res = conn.getresponse()
        except:
            message = f"An error occured trying to retrive information for ${symbol}. Could not connect to the remote server."
            dataMessages[symbol] = message
            return dataMessages

        data = res.read()
        jsonData = json.loads(data.decode())
        jsonDataError = jsonData['quoteResponse']['error']
        message = {}
        if jsonDataError == None:
            jsonDataResult = jsonData['quoteResponse']['result']
            if not len(jsonDataResult):
                message = f"Could not find information for ${symbol}."
                dataMessages[symbol] = message
            else:
                for tag in jsonDataResult:
                    try:
                        shortName = tag["shortName"]
                        price = tag["regularMarketPrice"] 
                        regMktDayRng = tag["regularMarketDayRange"]
                        fiftyTwoWeekRange = tag["fiftyTwoWeekRange"]
                        try:
                            marketCap = millify(tag["marketCap"])
                        except:
                            marketCap = "N/A"
                        try:
                            trailingPE = tag["trailingPE"]
                            if trailingPE <= 15:
                                peColor = ':green_circle:' 
                            else:
                                peColor = ':yellow_circle:' 
                            trailingPE = str(trailingPE) + peColor  
                        except:
                            trailingPE = "N/A"
                        try:
                            pegRatio = tag["pegRatio"]
                            if pegRatio <= 1:
                                pegColor = ':green_circle:'
                            else:
                                pegColor = ':yellow_circle:'
                            pegRatio = str(pegRatio) + pegColor
                        except:
                            pegRatio = "N/A"
                        try:
                            priceToBook = tag["priceToBook"]
                            if priceToBook <= 2:
                                priceToBookColor = ':green_circle:'
                            else:
                                priceToBookColor = ':yellow_circle:'
                            priceToBook = str(priceToBook) + priceToBookColor
                        except:
                            priceToBook = "N/A"
                        try:
                            priceToSales = tag["priceToSales"]
                            if priceToSales <= 4:
                                priceToSalesColor = ':green_circle:'
                            else:
                                priceToSalesColor = ':yellow_circle:'
                            priceToSales = str(priceToSales) + priceToSalesColor
                        except:
                            priceToSales = "N/A"
                        try:
                            dividendRate = tag["dividendRate"]
                            dividendYield = tag["dividendYield"]
                        except:
                            dividendRate  = "N/A"
                            dividendYield = "N/A"

                        print(shortName,price)
                        message=discord.Embed(title=str(shortName).upper(), url=f"https://finance.yahoo.com/quote/{symbol}", 
                                              description=f"The current price of [{symbol}](https://finance.yahoo.com/quote/{symbol}) is ${price}", 
                                              color=0xFF5733)
                        message.add_field(name="Market Cap", value=marketCap, inline=True)
                        message.add_field(name="Regular Market Day Range", value=regMktDayRng, inline=True)
                        message.add_field(name="Last 52 Week Range", value=fiftyTwoWeekRange, inline=True)
                        message.add_field(name="PE Ratio (TTM)", value=trailingPE, inline=True)
                        message.add_field(name="PEG Ratio", value=pegRatio, inline=True)
                        message.add_field(name="Price to Book", value=priceToBook, inline=True)
                        message.add_field(name="Price to Sales", value=priceToSales, inline=True)
                        rateAndYield = str(dividendRate) + " (" + str(dividendYield) + "%)"
                        message.add_field(name="Dividend Rate and Yield", value=rateAndYield , inline=True)
                        message.add_field(name="MorningStar Key Ratios", value=f"http://financials.morningstar.com/ratios/r.html?t={symbol}", inline=False)
                        #message = f"The current stock price of [{shortName}](https://finance.yahoo.com/quote/{symbol}) is ${price}"
                    except:
                        message = f"Could not find information for ${symbol}. Perhaps it is not an EQUITY or maybe I'm parsing the data poorly...."

                    dataMessages[symbol] = message
        else: 
            message = f"An error occured trying to retrive information for ${symbol}."
            dataMessages[symbol] = message

        
    return dataMessages

client = discord.Client()
bot = commands.Bot(command_prefix="!", description=help_text,)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

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
    dataMessages = {}
    conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
    url = f"/market/v2/get-movers?region=US&lang=en-US&start=0&count=25"
    try:
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
    except:
        message = f"An error occured trying to retrive market movers data. Could not connect to the remote server."
        dataMessages[symbol] = message
        return dataMessages

    data = res.read()
    jsonData = json.loads(data.decode())
    message = {}
    try:
        results = jsonData["finance"]["result"]
    except:
        message = f"An error occured trying to retrive market movers data."
    
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
            message.add_field(name=title, inline=False)
            for quote in quotes:
                symbol = quote["symbol"]
                symbolList += f"{symbol}, " 
        except:
            continue
    
    await ctx.send(embed = message)
    return
 
bot.run(TOKEN)
