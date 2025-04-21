from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import threading
import os
import json
import re
from datetime import datetime

# Import functions from demoAI.py
from demoAI import (
    speak, process_voice_query, 
    get_users, save_users, 
    get_tasks, save_tasks, 
    get_energy_levels, save_energy_levels,
    get_user_tasks, add_task, mark_task_complete,
    get_energy_level, update_energy_level,
    calculate_bmi, 
    handle_task_management, handle_outfit_recommendation, 
    handle_food_recommendation, handle_motivation
)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

app = Flask(__name__)
app.secret_key = '1b780d66cdf1b88a7ffe8b1991bf0fe3'  # Replace with a secure key in production

# Initialize database files if they don't exist
USER_DB_FILE = 'data/users.json'
TASK_DB_FILE = 'data/tasks.json'
ENERGY_DB_FILE = 'data/energy_levels.json'

for file_path in [USER_DB_FILE, TASK_DB_FILE, ENERGY_DB_FILE]:
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({}, f)

# Speech functions
def speak_in_thread(text):
    """Start speech in a separate thread to avoid blocking the main thread"""
    thread = threading.Thread(target=speak, args=(text,))
    thread.daemon = True
    thread.start()
    return thread

# Task management helper functions
def extract_task_from_query(query):
    """Extract task details from the user query with improved pattern matching"""
    query = query.lower()
    task_info = None
    
    # More flexible patterns for task detection
    task_patterns = [
        r"add task\s+(.+)", 
        r"add\s+(.+?)\s+to my task",
        r"create task\s+(.+)",
        r"remind me to\s+(.+)",
        r"new task\s+(.+)",
        r"add to-do\s+(.+)"
    ]
    
    for pattern in task_patterns:
        match = re.search(pattern, query)
        if match:
            task_text = match.group(1).strip()
            if task_text:
                # Extract priority and energy
                priority = "medium"
                if any(term in query for term in ["urgent", "important", "high priority"]):
                    priority = "high"
                elif any(term in query for term in ["low priority", "not urgent"]):
                    priority = "low"
                
                energy = 5
                if "high energy" in query:
                    energy = 8
                elif "low energy" in query:
                    energy = 3
                
                task_info = {
                    "task_text": task_text,
                    "priority": priority,
                    "energy": energy
                }
                break
    
    return task_info

def reschedule_tasks(username, energy_level):
    """Prioritize tasks based on user's current energy level"""
    tasks = get_user_tasks(username)
    
    # Sort tasks by priority and energy required
    high_priority = []
    medium_priority = []
    low_priority = []
    
    for task in tasks:
        if task.get('energy', 5) <= energy_level and not task.get('completed', False):
            if task.get('priority') == 'high':
                high_priority.append(task)
            elif task.get('priority') == 'medium':
                medium_priority.append(task)
            else:
                low_priority.append(task)
    
    # Combine tasks in priority order
    scheduled_tasks = high_priority + medium_priority + low_priority
    return scheduled_tasks

def get_tasks_summary(username):
    """Get a formatted summary of user's tasks"""
    if not username:
        return "Please log in to view your tasks."
        
    tasks = get_user_tasks(username)
    
    # Filter incomplete tasks
    incomplete_tasks = [task for task in tasks if not task.get('completed', False)]
    
    if not incomplete_tasks:
        return "You don't have any pending tasks. Great job!"
    
    # Sort by priority
    high_priority = []
    medium_priority = []
    low_priority = []
    
    for task in incomplete_tasks:
        if task.get('priority') == 'high':
            high_priority.append(task)
        elif task.get('priority') == 'medium':
            medium_priority.append(task)
        else:
            low_priority.append(task)
    
    # Format response
    response = "Here are your current tasks:\n"
    
    # Add high priority tasks
    if high_priority:
        response += "\nHigh Priority:\n"
        for task in high_priority:
            response += f"- {task['name']}\n"
    
    # Add medium priority tasks
    if medium_priority:
        response += "\nMedium Priority:\n"
        for task in medium_priority:
            response += f"- {task['name']}\n"
    
    # Add low priority tasks
    if low_priority:
        response += "\nLow Priority:\n"
        for task in low_priority:
            response += f"- {task['name']}\n"
    
    return response

