import pymongo
from flask import request, session
import datetime

client = pymongo.MongoClient('mongodb+srv://test:test1234@cluster0.mrtn9d5.mongodb.net/')
userdb = client['userdb']
users = userdb.customers
recipes = userdb.recipes
wardrobe = userdb.wardrobe
tasks = userdb.tasks
motivation = userdb.motivation

def insert_data():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['pass']
        
        reg_user = {}
        reg_user['name'] = name
        reg_user['email'] = email
        reg_user['password'] = password
        reg_user['height'] = 0
        reg_user['weight'] = 0
        reg_user['bmi'] = 0
        reg_user['energy_level'] = 5  # Default energy level on scale of 1-10
        reg_user['dietary_preferences'] = []
        reg_user['created_at'] = datetime.datetime.now()
        
        if users.find_one({"email": email}) == None:
            users.insert_one(reg_user)
            return True
        else:
            return False

def check_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pass']
        
        user = {
            "email": email,
            "password": password
        }
        
        user_data = users.find_one(user)
        
        if user_data == None:
            return False, ""
        else:
            # Store in session
            session['username'] = user_data["name"]
            session['email'] = user_data["email"]
            return True, user_data["name"]

def get_user_data(username):
    """Get full user profile data"""
    return users.find_one({"name": username})

def update_user_profile(username, profile_data):
    """Update user profile with new data"""
    users.update_one(
        {"name": username},
        {"$set": profile_data}
    )
    return True

def calculate_bmi(username, height, weight):
    """Calculate and store BMI for a user"""
    # BMI = weight(kg) / height(m)²
    bmi = weight / ((height/100) ** 2)
    
    users.update_one(
        {"name": username},
        {"$set": {
            "height": height,
            "weight": weight,
            "bmi": round(bmi, 2)
        }}
    )
    
    return round(bmi, 2)

def get_recipes(dietary_preferences=None, ingredients=None):
    """Get recipes based on preferences and ingredients"""
    query = {}
    
    if dietary_preferences:
        query["dietary_tags"] = {"$in": dietary_preferences}
    
    if ingredients:
        query["ingredients"] = {"$in": ingredients}
    
    return list(recipes.find(query))

def get_wardrobe_items(username, category=None):
    """Get user's wardrobe items, optionally filtered by category"""
    query = {"username": username}
    
    if category:
        query["category"] = category
    
    return list(wardrobe.find(query))

def add_wardrobe_item(username, item_data):
    """Add a new item to user's wardrobe"""
    item_data["username"] = username
    wardrobe.insert_one(item_data)
    return True

def get_user_tasks(username):
    """Get all tasks for a user"""
    return list(tasks.find({"username": username}).sort("priority", -1))

def add_task(username, task_data):
    """Add a new task for user"""
    task_data["username"] = username
    task_data["created_at"] = datetime.datetime.now()
    tasks.insert_one(task_data)
    return True

def update_energy_level(username, level):
    """Update user's current energy level"""
    users.update_one(
        {"name": username},
        {"$set": {"energy_level": level}}
    )
    return True

def get_motivation_message(category, level):
    """Get appropriate motivation message based on category and level"""
    return motivation.find_one({"category": category, "level": level})