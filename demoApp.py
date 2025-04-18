from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pyttsx3
import threading
import json
import db
from demoAI import greet, speak, takeCommand, working
from flask import jsonify

# Assuming the following modules exist:
from modules import task_module as task_manager
from modules import food_module as food_recommender
from modules import outfit_module as outfit_recommender
from modules import motivation_module as motivation_engine


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key in production

@app.before_request
def log_request_info():
    print(f"Request path: {request.path}")
    print(f"Current session: {session}")
    print(f"Username in session: {'username' in session}")
    
def check_login():
    if 'username' not in session:
        return redirect(url_for('home'))
    return None

def speak_safe(text):
    try:
        # Replace characters that might cause TTS issues
        text = str(text).replace("°C", " degrees Celsius")
        
        engine = pyttsx3.init()  # Create a new engine instance each time
        engine.setProperty("rate", 150)  # Adjust rate if needed
        engine.say(text)  # Text is already converted to string
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"Speech error: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def home():
    # Always clear the session when hitting the home route directly
    session.clear()
    print("Current session:", session)
    print("Username in session:", 'username' in session)
    
    # Now check if user is logged in (should always be False after clearing)
    if 'username' in session:
        return redirect(url_for('demoFun'))
    else:
        return render_template("signin.html")
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template("signup.html")

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    return render_template("index.html")

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    status, username = db.check_user()
    if status:
        session['username'] = username  # store user in session
    return jsonify({
    "username": username,
    "status": status
})

@app.route('/register', methods=['GET', 'POST'])
def register():
    status = db.insert_data()
    return json.dumps(status)

@app.route('/home', methods=['GET', 'POST'])
def demoFun():
    if 'username' not in session:
        return redirect(url_for('home'))

    user = session['username']
    
    if request.method == 'POST':
        user_input = request.form.get('command', '').lower()
        
        if not user_input or user_input == "none":
            response_text = "Sorry, please say that again."
        else:
            speak_safe("Searching. Please wait.")
            response_text = working(user_input, user)
        
        # Speak the response before rendering the template
        speech_success = speak_safe(response_text)
        
        return render_template('demoFlask.html', 
                               comp=response_text, 
                               userName=user, 
                               user=user.title(), 
                               user_input=user_input,
                               speech_status=speech_success)
    
    # GET request handling
    speak_safe(greet(user))
    return render_template('demoFlask.html', comp="", userName=user, user=user.title())

@app.route('/command', methods=['GET', 'POST'])
def commandPage():
    return render_template('demoCommands.html', commandName="demo")

@app.route('/aboutus', methods=['GET', 'POST'])
def aboutusPage():
    return render_template('demoAboutUs.html')

@app.route('/chat', methods=['GET', 'POST'])
def chatPage():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    username = session['username']
    user_data = db.get_user_data(username)
    tasks = task_manager.get_user_tasks(username)
    energy_level = task_manager.get_energy_level(username)

    return render_template('dashboard.html', 
                           user=user_data, 
                           tasks=tasks, 
                           energy_level=energy_level)

@app.route('/food', methods=['GET', 'POST'])
def food_recommendations():
    if 'username' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        ingredients = request.form.get('ingredients', '').split(',')
        dietary_restrictions = request.form.get('diet', '')
        recommendations = food_recommender.get_recommendations(
            session['username'], ingredients, dietary_restrictions)
        return render_template('food_module.html', recommendations=recommendations)

    return render_template('food_module.html')

@app.route('/outfit', methods=['GET', 'POST'])
def outfit_recommendations():
    if 'username' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        weather = request.form.get('weather', '')
        occasion = request.form.get('occasion', '')
        recommendations = outfit_recommender.get_recommendations(
            session['username'], weather, occasion)
        return render_template('outfit_module.html', recommendations=recommendations)

    return render_template('outfit_module.html')

@app.route('/tasks', methods=['GET', 'POST'])
def task_management():
    if 'username' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        task = request.form.get('task', '')
        priority = request.form.get('priority', '')
        energy = request.form.get('energy', '')
        task_manager.add_task(session['username'], task, priority, energy)

    tasks = task_manager.get_user_tasks(session['username'])
    return render_template('task_module.html', tasks=tasks)

@app.route('/api/update-energy', methods=['POST'])
def update_energy():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})

    level = request.json.get('level')
    task_manager.update_energy_level(session['username'], level)
    message = motivation_engine.get_motivation(session['username'], level)

    return jsonify({
        'status': 'success', 
        'energy_level': level,
        'motivation': message
    })

@app.route('/api/reschedule-tasks', methods=['POST'])
def reschedule_tasks():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})

    energy_level = request.json.get('energy_level')
    tasks = task_manager.reschedule_tasks(session['username'], energy_level)

    return jsonify({
        'status': 'success',
        'tasks': tasks
    })

if __name__ == "__main__":
    app.run(debug=True)