def check_urgent_tasks(username):
    """Check for urgent (high priority) tasks"""
    if not username:
        return None
        
    tasks = get_user_tasks(username)
    
    # Find high priority incomplete tasks
    urgent_tasks = [task for task in tasks if task.get('priority') == 'high' and not task.get('completed', False)]
    
    if urgent_tasks:
        if len(urgent_tasks) == 1:
            return f"Reminder: You have an urgent task that needs attention: '{urgent_tasks[0].get('name')}'."
        else:
            return f"Reminder: You have {len(urgent_tasks)} urgent tasks that need attention."
    
    return None

# Food recommendation helper functions
def get_food_recommendations(bmi):
    """Get food recommendations based on BMI"""
    if bmi < 18.5:
        return [
            "High-calorie, nutritious meals like avocado toast with eggs",
            "Protein smoothies with banana, peanut butter and milk",
            "Trail mix with nuts, dried fruits and dark chocolate",
            "Oatmeal with honey, nuts and fruits"
        ]
    elif bmi < 25:
        return [
            "Balanced meals with lean protein, whole grains and vegetables",
            "Greek yogurt with berries and honey",
            "Vegetable and hummus wraps",
            "Quinoa bowls with mixed vegetables and grilled chicken"
        ]
    elif bmi < 30:
        return [
            "High-fiber vegetables like broccoli, cauliflower and spinach",
            "Lean proteins such as chicken breast, tofu or fish",
            "Whole grain options in moderate portions",
            "Fresh fruit instead of sugary desserts"
        ]
    else:
        return [
            "Plenty of vegetables to fill your plate",
            "Lean proteins without added fats",
            "Whole grains in small portions",
            "Low-calorie soups before meals to increase fullness"
        ]

# Outfit recommendation helper functions
def get_outfit_recommendations(weather, occasion):
    """Get outfit recommendations based on weather and occasion"""
    outfits = {
        'sunny': {
            'casual': [
                "Light t-shirt with shorts or a skirt", 
                "Sunglasses and a hat", 
                "Comfortable sandals"
            ],
            'formal': [
                "Light blazer with a dress shirt/blouse", 
                "Lightweight trousers or skirt", 
                "Dress shoes with breathable socks"
            ],
            'sports': [
                "Breathable athletic shirt", 
                "Sports shorts", 
                "Running shoes and a cap"
            ]
        },
        'rainy': {
            'casual': [
                "Waterproof jacket", 
                "Water-resistant pants", 
                "Waterproof boots"
            ],
            'formal': [
                "Trench coat over formal attire", 
                "Formal water-resistant shoes", 
                "Umbrella as an accessory"
            ],
            'sports': [
                "Water-resistant sports jacket", 
                "Quick-dry athletic wear", 
                "Water-resistant athletic shoes"
            ]
        },
        'cold': {
            'casual': [
                "Warm sweater or hoodie", 
                "Jeans with thermal underlayer if needed", 
                "Boots and a warm coat"
            ],
            'formal': [
                "Wool coat over formal attire", 
                "Scarf as an elegant accessory", 
                "Insulated dress boots"
            ],
            'sports': [
                "Thermal athletic wear", 
                "Athletic jacket suitable for cold weather", 
                "Warm running shoes with appropriate socks"
            ]
        }
    }
    
    # Fallback if specific combination not found
    if weather not in outfits or occasion not in outfits.get(weather, {}):
        return ["Standard outfit appropriate for the weather and occasion"]
    
    return outfits[weather][occasion]

# Motivation helper functions
def get_motivation_message(energy_level, task=None):
    """Get a motivation message based on energy level and optionally for a specific task"""
    if energy_level <= 3:
        messages = [
            f"Remember, even small steps toward {'completing ' + task if task else 'your goals'} are progress!",
            f"It's okay to take {'this task' if task else 'things'} one step at a time. You got this!",
            f"Low energy days happen to everyone. Be kind to yourself while working on {'this task' if task else 'your tasks'}."
        ]
    elif energy_level <= 6:
        messages = [
            f"Your energy is building - this is a great time to make progress on {'this task' if task else 'your priorities'}.",
            f"You've got enough energy to make meaningful progress {'on ' + task if task else 'today'}.",
            f"Choose to focus fully on {'this task' if task else 'one important thing'} and you'll be surprised what you can accomplish."
        ]
    else:
        messages = [
            f"Your energy is high! Make the most of it {'with ' + task if task else 'with your important tasks'}.",
            f"This is the perfect time to tackle {'this task' if task else 'challenging items on your list'}.",
            f"Keep this momentum going - you're in a great state to accomplish {'this task' if task else 'a lot today'}!"
        ]
    
    import random
    return random.choice(messages)

