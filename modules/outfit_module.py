import db
import requests
import random

class OutfitRecommender:
    def __init__(self):
        self.weather_api_key = "your_weather_api_key"  # Replace with actual API key
        self.weather_categories = {
            "hot": {"min_temp": 30},
            "warm": {"min_temp": 20, "max_temp": 30},
            "mild": {"min_temp": 15, "max_temp": 20},
            "cool": {"min_temp": 5, "max_temp": 15},
            "cold": {"max_temp": 5},
            "rainy": {"conditions": ["rain", "drizzle", "thunderstorm"]},
            "snowy": {"conditions": ["snow", "sleet"]},
            "windy": {"min_wind": 20}  # Wind speed in km/h
        }
        
    def get_recommendations(self, username, weather=None, occasion=None):
        """
        Get outfit recommendations based on weather and occasion
        """
        # Get user's wardrobe items
        wardrobe_items = db.get_wardrobe_items(username)
        
        if not wardrobe_items:
            return {
                "status": "no_items",
                "message": "Please add items to your wardrobe first."
            }
            
        # If weather not provided, try to get it from API
        weather_category = weather
        if not weather_category:
            weather_category = self._get_current_weather_category(username)
            
        # Filter items by weather category
        suitable_items = self._filter_by_weather(wardrobe_items, weather_category)
        
        # If occasion provided, further filter
        if occasion:
            suitable_items = self._filter_by_occasion(suitable_items, occasion)
            
        # Create outfit combinations
        outfits = self._create_outfits(suitable_items)
        
        return {
            "status": "success",
            "weather": weather_category,
            "occasion": occasion,
            "outfits": outfits
        }
        
    def _get_current_weather_category(self, username):
        """Get current weather for user's location and categorize it"""
        # In real app, you'd get location from user profile
        user_data = db.get_user_data(username)
        location = user_data.get('location', 'New York')  # Default
        
        try:
            # Call weather API (e.g., OpenWeatherMap)
            # response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.weather_api_key}&units=metric")
            # data = response.json()
            
            # For demo, return a default weather
            # Normally would parse API response:
            # temp = data["main"]["temp"]
            # conditions = data["weather"][0]["main"].lower()
            # wind_speed = data["wind"]["speed"] * 3.6  # Convert from m/s to km/h
            
            # For demo, hardcode a weather category
            return "mild"
            
        except Exception as e:
            print(f"Weather API error: {e}")
            return "mild"  # Default fallback
        
    def _filter_by_weather(self, items, weather_category):
        """Filter wardrobe items by weather category"""
        return [item for item in items if weather_category in item.get('suitable_weather', [])]
        
    def _filter_by_occasion(self, items, occasion):
        """Filter wardrobe items by occasion"""
        return [item for item in items if occasion in item.get('suitable_occasions', [])]
        
    def _create_outfits(self, items):
        """Create outfit combinations from filtered items"""
        # Group items by category
        categories = {}
        for item in items:
            category = item.get('category')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
            
        # Create up to 3 outfit combinations
        outfits = []
        max_outfits = min(3, len(items) // 3)  # Need at least 3 items per outfit
        
        for _ in range(max_outfits):
            outfit = {}
            for category, items in categories.items():
                if items:  # If category has items
                    outfit[category] = random.choice(items)
            
            # Only add if outfit has minimum categories (e.g., top, bottom, shoes)
            required_categories = {'top', 'bottom', 'shoes'}
            if all(category in outfit for category in required_categories):
                outfits.append(outfit)
                
        return outfits
        
    def add_wardrobe_item(self, username, item_data):
        """Add item to user's wardrobe"""
        return db.add_wardrobe_item(username, item_data)