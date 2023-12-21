import time
import random
import tkinter as tk
from tkinter import messagebox
import pickle
import winsound
import threading
import tkinter.ttk as ttk
import datetime


# Initialize progress bars
xp_progress_bars = {}

# File to store study time data
DATA_FILE = "study_time_data.pkl"

# Subjects list
subjects = ["Data", "SQL", "DAX", "AI", "Mastery"]

# Define multiple reward lists with their odds
minute_rewards = {
    "Globus": 0.00004,
    "1 spin": 0.008 
}

xp_length = 1799
#----------waiting list-----------
#Kort
#Bogreol
#Skrivebord stol
#Bøger
#Skib
#Lampe
#Maleri
# Amor fati symbol
# læsestol
#læsebord
#fyldepen
#Tæppe
#Papirholder
#
session_end_rewards = {
    "Globus": 0.001,
    "Buste": 0.001,
    "Middag med kat": 0.004,
    "5 spins": 0.01,
    "Ekstra spin": 0.1,
    "Ny item til listen": 0.0009,
    "Leather ring binder": 0.001,
    "Skrivebord": 0.003,
    "Snack": 0.05,
    "Gå tur": 0.1,
    "Tavle": 0.001
}

last_xp_update_time = time.time()  # Initialize the last XP update time

def debounce(wait):
    """ Decorator that will postpone a functions
        execution until after `wait` seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            if 'timer' in debounced.__dict__:
                debounced.timer.cancel()
            debounced.timer = threading.Timer(wait, call_it)
            debounced.timer.start()
        return debounced
    return decorator
  
def add_new_subject(subject_name):
    if subject_name not in study_time_data:
        study_time_data[subject_name] = {"time": 0, "xp": 0}

# Load study time data from the file or create a new dictionary
def load_data():
    try:
        with open(DATA_FILE, "rb") as file:
            data = pickle.load(file)
            
            # Initialize XP for each subject if not already present
            for subject in subjects:
                if subject not in data:
                    data[subject] = {'study_time': 0, 'xp': 0}

            return data
    except FileNotFoundError:
        return {subject: {'study_time': 0, 'xp': 0} for subject in subjects}

study_time_data = load_data()  # Load the data once and don't overwrite it again

# Function to save study time data to the file

def save_study_time_data():
    attempts = 0
    max_attempts = 5
    while attempts < max_attempts:
        try:
            with open(DATA_FILE, "wb") as file:
                pickle.dump(study_time_data, file)
            break  # Success, exit the loop
        except PermissionError:
            attempts += 1
            time.sleep(1)  # Wait for 1 second before retrying
            if attempts == max_attempts:
                print("Failed to save data after several attempts.")   
# Variables for tracking study time and pause state
start_time = 0
paused = False
paused_time = 0
pause_start_time = 0
end_time = 0
last_reward_time = 0  # Add this line
selected_subject = None  # Initialize this to None or default subject


def toggle_pause():
    global paused, paused_time, pause_start_time, end_time
    if paused:
        # Resuming from pause
        paused_duration = time.time() - pause_start_time
        paused_time += paused_duration
        end_time += paused_duration  # Extend the end time by the paused duration
        pause_button.config(text="Pause Study Session")
        paused = False
        update_study_time()  # Resume the main timer
    else:
        # Pausing the timer
        pause_start_time = time.time()
        pause_button.config(text="Resume Study Session")
        paused = True
        study_time_label.config(text="Study session paused.")

# Function to start the study session
@debounce(0.3)  # 300 milliseconds delay
def start_study_session():
    global start_time, paused, paused_time, end_time, selected_subject,last_xp_update_time
    try:
        duration_minutes = int(timer_entry.get())
        start_time = time.time()
        end_time = start_time + duration_minutes * 60
        paused_time = 0
        
        print(f"---------Study session started at: {datetime.datetime.fromtimestamp(start_time)}, Ends at: {end_time}, Current XP: {study_time_data}")  # Debugging print

        start_button.config(state=tk.DISABLED)  # Disable start button during the session
        pause_button.config(state=tk.NORMAL)    # Enable pause button
        paused = False

        # Schedule the end of the study session
        root.after(duration_minutes * 60 * 1000, end_study_session)
        # Reset last XP update time at the start of the session
        last_xp_update_time = time.time()
        update_study_time()  # Start the main timer

    except ValueError:
        messagebox.showerror("Error", "Invalid input for timer duration.")

def update_xp_labels():
    for subject in subjects:
        xp = study_time_data[subject]['xp']
        xp_labels[subject].config(text=f"XP: {xp}")
        update_progress_bar(subject)  # If you have a progress bar to update

def update_study_time():
    global start_time, paused, paused_time, last_reward_time
    if not paused and start_time != 0:
        current_time = time.time()
        elapsed_time = current_time - start_time - paused_time
        selected_subject = selected_subject_var.get()
        study_time_label.config(text=f"Total {selected_subject} Study Time: {int(elapsed_time // 60)} minutes {int(elapsed_time % 60)} seconds")
        
        if current_time >= end_time:
            end_study_session()
            return  # Do not schedule a new update

        # Schedule the next update after 1000ms
        root.after(1000, update_study_time)
        
        # Check if a minute has passed since the last reward
        if current_time - last_reward_time >= 60:
            last_reward_time = current_time
            roll_reward(minute_rewards)
        
# XP points variable
xp_points = 0

def end_study_session():
    global start_time, selected_subject, paused_time, xp_points, last_xp_update_time
    selected_subject = selected_subject_var.get()
    current_time = time.time()
    elapsed_time = current_time - start_time - paused_time

    if elapsed_time > 0:
        xp_earned = int(elapsed_time / xp_length)
        study_time_data[selected_subject]['xp'] += xp_earned
        study_time_data[selected_subject]['study_time'] += elapsed_time
        save_study_time_data()
        xp_points += xp_earned  # Adjust based on your logic

    start_time = 0
    paused_time = 0
    last_reward_time = 0
    last_xp_update_time = time.time()

    start_button.config(state=tk.NORMAL)
    pause_button.config(state=tk.DISABLED)
    update_xp_labels()
    initialize_study_time_label()
    print(f"study session ended, Current XP: {study_time_data}")  # Debugging print

    winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS)
    messagebox.showinfo("done")
    time.sleep(0.5)
    roll_reward(session_end_rewards)

# Function to roll a reward
@debounce(0.3)  # 300 milliseconds delay
def roll_reward(reward_list):
    print("rolling reward")
    roll = random.random()
    cumulative_odds = 0.0
    for reward, odds in reward_list.items():
        cumulative_odds += odds
        if roll < cumulative_odds:
            messagebox.showinfo("Reward!", f"You've earned a reward: {reward}")
            break


# Create the main tkinter window
root = tk.Tk()
root.title("Study Timer")
#spin
spin_button = tk.Button(root, text="Roll", command=lambda: roll_reward(session_end_rewards))
spin_button.pack()
# Subject selection dropdown
selected_subject_var = tk.StringVar(root)
selected_subject_var.set(subjects[0])  # default value
subject_label = tk.Label(root, text="Select a subject:")
subject_label.pack()
subject_menu = tk.OptionMenu(root, selected_subject_var, *subjects)
subject_menu.pack()

# Timer input field
timer_label = tk.Label(root, text="Enter study time (minutes):")
timer_label.pack()
timer_entry = tk.Entry(root)
timer_entry.pack()

# Start, pause, and study time labels
start_button = tk.Button(root, text="Start Study Session", command=start_study_session)
start_button.pack()
pause_button = tk.Button(root, text="Pause Study Session", command=toggle_pause, state=tk.DISABLED)
pause_button.pack()
study_time_label = tk.Label(root)
study_time_label.pack()



# Constants
MAX_XP = 24999
MAX_LEVEL = 99

# Function to calculate XP required for given level
def calculate_xp_for_level(level, max_level=MAX_LEVEL, max_xp=MAX_XP):
    
    return int(level*level/0.4)

# Create a dictionary to hold the XP for each level
LEVELS = {level: calculate_xp_for_level(level) for level in range(1, MAX_LEVEL + 1)}

# Function to calculate the current level based on XP
def calculate_level(xp):
    for level in range(MAX_LEVEL, 0, -1):
        if xp >= LEVELS[level]:
            return level
    return 0

# Function to update XP based on study time
def update_xp(subject, time_elapsed):
    xp_earned = int(time_elapsed // xp_length)
    if xp_earned > 0:
        print(f"Updating XP for {subject}: Earned {xp_earned}, Time elapsed {time_elapsed}")  # Debugging print
        study_time_data[subject]['xp'] += xp_earned
        # Cap XP at MAX_XP
        study_time_data[subject]['xp'] = min(study_time_data[subject]['xp'], MAX_XP)
        save_study_time_data()
        update_progress_bar(subject)

# Initialize study time label
def initialize_study_time_label():
    selected_subject = selected_subject_var.get()
    subject_data = study_time_data.get(selected_subject, {"time": 0, "xp": 0})
    elapsed_time = subject_data.get('time', 0)
    xp = subject_data.get('xp', 0)
    level = calculate_level(xp)

    study_time_label.config(
        text=f"Total {selected_subject} Study Time: {int(elapsed_time // xp_length)} minutes {int(elapsed_time % 60)} seconds\nXP: {xp} Level: {level}"
    )
# Update study time label when a different subject is selected
selected_subject_var.trace("w", lambda *args: initialize_study_time_label())

# Initialize the study time label
initialize_study_time_label()  # This call should happen after loading the data


# Modify add_xp function to update XP in the study_time_data dictionary
@debounce(0.5)  # 300 milliseconds delay
def add_xp(area):
    print(f"current xp is {study_time_data[area]['xp']}")
    study_time_data[area]['xp'] += 1  # Increment by 10 for example
    study_time_data[area]['xp'] = min(study_time_data[area]['xp'], MAX_XP)  # Cap XP at MAX_XP
    xp_labels[area].config(text=f"XP: {study_time_data[area]['xp']}")
    level = calculate_level(study_time_data[area]['xp'])
    level_labels[area].config(text=f"Level: {level}")
    save_study_time_data()  # Save the updated XP to the file
    update_progress_bar(area)
xp_labels = {}
level_labels = {}

# Function to update the progress bar
def update_progress_bar(subject):
    xp = study_time_data[subject]['xp']
    current_level = calculate_level(xp)
    xp_for_current_level = LEVELS[current_level] if current_level > 0 else 0
    xp_for_next_level = LEVELS[current_level + 1]

    # Calculate the progress percentage
    progress = (xp - xp_for_current_level) / (xp_for_next_level - xp_for_current_level)
    progress_percentage = int(progress * 100)

    xp_progress_bars[subject]['value'] = progress_percentage
    xp_progress_bars[subject].update()

# Initialize XP and level labels with data from the file
for i, subject in enumerate(subjects, start=len(subjects) + 4):
    # Label for the subject
    tk.Label(root, text=subject).pack()
    
    # Button to add XP
    button = tk.Button(root, text="Add XP", command=lambda a=subject: add_xp(a))
    button.pack()

    # Label to show current XP
    xp = study_time_data[subject]['xp']
    xp_label = tk.Label(root, text=f"XP: {xp}")
    xp_label.pack()
    xp_labels[subject] = xp_label

    # Label to show current level
    level = calculate_level(xp)
    level_label = tk.Label(root, text=f"Level: {level}")
    level_label.pack()
    level_labels[subject] = level_label
    
    # Setup a progress bar for XP
    progress = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
    progress.pack()
    xp_progress_bars[subject] = progress
        # Update the progress bar for this subject
    update_progress_bar(subject)
# Start the tkinter main loop
root.mainloop()