def detect_multiple_intents(query):
    """Detect if a query contains multiple intents"""
    intents = []
    
    # Check for task intent
    if any(word in query.lower() for word in ["task", "todo", "remind me", "add task"]):
        intents.append("task")
    
    # Check for outfit intent
    if any(word in query.lower() for word in ["outfit", "wear", "clothes", "dress"]):
        intents.append("outfit")
    
    # Check for food intent
    if any(word in query.lower() for word in ["food", "eat", "meal", "diet", "nutrition"]):
        intents.append("food")
    
    # Check for motivation intent
    if any(word in query.lower() for word in ["motivate", "encourage", "inspire"]):
        intents.append("motivation")
    
    return intents

# AI processing function
def process_query(query, username=None):
    """Process the user query and return appropriate response"""
    query = query.lower()
    
    # Add this at the beginning of process_query
    intents = detect_multiple_intents(query)
    if len(intents) > 1:
        # Process each intent separately and combine responses
        responses = []
        for intent in intents:
            if intent == "task":
                # Process task intent
                task_response = handle_task_management(query, username)
                responses.append(task_response)
            elif intent == "outfit":
                # Process outfit intent
                outfit_response = handle_outfit_recommendation(query)
                responses.append(outfit_response)
            elif intent == "food":
                # Process food intent
                users = get_users()
                user_data = users.get(username, {})
                bmi_data = user_data.get('bmi_data', {})
                
                if bmi_data and 'height' in bmi_data and 'weight' in bmi_data:
                    height = bmi_data['height']
                    weight = bmi_data['weight']
                    bmi = weight / ((height / 100) ** 2)
                    food_response = handle_food_recommendation(query, bmi=bmi)
                else:
                    food_response = "I need your height and weight to give personalized food recommendations."
                
                responses.append(food_response)
            elif intent == "motivation":
                # Process motivation intent
                motivation_response = handle_motivation(query, username)
                responses.append(motivation_response)
        
        combined_response = " ".join(responses)
        return {
            "response": combined_response,
            "action": "multi_intent",
            "data": {"intents": intents}
        }
    
    # Check for urgent tasks reminder
    if username and ("any urgent" in query or "urgent task" in query or "important task" in query):
        urgent_reminder = check_urgent_tasks(username)
        if urgent_reminder:
            return {
                "response": urgent_reminder,
                "action": "urgent_tasks",
                "data": {}
            }
        else:
            return {
                "response": "You don't have any urgent tasks at the moment.",
                "action": "no_urgent_tasks",
                "data": {}
            }
    
    # Task management: Adding tasks
    task_info = extract_task_from_query(query)
    if task_info:
        if username:
            task_id = add_task(username, task_info["task_text"], task_info["priority"], task_info["energy"])
            priority_text = task_info["priority"].capitalize()
            return {
                "response": f"I've added '{task_info['task_text']}' to your tasks with {priority_text} priority.",
                "action": "add_task",
                "data": {"task_name": task_info["task_text"], "task_id": task_id}
            }
        else:
            return {
                "response": "Please log in to add tasks to your list.",
                "action": "require_login"
            }
    
    # Task management: Listing tasks
    elif any(word in query for word in ["my tasks", "show tasks", "list tasks", "what do i need to do"]):
        if username:
            tasks_summary = get_tasks_summary(username)
            return {
                "response": tasks_summary,
                "action": "show_tasks",
                "data": {"tasks": get_user_tasks(username)}
            }
        else:
            return {
                "response": "Please log in to view your tasks.",
                "action": "require_login"
            }
    
    # Task management: Completing tasks
    elif "complete task" in query or "mark task as done" in query or "finished task" in query:
        if username:
            # Extract task name from query
            task_name = query.lower()
            for phrase in ["complete task", "mark task as done", "finished task"]:
                task_name = task_name.replace(phrase, "").strip()
            
            tasks = get_user_tasks(username)
            for task in tasks:
                if task.get("name", "").lower() == task_name and not task.get("completed", False):
                    mark_task_complete(username, task.get("id"))
                    return {
                        "response": f"Great job! I've marked '{task.get('name')}' as complete.",
                        "action": "complete_task",
                        "data": {"task_id": task.get("id")}
                    }
            
            return {
                "response": f"I couldn't find an active task named '{task_name}'. Could you try again with the exact task name?",
                "action": "task_not_found"
            }
        else:
            return {
                "response": "Please log in to manage your tasks.",
                "action": "require_login"
            }
    
    # Energy level update
    elif "energy level" in query or ("update" in query and "energy" in query):
        if username:
            # Try to extract energy level from query
            level_match = re.search(r'(\d+)', query)
            if level_match:
                level = int(level_match.group(1))
                if 1 <= level <= 10:
                    update_energy_level(username, level)
                    motivation = get_motivation_message(level)
                    
                    # Reschedule tasks based on new energy level
                    rescheduled_tasks = reschedule_tasks(username, level)
                    
                    return {
                        "response": f"I've updated your energy level to {level}. {motivation}",
                        "action": "update_energy",
                        "data": {
                            "energy_level": level,
                            "tasks": rescheduled_tasks
                        }
                    }
                else:
                    return {
                        "response": "Please provide an energy level between 1 and 10.",
                        "action": "energy_level_error"
                    }
            else:
                return {
                    "response": "What's your current energy level on a scale of 1 to 10?",
                    "action": "request_energy_level"
                }
        else:
            return {
                "response": "Please log in to update your energy level.",
                "action": "require_login"
            }
    
    # Food recommendations
    # In process_query function when handling food recommendations
    elif any(word in query for word in ["food", "eat", "meal",  "diet", "nutrition", "bmi"]):
        # Check if user has BMI data
        users = get_users()
        user_data = users.get(username, {})
        bmi_data = user_data.get('bmi_data', {})

        if not bmi_data or 'height' not in bmi_data or 'weight' not in bmi_data:
            return {
                "response": "I need your height and weight to give personalized food recommendations. What is your height in cm and weight in kg?",
                "action": "request_bmi_info",
                "data": {}
            }
        else:
            # Calculate BMI using stored user data
            height = bmi_data['height']  # in cm
            weight = bmi_data['weight']  # in kg
        
            # Calculate BMI: weight(kg) / (height(m))²
            height_in_meters = height / 100
            bmi = weight / (height_in_meters ** 2)
        
            response = handle_food_recommendation(query, bmi=bmi)
            return {
                "response": response,
                "action": "food_recommendation",
                "data": {"bmi": round(bmi, 1)}
        }
    
    # Outfit recommendations
    elif any(word in query for word in ["outfit", "wear", "clothes", "dress"]):
        # Try to extract weather and occasion
        weather = "sunny"  # Default
        if "rain" in query or "rainy" in query:
            weather = "rainy"
        elif "snow" in query or "snowy" in query or "cold" in query:
            weather = "cold"
        
        occasion = "casual"  # Default
        if any(word in query for word in ["formal", "business", "meeting", "work"]):
            occasion = "formal"
        elif any(word in query for word in ["sport", "exercise", "workout", "gym"]):
            occasion = "sports"
        
        response = handle_outfit_recommendation(query)
        return {
            "response": response,
            "action": "outfit_recommendation",
            "data": {
                "weather": weather,
                "occasion": occasion
            }
        }
    
    # Motivation
    elif any(word in query for word in ["motivate", "motivation", "encourage", "inspire"]):
        if username:
            energy_level = get_energy_level(username)
            
            # Check if motivation is for a specific task
            task_match = re.search(r'motivate me (for|to|about) (.*)', query)
            task = task_match.group(2) if task_match else None
            
            motivation = handle_motivation(query, username)
            return {
                "response": motivation,
                "action": "motivation",
                "data": {
                    "energy_level": energy_level,
                    "task": task
                }
            }
        else:
            # Generic motivation without user context
            motivation = handle_motivation(query)
            return {
                "response": motivation,
                "action": "motivation_generic"
            }
    
    # General queries using process_voice_query from demoAI.py
    else:
        response = process_voice_query(query, username if username else "User")
        return {
            "response": response,
            "action": "general_query"
        }

