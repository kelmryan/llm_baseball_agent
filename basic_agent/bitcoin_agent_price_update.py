# Bitcoin AI Agent with Mistral 7B
# A comprehensive Bitcoin price monitoring and analysis agent

# ## Installation and Setup
# First, install required packages (run this cell first)

# !pip install requests ollama schedule datetime threading

# ## Import Required Libraries

import requests
import json
import time
import schedule
import threading
from datetime import datetime, timedelta
import ollama
from typing import Dict, List, Optional

# ## Bitcoin Price Manager Class

class BitcoinPriceManager:
    def __init__(self):
        self.current_price = None
        self.price_history = []
        self.price_alerts = []
        self.last_update = None
        
    def fetch_bitcoin_price(self) -> Dict:
        """Fetch current Bitcoin price from CoinGecko API"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            bitcoin_data = data['bitcoin']
            
            price_info = {
                'price': bitcoin_data['usd'],
                '24h_change': bitcoin_data.get('usd_24h_change', 0),
                'timestamp': datetime.now(),
                'last_updated': bitcoin_data.get('last_updated_at', int(time.time()))
            }
            
            return price_info
            
        except Exception as e:
            print(f"Error fetching Bitcoin price: {e}")
            return None
    
    def update_price(self):
        """Update the current Bitcoin price and store in history"""
        price_info = self.fetch_bitcoin_price()
        if price_info:
            self.current_price = price_info
            self.price_history.append(price_info)
            self.last_update = datetime.now()
            
            # Keep only last 168 hours (7 days) of data
            if len(self.price_history) > 168:
                self.price_history = self.price_history[-168:]
            
            print(f"✅ Bitcoin price updated: ${price_info['price']:,.2f} at {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check alerts
            self.check_alerts()
        else:
            print("❌ Failed to update Bitcoin price")
    
    def add_price_alert(self, target_price: float, alert_type: str = "above"):
        """Add a price alert (above or below target price)"""
        alert = {
            'target_price': target_price,
            'type': alert_type,  # 'above' or 'below'
            'created_at': datetime.now(),
            'triggered': False
        }
        self.price_alerts.append(alert)
        print(f"🔔 Alert set: Notify when Bitcoin goes {alert_type} ${target_price:,.2f}")
    
    def check_alerts(self):
        """Check if any price alerts should be triggered"""
        if not self.current_price:
            return
            
        current = self.current_price['price']
        
        for alert in self.price_alerts:
            if alert['triggered']:
                continue
                
            if alert['type'] == 'above' and current >= alert['target_price']:
                print(f"🚨 ALERT: Bitcoin price (${current:,.2f}) is now ABOVE your target of ${alert['target_price']:,.2f}!")
                alert['triggered'] = True
                
            elif alert['type'] == 'below' and current <= alert['target_price']:
                print(f"🚨 ALERT: Bitcoin price (${current:,.2f}) is now BELOW your target of ${alert['target_price']:,.2f}!")
                alert['triggered'] = True
    
    def get_price_summary(self) -> str:
        """Get a formatted summary of current Bitcoin price and recent changes"""
        if not self.current_price:
            return "No price data available. Please update the price first."
        
        current = self.current_price
        summary = f"""
