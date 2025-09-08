import requests
import json
from datetime import datetime
from collections import defaultdict
from chat_misteral import  get_crypto_price, get_orioles_roster, get_weather, get_orioles_schedule  
import re
import difflib


class MistralAgent:
    def __init__(self):
        self.conversation_history = []
        self.cached_data = {}
        self.current_roster = None
        
    def chat_ollama(self, prompt):
        try:
            response = requests.post('http://localhost:11434/api/generate',
                                   json={
                                       'model': 'mistral:7b',
                                       'prompt': prompt,
                                       'stream': False
                                   })
            return response.json()['response']
        except Exception as e:
            return f"Error: {e}"

    def get_detailed_orioles_roster(self):
        """Get roster with detailed position information"""
        try:
            response = requests.get("https://statsapi.mlb.com/api/v1/teams/110/roster/Active")
            data = response.json()
            
            players = []
            for player in data['roster']:
                player_info = {
                    'name': player['person']['fullName'],
                    'position': player['position']['abbreviation'],
                    'position_type': player['position']['type'],
                    'jersey': player.get('jerseyNumber', 'N/A'),
                    'id': player['person']['id']
                }
                players.append(player_info)
            
            # Cache the roster for player lookups
            self.current_roster = players
            return players
        except Exception as e:
            return f"Error fetching roster: {e}"
    
    def find_player_by_name(self, player_name):
        """Find a player in the roster by name (fuzzy matching)"""
        if not self.current_roster:
            roster = self.get_detailed_orioles_roster()
            if isinstance(roster, str):  # Error occurred
                return None
        
        player_name = player_name.lower().strip()
        
        # Exact match first
        for player in self.current_roster:
            if player_name in player['name'].lower():
                return player
        
        # Fuzzy matching for close names
        player_names = [player['name'] for player in self.current_roster]
        matches = difflib.get_close_matches(player_name, player_names, n=1, cutoff=0.6)
        
        if matches:
            for player in self.current_roster:
                if player['name'] == matches[0]:
                    return player
        
        return None
    
    def get_player_batting_stats(self, player_id, season=None):
        """Get batting statistics for a specific player"""
        if season is None:
            season = datetime.now().year
        
        try:
            # Get player stats for the current season
            url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
            params = {
                'stats': 'season',
                'group': 'hitting',
                'season': season
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'stats' not in data or not data['stats']:
                return None
            
            # Extract batting stats
            hitting_stats = data['stats'][0]
            if 'splits' not in hitting_stats or not hitting_stats['splits']:
                return None
                
            stats = hitting_stats['splits'][0]['stat']
            
            # Format the important batting statistics
            batting_info = {
                'games': stats.get('gamesPlayed', 0),
                'at_bats': stats.get('atBats', 0),
                'runs': stats.get('runs', 0),
                'hits': stats.get('hits', 0),
                'doubles': stats.get('doubles', 0),
                'triples': stats.get('triples', 0),
                'home_runs': stats.get('homeRuns', 0),
                'rbi': stats.get('rbi', 0),
                'stolen_bases': stats.get('stolenBases', 0),
                'batting_avg': stats.get('avg', '.000'),
                'obp': stats.get('obp', '.000'),
                'slg': stats.get('slg', '.000'),
                'ops': stats.get('ops', '.000'),
                'strikeouts': stats.get('strikeOuts', 0),
                'walks': stats.get('baseOnBalls', 0)
            }
            
            return batting_info
            
        except Exception as e:
            return f"Error fetching batting stats: {e}"
    
    def format_batting_stats(self, player, stats):
        """Format batting stats into a readable report"""
        if isinstance(stats, str):  # Error message
            return stats
        
        if not stats:
            return f"No batting statistics found for {player['name']} this season."
        
        report = []
        report.append(f"BATTING STATISTICS: {player['name']}")
        report.append(f"Position: {player['position']} | Jersey: #{player['jersey']}")
        report.append("=" * 50)
        
        # Basic stats
        report.append("\nBATTING PERFORMANCE:")
        report.append(f"  Games Played: {stats['games']}")
        report.append(f"  At Bats: {stats['at_bats']}")
        report.append(f"  Hits: {stats['hits']}")
        report.append(f"  Runs: {stats['runs']}")
        report.append(f"  RBI: {stats['rbi']}")
        
        # Power numbers
        report.append("\nPOWER NUMBERS:")
        report.append(f"  Doubles: {stats['doubles']}")
        report.append(f"  Triples: {stats['triples']}")
        report.append(f"  Home Runs: {stats['home_runs']}")
        report.append(f"  Stolen Bases: {stats['stolen_bases']}")
        
        # Rate stats
        report.append("\nRATE STATISTICS:")
        report.append(f"  Batting Average: {stats['batting_avg']}")
        report.append(f"  On-Base Percentage: {stats['obp']}")
        report.append(f"  Slugging Percentage: {stats['slg']}")
        report.append(f"  OPS: {stats['ops']}")
        
        # Discipline
        report.append("\nPLATE DISCIPLINE:")
        report.append(f"  Walks: {stats['walks']}")
        report.append(f"  Strikeouts: {stats['strikeouts']}")
        
        return "\n".join(report)
    
    def regex_pattern_handler(self, user_input):
        """Handle regex patterns for different query types"""
        
        # Define pattern groups for better organization
        pattern_groups = {
            'what_questions': [
                r"what is (.+?)(?:'s|s)?\s+(?:batting average|avg|home runs?|hr|rbi|ops|obp|slg|stats?)",
                r"what's (.+?)(?:'s|s)?\s+(?:batting average|avg|home runs?|hr|rbi|ops|obp|slg|stats?)",
                r"what is (.+?) (?:batting|hitting)",
                r"what's (.+?) (?:batting|hitting)",
            ],
            
            'possessive_forms': [
                r"(.+?)(?:'s|s)\s+(?:batting average|avg|home runs?|hr|rbi|ops|obp|slg|stats?)",
                r"(.+?)(?:'s|s)\s+(?:batting|hitting|performance)",
            ],
            
            'show_me_patterns': [
                r"show me (.+?)(?:'s|s)?\s+(?:stats?|batting|hitting|performance)",
                r"show me (.+)",
            ],
            
            'how_questions': [
                r"how (?:is|'s) (.+) (?:doing|batting|hitting)",
            ],
            
            'stats_requests': [
                r"(?:stats?|batting stats?|hitting stats?) for (.+)",
                r"(.+) (?:stats?|batting|hitting|performance)",
                r"(.+) (?:avg|average|home runs?|hr|rbi|ops|obp|slg)",
            ],
            
            'general_patterns': [
                r"tell me about (.+?)(?:'s|s)?\s+(?:stats?|batting|hitting)",
                r"give me (.+?)(?:'s|s)?\s+(?:stats?|batting|hitting)",
                r"(.+) numbers",
                r"(.+) season stats?",
            ]
        }
        
        # Try each pattern group
        for group_name, patterns in pattern_groups.items():
            for pattern in patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    return {
                        'player_name': match.group(1).strip(),
                        'pattern_group': group_name,
                        'matched_pattern': pattern
                    }
        
        return None
    
    def clean_player_name(self, raw_name):
        """Clean and normalize extracted player name"""
        if not raw_name:
            return None
            
        # Remove common filler words
        cleaned = re.sub(r'\b(the|orioles?|player|stats?|batting|hitting|what|is|whats|show|me|tell|give|about)\b', 
                        '', raw_name, flags=re.IGNORECASE)
        
        # Remove possessive endings and punctuation
        cleaned = re.sub(r"[''`]s?$", '', cleaned)
        cleaned = re.sub(r'[^\w\s]', '', cleaned)  # Remove special characters except spaces
        
        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned if cleaned else None
    
    def extract_player_name_from_query(self, user_input):
        """Extract player name from user query using regex handler"""
        
        # Use the regex handler to find matches
        regex_result = self.regex_pattern_handler(user_input)
        
        if not regex_result:
            return None
        
        # Clean the extracted player name
        player_name = self.clean_player_name(regex_result['player_name'])
        
        # Optional: Log which pattern matched for debugging
        # print(f"[DEBUG] Matched pattern group: {regex_result['pattern_group']}")
        
        return player_name
    
    def think_defensive_arrangement(self, roster):
        """Think through optimal defensive positioning"""
        
        # Organize players by position
        position_groups = defaultdict(list)
        for player in roster:
            pos = player['position']
            position_groups[pos].append(player)
        
        # Define defensive positions needed
        defensive_positions = {
            'C': 'Catcher',
            '1B': 'First Base', 
            '2B': 'Second Base',
            '3B': 'Third Base',
            'SS': 'Shortstop',
            'LF': 'Left Field',
            'CF': 'Center Field', 
            'RF': 'Right Field',
            'P': 'Pitcher'
        }
        
        # Think through the arrangement
        defensive_lineup = {}
        reasoning = []
        
        reasoning.append("THINKING PROCESS:")
        reasoning.append("Analyzing roster to create optimal defensive arrangement...")
        
        # Fill primary positions first
        for pos_code, pos_name in defensive_positions.items():
            if pos_code in position_groups and position_groups[pos_code]:
                # Choose first available player at this position
                chosen_player = position_groups[pos_code][0]
                defensive_lineup[pos_code] = chosen_player
                reasoning.append(f"✓ {pos_name}: {chosen_player['name']} (primary position)")
            else:
                # Need to find alternative
                reasoning.append(f"⚠ {pos_name}: No primary {pos_code} available, need to find alternative")
        
        # Handle missing positions with versatile players
        self._fill_missing_positions(defensive_lineup, position_groups, reasoning)
        
        return defensive_lineup, reasoning
    
    def _fill_missing_positions(self, lineup, position_groups, reasoning):
        """Fill missing positions with versatile players"""
        
        # Common position flexibility in baseball
        position_flexibility = {
            'OF': ['LF', 'CF', 'RF'],  # Outfielders can play any OF position
            'IF': ['1B', '2B', '3B', 'SS'],  # Infielders have some flexibility
            'MI': ['2B', 'SS'],  # Middle infielders
            'CI': ['1B', '3B']   # Corner infielders
        }
        
        needed_positions = []
        for pos in ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'P']:
            if pos not in lineup:
                needed_positions.append(pos)
        
        if needed_positions:
            reasoning.append(f"Missing positions: {', '.join(needed_positions)}")
            
            # Look for utility players or flexible positions
            for pos in needed_positions:
                if pos in ['LF', 'CF', 'RF'] and 'OF' in position_groups:
                    if position_groups['OF']:
                        player = position_groups['OF'].pop(0)
                        lineup[pos] = player
                        reasoning.append(f"✓ {pos}: {player['name']} (utility outfielder)")
                
                elif pos in ['2B', 'SS'] and 'MI' in position_groups:
                    if position_groups['MI']:
                        player = position_groups['MI'].pop(0)
                        lineup[pos] = player
                        reasoning.append(f"✓ {pos}: {player['name']} (middle infielder)")
    
    def create_defensive_report(self, lineup, reasoning):
        """Generate a comprehensive defensive report"""
        
        report = []
        report.append("BALTIMORE ORIOLES DEFENSIVE ARRANGEMENT")
        report.append("=" * 45)
        
        # Infield
        report.append("\nINFIELD:")
        infield_positions = [('P', 'Pitcher'), ('C', 'Catcher'), ('1B', 'First Base'), 
                           ('2B', 'Second Base'), ('3B', 'Third Base'), ('SS', 'Shortstop')]
        
        for pos_code, pos_name in infield_positions:
            if pos_code in lineup:
                player = lineup[pos_code]
                report.append(f"  {pos_name}: #{player['jersey']} {player['name']}")
            else:
                report.append(f"  {pos_name}: [POSITION VACANT]")
        
        # Outfield
        report.append("\nOUTFIELD:")
        outfield_positions = [('LF', 'Left Field'), ('CF', 'Center Field'), ('RF', 'Right Field')]
        
        for pos_code, pos_name in outfield_positions:
            if pos_code in lineup:
                player = lineup[pos_code]
                report.append(f"  {pos_name}: #{player['jersey']} {player['name']}")
            else:
                report.append(f"  {pos_name}: [POSITION VACANT]")
        
        # Add reasoning
        report.append("\nCOACH'S NOTES:")
        for note in reasoning:
            report.append(f"  {note}")
        
        return "\n".join(report)
    
    def think_and_act(self, user_input):
        """Main thinking and acting function"""
        input_lower = user_input.lower()
        
        # Check for weather requests
        if any(phrase in input_lower for phrase in ['weather', 'forecast']):
            print("[ACTION] Fetching weather...")
            match = re.search(r'in ([\w\s]+)', user_input, re.IGNORECASE)
            city = match.group(1).strip() if match else 'Baltimore'
            return get_weather(city)
        
        # Check for crypto price requests
        if any(phrase in input_lower for phrase in ['bitcoin', 'bitcoin price', 'btc', 'litecoin', 'ltc']):
            print("[ACTION] Fetching Bitcoin price...")
            match = re.search(r'(bitcoin|btc|litecoin|ltc)', input_lower)
            crypto = match.group(1).strip()
            return get_crypto_price(crypto)
        
        # Check for player batting stats requests
        if any(phrase in input_lower for phrase in ['stats', 'batting', 'performance', 'how is', 'hitting', 'players']):
            player_name = self.extract_player_name_from_query(user_input)
            if player_name is None:
            # Skip this block if no player name is found
                pass
            else:
                print("player name is ", player_name)
                print(f"[THINKING] User wants batting stats for: {player_name}")
                print("[ACTION] Searching for player...")
                
                player = self.find_player_by_name(player_name)
            
                if not player:
                     return f"Could not find player '{player_name}' on the current Orioles roster. Please check the spelling or try a different name."
                
                print(f"[ACTION] Found player: {player['name']}")
                print("[ACTION] Fetching batting statistics...")
                
                batting_stats = self.get_player_batting_stats(player['id'])
                stats_report = self.format_batting_stats(player, batting_stats)
            
            # Get AI commentary on the stats
            if batting_stats and not isinstance(batting_stats, str):
                enhanced_prompt = f"""You are a baseball analyst. Here are the current season batting statistics for Baltimore Orioles player {player['name']}:

    {stats_report}

    Please provide insightful commentary about this player's performance, noting strengths, areas for improvement, and how these numbers compare to typical MLB standards."""

                print("[ACTION] Getting expert analysis...")
                commentary = self.chat_ollama(enhanced_prompt)
                
                return f"{stats_report}\n\nEXPERT ANALYSIS:\n{commentary}"
            else:
                return stats_report
            player_name = self.extract_player_name_from_query(user_input)
            print("player name is ", player_name)
            if player_name:
                print(f"[THINKING] User wants batting stats for: {player_name}")
                print("[ACTION] Searching for player...")
                
                player = self.find_player_by_name(player_name)
                
                # if not player:
                #     return f"Could not find player '{player_name}' on the current Orioles roster. Please check the spelling or try a different name."
                
                print(f"[ACTION] Found player: {player['name']}")
                print("[ACTION] Fetching batting statistics...")
                
                batting_stats = self.get_player_batting_stats(player['id'])
                stats_report = self.format_batting_stats(player, batting_stats)
                
                # Get AI commentary on the stats
                if batting_stats and not isinstance(batting_stats, str):
                    enhanced_prompt = f"""You are a baseball analyst. Here are the current season batting statistics for Baltimore Orioles player {player['name']}:

{stats_report}

Please provide insightful commentary about this player's performance, noting strengths, areas for improvement, and how these numbers compare to typical MLB standards."""

                    print("[ACTION] Getting expert analysis...")
                    commentary = self.chat_ollama(enhanced_prompt)
                    
                    return f"{stats_report}\n\nEXPERT ANALYSIS:\n{commentary}"
                else:
                    return stats_report
        
        # Check for defensive arrangement requests
        if any(phrase in input_lower for phrase in ['defense', 'defensive lineup', 'field arrangement', 'starting lineup', 'players', 'roster']):
            print("[THINKING] User wants defensive arrangement...")
            print("[ACTION] Fetching Orioles roster...")
            
            roster = self.get_detailed_orioles_roster()
            if isinstance(roster, str):  # Error occurred
                return roster
            
            print("[THINKING] Analyzing player positions...")
            print("[ACTION] Creating optimal defensive arrangement...")
            
            defensive_lineup, reasoning = self.think_defensive_arrangement(roster)
            defensive_report = self.create_defensive_report(defensive_lineup, reasoning)
            
            # Use Mistral to provide commentary
            enhanced_prompt = f"""You are a baseball analyst. Here's the Baltimore Orioles defensive arrangement I've created:

{defensive_report}

Please provide insightful commentary about this defensive arrangement, noting any strengths, potential concerns, or interesting observations about the lineup."""

            print("[ACTION] Getting expert analysis...")
            commentary = self.chat_ollama(enhanced_prompt)
            
            return f"{defensive_report}\n\nEXPERT ANALYSIS:\n{commentary}"
        
        # Handle other requests normally
        else:
            return self.handle_regular_query(user_input)
    
    def handle_regular_query(self, user_input):
        """Handle non-specific queries"""
        live_data = self.smart_data_lookup(user_input)
        
        if live_data:
            live_data_text = "\n\n".join(live_data)
            enhanced_prompt = f"""LIVE DATA: {live_data_text}

User question: "{user_input}"

Use the live data above to answer."""
            return self.chat_ollama(enhanced_prompt)
        else:
            return self.chat_ollama(user_input)
    
    def smart_data_lookup(self, user_input):
        """Your existing data lookup functions"""
        # Bitcoin, weather, etc. - same as before
        pass

# Usage
def main():
    agent = MistralAgent()
    
    print("Baltimore Orioles AI Agent - Enhanced with Team Stats")
    print("Commands you can try:")
    print("\n--- Individual Player Stats ---")
    print("- 'Show me Adley Rutschman stats'")
    print("- 'How is Gunnar Henderson batting?'")
    print("- 'What was Adley Rutschman batting average in 2023?'")
    print("- 'Show me Gunnar Henderson 2022 stats'")
    print("\n--- Team Rankings (Now More Efficient!) ---")
    print("- 'Rank Orioles by batting average'")
    print("- 'Top 5 home run hitters'")
    print("- 'Best RBI players'")
    print("- 'Top 10 OPS leaders'")
    print("- 'Rank by hits in 2023'")
    print("- 'Rank orioles batting average'")
    print("\n--- Other Features ---")
    print("- 'Show me the Orioles defensive lineup'")
    print("- 'Weather in Baltimore'")
    print("- 'Bitcoin price'")
    print("\nType 'quit' to exit\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        
        response = agent.think_and_act(user_input)
        print(f"\nAgent: {response}\n")

if __name__ == "__main__":
    main()