# Flask routes
@app.route('/')
def home():
    """Home page route"""
    return render_template('index.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page route"""
    if request.method == 'POST':
        try:
            data = request.json
            print(f"Login data received: {data}")
            if data is None:
                return jsonify({
                    "status": False,
                    "message": "No JSON data received"
                })
                
            email = data.get('email')
            password = data.get('pass')
            
            print(f"Login attempt with email: {email}, password: {password}")
            
            users = get_users()
            print(f"Users in database: {users}")
            #print(f"Available users: {list(users.keys())}")
            
            # Look up user by email instead of username
            user_found = False
            for username, user_data in users.items():
                print(f"Checking user: {username}, data: {user_data}")
                if user_data.get('email') == email and user_data.get('password') == password:
                    session['username'] = username
                    user_found = True
                    print(f"Login successful for user: {username}")
                    response =  jsonify({
                        "status": True,
                        "username": username
                    })
                    print(f"Success response: {response}")
                    return response
            
            if not user_found:
                response =  jsonify({
                    "status": False,
                    "message": "Invalid email or password"
                })
                print(f"Failure response: {response}")
                return response
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({
                "status": False,
                "message": f"Server error: {str(e)}"
            })
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page route"""
    if request.method == 'POST':
        data = request.json
        print(f"Received signup data: {data}")  # Debug print
        name = data.get('name')  # Changed from username
        email = data.get('email')
        password = data.get('pass')  # Changed from password
        
        print(f"Name: {name}, Email: {email}, Password exists: {'Yes' if password else 'No'}")  # Debug print
        
        users = get_users()
        # Check for duplicate email
        for user_data in users.values():
            if user_data.get('email') == email:
                return jsonify({
                    "status": False,
                    "message": "Email already exists"
                })
        if name in users:
            return jsonify({
                "status": False,
                "message": "Username already exists"
            })
        
        # Make sure name is not None before using it as a key
        if name is None:
            return jsonify({
                "status": False,
                "message": "Invalid username"
            })
        
        users[name] = {
            "email": email,
            "password": password,
            "bmi_data": {},
            "preferences": {}
        }
        save_users(users)
        
        session['username'] = name
        return jsonify({
            "status": True,
            "username": name
        })
    
    return render_template('signup.html')


@app.route('/logout')
def logout():
    """Logout route"""
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/home')
def home_page():
    # Check if user is logged in via session
    if 'username' in session:
        username = session['username']
        # Render your home page
        return render_template('index.html', username=username)
    else:
        # Redirect to login if no session is active
        return redirect(url_for('login'))

@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.get_json()
        query = data.get('query', '')
        speak_response = data.get('speak', False)
    
        # Get username if logged in
        username = session.get('username', None)
        
        # Use the more comprehensive process_query function
        print(f"Processing query: '{query}' for user: '{username}'")  # Add this debug line
        result = process_query(query, username)
        print(f"Process result: {result}")  # Add this debug line
        
        # If speech is requested, start speech in background
        if speak_response and e1 in globals():
            speak_in_thread(result["response"])
            
        return jsonify(result)
    except Exception as e:
        print(f"Error processing query: {e}")
        return jsonify({"response": "Sorry, something went wrong", "action": None})

@app.route('/test')
def test():
    return "Flask app is running correctly!"

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    """Tasks management page route"""
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.json
        action = data.get('action')
        
        if action == 'add':
            task_name = data.get('task_name')
            priority = data.get('priority', 'medium')
            energy = int(data.get('energy', 5))
            task_id = add_task(username, task_name, priority, energy)
            return jsonify({
                "status": "success", 
                "task_id": task_id
            })
        
        elif action == 'complete':
            task_id = data.get('task_id')
            if mark_task_complete(username, task_id):
                return jsonify({"status": "success"})
            else:
                return jsonify({"status": "error", "message": "Task not found"})
        
        return jsonify({"status": "error", "message": "Invalid action"})
    
    tasks = get_user_tasks(username)
    energy_level = get_energy_level(username)
    return render_template('tasks.html', tasks=tasks, energy_level=energy_level)

@app.route('/food', methods=['GET', 'POST'])
def food():
    """Food recommendations page route"""
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.json
        height = float(data.get('height', 0))
        weight = float(data.get('weight', 0))
        
        if height <= 0 or weight <= 0:
            return jsonify({
                "status": "error",
                "message": "Please provide valid height and weight values."
            })
        
        # Update user BMI data
        users = get_users()
        if username in users:
            users[username]['bmi_data'] = {
                'height': height,
                'weight': weight
            }
            save_users(users)
        
        bmi = calculate_bmi(height, weight)
        recommendations = get_food_recommendations(bmi)
        
        return jsonify({
            "status": "success",
            "bmi": round(bmi, 1),
            "recommendations": recommendations
        })
    
    # Get existing BMI data if available
    users = get_users()
    bmi_data = users.get(username, {}).get('bmi_data', {})
    
    return render_template('food.html', bmi_data=bmi_data)

@app.route('/outfit', methods=['GET', 'POST'])
def outfit():
    """Outfit recommendations page route"""
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.json
        weather = data.get('weather', 'sunny')
        occasion = data.get('occasion', 'casual')
        
        recommendations = get_outfit_recommendations(weather, occasion)
        
        return jsonify({
            "status": "success",
            "recommendations": recommendations
        })
    
    return render_template('outfit.html')

@app.route('/energy', methods=['GET', 'POST'])
def energy():
    """Energy level management page route"""
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.json
        level = int(data.get('level', 5))
        
        if level < 1 or level > 10:
            return jsonify({
                "status": "error",
                "message": "Energy level must be between 1 and 10"
            })
        
        update_energy_level(username, level)
        motivation = get_motivation_message(level)
        
        # Reschedule tasks based on new energy level
        tasks = reschedule_tasks(username, level)
        
        return jsonify({
            "status": "success",
            "energy_level": level,
            "motivation": motivation,
            "tasks": tasks
        })
    
    current_level = get_energy_level(username)
    return render_template('energy.html', energy_level=current_level)

@app.route('/dashboard')
def dashboard():
    """User dashboard page route"""
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    
    # Get user data
    tasks = get_user_tasks(username)
    energy_level = get_energy_level(username)
    users = get_users()
    user_data = users.get(username, {})
    
    return render_template('dashboard.html', 
                           username=username,
                           tasks=tasks,
                           energy_level=energy_level,
                           user_data=user_data)
    
@app.route('/api/dashboard-data')
def dashboard_data():
    """API endpoint for dashboard data"""
    username = session.get('username')
    if not username:
        return jsonify({
            "status": "error",
            "message": "Not logged in"
        })
    
    # Get user data
    tasks = get_user_tasks(username)
    energy_level = get_energy_level(username)
    
    # Get user BMI data
    users = get_users()
    user_data = users.get(username, {})
    bmi_data = user_data.get('bmi_data', {})
    
    # Calculate BMI if data available
    bmi = None
    if bmi_data and 'height' in bmi_data and 'weight' in bmi_data:
        if bmi_data['height'] > 0 and bmi_data['weight'] > 0:
            bmi = calculate_bmi(bmi_data['height'], bmi_data['weight'])
    
    # Get a motivation message
    motivation = get_motivation_message(energy_level)
    
    # Count completed tasks
    completed_tasks = [task for task in tasks if task.get('completed')]
    active_tasks = [task for task in tasks if not task.get('completed')]
    
    # Check for urgent tasks
    urgent_tasks = [task for task in active_tasks if task.get('priority') == 'high']
    
    return jsonify({
        "status": "success",
        "username": username,
        "energy_level": energy_level,
        "tasks": tasks,
        "active_tasks": len(active_tasks),
        "completed_tasks": len(completed_tasks),
        "urgent_tasks": len(urgent_tasks),
        "bmi_data": bmi_data,
        "bmi": round(bmi, 1) if bmi else None,
        "motivation": motivation
    })

@app.route('/api/reschedule-tasks', methods=['POST'])
def api_reschedule_tasks():
    """API endpoint for rescheduling tasks based on energy level"""
    username = session.get('username')
    if not username:
        return jsonify({
            "status": "error",
            "message": "Not logged in"
        })
    
    data = request.json
    energy_level = int(data.get('energy_level', 5))
    
    # Reschedule tasks based on energy level
    tasks = reschedule_tasks(username, energy_level)
    
    return jsonify({
        "status": "success",
        "tasks": tasks
    })

@app.route('/voice-recognition')
def voice_recognition():
    """Voice recognition page"""
    username = session.get('username')
    return render_template('voice.html', username=username)

# Add this to your Flask app temporarily to debug
@app.route('/debug/users')
def debug_users():
    return jsonify(get_users())

if __name__ == "__main__":
    app.run(debug=True)