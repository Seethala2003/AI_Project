import datetime
from bs4 import BeautifulSoup
import pyttsx3
import speech_recognition as sr
import wikipedia
import webbrowser
import wolframalpha
import random
import requests
import json
import os
import re

# File paths for data storage
USER_DB_FILE = os.path.join('data', 'users.json')
TASK_DB_FILE = os.path.join('data', 'tasks.json')
ENERGY_DB_FILE = os.path.join('data', 'energy_levels.json')

# Create directories if they don't exist
os.makedirs('data', exist_ok=True)
os.makedirs(os.path.join('static', 'Songs'), exist_ok=True)

# Use relative paths for files
music_dir = os.path.join("static", "Songs")
read_file_path = os.path.join("static", "read.txt")

# Ensure the remember file exists
if not os.path.exists(read_file_path):
    with open(read_file_path, 'w') as f:
        pass

# Initialize database files if they don't exist
if not os.path.exists(USER_DB_FILE):
    with open(USER_DB_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(TASK_DB_FILE):
    with open(TASK_DB_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(ENERGY_DB_FILE):
    with open(ENERGY_DB_FILE, 'w') as f:
        json.dump({}, f)

# API Keys
appId = "ad2706636ddfcf6579b8e07d682d9e68"  # Weather API key
clientObj = wolframalpha.Client("QAY9L8-W7G3WGJ875")  # WolframAlpha API Key

# Text-to-speech setup
try:
    e1 = pyttsx3.init("sapi5")
    e1.setProperty("voice", e1.getProperty("voices")[0].id)
except Exception as e:
    print(f"Text-to-speech initialization error: {e}")
    e1 = None

# Define stopwords for query preprocessing
STOPWORDS = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", 
             "by", "about", "that", "this", "these", "those", "is", "am", "are", "was", 
             "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", 
             "of", "me", "my", "mine", "your", "yours", "he", "him", "his", "she", "her", 
             "hers", "it", "its", "we", "us", "our", "ours", "they", "them", "their", "theirs"}

def speak(audio):
    """Convert text to speech"""
    if e1:
        try:
            e1.say(audio)
            e1.runAndWait()
        except Exception as e:
            print(f"Error in speak function: {e}")
    else:
        print(f"Speech output (TTS disabled): {audio}")

def greet(name):
    """Generate a time-appropriate greeting"""
    getTime = datetime.datetime.now()
    hr = getTime.hour
    if hr < 12:
        return f"Good morning {name}"
    elif hr < 18:
        return f"Good afternoon {name}"
    else:
        return f"Good evening {name}"

def takeCommand():  
    """Takes microphone input from the user and returns string output"""
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening...")
            r.pause_threshold = 1.0
            r.energy_threshold = 300
            audio = r.listen(source)
            
            # Add ambient noise adjustment
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source)

        try:
            print("Recognizing...")
            query = r.recognize_google(audio, language="en-in")
            print(f"User said: {query}\n")
            return query
        
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return "None"
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition; {e}")
            return "None"
        except Exception as e:
            print(f"Error in speech recognition: {e}")
            return "None"
    except Exception as e:
        print(f"Microphone error: {e}")
        return "None"

# Database functions
def get_users():
    if not os.path.exists(USER_DB_FILE):
        return {}

    try:
        with open(USER_DB_FILE, 'r') as f:
            data = json.load(f)
            # Ensure the loaded data is a dictionary
            if isinstance(data, dict):
                return data
            else:
                # Reset to empty dictionary if data is not in expected format
                return {}
    except json.JSONDecodeError:
        # Corrupt or invalid JSON — start fresh
        return {}