📊 Bitcoin Price Summary (Last Updated: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')})

💰 Current Price: ${current['price']:,.2f}
📈 24h Change: {current['24h_change']:+.2f}%
🕒 Data Age: {(datetime.now() - self.last_update).total_seconds() / 60:.1f} minutes old

🔔 Active Alerts: {len([a for a in self.price_alerts if not a['triggered']])}
📊 Price History Points: {len(self.price_history)}
"""
        
        # Add recent trend if we have enough data
        if len(self.price_history) >= 2:
            recent_change = self.price_history[-1]['price'] - self.price_history[-2]['price']
            trend = "📈 Rising" if recent_change > 0 else "📉 Falling" if recent_change < 0 else "➡️ Stable"
            summary += f"\n🎯 Recent Trend: {trend} (${recent_change:+.2f} from last update)"
        
        return summary

# ## AI Agent Class

class BitcoinAIAgent:
    def __init__(self, model_name: str = "mistral:7b"):
        self.model_name = model_name
        self.price_manager = BitcoinPriceManager()
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
        
        # Prepare context with current Bitcoin data
        context = self.price_manager.get_price_summary()
        
        # Create system prompt
        system_prompt = f"""You are a helpful Bitcoin price monitoring AI assistant. You have access to current Bitcoin price data and can help users with:
1. Current Bitcoin price information
2. Setting up price alerts
3. Analyzing price trends
4. Answering questions about Bitcoin

Current Bitcoin Data:
{context}

Instructions:
- Be helpful and informative
- Use the provided Bitcoin data to answer questions accurately
- If asked to set alerts, extract the price and type (above/below) from the user's message
- Keep responses concise but informative
- Use relevant emojis to make responses engaging"""

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
            self.price_manager.update_price()
            return self.price_manager.get_price_summary()
        
        # Handle alert setting (simple parsing)
        if "alert" in user_input_lower or "notify" in user_input_lower:
            try:
                # Simple price extraction (you can make this more sophisticated)
                words = user_input_lower.split()
                price_candidates = [word.replace('$', '').replace(',', '') for word in words if word.replace('$', '').replace(',', '').replace('.', '').isdigit()]
                
                if price_candidates:
                    target_price = float(price_candidates[0])
                    alert_type = "above" if "above" in user_input_lower or "over" in user_input_lower else "below"
                    self.price_manager.add_price_alert(target_price, alert_type)
                    return f"✅ Alert set! I'll notify you when Bitcoin goes {alert_type} ${target_price:,.2f}"
                else:
                    return "❌ I couldn't find a price in your message. Please specify a price like 'Alert me when Bitcoin goes above $50000'"
                    
            except Exception as e:
                return f"❌ Error setting alert: {e}"
        
        # For other queries, use AI generation
        return self.generate_response(user_input)

# ## Initialize the Bitcoin AI Agent

# Create the agent instance
agent = BitcoinAIAgent()

print("🚀 Bitcoin AI Agent initialized!")
print("🔄 Fetching initial Bitcoin price...")

# Get initial price
agent.price_manager.update_price()

# ## Set up Hourly Price Updates

def start_hourly_updates():
    """Start the hourly price update scheduler"""
    schedule.every().hour.do(agent.price_manager.update_price)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    # Run scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("⏰ Hourly price updates started!")

# Start the scheduler
start_hourly_updates()

# ## Interactive Chat Interface

def chat_with_agent():
    """Interactive chat interface with the AI agent"""
    print("\n" + "="*60)
    print("🤖 Bitcoin AI Agent - Interactive Chat")
    print("="*60)
    print("Commands you can try:")
    print("- 'What's the current Bitcoin price?'")
    print("- 'Update the price'")
    print("- 'Set an alert when Bitcoin goes above $60000'")
    print("- 'Alert me when Bitcoin drops below $40000'")
    print("- 'Show me the price summary'")
    print("- Type 'quit' to exit")
    print("="*60)
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Bitcoin monitoring will continue in the background.")
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

# ## Quick Test Functions

def test_agent():
    """Run some quick tests of the agent functionality"""
    print("\n🧪 Testing Bitcoin AI Agent...")
    
    # Test 1: Price summary
    print("\n1️⃣ Testing price summary:")
    print(agent.price_manager.get_price_summary())
    
    # Test 2: Set an alert
    print("\n2️⃣ Testing price alert:")
    agent.price_manager.add_price_alert(50000, "above")
    
    # Test 3: AI response
    print("\n3️⃣ Testing AI response:")
    response = agent.process_command("What's the current Bitcoin price?")
    print(f"AI Response: {response}")
    
    print("\n✅ Tests completed!")

# ## Usage Examples

# Uncomment the lines below to run different parts of the agent:

# Run tests
# test_agent()

# Start interactive chat
# chat_with_agent()

# Manual commands (you can run these in separate cells):
print("\n📋 Manual Command Examples:")
print("Run these commands in separate cells to interact with the agent:")
print()
print("# Update Bitcoin price manually:")
print("# agent.price_manager.update_price()")N
print()
print("# Get current price summary:")
print("# print(agent.price_manager.get_price_summary())")
print()
print("# Set a price alert:")
print("# agent.price_manager.add_price_alert(55000, 'above')")
print()
print("# Ask the AI a question:")
print("# response = agent.process_command('Should I buy Bitcoin now?')")
print("# print(response)")
print()
print("# Start interactive chat:")
print("# chat_with_agent()")

print("\n🎉 Bitcoin AI Agent is ready to use!")
print("💡 The agent will automatically update Bitcoin prices every hour.")
print("🔔 Set price alerts and ask questions about Bitcoin anytime!")