import datetime
import json
import os
import requests

# ==================== EXCEPTIONS ====================
class TaskNotFoundError(Exception):
    """Raised when a task ID cannot be found in the database."""
    pass

class InvalidInputError(Exception):
    """Raised when user input fails validation constraints."""
    pass


# ==================== TASK MODEL ====================
class Task:
    def __init__(self, task_id, title, description="", priority="Medium", due_date=None, completed=False):
        self.task_id = int(task_id)
        self.title = title.strip()
        self.description = description.strip()
        self.priority = priority.capitalize()
        self.due_date = due_date if due_date else datetime.date.today().strftime("%Y-%m-%d")
        self.completed = completed

    def to_dict(self):
        """Converts the Task object into a dictionary for JSON writing."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "due_date": self.due_date,
            "completed": self.completed
        }

    @classmethod
    def from_dict(cls, data):
        """Instantiates a Task object from a dictionary loaded from JSON."""
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            description=data.get("description", ""),
            priority=data.get("priority", "Medium"),
            due_date=data.get("due_date"),
            completed=data.get("completed", False)
        )


# ==================== API CLIENT ====================
class APIClient:
    @staticmethod
    def fetch_daily_quote():
        """Fetches a random inspirational/productivity quote from a public API."""
        url = "https://api.quotable.io/random?tags=inspirational|perseverance"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return f'"{data.get("content")}" — {data.get("author")}'
        except (requests.RequestException, ValueError):
            pass
        return '"Stay focused, set goals, and keep building." — TaskHub Team'


# ==================== TASK MANAGER ====================
class TaskManager:
    def __init__(self, filepath="data/tasks.json"):
        self.filepath = filepath
        self.tasks = []
        self._ensure_file_exists()
        self.load_tasks()

    def _ensure_file_exists(self):
        """Ensures the storage directory and JSON file exist."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                json.dump([], f)

    def load_tasks(self):
        """Loads tasks from the JSON storage file with error handling."""
        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
                self.tasks = [Task.from_dict(item) for item in data]
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Warning] Error loading task database: {e}. Starting with an empty list.")
            self.tasks = []

    def save_tasks(self):
        """Saves current tasks list to the JSON file."""
        try:
            with open(self.filepath, "w") as f:
                json.dump([task.to_dict() for task in self.tasks], f, indent=4)
        except IOError as e:
            print(f"[Error] Failed to save tasks to file: {e}")

    def _generate_id(self):
        """Generates a unique auto-incrementing ID for new tasks."""
        if not self.tasks:
            return 1
        return max(task.task_id for task in self.tasks) + 1

    # --- CRUD Operations ---

    def create_task(self, title, description="", priority="Medium", due_date=None):
        """CREATE: Adds a new task to the collection."""
        if not title.strip():
            raise InvalidInputError("Task title cannot be empty.")
        
        new_id = self._generate_id()
        task = Task(new_id, title, description, priority, due_date)
        self.tasks.append(task)
        self.save_tasks()
        return task

    def get_all_tasks(self):
        """READ: Returns all saved tasks."""
        return self.tasks

    def update_task(self, task_id, title=None, description=None, priority=None, due_date=None, completed=None):
        """UPDATE: Modifies fields of an existing task."""
        task = self.find_task_by_id(task_id)
        
        if title is not None:
            if not title.strip():
                raise InvalidInputError("Task title cannot be blank.")
            task.title = title.strip()
        if description is not None:
            task.description = description.strip()
        if priority is not None:
            task.priority = priority.capitalize()
        if due_date is not None:
            task.due_date = due_date
        if completed is not None:
            task.completed = bool(completed)
            
        self.save_tasks()
        return task

    def delete_task(self, task_id):
        """DELETE: Removes a task by ID."""
        task = self.find_task_by_id(task_id)
        self.tasks.remove(task)
        self.save_tasks()

    def find_task_by_id(self, task_id):
        """Helper method to find a task by ID or raise TaskNotFoundError."""
        try:
            tid = int(task_id)
        except ValueError:
            raise InvalidInputError("Task ID must be a valid integer.")
            
        for task in self.tasks:
            if task.task_id == tid:
                return task
        raise TaskNotFoundError(f"Task with ID {tid} does not exist.")


# ==================== MAIN INTERFACE ====================
def print_header(title):
    print("\n" + "=" * 55)
    print(f"  {title.upper()}")
    print("=" * 55)

def main():
    manager = TaskManager()
    
    # App startup banner & API quote integration
    print_header("Welcome to TaskHub")
    print(f"💡 Daily Inspiration: {APIClient.fetch_daily_quote()}")

    while True:
        print("\n--- MAIN MENU ---")
        print("1. View All Tasks")
        print("2. Add a New Task")
        print("3. Update a Task")
        print("4. Toggle Task Completion Status")
        print("5. Delete a Task")
        print("6. Exit Application")

        choice = input("\nSelect an option (1-6): ").strip()

        try:
            if choice == "1":
                print_header("Your Task List")
                tasks = manager.get_all_tasks()
                if not tasks:
                    print("No tasks recorded yet. Time to add your first task!")
                else:
                    for t in tasks:
                        status = "✅ Done" if t.completed else "⏳ Pending"
                        print(f"[{t.task_id}] {t.title} | Priority: {t.priority} | Due: {t.due_date} | Status: {status}")
                        if t.description:
                            print(f"    ↳ Note: {t.description}")

            elif choice == "2":
                print_header("Create New Task")
                title = input("Enter task title: ")
                desc = input("Enter description (optional): ")
                priority = input("Enter priority (Low / Medium / High) [Default: Medium]: ") or "Medium"
                due_date = input("Enter due date (YYYY-MM-DD) [Leave blank for today]: ") or None
                
                manager.create_task(title, desc, priority, due_date)
                print("✅ Task successfully created and saved!")

            elif choice == "3":
                print_header("Update Existing Task")
                tid = input("Enter Task ID to update: ")
                task = manager.find_task_by_id(tid)
                
                print(f"Editing Task #{task.task_id}: {task.title}")
                new_title = input(f"New title [{task.title}]: ") or None
                new_desc = input(f"New description [{task.description}]: ") or None
                new_priority = input(f"New priority [{task.priority}]: ") or None
                
                manager.update_task(tid, title=new_title, description=new_desc, priority=new_priority)
                print("✅ Task successfully updated!")

            elif choice == "4":
                print_header("Toggle Task Status")
                tid = input("Enter Task ID to toggle completion: ")
                task = manager.find_task_by_id(tid)
                new_status = not task.completed
                manager.update_task(tid, completed=new_status)
                status_str = "Completed" if new_status else "Pending"
                print(f"✅ Task {tid} marked as {status_str}!")

            elif choice == "5":
                print_header("Delete Task")
                tid = input("Enter Task ID to delete: ")
                manager.delete_task(tid)
                print(f"🗑️ Task {tid} deleted successfully!")

            elif choice == "6":
                print("\nThank you for using TaskHub. Stay productive!")
                break
            else:
                print("❌ Invalid selection. Please enter a number between 1 and 6.")

        except (TaskNotFoundError, InvalidInputError) as e:
            print(f"⚠️ Error: {e}")
        except Exception as e:
            print(f"🚨 An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()