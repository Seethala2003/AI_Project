import db
import random

class FoodRecommender:
    def __init__(self):
        # You might want to initialize with recipes from a dataset
        self.meal_types = ["breakfast", "lunch", "dinner", "snack"]
        
    def get_recommendations(self, username, ingredients=None, dietary_restrictions=None):
        """
        Get food recommendations based on user profile, available ingredients,
        and dietary restrictions
        """
        user_data = db.get_user_data(username)
        bmi = user_data.get('bmi', 0)
        
        # If BMI not calculated yet, return message to complete profile
        if bmi == 0:
            return {
                "status": "incomplete_profile",
                "message": "Please complete your profile with height and weight to get personalized recommendations."
            }
            
        # Get dietary category based on BMI
        dietary_category = self._get_dietary_category(bmi)
        
        # Get recipes from database matching criteria
        recipes = db.get_recipes(dietary_restrictions, ingredients)
        
        # Filter by dietary category
        suitable_recipes = [r for r in recipes if r.get('dietary_category') == dietary_category]
        
        # If no suitable recipes, fallback to general recipes
        if not suitable_recipes and recipes:
            suitable_recipes = recipes
            
        # Organize by meal type
        recommendations = {}
        for meal_type in self.meal_types:
            meal_recipes = [r for r in suitable_recipes if r.get('meal_type') == meal_type]
            if meal_recipes:
                # Select random recipes for variety
                recommendations[meal_type] = random.sample(
                    meal_recipes, 
                    min(3, len(meal_recipes))
                )
            else:
                recommendations[meal_type] = []
                
        return {
            "status": "success",
            "bmi": bmi,
            "dietary_category": dietary_category,
            "recommendations": recommendations
        }
        
    def _get_dietary_category(self, bmi):
        """Map BMI to dietary category"""
        if bmi < 18.5:
            return "underweight"
        elif bmi < 25:
            return "normal"
        elif bmi < 30:
            return "overweight"
        else:
            return "obese"
            
    def calculate_bmi(self, username, height, weight):
        """Calculate BMI for a user"""
        return db.calculate_bmi(username, height, weight)