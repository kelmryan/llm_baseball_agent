import requests
import json
from datetime import datetime


def get_crypto_price(block="BTC"):
    # Normalize input to handle 'bitcoin'
    if block.lower() == "bitcoin":
        block = "BTC"
    elif block.lower() == "litecoin":
        block = "LTC"
    try:
        response = requests.get("https://api.coinbase.com/v2/exchange-rates?currency=" + block)
        data = response.json()
        price = float(data['data']['rates']['USD'])
        return f"${block} current price: ${price:,.2f} USD"
    except:
        return "Couldn't fetch Bitcoin price"

def get_orioles_roster():
    try:
        # Using MLB Stats API (free)
        response = requests.get("https://statsapi.mlb.com/api/v1/teams/110/roster/Active")
        data = response.json()
        
        roster_info = []
        roster_info.append("BALTIMORE ORIOLES ACTIVE ROSTER:")
        
        for player in data['roster'][:10]:  # First 10 players
            name = player['person']['fullName']
            position = player['position']['abbreviation']
            jersey = player.get('jerseyNumber', 'N/A')
            roster_info.append(f"#{jersey} {name} ({position})")
        
        if len(data['roster']) > 10:
            roster_info.append(f"...and {len(data['roster']) - 10} more players")
            
        return "\n".join(roster_info)
    except Exception as e:
        return f"Couldn't fetch Orioles roster: {e}"

def get_orioles_schedule():
    try:
        # Get next few games
        response = requests.get("https://statsapi.mlb.com/api/v1/schedule?teamId=110&sportId=1&hydrate=team,linescore")
        data = response.json()
        
        if data['dates']:
            game_info = []
            game_info.append("ORIOLES UPCOMING GAMES:")
            
            for date_info in data['dates'][:3]:  # Next 3 game dates
                for game in date_info['games']:
                    away_team = game['teams']['away']['team']['name']
                    home_team = game['teams']['home']['team']['name']
                    game_date = game['gameDate'][:10]  # YYYY-MM-DD
                    game_info.append(f"{game_date}: {away_team} @ {home_team}")
            
            return "\n".join(game_info)
        else:
            return "No upcoming Orioles games found"
    except Exception as e:
        return f"Couldn't fetch Orioles schedule: {e}"

def get_weather(city="Baltimore"):
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3")
        return f"Weather in {city}: {response.text.strip()}"
    except:
        return f"Couldn't get weather for {city}"

def get_stock_price(symbol):
    try:
        # Using Yahoo Finance API alternative
        response = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}")
        data = response.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        return f"{symbol.upper()} current price: ${price:.2f}"
    except:
        return f"Couldn't fetch {symbol} stock price"

def smart_data_lookup(user_input):
    """Determine what data to fetch based on user input"""
    input_lower = user_input.lower()
    data_results = []
    
    # Crypto prices
    if any(word in input_lower for word in ['bitcoin', 'btc', 'crypto']):
        data_results.append(get_bitcoin_price())
    
    # Orioles data
    if any(word in input_lower for word in ['orioles', 'o\'s', 'baltimore']):
        if any(word in input_lower for word in ['roster', 'players', 'team']):
            data_results.append(get_orioles_roster())
        elif any(word in input_lower for word in ['schedule', 'games', 'next']):
            data_results.append(get_orioles_schedule())
        else:
            # Default to roster if just asking about Orioles
            data_results.append(get_orioles_roster())
    
    # Weather
    if any(word in input_lower for word in ['weather', 'temperature']):
        city = "Baltimore"  # Default to Baltimore since you mentioned Orioles
        # Try to extract city name
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ['in', 'for'] and i + 1 < len(words):
                city = words[i + 1].replace('?', '').replace(',', '')
                break
        data_results.append(get_weather(city))
    
    # Stock prices
    if any(word in input_lower for word in ['stock', 'share', 'tsla', 'aapl', 'msft', 'googl']):
        # Try to extract stock symbol
        common_stocks = {'tesla': 'TSLA', 'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'amazon': 'AMZN'}
        for company, symbol in common_stocks.items():
            if company in input_lower or symbol.lower() in input_lower:
                data_results.append(get_stock_price(symbol))
                break
    
    return data_results

def main():
    print("Enhanced Ollama Chat with Live Data Lookup")
    print("Ask about: Bitcoin prices, Orioles roster/schedule, weather, stocks")
    print("Type 'quit' to exit\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        
        # Get relevant live data
        live_data = smart_data_lookup(user_input)
        
        if live_data:
            print(f"[Fetching live data...]")
            
            # Combine all live data
            live_data_text = "\n\n".join(live_data)
            
            # Strong prompting to use live data
            enhanced_prompt = f"""SYSTEM: You are being provided with LIVE, REAL-TIME data. Your training data may be outdated.

LIVE DATA (fetched at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):
{live_data_text}

User question: "{user_input}"

IMPORTANT: Use ONLY the live data provided above. Do not reference your training data if it conflicts with this current information. Answer the user's question using this up-to-date data."""

        else:
            enhanced_prompt = user_input
        
        print("Mistral: ", end="")
        response = chat_ollama(enhanced_prompt)
        print(response)

if __name__ == "__main__":
    main()