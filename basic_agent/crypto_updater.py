# Multi-Cryptocurrency AI Agent with Mistral 7B
# Supports any cryptocurrency available on CoinGecko

import requests
import json
import time
import schedule
import threading
from datetime import datetime, timedelta
import ollama
from typing import Dict, List, Optional

class CryptoPriceManager:
    def __init__(self, cryptocurrencies=['bitcoin', 'ethereum', 'litecoin']):
        self.cryptocurrencies = cryptocurrencies
        self.current_prices = {}
        self.price_history = {crypto: [] for crypto in cryptocurrencies}
        self.price_alerts = []
        self.last_update = None
        
    def add_cryptocurrency(self, crypto_id: str):
        """Add a new cryptocurrency to track"""
        if crypto_id not in self.cryptocurrencies:
            self.cryptocurrencies.append(crypto_id)
            self.price_history[crypto_id] = []
            print(f"✅ Added {crypto_id} to tracking list")
        else:
            print(f"ℹ️ {crypto_id} is already being tracked")
    
    def remove_cryptocurrency(self, crypto_id: str):
        """Remove a cryptocurrency from tracking"""
        if crypto_id in self.cryptocurrencies:
            self.cryptocurrencies.remove(crypto_id)
            if crypto_id in self.price_history:
                del self.price_history[crypto_id]
            print(f"✅ Removed {crypto_id} from tracking list")
        else:
            print(f"❌ {crypto_id} is not being tracked")
    
    def search_cryptocurrency(self, search_term: str) -> List[Dict]:
        """Search for cryptocurrency by name/symbol"""
        try:
            url = "https://api.coingecko.com/api/v3/search"
            params = {'query': search_term}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            coins = data.get('coins', [])[:10]  # Limit to top 10 results
            
            results = []
            for coin in coins:
                results.append({
                    'id': coin['id'],
                    'name': coin['name'],
                    'symbol': coin['symbol'].upper(),
                    'market_cap_rank': coin.get('market_cap_rank', 'N/A')
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching cryptocurrencies: {e}")
            return []
    
    def fetch_crypto_prices(self) -> Dict:
        """Fetch current cryptocurrency prices from CoinGecko API"""
        try:
            if not self.cryptocurrencies:
                return {}
                
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ','.join(self.cryptocurrencies),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            price_info = {}
            for crypto in self.cryptocurrencies:
                if crypto in data:
                    crypto_data = data[crypto]
                    price_info[crypto] = {
                        'price': crypto_data['usd'],
                        '24h_change': crypto_data.get('usd_24h_change', 0),
                        'market_cap': crypto_data.get('usd_market_cap', 0),
                        '24h_volume': crypto_data.get('usd_24h_vol', 0),
                        'timestamp': datetime.now(),
                        'last_updated': crypto_data.get('last_updated_at', int(time.time()))
                    }
            
            return price_info
            
        except Exception as e:
            print(f"Error fetching crypto prices: {e}")
            return None
    
    def update_prices(self):
        """Update all cryptocurrency prices and store in history"""
        price_info = self.fetch_crypto_prices()
        if price_info:
            self.current_prices = price_info
            self.last_update = datetime.now()
            
            # Add to history for each crypto
            for crypto, data in price_info.items():
                self.price_history[crypto].append(data)
                
                # Keep only last 168 hours (7 days) of data for each crypto
                if len(self.price_history[crypto]) > 168:
                    self.price_history[crypto] = self.price_history[crypto][-168:]
            
            print(f"✅ Crypto prices updated at {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}:")
            for crypto, data in price_info.items():
                crypto_display = crypto.replace('-', ' ').title()
                print(f"   💰 {crypto_display}: ${data['price']:,.4f} ({data['24h_change']:+.2f}%)")
            
            # Check alerts
            self.check_alerts()
        else:
            print("❌ Failed to update crypto prices")
    
    def add_price_alert(self, target_price: float, cryptocurrency: str = "bitcoin", alert_type: str = "above"):
        """Add a price alert for any supported cryptocurrency"""
        if cryptocurrency not in self.cryptocurrencies:
            print(f"❌ {cryptocurrency} not being tracked. Use add_cryptocurrency() first or search for the correct ID.")
            return
            
        alert = {
            'target_price': target_price,
            'cryptocurrency': cryptocurrency,
            'type': alert_type,  # 'above' or 'below'
            'created_at': datetime.now(),
            'triggered': False
        }
        self.price_alerts.append(alert)
        crypto_display = cryptocurrency.replace('-', ' ').title()
        print(f"🔔 Alert set: Notify when {crypto_display} goes {alert_type} ${target_price:,.4f}")
    
    def check_alerts(self):
        """Check if any price alerts should be triggered"""
        if not self.current_prices:
            return
            
        for alert in self.price_alerts:
            if alert['triggered']:
                continue
            
            crypto = alert['cryptocurrency']
            if crypto not in self.current_prices:
                continue
                
            current = self.current_prices[crypto]['price']
            crypto_display = crypto.replace('-', ' ').title()
            
            if alert['type'] == 'above' and current >= alert['target_price']:
                print(f"🚨 ALERT: {crypto_display} price (${current:,.4f}) is now ABOVE your target of ${alert['target_price']:,.4f}!")
                alert['triggered'] = True
                
            elif alert['type'] == 'below' and current <= alert['target_price']:
                print(f"🚨 ALERT: {crypto_display} price (${current:,.4f}) is now BELOW your target of ${alert['target_price']:,.4f}!")
                alert['triggered'] = True
    
    def get_price_summary(self) -> str:
        """Get a formatted summary of all cryptocurrency prices and recent changes"""
        if not self.current_prices:
            return "No price data available. Please update prices first."
        
        summary = f"""
📊 Cryptocurrency Price Summary (Last Updated: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')})
🕒 Data Age: {(datetime.now() - self.last_update).total_seconds() / 60:.1f} minutes old

"""
        
        # Add price info for each cryptocurrency
        for crypto, data in self.current_prices.items():
            crypto_display = crypto.replace('-', ' ').title()
            market_cap_billions = data.get('market_cap', 0) / 1e9
            volume_millions = data.get('24h_volume', 0) / 1e6
            
            summary += f"💰 {crypto_display}:\n"
            summary += f"   Price: ${data['price']:,.4f}\n"
            summary += f"   24h Change: {data['24h_change']:+.2f}%\n"
            summary += f"   Market Cap: ${market_cap_billions:.1f}B\n"
            summary += f"   24h Volume: ${volume_millions:.1f}M\n"
            
            # Add recent trend if we have enough data
            if len(self.price_history[crypto]) >= 2:
                recent_change = self.price_history[crypto][-1]['price'] - self.price_history[crypto][-2]['price']
                trend = "📈 Rising" if recent_change > 0 else "📉 Falling" if recent_change < 0 else "➡️ Stable"
                summary += f"   Recent Trend: {trend} (${recent_change:+.4f} from last update)\n\n"
            else:
                summary += "\n"
        
        summary += f"🔔 Active Alerts: {len([a for a in self.price_alerts if not a['triggered']])}\n"
        summary += f"📊 Cryptocurrencies Tracked: {len(self.cryptocurrencies)}\n"
        summary += f"📈 Total Price History Points: {sum(len(history) for history in self.price_history.values())}"
        
        return summary

class CryptoAIAgent:
    def __init__(self, model_name: str = "mistral:7b", initial_cryptos=['bitcoin', 'ethereum', 'litecoin']):
        self.model_name = model_name
        self.price_manager = CryptoPriceManager(initial_cryptos)
        self.conversation_history = []
        
        # Test Ollama connection
        try:
            ollama.list()
            print(f"✅ Connected to Ollama. Using model: {model_name}")
        except Exception as e:
            print(f"❌ Error connecting to Ollama: {e}")
            print("Make sure Ollama is running and Mistral 7B is installed")
    
    def generate_response(self, user_input: str) -> str:
        """Generate AI response using Mistral 7B"""
        
        # Prepare context with current cryptocurrency data
        context = self.price_manager.get_price_summary()
        tracked_cryptos = ', '.join([crypto.replace('-', ' ').title() for crypto in self.price_manager.cryptocurrencies])
        
        # Create system prompt
        system_prompt = f"""You are a helpful cryptocurrency price monitoring AI assistant. You have access to current price data for multiple cryptocurrencies and can help users with:
1. Current cryptocurrency price information
2. Setting up price alerts for any supported crypto
3. Analyzing price trends and comparisons
4. Adding new cryptocurrencies to track
5. Answering questions about cryptocurrencies

Currently tracking: {tracked_cryptos}

Current Cryptocurrency Data:
{context}

Instructions:
- Be helpful and informative
- Use the provided crypto data to answer questions accurately
- If asked to set alerts, extract the price, cryptocurrency, and type (above/below) from the user's message
- Keep responses concise but informative
- Use relevant emojis to make responses engaging
- When comparing cryptocurrencies, use the current data provided
- If asked about a crypto not being tracked, suggest using the search function"""

        try:
            # Add user input to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Prepare messages for Ollama
            messages = [
                {"role": "system", "content": system_prompt},
                *self.conversation_history[-5:]  # Keep last 5 exchanges for context
            ]
            
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                stream=False
            )
            
            ai_response = response['message']['content']
            
            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            return f"Error generating response: {e}"
    
    def process_command(self, user_input: str) -> str:
        """Process user commands and return appropriate response"""
        user_input_lower = user_input.lower()
        
        # Handle price update requests
        if "update" in user_input_lower and "price" in user_input_lower:
            self.price_manager.update_prices()
            return self.price_manager.get_price_summary()
        
        # Handle cryptocurrency search
        if "search" in user_input_lower and ("crypto" in user_input_lower or "coin" in user_input_lower):
            # Extract search term (simple approach)
            words = user_input.split()
            search_term = None
            for i, word in enumerate(words):
                if word.lower() in ["search", "find", "look"]:
                    if i + 1 < len(words):
                        search_term = " ".join(words[i+1:])
                        break
            
            if search_term:
                results = self.price_manager.search_cryptocurrency(search_term)
                if results:
                    response = f"🔍 Search results for '{search_term}':\n\n"
                    for result in results:
                        response += f"💎 {result['name']} ({result['symbol']})\n"
                        response += f"   ID: {result['id']}\n"
                        response += f"   Rank: #{result['market_cap_rank']}\n\n"
                    response += "Use the ID to add a cryptocurrency: 'add cardano' or 'track solana'"
                    return response
                else:
                    return f"❌ No results found for '{search_term}'"
            else:
                return "❌ Please specify what to search for: 'search for cardano'"
        
        # Handle adding new cryptocurrencies
        if any(word in user_input_lower for word in ["add", "track", "include"]) and ("crypto" in user_input_lower or "coin" in user_input_lower or len(user_input.split()) <= 3):
            # Extract crypto name (simple approach)
            words = user_input_lower.split()
            crypto_candidates = [word for word in words if word not in ["add", "track", "include", "crypto", "cryptocurrency", "coin"]]
            
            if crypto_candidates:
                crypto_id = crypto_candidates[0]
                self.price_manager.add_cryptocurrency(crypto_id)
                return f"✅ Added {crypto_id} to tracking. Updating prices..."
            else:
                return "❌ Please specify which cryptocurrency to add: 'add cardano' or 'track solana'"
        
        # Handle alert setting (enhanced parsing for multiple cryptos)
        if "alert" in user_input_lower or "notify" in user_input_lower:
            try:
                # Extract cryptocurrency mention
                crypto = "bitcoin"  # default
                for tracked_crypto in self.price_manager.cryptocurrencies:
                    if tracked_crypto in user_input_lower or tracked_crypto.replace('-', '') in user_input_lower:
                        crypto = tracked_crypto
                        break
                
                # Simple price extraction
                words = user_input_lower.split()
                price_candidates = []
                for word in words:
                    cleaned = word.replace('$', '').replace(',', '')
                    try:
                        price = float(cleaned)
                        price_candidates.append(price)
                    except ValueError:
                        continue
                
                if price_candidates:
                    target_price = price_candidates[0]
                    alert_type = "above" if "above" in user_input_lower or "over" in user_input_lower else "below"
                    self.price_manager.add_price_alert(target_price, crypto, alert_type)
                    crypto_display = crypto.replace('-', ' ').title()
                    return f"✅ Alert set! I'll notify you when {crypto_display} goes {alert_type} ${target_price:,.4f}"
                else:
                    return "❌ I couldn't find a price in your message. Please specify a price like 'Alert me when Bitcoin goes above $50000'"
                    
            except Exception as e:
                return f"❌ Error setting alert: {e}"
        
        # For other queries, use AI generation
        return self.generate_response(user_input)

def start_hourly_updates(agent):
    """Start the hourly price update scheduler"""
    schedule.every().hour.do(agent.price_manager.update_prices)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    # Run scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("⏰ Hourly price updates started!")

def chat_with_agent(agent):
    """Interactive chat interface with the AI agent"""
    print("\n" + "="*60)
    print("🤖 Cryptocurrency AI Agent - Interactive Chat")
    print("="*60)
    print("Commands you can try:")
    print("- 'What's the current Bitcoin price?'")
    print("- 'Update prices'")
    print("- 'Set an alert when Bitcoin goes above $60000'")
    print("- 'Add cardano' or 'track solana'")
    print("- 'Search for dogecoin'")
    print("- 'Compare Bitcoin and Ethereum'")
    print("- Type 'quit' to exit")
    print("="*60)
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Crypto monitoring will continue in the background.")
                break
            
            if not user_input:
                continue
            
            print("🤖 Agent: ", end="")
            response = agent.process_command(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def test_agent(agent):
    """Run some quick tests of the agent functionality"""
    print("\n🧪 Testing Cryptocurrency AI Agent...")
    
    # Test 1: Price summary
    print("\n1️⃣ Testing price summary:")
    print(agent.price_manager.get_price_summary())
    
    # Test 2: Search for a cryptocurrency
    print("\n2️⃣ Testing crypto search:")
    results = agent.price_manager.search_cryptocurrency("cardano")
    for result in results[:3]:
        print(f"Found: {result['name']} ({result['symbol']}) - ID: {result['id']}")
    
    # Test 3: Add a new cryptocurrency
    print("\n3️⃣ Testing add cryptocurrency:")
    agent.price_manager.add_cryptocurrency("cardano")
    
    # Test 4: Set an alert
    print("\n4️⃣ Testing price alert:")
    agent.price_manager.add_price_alert(50000, "bitcoin", "above")
    
    # Test 5: AI response
    print("\n5️⃣ Testing AI response:")
    response = agent.process_command("What's the best performing crypto today?")
    print(f"AI Response: {response}")
    
    print("\n✅ Tests completed!")

# Main execution
if __name__ == "__main__":
    # Initialize the agent with some popular cryptocurrencies
    agent = CryptoAIAgent(initial_cryptos=['bitcoin', 'ethereum', 'litecoin'])
    
    print("🚀 Cryptocurrency AI Agent initialized!")
    print("🔄 Fetching initial crypto prices...")
    
    # Get initial prices
    agent.price_manager.update_prices()
    
    # Start hourly updates
    start_hourly_updates(agent)
    
    # Run tests (uncomment to test)
    # test_agent(agent)
    
    # Start interactive chat
    chat_with_agent(agent)
    
    print("\n🎉 Cryptocurrency AI Agent is ready to use!")
    print("💡 The agent will automatically update crypto prices every hour.")
    print("🔔 Set price alerts and ask questions about any cryptocurrency!")

# Example usage functions:
"""
# Manual commands you can run:

# Update prices manually:
agent.price_manager.update_prices()

# Get current price summary:
print(agent.price_manager.get_price_summary())

# Search for a cryptocurrency:
results = agent.price_manager.search_cryptocurrency("polkadot")
print(results)

# Add a new cryptocurrency:
agent.price_manager.add_cryptocurrency("polkadot")

# Set a price alert:
agent.price_manager.add_price_alert(25.0, "polkadot", "above")

# Ask the AI a question:
response = agent.process_command("Which crypto has the highest 24h volume?")
print(response)

# Start interactive chat:
chat_with_agent(agent)
"""