def save_users(users):
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def get_tasks():
    try:
        with open(TASK_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_tasks(tasks):
    with open(TASK_DB_FILE, 'w') as f:
        json.dump(tasks, f)

def get_energy_levels():
    try:
        with open(ENERGY_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_energy_levels(energy_levels):
    with open(ENERGY_DB_FILE, 'w') as f:
        json.dump(energy_levels, f)

# Task management functions
def get_user_tasks(username):
    all_tasks = get_tasks()
    return all_tasks.get(username, [])

def add_task(username, task_name, priority="medium", energy_required=5):
    if not username:
        return False
        
    all_tasks = get_tasks()
    if username not in all_tasks:
        all_tasks[username] = []
    
    # Generate a unique ID for the task
    task_id = str(os.urandom(8).hex())
    
    all_tasks[username].append({
        'id': task_id,
        'name': task_name,
        'priority': priority,
        'energy': energy_required,
        'completed': False,
        'created_at': datetime.datetime.now().isoformat()
    })
    
    save_tasks(all_tasks)
    return task_id

def mark_task_complete(username, task_id):
    if not username:
        return False
        
    all_tasks = get_tasks()
    if username not in all_tasks:
        return False
    
    for task in all_tasks[username]:
        if task.get('id') == task_id:
            task['completed'] = True
            save_tasks(all_tasks)
            return True
    
    return False

def get_energy_level(username):
    energy_levels = get_energy_levels()
    return energy_levels.get(username, 5)  # Default energy level is 5

def update_energy_level(username, level):
    energy_levels = get_energy_levels()
    energy_levels[username] = level
    save_energy_levels(energy_levels)
    return True

# Feature 1: Task Management based on energy level
def handle_task_management(query, username=None):
    # Extract energy level (low, medium, high)
    energy_level = "medium"  # Default
    energy_value = 5  # Default numeric value
    
    if "low energy" in query.lower():
        energy_level = "low"
        energy_value = 3
    elif "high energy" in query.lower():
        energy_level = "high"
        energy_value = 8
    
    # Modify the regex pattern to be more flexible
    task_match = re.search(r'(add|create|finish|complete)[\s]+(task|to my task|to-do|todo)?\s*(.+?)(\s+with|\s+for|\s+when|\s+how|\s+where|$)', query.lower())
    if task_match:
        task_name = task_match.group(3).strip() if task_match.group(3) else ""
        
        # Extract priority if present
        priority = "medium"
        if re.search(r'(urgent|important|high priority)', query.lower()):
            priority = "high"
        elif re.search(r'(low priority|not urgent)', query.lower()):
            priority = "low"
        
        task_id = add_task(username, task_name, priority, energy_value)
        return f"I've added '{task_name}' to your tasks with {priority} priority."
    
    # If no task to add, provide recommendations based on energy level
    tasks = {
        "low": ["Review documents", "Answer emails", "Organize digital files"],
        "medium": ["Team meetings", "Project planning", "Writing tasks"],
        "high": ["Brainstorming sessions", "Learning new skills", "Complex problem solving"]
    }
    
    if "list" in query.lower() or "show" in query.lower() or "what" in query.lower():
        if username:
            user_tasks = get_user_tasks(username)
            incomplete_tasks = [task for task in user_tasks if not task.get('completed', False)]
            
            if not incomplete_tasks:
                return "You don't have any pending tasks. Great job!"
            
            response = "Here are your current tasks:\n"
            for task in incomplete_tasks[:5]:  # Show up to 5 tasks
                response += f"- {task['name']} (Priority: {task['priority'].capitalize()})\n"
            
            return response
        else:
            return "Please log in to view your tasks."
    
    response = f"For your {energy_level} energy level, I recommend these tasks: {', '.join(tasks[energy_level])}"
    return response

# Feature 2: Outfit Recommendation based on weather
def handle_outfit_recommendation(query):
    # Extract or assume weather
    weather = "sunny"  # Default
    temp = 75  # Default in F
    occasion = "casual"  # Default occasion
    
    # Extract weather info from query
    if "rain" in query.lower() or "rainy" in query.lower():
        weather = "rainy"
    elif "snow" in query.lower() or "snowy" in query.lower():
        weather = "snowy"
    elif "cold" in query.lower():
        weather = "cold"
        temp = 45
    elif "hot" in query.lower():
        temp = 90
    
    # Extract occasion if present
    if "formal" in query.lower() or "business" in query.lower() or "meeting" in query.lower():
        occasion = "formal"
    elif "sport" in query.lower() or "workout" in query.lower() or "exercise" in query.lower():
        occasion = "sports"
    
    # Outfit recommendations based on weather and occasion
    outfits = {
        "rainy": {
            "casual": ["Rain jacket", "Waterproof boots", "Umbrella"],
            "formal": ["Trench coat", "Formal shoes", "Umbrella"],
            "sports": ["Waterproof jacket", "Quick-dry pants", "Sports cap"]
        },
        "cold": {
            "casual": ["Warm sweater", "Jeans", "Winter coat", "Boots"],
            "formal": ["Wool coat", "Formal suit/dress", "Dress boots", "Scarf"],
            "sports": ["Thermal layer", "Running tights", "Windbreaker", "Beanie"]
        },
        "sunny": {
            "casual": ["T-shirt", "Shorts", "Sunglasses", "Hat"],
            "formal": ["Light blazer", "Dress shirt/blouse", "Formal pants/skirt"],
            "sports": ["Breathable shirt", "Sports shorts", "Cap", "Sunscreen"]
        }
    }
    
    # Default to sunny if weather not found
    if weather not in outfits:
        weather = "sunny"
    
    recommended_outfit = outfits[weather][occasion]
    response = f"For {weather} weather at {temp}°F and a {occasion} occasion, I recommend wearing: {', '.join(recommended_outfit)}"
    return response

# Feature 3: Food Recommendation based on BMI
def calculate_bmi(height, weight):
    """Calculate BMI given height in cm and weight in kg"""
    if height <= 0 or weight <= 0:
        return 0
    return weight / ((height/100) ** 2)

def handle_food_recommendation(query):
    # Try to extract BMI from query
    bmi = None
    
    # Try to extract height and weight from query
    height_match = re.search(r'height[:\s]*(\d+\.?\d*)', query.lower())
    weight_match = re.search(r'weight[:\s]*(\d+\.?\d*)', query.lower())
    
    if height_match and weight_match:
        height = float(height_match.group(1))
        weight = float(weight_match.group(1))
        bmi = calculate_bmi(height, weight)
    else:
        # Try to extract BMI directly
        bmi_match = re.search(r'bmi[:\s]*(\d+\.?\d*)', query.lower())
        if bmi_match:
            bmi = float(bmi_match.group(1))
        else:
            # Default BMI if nothing is found
            bmi = 22
    
    # Food recommendations based on BMI
    if bmi < 18.5:
        foods = ["Protein-rich foods like eggs and chicken", 
                "Nuts and seeds for healthy fats", 
                "Whole milk dairy products", 
                "Nutritious carbs like oatmeal and sweet potatoes"]
        category = "underweight"
    elif bmi < 25:
        foods = ["Balanced meals with lean protein, whole grains and vegetables",
                "Greek yogurt with berries and honey",
                "Vegetable and hummus wraps",
                "Quinoa bowls with mixed vegetables"]
        category = "normal weight"
    elif bmi < 30:
        foods = ["High-fiber vegetables like broccoli and spinach",
                "Lean proteins such as chicken breast or tofu",
                "Whole grain options in moderate portions",
                "Fresh fruit instead of processed sweets"]
        category = "overweight"
    else:
        foods = ["Plenty of vegetables to fill your plate",
                "Lean proteins without added fats",
                "Whole grains in small portions",
                "Low-calorie soups before meals"]
        category = "obese"
    
    response = f"For a BMI of {bmi:.1f} ({category}), I recommend these foods:\n"
    for food in foods:
        response += f"- {food}\n"
    
    return response

# Feature 4: Motivation
def handle_motivation(query, username=None):
    # Extract task from query if present
    task = "your task"
    task_match = re.search(r'motivate me (for|to|about) (.*)', query.lower())
    if task_match:
        task = task_match.group(2)
    
    # Get energy level if username is provided
    energy_level = 5  # Default
    if username:
        energy_level = get_energy_level(username)
    
    # Different motivation based on energy level
    low_energy_motivations = [
        f"Remember that even small progress on {task} is still progress!",
        f"You can break {task} into smaller steps and just do one at a time.",
        f"It's okay to start slow with {task} - what's the smallest step you could take?"
    ]
    
    medium_energy_motivations = [
        f"You've got this! Completing {task} will bring you one step closer to your goals.",
        f"Remember why you started {task}. Your future self will thank you!",
        f"Imagine how great you'll feel once you've completed {task}. That feeling is worth it!"
    ]
    
    high_energy_motivations = [
        f"Now's the perfect time to tackle {task} head-on!",
        f"Your energy is high - nothing can stop you from conquering {task}!",
        f"Channel your momentum into {task} and you'll be unstoppable!"
    ]
    
    # Select appropriate motivations based on energy level
    if energy_level <= 3:
        motivations = low_energy_motivations
    elif energy_level <= 7:
        motivations = medium_energy_motivations
    else:
        motivations = high_energy_motivations
    
    message = random.choice(motivations)
    return message

def working(query, userName="User"):
    """Process the user's query and return an appropriate response"""
    # Extract username for persistence (if available)
    username = userName if userName != "User" else None
    
    # Check for the four main features first
    if any(word in query.lower() for word in ["task", "todo", "remind me", "add task"]):
        return handle_task_management(query, username)
    
    elif any(word in query.lower() for word in ["outfit", "wear", "clothes", "dress", "what should i wear"]):
        return handle_outfit_recommendation(query)
    
    elif any(word in query.lower() for word in ["food", "eat", "meal", "diet", "nutrition", "bmi"]):
        return handle_food_recommendation(query)
    
    elif any(word in query.lower() for word in ["motivate", "encourage", "inspire", "motivation"]):
        return handle_motivation(query, username)
    
    # Check for energy level update
    elif "energy level" in query.lower():
        level_match = re.search(r'energy level[:\s]*(\d+)', query.lower())
        if level_match and username:
            level = int(level_match.group(1))
            if 1 <= level <= 10:
                update_energy_level(username, level)
                return f"I've updated your energy level to {level}. " + handle_motivation("motivate me", username)
            else:
                return "Please provide an energy level between 1 and 10."
        else:
            return "What's your current energy level on a scale of 1 to 10?"
    
    # Continue with original functionality
    elif "time" in query:
        strTime = datetime.datetime.now().strftime("%H hours & %M minute")
        return f"{userName} the time is {strTime}"

    elif "date" in query:
        Year = datetime.datetime.now().date().year
        Month = datetime.datetime.now().date().month
        Date = datetime.datetime.now().date().day
        return f"{userName} Today's Date is {Date} {Month} {Year}"

    elif "how are you" in query:
        return f"I am Fine, How are you {userName}"
    
    elif "wikipedia" in query:
        try:
            query = query.replace("wikipedia", "", 1)
            results = wikipedia.summary(query, sentences=2)
            return f"According to Wikipedia. {results}"
        except Exception as e:
            return f'The Term "{query}" may refer to one or more similar terms. Please Describe it more specifically.'

    elif "youtube" in query:
        if "open youtube"in query:
            webbrowser.open("www.youtube.in")
            return f"Opening youtube please Hold a second"
        else:
            newQuery = query.replace("youtube", "")
            youtubeLink = "https://www.youtube.com/results?search_query="
            newUrl = youtubeLink+newQuery.replace(" ", "+").rstrip("+")
            webbrowser.open(newUrl)
            return f"Opening youtube with search query as {newQuery}"

    elif "open stack overflow" in query:
        webbrowser.open("www.stackoverflow.com")
        return f"Opening stack overflow please Hold a second"

    elif "amazon" in query:
        if "open amazon"in query:
            webbrowser.open("www.amazon.in")
            return f"Opening amazon please Hold a second"
        else:
            newQuery = query.replace("amazon", "")
            amazonLink = "https://www.amazon.in/s?k="
            newUrl = amazonLink+newQuery.replace(" ", "+").rstrip("+")
            webbrowser.open(newUrl)
            return f"Opening Amazon with search query as {newQuery}"

    elif "open spotify" in query:
        webbrowser.open("https://www.spotify.com/in-en/")
        return f"Opening Spotify please Hold a second"

    elif query.startswith("search for "):
        keyWord = query[len("search for "):]
        webbrowser.open("https://www.google.com/search?q=" + keyWord)
        return f"This what I found for {keyWord}"

    elif "play music" in query:
        songs = os.listdir(music_dir)
        if songs:
            i = random.randint(0, len(songs) - 1)
            song_path = os.path.join(music_dir, songs[i])
            try:
                os.startfile(song_path)
                return f"Playing {songs[i]} Song"
            except Exception as e:
                print(f"Error playing music: {e}")
                return "I couldn't play the music"
        else:
            return "No music files found in the Songs directory"

    elif "weather" in query:
        baseUrl = "http://api.openweathermap.org/data/2.5/weather?"
        try:
            city = query.replace("weather", "").strip()
            res = requests.get(baseUrl+"appid="+appId+"&q="+city)
            data = res.json()
            Celius = data["main"]["temp"] - 273.15
            windSpeed = data["wind"]["speed"]
            return f"{userName}, The Current Temperature is {round(Celius, 2)}°C and Wind Speed is {windSpeed} miles per second"
        except Exception:
            return "Sorry, No Such City"

    elif "recall the remember task" in query:
        try:
            with open(read_file_path, mode="r+") as readFile:
                reading = readFile.read()
                
                if not reading:
                    return "No task to remember"
                else:
                    readFile.seek(0)
                    readFile.truncate(0)
                    return "You said me to remember that " + reading
        except Exception as e:
            print(f"Error recalling tasks: {e}")
            return "Sorry, I couldn't recall any tasks."

    elif "remember" in query:
        try:
            save = query.replace("remember", "", 1)
            with open(read_file_path, mode="a") as openFile:
                openFile.write(save + "\n")
            return f"Ok {userName}, I will remember this"
        except Exception as e:
            print(f"Error saving to remember file: {e}")
            return f"Sorry {userName}, I couldn't save that information."
    
    elif "calculate" in query:
        try:
            res = clientObj.query(query)
            return f"Your answer is {next(res.results).get('subpod').get('plaintext')}"
        except Exception:
            return f"Sorry {userName}, I couldn't calculate that."

    else:
        return f"Sorry {userName}, I didn't get that. I'm Still Learning New Stuff"

def preprocess_query(query):
    """Break down long queries into manageable parts"""
    # Split into sentences if multiple exist
    sentences = query.split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Extract main keywords for each sentence
    important_words = []
    for sentence in sentences:
        words = sentence.lower().split()
        # Filter out stopwords or focus on nouns/verbs
        keywords = [w for w in words if w not in STOPWORDS]
        important_words.extend(keywords)
    
    # Find primary intent
    possible_intents = ["task", "outfit", "food", "motivation", "information", "control"]
    intent_scores = {intent: 0 for intent in possible_intents}
    
    for word in important_words:
        if any(task_word in word for task_word in ["task", "todo", "remind"]):
            intent_scores["task"] += 1
        elif any(outfit_word in word for outfit_word in ["wear", "cloth", "outfit"]):
            intent_scores["outfit"] += 1
        elif any(food_word in word for food_word in ["food", "eat", "meal", "diet"]):
            intent_scores["food"] += 1
        elif any(motivation_word in word for motivation_word in ["motivate", "encourage", "inspire"]):
            intent_scores["motivation"] += 1
        elif any(info_word in word for info_word in ["what", "how", "when", "where", "who", "why"]):
            intent_scores["information"] += 1
        elif any(control_word in word for control_word in ["open", "play", "start", "stop"]):
            intent_scores["control"] += 1
    
    primary_intent = max(intent_scores, key=intent_scores.get)
    
    return {
        "original_query": query,
        "sentences": sentences,
        "keywords": important_words,
        "primary_intent": primary_intent,
        "confidence": intent_scores[primary_intent] / len(important_words) if important_words else 0.5
    }

def process_voice_query(query, userName="User"):
    """
    Process voice or text query and return a response
    This function can be called from your Flask app
    """
    if query.lower() == "none":
        return "Sorry, I didn't catch that. Could you please repeat?"
    
    # Preprocess the query
    processed = preprocess_query(query)
    
    # If we're not confident, use the traditional approach
    if processed["confidence"] < 0.3:
        return working(query, userName)
    
    # Focus on the primary intent
    if processed["primary_intent"] == "task":
        return handle_task_management(query, userName if userName != "User" else None)
    elif processed["primary_intent"] == "outfit":
        return handle_outfit_recommendation(query)
    elif processed["primary_intent"] == "food":
        return handle_food_recommendation(query)
    elif processed["primary_intent"] == "motivation":
        return handle_motivation(query, userName if userName != "User" else None)
    else:
        # For other intents or low confidence, use the original function
        return working(query, userName)

# For testing in standalone mode
if __name__ == "__main__":
    user_name = input("Enter your name: ")
    print(greet(user_name))
    while True:
        print("Listening for command...")
        command = takeCommand()
        if "exit" in command.lower() or "quit" in command.lower():
            print("Goodbye!")
            break
        response = process_voice_query(command, user_name)
        print(response)
        speak(response)