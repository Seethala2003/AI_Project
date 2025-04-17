import db
import random

class MotivationEngine:
    def __init__(self):
        # Sample motivation messages by energy level
        self.motivation_messages = {
            'low': [
                "It's okay to start small. Every step matters.",
                "Low energy days are perfect for gentle progress. Be kind to yourself.",
                "Even small steps move you forward. You're doing great!",
                "Energy fluctuates - that's normal. Focus on what you can do today."
            ],
            'medium': [
                "You've got this! Your energy is building nicely.",
                "This is a perfect time to tackle those medium-priority tasks.",
                "You're in a good flow state. Keep that momentum going!",
                "Balance is key - you're in a good place to make steady progress."
            ],
            'high': [
                "Your energy is at its peak! Time to tackle those challenging tasks.",
                "Amazing energy today! Make the most of this productive state.",
                "You're unstoppable right now. Challenge yourself!",
                "This is your time to shine. Your motivation is inspiring!"
            ]
        }
        
        # Pomodoro technique explanations
        self.pomodoro_tips = [
            "Try the Pomodoro Technique: 25 minutes of focused work, then a 5-minute break.",
            "Break large tasks into 25-minute focused sessions with short breaks between.",
            "Set a timer for 25 minutes and focus on just one task. Then reward yourself with a break."
        ]
        
        # Mindfulness suggestions
        self.mindfulness_tips = [
            "Take 3 deep breaths before starting your next task.",
            "Pause for a moment. How does your body feel right now?",
            "Try a quick 2-minute meditation to reset your focus."
        ]
        
    def get_motivation(self, username, energy_level):
        """Get personalized motivation based on user's energy level"""
        # Convert energy level to category
        category = self._energy_level_to_category(energy_level)
        
        # Get user's task data
        tasks = db.get_user_tasks(username)
        pending_tasks = [t for t in tasks if t.get('status') == 'pending']
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        
        # Personalize motivation approach
        response = {}
        response['energy_category'] = category
        
        # Select random motivation message for this energy level
        response['message'] = random.choice(self.motivation_messages[category])
        
        # Add technique recommendation based on energy level
        if category == 'low':
            response['technique'] = random.choice(self.mindfulness_tips)
        elif category == 'medium':
            response['technique'] = random.choice(self.pomodoro_tips) 
        else:  # high energy
            response['technique'] = "This is a great time to tackle your most challenging task!"
            
        # Add progress encouragement if user has completed tasks
        if completed_tasks:
            completed_count = len(completed_tasks)
            response['progress'] = f"You've completed {completed_count} tasks already. Great work!"
            
        # Add task suggestion based on energy level
        if pending_tasks:
            if category == 'low':
                # Suggest easiest task
                easy_tasks = [t for t in pending_tasks if t.get('energy_required') == 'low']
                if easy_tasks:
                    suggested_task = sorted(easy_tasks, key=lambda x: x.get('priority', 0), reverse=True)[0]
                    response['suggestion'] = f"Consider working on '{suggested_task['name']}' - it requires low energy but still moves you forward."
            elif category == 'high':
                # Suggest most important task
                important_tasks = sorted(pending_tasks, key=lambda x: x.get('priority', 0), reverse=True)
                if important_tasks:
                    response['suggestion'] = f"You've got great energy! Now would be perfect for your highest priority task: '{important_tasks[0]['name']}'."
        
        return response
        
    def _energy_level_to_category(self, level):
        """Convert numeric energy level to category"""
        level = int(level)
        
        if level <= 3:
            return 'low'
        elif level <= 7:
            return 'medium'
        else:
            return 'high'