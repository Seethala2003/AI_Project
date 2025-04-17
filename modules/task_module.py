import db
import datetime

class TaskManager:
    def __init__(self):
        self.energy_levels = {
            'low': range(1, 4),
            'medium': range(4, 7),
            'high': range(7, 11)
        }
        
    def get_user_tasks(self, username):
        """Get all tasks for a user"""
        return db.get_user_tasks(username) 
        
    def add_task(self, username, task_name, priority, energy_required):
        """Add a new task for the user"""
        task_data = {
            "name": task_name,
            "priority": int(priority),
            "energy_required": energy_required,
            "status": "pending",
            "scheduled_for": datetime.datetime.now()
        }
        
        return db.add_task(username, task_data)
        
    def update_energy_level(self, username, level):
        """Update user's current energy level"""
        return db.update_energy_level(username, int(level))
        
    def get_energy_level(self, username):
        """Get user's current energy level"""
        user_data = db.get_user_data(username)
        return user_data.get('energy_level', 5)
        
    def reschedule_tasks(self, username, energy_level):
        """
        Reschedule tasks based on user's current energy level
        Returns recommended task order
        """
        # Get all pending tasks
        all_tasks = db.get_user_tasks(username)
        pending_tasks = [t for t in all_tasks if t.get('status') == 'pending']
        
        # Determine energy category
        energy_category = self._get_energy_category(energy_level)
        
        # Filter tasks by energy requirement
        suitable_tasks = []
        deferred_tasks = []
        
        for task in pending_tasks:
            task_energy = task.get('energy_required', 'medium')
            
            # If task matches current energy level or is high priority
            if (task_energy == energy_category or task.get('priority', 0) >= 8):
                suitable_tasks.append(task)
            else:
                deferred_tasks.append(task)
                
        # Sort suitable tasks by priority (highest first)
        suitable_tasks.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        # Combine with deferred tasks (will be done later)
        recommended_tasks = suitable_tasks + deferred_tasks
        
        return {
            "energy_level": energy_level,
            "energy_category": energy_category,
            "suitable_tasks": suitable_tasks,
            "deferred_tasks": deferred_tasks,
            "all_tasks": recommended_tasks
        }
        
    def _get_energy_category(self, level):
        """Convert numeric energy level to category"""
        level = int(level)
        
        if level in self.energy_levels['low']:
            return 'low'
        elif level in self.energy_levels['medium']:
            return 'medium'
        else:
            return 'high'