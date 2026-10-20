import os
import json
import uuid
import math
import random
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date, timedelta

import customtkinter as ctk
import pygame
from tkcalendar import DateEntry


# ==========================================================
# TASKTALE — THE ENCHANTED AUTUMN DESK
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "tasks.json")
MUSIC_FOLDER = os.path.join(BASE_DIR, "music")

os.makedirs(MUSIC_FOLDER, exist_ok=True)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


# ==========================================================
# COLOUR PALETTE
# ==========================================================

BG = "#171F1A"
BG_LIGHT = "#202B23"

CARD = "#26372C"
CARD_LIGHT = "#304436"
CARD_HOVER = "#394C3D"

GREEN = "#58745B"
GREEN_DARK = "#354C3A"
SAGE = "#A6B99A"

GOLD = "#E4C58A"
GOLD_DARK = "#AD8D56"

CREAM = "#F5EBDD"
MUTED = "#B9C4B5"

ROSE = "#C98D91"
ROSE_DARK = "#80545A"

ORANGE = "#C98251"
RED = "#CF7770"

FONT = "Georgia"
UI_FONT = "Segoe UI"


# ==========================================================
# WINDOW
# ==========================================================

app = ctk.CTk()
app.title("TaskTale | An Enchanted Little Planner")
app.geometry("1050x740")
app.minsize(900, 650)
app.configure(fg_color=BG)

app.grid_rowconfigure(1, weight=1)
app.grid_columnconfigure(0, weight=1)


# ==========================================================
# STATE
# ==========================================================

tasks = []
current_filter = "All"

timer_running = False
timer_seconds = 25 * 60
timer_end_time = None
timer_after_id = None

music_files = []
music_paused = False
pygame_ready = False

notified_tasks = set()

sparkle_canvas = None
sparkle_particles = []


# ==========================================================
# TASK STORAGE
# ==========================================================

def load_tasks():
    global tasks

    if not os.path.exists(DATA_FILE):
        tasks = []
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            result = json.load(file)

        tasks = result if isinstance(result, list) else []

        # Ensure every task has an ID.
        for task in tasks:
            if not task.get("id"):
                task["id"] = str(uuid.uuid4())

    except (OSError, json.JSONDecodeError):
        tasks = []


def save_tasks():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(tasks, file, indent=4, ensure_ascii=False)
    except OSError as error:
        messagebox.showerror(
            "Saving failed",
            f"Could not save your tasks.\n\n{error}"
        )


load_tasks()


# ==========================================================
# REUSABLE UI HELPERS
# ==========================================================

def label(parent, text, size=12, color=CREAM, bold=False):
    return ctk.CTkLabel(
        parent,
        text=text,
        font=(FONT if bold else UI_FONT, size,
              "bold" if bold else "normal"),
        text_color=color
    )


def button(parent, text, command, width=100, color=GREEN):
    hover = ORANGE if color == GREEN else ROSE_DARK

    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=32,
        corner_radius=10,
        fg_color=color,
        hover_color=hover,
        text_color=CREAM,
        font=(UI_FONT, 11),
        border_width=0
    )


def parse_due(task):
    try:
        return datetime.strptime(
            f"{task.get('date', '')} {task.get('time', '23:59')}",
            "%Y-%m-%d %H:%M"
        )
    except (ValueError, TypeError):
        return None


def task_status(task):
    if task.get("completed", False):
        return "Bloomed"

    due = parse_due(task)

    if due and due < datetime.now():
        return "Past due"

    return "Growing"


# ==========================================================
# ANIMATED SPARKLES
# ==========================================================

# The stars are drawn on a real Tkinter Canvas.
# No emoji characters are used for the decorative effect.

def create_sparkle_header(parent):
    global sparkle_canvas, sparkle_particles

    sparkle_canvas = tk.Canvas(
        parent,
        height=105,
        bg=BG_LIGHT,
        highlightthickness=0,
        bd=0
    )

    sparkle_canvas.pack(fill="x", expand=True)

    sparkle_particles = []

    def initialise_particles(event=None):
        if sparkle_canvas is None:
            return

        width = max(sparkle_canvas.winfo_width(), 600)
        height = max(sparkle_canvas.winfo_height(), 105)

        sparkle_canvas.delete("all")
        sparkle_particles.clear()

        # Subtle decorative curves.
        sparkle_canvas.create_oval(
            width - 190, -95, width + 40, 130,
            outline="#34483A",
            width=2
        )

        sparkle_canvas.create_oval(
            width - 155, -75, width + 15, 105,
            outline="#2D4033",
            width=1
        )

        for _ in range(34):
            x = random.randint(10, width - 10)
            y = random.randint(5, height - 5)
            size = random.choice([1, 2, 2, 3])

            particle = {
                "x": x,
                "y": y,
                "size": size,
                "phase": random.random() * math.tau,
                "speed": random.uniform(0.025, 0.075),
                "drift": random.uniform(-0.15, 0.15),
                "item": None
            }

            sparkle_particles.append(particle)

    def animate():
        if not app.winfo_exists() or sparkle_canvas is None:
            return

        try:
            width = sparkle_canvas.winfo_width()
            height = sparkle_canvas.winfo_height()

            if width < 20 or height < 20:
                app.after(150, animate)
                return

            for particle in sparkle_particles:
                particle["phase"] += particle["speed"]

                brightness = (math.sin(particle["phase"]) + 1) / 2

                size = particle["size"]

                if brightness > 0.78:
                    colour = GOLD
                elif brightness > 0.43:
                    colour = "#A9B59A"
                else:
                    colour = "#465B49"

                x = particle["x"] + math.sin(
                    particle["phase"] * 0.7
                ) * 2

                y = particle["y"] + math.cos(
                    particle["phase"] * 0.8
                ) * 1.3

                sparkle_canvas.delete(particle["item"])

                if brightness > 0.8 and size >= 2:
                    points = [
                        x, y - size * 2,
                        x + size * 0.55, y - size * 0.55,
                        x + size * 2, y,
                        x + size * 0.55, y + size * 0.55,
                        x, y + size * 2,
                        x - size * 0.55, y + size * 0.55,
                        x - size * 2, y,
                        x - size * 0.55, y - size * 0.55
                    ]

                    particle["item"] = sparkle_canvas.create_polygon(
                        points,
                        fill=colour,
                        outline=""
                    )

                else:
                    particle["item"] = sparkle_canvas.create_oval(
                        x - size,
                        y - size,
                        x + size,
                        y + size,
                        fill=colour,
                        outline=""
                    )

            app.after(65, animate)

        except tk.TclError:
            return

    sparkle_canvas.bind("<Configure>", initialise_particles)
    initialise_particles()
    app.after(100, animate)


# ==========================================================
# HEADER
# ==========================================================

header = ctk.CTkFrame(
    app,
    fg_color=BG_LIGHT,
    corner_radius=0,
    height=105
)

header.grid(row=0, column=0, sticky="ew")
header.grid_columnconfigure(0, weight=1)

create_sparkle_header(header)

# Put the title over the decorative header.
title_area = ctk.CTkFrame(
    header,
    fg_color="transparent"
)

title_area.place(
    x=24,
    y=15
)

label(
    title_area,
    "TaskTale",
    size=29,
    color=GOLD,
    bold=True
).pack(anchor="w")

label(
    title_area,
    "a tiny garden for your growing dreams",
    size=11,
    color=MUTED
).pack(anchor="w", pady=(1, 0))


# ==========================================================
# MAIN LAYOUT
# ==========================================================

main = ctk.CTkFrame(
    app,
    fg_color="transparent"
)

main.grid(
    row=1,
    column=0,
    sticky="nsew",
    padx=14,
    pady=12
)

main.grid_rowconfigure(0, weight=1)

# Narrow left panel and compact Garden panel.
main.grid_columnconfigure(0, weight=0, minsize=305)
main.grid_columnconfigure(1, weight=1)


left = ctk.CTkScrollableFrame(
    main,
    width=285,
    fg_color="transparent",
    corner_radius=0,
    scrollbar_button_color=GREEN,
    scrollbar_button_hover_color=GOLD
)

left.grid(
    row=0,
    column=0,
    sticky="nsew",
    padx=(0, 10)
)

left.grid_columnconfigure(0, weight=1)


garden = ctk.CTkFrame(
    main,
    fg_color=CARD,
    corner_radius=17,
    border_width=1,
    border_color="#344638"
)

garden.grid(
    row=0,
    column=1,
    sticky="nsew"
)

garden.grid_columnconfigure(0, weight=1)
garden.grid_rowconfigure(3, weight=1)


# ==========================================================
# CREATE TASK CARD
# ==========================================================

create_card = ctk.CTkFrame(
    left,
    fg_color=CARD,
    corner_radius=15,
    border_width=1,
    border_color="#344638"
)

create_card.grid(
    row=0,
    column=0,
    sticky="ew",
    pady=(0, 10)
)

create_card.grid_columnconfigure(0, weight=1)

label(
    create_card,
    "Create a little plan",
    size=17,
    color=GOLD,
    bold=True
).grid(
    row=0,
    column=0,
    sticky="w",
    padx=13,
    pady=(13, 10)
)


title_entry = ctk.CTkEntry(
    create_card,
    placeholder_text="Give your task a name...",
    height=34,
    corner_radius=9,
    fg_color=BG,
    border_color=CARD_LIGHT,
    text_color=CREAM,
    placeholder_text_color="#829080"
)

title_entry.grid(
    row=1,
    column=0,
    sticky="ew",
    padx=13,
    pady=(0, 8)
)


notes_entry = ctk.CTkTextbox(
    create_card,
    height=48,
    corner_radius=9,
    fg_color=BG,
    border_color=CARD_LIGHT,
    text_color=CREAM,
    font=(UI_FONT, 11)
)

notes_entry.grid(
    row=2,
    column=0,
    sticky="ew",
    padx=13,
    pady=(0, 8)
)

# A placeholder-like hint that is removed when the user types.
notes_entry.insert("1.0", "Little notes (optional)")
notes_entry.configure(text_color="#829080")


def notes_focus_in(event=None):
    if notes_entry.get("1.0", "end").strip() == "Little notes (optional)":
        notes_entry.delete("1.0", "end")
        notes_entry.configure(text_color=CREAM)


def notes_focus_out(event=None):
    if not notes_entry.get("1.0", "end").strip():
        notes_entry.insert("1.0", "Little notes (optional)")
        notes_entry.configure(text_color="#829080")


notes_entry.bind("<FocusIn>", notes_focus_in)
notes_entry.bind("<FocusOut>", notes_focus_out)


label(
    create_card,
    "When is it due?",
    size=11,
    color=MUTED
).grid(
    row=3,
    column=0,
    sticky="w",
    padx=13,
    pady=(0, 4)
)


date_entry = DateEntry(
    create_card,
    width=22,
    date_pattern="yyyy-mm-dd",
    background=GREEN,
    foreground=CREAM,
    headersbackground=CARD_LIGHT,
    headersforeground=CREAM,
    selectbackground=ORANGE,
    selectforeground=CREAM,
    normalbackground=BG,
    normalforeground=CREAM,
    weekendbackground=CARD,
    weekendforeground=CREAM,
    borderwidth=0
)

date_entry.grid(
    row=4,
    column=0,
    sticky="ew",
    padx=13,
    pady=(0, 8)
)


time_row = ctk.CTkFrame(
    create_card,
    fg_color="transparent"
)

time_row.grid(
    row=5,
    column=0,
    sticky="ew",
    padx=13,
    pady=(0, 10)
)

time_row.grid_columnconfigure((0, 1), weight=1)

hour_var = ctk.StringVar(value="18")
minute_var = ctk.StringVar(value="00")

ctk.CTkOptionMenu(
    time_row,
    values=[f"{h:02d}" for h in range(24)],
    variable=hour_var,
    height=30,
    fg_color=GREEN,
    button_color=ORANGE,
    button_hover_color=ROSE_DARK,
    text_color=CREAM
).grid(
    row=0,
    column=0,
    sticky="ew",
    padx=(0, 4)
)

ctk.CTkOptionMenu(
    time_row,
    values=[f"{m:02d}" for m in range(0, 60, 5)],
    variable=minute_var,
    height=30,
    fg_color=GREEN,
    button_color=ORANGE,
    button_hover_color=ROSE_DARK,
    text_color=CREAM
).grid(
    row=0,
    column=1,
    sticky="ew",
    padx=(4, 0)
)


# ==========================================================
# ADD TASK
# ==========================================================

def add_task():
    title = title_entry.get().strip()

    notes = notes_entry.get("1.0", "end").strip()

    if notes == "Little notes (optional)":
        notes = ""

    if not title:
        messagebox.showwarning(
            "A little reminder",
            "Please give your task a name first."
        )
        return

    try:
        selected_date = date_entry.get_date().isoformat()
    except (ValueError, AttributeError):
        messagebox.showwarning(
            "Invalid date",
            "Please select a valid date."
        )
        return

    task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "notes": notes,
        "date": selected_date,
        "time": f"{hour_var.get()}:{minute_var.get()}",
        "completed": False,
        "created_at": datetime.now().isoformat()
    }

    tasks.append(task)

    save_tasks()
    refresh_tasks()

    title_entry.delete(0, "end")
    notes_entry.delete("1.0", "end")
    notes_entry.configure(text_color="#829080")
    notes_entry.insert("1.0", "Little notes (optional)")

    title_entry.focus()


button(
    create_card,
    "Add to my garden",
    add_task,
    width=200,
    color=ORANGE
).grid(
    row=6,
    column=0,
    sticky="ew",
    padx=13,
    pady=(0, 13)
)


# ==========================================================
# FOCUS CORNER
# ==========================================================

focus_card = ctk.CTkFrame(
    left,
    fg_color=CARD,
    corner_radius=15,
    border_width=1,
    border_color="#344638"
)

focus_card.grid(
    row=1,
    column=0,
    sticky="ew",
    pady=(0, 10)
)

focus_card.grid_columnconfigure(0, weight=1)


label(
    focus_card,
    "The quiet little hour",
    size=16,
    color=GOLD,
    bold=True
).grid(
    row=0,
    column=0,
    sticky="w",
    padx=13,
    pady=(13, 3)
)

label(
    focus_card,
    "Choose a duration and settle in.",
    size=11,
    color=MUTED
).grid(
    row=1,
    column=0,
    sticky="w",
    padx=13,
    pady=(0, 9)
)


# Timer presets.
preset_row = ctk.CTkFrame(
    focus_card,
    fg_color="transparent"
)

preset_row.grid(
    row=2,
    column=0,
    sticky="ew",
    padx=10,
    pady=(0, 8)
)

for col in range(4):
    preset_row.grid_columnconfigure(col, weight=1)


def set_timer_preset(minutes):
    global timer_seconds, timer_running, timer_end_time

    if timer_running:
        pause_timer()

    timer_seconds = minutes * 60
    timer_end_time = None

    focus_hours.set("0")
    focus_minutes.set(str(minutes))

    update_timer_display()


for col, minutes in enumerate([15, 25, 45, 60]):
    button(
        preset_row,
        f"{minutes}m",
        lambda m=minutes: set_timer_preset(m),
        width=52
    ).grid(
        row=0,
        column=col,
        sticky="ew",
        padx=2
    )


# Adjustable custom duration.
duration_row = ctk.CTkFrame(
    focus_card,
    fg_color="transparent"
)

duration_row.grid(
    row=3,
    column=0,
    sticky="ew",
    padx=13,
    pady=(0, 8)
)

duration_row.grid_columnconfigure((0, 1), weight=1)

focus_hours = ctk.StringVar(value="0")
focus_minutes = ctk.StringVar(value="25")

ctk.CTkOptionMenu(
    duration_row,
    values=[str(x) for x in range(13)],
    variable=focus_hours,
    height=30,
    fg_color=GREEN,
    button_color=ORANGE,
    button_hover_color=ROSE_DARK,
    text_color=CREAM
).grid(
    row=0,
    column=0,
    sticky="ew",
    padx=(0, 4)
)

ctk.CTkOptionMenu(
    duration_row,
    values=[str(x) for x in range(60)],
    variable=focus_minutes,
    height=30,
    fg_color=GREEN,
    button_color=ORANGE,
    button_hover_color=ROSE_DARK,
    text_color=CREAM
).grid(
    row=0,
    column=1,
    sticky="ew",
    padx=(4, 0)
)


def custom_duration_minutes():
    try:
        hours = int(focus_hours.get())
        minutes = int(focus_minutes.get())
    except ValueError:
        return None

    total = hours * 60 + minutes

    if total < 1 or total > 720:
        return None

    return total


def apply_duration():
    global timer_seconds, timer_end_time

    if timer_running:
        pause_timer()

    duration = custom_duration_minutes()

    if duration is None:
        messagebox.showwarning(
            "Choose a duration",
            "Choose between 1 and 720 minutes."
        )
        return

    timer_seconds = duration * 60
    timer_end_time = None

    update_timer_display()

    timer_status.configure(
        text="Your time is ready.",
        text_color=MUTED
    )


button(
    focus_card,
    "Apply custom time",
    apply_duration,
    width=200
).grid(
    row=4,
    column=0,
    sticky="ew",
    padx=13,
    pady=(0, 8)
)


timer_display = label(
    focus_card,
    "25:00",
    size=34,
    color=CREAM,
    bold=True
)

timer_display.grid(
    row=5,
    column=0,
    pady=(0, 1)
)


timer_status = label(
    focus_card,
    "A moment just for you.",
    size=10,
    color=MUTED
)

timer_status.grid(
    row=6,
    column=0,
    pady=(0, 8)
)


timer_button_row = ctk.CTkFrame(
    focus_card,
    fg_color="transparent"
)

timer_button_row.grid(
    row=7,
    column=0,
    sticky="ew",
    padx=10,
    pady=(0, 13)
)

for col in range(3):
    timer_button_row.grid_columnconfigure(col, weight=1)


def update_timer_display():
    minutes, seconds = divmod(max(0, timer_seconds), 60)
    timer_display.configure(text=f"{minutes:02d}:{seconds:02d}")


def timer_tick():
    global timer_seconds, timer_running, timer_end_time, timer_after_id

    timer_after_id = None

    if not timer_running or timer_end_time is None:
        return

    timer_seconds = max(
        0,
        math.ceil(timer_end_time - datetime.now().timestamp())
    )

    update_timer_display()

    if timer_seconds <= 0:
        timer_running = False
        timer_end_time = None

        timer_status.configure(
            text="Your session has bloomed.",
            text_color=GOLD
        )

        messagebox.showinfo(
            "Focus session complete",
            "You've completed your focus session.\n\n"
            "Take a little break. You've earned it."
        )

        return

    timer_after_id = app.after(250, timer_tick)


def start_timer():
    global timer_running, timer_end_time, timer_seconds, timer_after_id

    if timer_running:
        return

    if timer_seconds <= 0:
        duration = custom_duration_minutes()

        if duration is None:
            messagebox.showwarning(
                "Choose a duration",
                "Select a valid timer duration first."
            )
            return

        timer_seconds = duration * 60

    timer_running = True
    timer_end_time = datetime.now().timestamp() + timer_seconds

    timer_status.configure(
        text="One thing at a time.",
        text_color=GOLD
    )

    if timer_after_id is None:
        timer_after_id = app.after(250, timer_tick)


def pause_timer():
    global timer_running, timer_end_time, timer_seconds, timer_after_id

    if not timer_running:
        return

    timer_seconds = max(
        0,
        math.ceil(timer_end_time - datetime.now().timestamp())
    )

    timer_running = False
    timer_end_time = None

    if timer_after_id is not None:
        app.after_cancel(timer_after_id)
        timer_after_id = None

    update_timer_display()

    timer_status.configure(
        text="Paused. Breathe for a moment.",
        text_color=MUTED
    )


def reset_timer():
    global timer_running, timer_end_time, timer_seconds, timer_after_id

    timer_running = False
    timer_end_time = None

    if timer_after_id is not None:
        app.after_cancel(timer_after_id)
        timer_after_id = None

    duration = custom_duration_minutes()

    timer_seconds = (duration if duration else 25) * 60

    update_timer_display()

    timer_status.configure(
        text="A fresh beginning.",
        text_color=MUTED
    )


button(
    timer_button_row,
    "Start",
    start_timer,
    width=68,
    color=ORANGE
).grid(row=0, column=0, sticky="ew", padx=2)

button(
    timer_button_row,
    "Pause",
    pause_timer,
    width=68
).grid(row=0, column=1, sticky="ew", padx=2)

button(
    timer_button_row,
    "Reset",
    reset_timer,
    width=68
).grid(row=0, column=2, sticky="ew", padx=2)


# ==========================================================
# MUSIC NOOK
# ==========================================================

music_card = ctk.CTkFrame(
    left,
    fg_color=CARD,
    corner_radius=15,
    border_width=1,
    border_color="#344638"
)

music_card.grid(
    row=2,
    column=0,
    sticky="ew",
    pady=(0, 10)
)

music_card.grid_columnconfigure(0, weight=1)

label(
    music_card,
    "The music nook",
    size=16,
    color=GOLD,
    bold=True
).grid(
    row=0,
    column=0,
    sticky="w",
    padx=13,
    pady=(13, 3)
)

label(
    music_card,
    "A soundtrack for little adventures.",
    size=10,
    color=MUTED
).grid(
    row=1,
    column=0,
    sticky="w",
    padx=13,
    pady=(0, 8)
)


music_var = ctk.StringVar(value="No music found")

music_menu = ctk.CTkOptionMenu(
    music_card,
    values=["No music found"],
    variable=music_var,
    height=31,
    fg_color=GREEN,
    button_color=ORANGE,
    button_hover_color=ROSE_DARK,
    text_color=CREAM
)

music_menu.grid(
    row=2,
    column=0,
    sticky="ew",
    padx=13,
    pady=(0, 8)
)


music_status = label(
    music_card,
    "Your soundtrack awaits.",
    size=10,
    color=MUTED
)

music_status.grid(
    row=3,
    column=0,
    sticky="w",
    padx=13,
    pady=(0, 8)
)


def initialize_music():
    global pygame_ready

    try:
        pygame.mixer.init()
        pygame_ready = True
        pygame.mixer.music.set_volume(0.7)
    except Exception:
        pygame_ready = False


def refresh_music():
    global music_files

    try:
        music_files = [
            name for name in os.listdir(MUSIC_FOLDER)
            if name.lower().endswith((".mp3", ".wav", ".ogg"))
        ]
    except OSError:
        music_files = []

    music_files.sort(key=str.lower)

    if music_files:
        music_menu.configure(values=music_files)

        if music_var.get() not in music_files:
            music_var.set(music_files[0])
    else:
        music_menu.configure(values=["No music found"])
        music_var.set("No music found")


def play_music():
    global music_paused

    if not pygame_ready:
        messagebox.showwarning(
            "Music unavailable",
            "The audio system could not be initialized."
        )
        return

    selected = music_var.get()

    if selected not in music_files:
        messagebox.showinfo(
            "Your music nook",
            f"Add audio files to:\n{MUSIC_FOLDER}"
        )
        return

    if music_paused:
        try:
            pygame.mixer.music.unpause()
            music_paused = False
            music_status.configure(text="Music resumed.")
            return
        except Exception:
            pass

    filepath = os.path.join(MUSIC_FOLDER, selected)

    try:
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        music_paused = False
        music_status.configure(text=f"Playing: {selected}")
    except Exception as error:
        messagebox.showerror(
            "Playback error",
            f"Could not play the selected file.\n\n{error}"
        )


def pause_music():
    global music_paused

    if not pygame_ready:
        return

    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            music_paused = True
            music_status.configure(text="Music paused.")
    except Exception:
        pass


def stop_music():
    global music_paused

    if not pygame_ready:
        return

    try:
        pygame.mixer.music.stop()
        music_paused = False
        music_status.configure(text="Music stopped.")
    except Exception:
        pass


music_controls = ctk.CTkFrame(
    music_card,
    fg_color="transparent"
)

music_controls.grid(
    row=4,
    column=0,
    sticky="ew",
    padx=10,
    pady=(0, 8)
)

for col in range(3):
    music_controls.grid_columnconfigure(col, weight=1)


button(
    music_controls,
    "Play",
    play_music,
    width=65,
    color=ORANGE
).grid(row=0, column=0, sticky="ew", padx=2)

button(
    music_controls,
    "Pause",
    pause_music,
    width=65
).grid(row=0, column=1, sticky="ew", padx=2)

button(
    music_controls,
    "Stop",
    stop_music,
    width=65
).grid(row=0, column=2, sticky="ew", padx=2)


button(
    music_card,
    "Refresh music list",
    refresh_music,
    width=200
).grid(
    row=5,
    column=0,
    sticky="ew",
    padx=13,
    pady=(0, 13)
)


# ==========================================================
# GARDEN HEADER
# ==========================================================

garden_header = ctk.CTkFrame(
    garden,
    fg_color="transparent"
)

garden_header.grid(
    row=0,
    column=0,
    sticky="ew",
    padx=15,
    pady=(15, 8)
)

garden_header.grid_columnconfigure(0, weight=1)

label(
    garden_header,
    "Your Little Garden",
    size=21,
    color=GOLD,
    bold=True
).grid(
    row=0,
    column=0,
    sticky="w"
)

label(
    garden_header,
    "Small steps become lovely things.",
    size=10,
    color=MUTED
).grid(
    row=1,
    column=0,
    sticky="w",
    pady=(3, 0)
)


# ==========================================================
# COMPACT PROGRESS CARDS
# ==========================================================

stats = ctk.CTkFrame(
    garden,
    fg_color="transparent"
)

stats.grid(
    row=1,
    column=0,
    sticky="ew",
    padx=10,
    pady=(0, 10)
)

for col in range(3):
    stats.grid_columnconfigure(col, weight=1)


def stat_card(parent, column, heading):
    frame = ctk.CTkFrame(
        parent,
        fg_color=CARD_LIGHT,
        corner_radius=10
    )

    frame.grid(
        row=0,
        column=column,
        sticky="ew",
        padx=3
    )

    label(
        frame,
        heading,
        size=9,
        color=MUTED
    ).pack(pady=(8, 0))

    value = label(
        frame,
        "0",
        size=19,
        color=GOLD,
        bold=True
    )

    value.pack(pady=(0, 7))

    return value


total_value = stat_card(stats, 0, "PLANNED")
pending_value = stat_card(stats, 1, "GROWING")
completed_value = stat_card(stats, 2, "BLOOMED")


# ==========================================================
# FILTERS
# ==========================================================

filter_bar = ctk.CTkFrame(
    garden,
    fg_color="transparent"
)

filter_bar.grid(
    row=2,
    column=0,
    sticky="ew",
    padx=15,
    pady=(0, 8)
)

filter_bar.grid_columnconfigure(0, weight=1)

label(
    filter_bar,
    "Your plans",
    size=14,
    color=CREAM,
    bold=True
).grid(
    row=0,
    column=0,
    sticky="w"
)


def change_filter(value):
    global current_filter
    current_filter = value
    refresh_tasks()


filter_var = ctk.StringVar(value="All")

filter_menu = ctk.CTkOptionMenu(
    filter_bar,
    values=["All", "Today", "Pending", "Completed", "Overdue"],
    variable=filter_var,
    command=change_filter,
    width=120,
    height=29,
    fg_color=GREEN,
    button_color=ORANGE,
    button_hover_color=ROSE_DARK,
    text_color=CREAM,
    font=(UI_FONT, 10)
)

filter_menu.grid(
    row=0,
    column=1,
    sticky="e"
)


# ==========================================================
# SCROLLABLE TASK LIST
# ==========================================================

task_list = ctk.CTkScrollableFrame(
    garden,
    fg_color="transparent",
    corner_radius=10,
    scrollbar_button_color=GREEN,
    scrollbar_button_hover_color=GOLD
)

task_list.grid(
    row=3,
    column=0,
    sticky="nsew",
    padx=9,
    pady=(0, 10)
)

task_list.grid_columnconfigure(0, weight=1)


# ==========================================================
# TASK FILTERING
# ==========================================================

def get_filtered_tasks():
    today = date.today().isoformat()

    if current_filter == "Today":
        return [
            task for task in tasks
            if task.get("date") == today
        ]

    if current_filter == "Pending":
        return [
            task for task in tasks
            if not task.get("completed", False)
        ]

    if current_filter == "Completed":
        return [
            task for task in tasks
            if task.get("completed", False)
        ]

    if current_filter == "Overdue":
        now = datetime.now()

        return [
            task for task in tasks
            if (
                not task.get("completed", False)
                and parse_due(task) is not None
                and parse_due(task) < now
            )
        ]

    return tasks[:]


# ==========================================================
# COMPLETE / DELETE / EDIT
# ==========================================================

def toggle_task(task_id):
    for task in tasks:
        if task.get("id") == task_id:
            task["completed"] = not task.get("completed", False)

            if task["completed"]:
                task["completed_at"] = datetime.now().isoformat()
            else:
                task.pop("completed_at", None)

            break

    save_tasks()
    refresh_tasks()


def delete_task(task_id):
    if not messagebox.askyesno(
        "Remove this task?",
        "Would you like to remove this little plan?"
    ):
        return

    tasks[:] = [
        task for task in tasks
        if task.get("id") != task_id
    ]

    notified_tasks.discard(task_id)

    save_tasks()
    refresh_tasks()


def edit_task(task_id):
    task = next(
        (item for item in tasks if item.get("id") == task_id),
        None
    )

    if task is None:
        return

    window = ctk.CTkToplevel(app)
    window.title("Edit a Little Plan")
    window.geometry("390x440")
    window.configure(fg_color=BG)
    window.transient(app)
    window.grab_set()
    window.grid_columnconfigure(0, weight=1)

    label(
        window,
        "Tend to your plan",
        size=22,
        color=GOLD,
        bold=True
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=18,
        pady=(18, 12)
    )

    label(window, "Title", color=MUTED).grid(
        row=1, column=0, sticky="w", padx=18, pady=(0, 4)
    )

    edit_title = ctk.CTkEntry(window, height=34)
    edit_title.grid(
        row=2, column=0, sticky="ew", padx=18, pady=(0, 9)
    )
    edit_title.insert(0, task.get("title", ""))

    label(window, "Notes", color=MUTED).grid(
        row=3, column=0, sticky="w", padx=18, pady=(0, 4)
    )

    edit_notes = ctk.CTkTextbox(window, height=75)
    edit_notes.grid(
        row=4, column=0, sticky="ew", padx=18, pady=(0, 9)
    )
    edit_notes.insert("1.0", task.get("notes", ""))

    label(
        window,
        "Date (YYYY-MM-DD)",
        color=MUTED
    ).grid(
        row=5, column=0, sticky="w", padx=18, pady=(0, 4)
    )

    edit_date = ctk.CTkEntry(window, height=34)
    edit_date.grid(
        row=6, column=0, sticky="ew", padx=18, pady=(0, 9)
    )
    edit_date.insert(0, task.get("date", date.today().isoformat()))

    label(
        window,
        "Time (HH:MM)",
        color=MUTED
    ).grid(
        row=7, column=0, sticky="w", padx=18, pady=(0, 4)
    )

    edit_time = ctk.CTkEntry(window, height=34)
    edit_time.grid(
        row=8, column=0, sticky="ew", padx=18, pady=(0, 12)
    )
    edit_time.insert(0, task.get("time", "18:00"))

    def save_edit():
        new_title = edit_title.get().strip()
        new_notes = edit_notes.get("1.0", "end").strip()
        new_date = edit_date.get().strip()
        new_time = edit_time.get().strip()

        if not new_title:
            messagebox.showwarning(
                "Missing title",
                "Please enter a task title.",
                parent=window
            )
            return

        try:
            datetime.strptime(
                f"{new_date} {new_time}",
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            messagebox.showwarning(
                "Invalid date or time",
                "Use YYYY-MM-DD and HH:MM.",
                parent=window
            )
            return

        task["title"] = new_title
        task["notes"] = new_notes
        task["date"] = new_date
        task["time"] = new_time

        notified_tasks.discard(task_id)

        save_tasks()
        refresh_tasks()
        window.destroy()

    button(
        window,
        "Save changes",
        save_edit,
        width=200,
        color=ORANGE
    ).grid(
        row=9,
        column=0,
        sticky="ew",
        padx=18,
        pady=(0, 18)
    )


# ==========================================================
# UPDATE TASK COUNTS
# ==========================================================

def refresh_stats():
    total = len(tasks)
    completed = sum(
        1 for task in tasks
        if task.get("completed", False)
    )

    total_value.configure(text=str(total))
    pending_value.configure(text=str(total - completed))
    completed_value.configure(text=str(completed))


# ==========================================================
# RENDER TASKS
# ==========================================================

def refresh_tasks():
    for widget in task_list.winfo_children():
        widget.destroy()

    refresh_stats()

    visible_tasks = get_filtered_tasks()

    visible_tasks.sort(
        key=lambda task: (
            task.get("completed", False),
            parse_due(task) or datetime.max
        )
    )

    if not visible_tasks:
        empty = ctk.CTkFrame(
            task_list,
            fg_color=CARD_LIGHT,
            corner_radius=13
        )

        empty.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=3,
            pady=6
        )

        label(
            empty,
            "A little room to breathe",
            size=16,
            color=GOLD,
            bold=True
        ).pack(pady=(22, 5))

        label(
            empty,
            "Your next little adventure starts here.",
            size=10,
            color=MUTED
        ).pack(pady=(0, 22))

        return

    for index, task in enumerate(visible_tasks):
        task_id = task["id"]
        completed = task.get("completed", False)

        card = ctk.CTkFrame(
            task_list,
            fg_color=CARD_LIGHT if completed else "#2A3B2F",
            corner_radius=12,
            border_width=1,
            border_color="#3A4C3C"
        )

        card.grid(
            row=index,
            column=0,
            sticky="ew",
            padx=2,
            pady=4
        )

        card.grid_columnconfigure(1, weight=1)

        checkbox = ctk.CTkCheckBox(
            card,
            text="",
            width=22,
            checkbox_width=18,
            checkbox_height=18,
            variable=ctk.BooleanVar(value=completed),
            command=lambda tid=task_id: toggle_task(tid),
            fg_color=GREEN,
            hover_color=ORANGE,
            border_color=GOLD
        )

        checkbox.grid(
            row=0,
            column=0,
            rowspan=3,
            padx=(10, 6),
            pady=10,
            sticky="n"
        )

        task_title = label(
            card,
            task.get("title", "Untitled"),
            size=12,
            color=MUTED if completed else CREAM,
            bold=True
        )

        task_title.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, 5),
            pady=(9, 2)
        )

        due = (
            f"{task.get('date', 'No date')}  ·  "
            f"{task.get('time', 'No time')}"
        )

        label(
            card,
            due,
            size=10,
            color=MUTED
        ).grid(
            row=1,
            column=1,
            sticky="w",
            padx=(0, 5),
            pady=(0, 2)
        )

        status = task_status(task)

        label(
            card,
            status,
            size=9,
            color=(
                SAGE if completed
                else RED if status == "Past due"
                else GOLD
            )
        ).grid(
            row=2,
            column=1,
            sticky="w",
            padx=(0, 5),
            pady=(0, 9)
        )

        actions = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        actions.grid(
            row=0,
            column=2,
            rowspan=3,
            padx=(0, 7),
            pady=8,
            sticky="e"
        )

        ctk.CTkButton(
            actions,
            text="Edit",
            command=lambda tid=task_id: edit_task(tid),
            width=43,
            height=25,
            corner_radius=7,
            fg_color=GREEN,
            hover_color=ORANGE,
            text_color=CREAM,
            font=(UI_FONT, 10)
        ).pack(pady=(0, 4))

        ctk.CTkButton(
            actions,
            text="×",
            command=lambda tid=task_id: delete_task(tid),
            width=43,
            height=25,
            corner_radius=7,
            fg_color=ROSE_DARK,
            hover_color=RED,
            text_color=CREAM,
            font=(UI_FONT, 12)
        ).pack()

        notes = task.get("notes", "").strip()

        if notes:
            notes_label = label(
                card,
                notes,
                size=10,
                color=MUTED
            )

            notes_label.configure(
                wraplength=230,
                justify="left"
            )

            notes_label.grid(
                row=3,
                column=1,
                sticky="w",
                padx=(0, 5),
                pady=(0, 8)
            )


# ==========================================================
# TASK REMINDERS
# ==========================================================

def check_reminders():
    now = datetime.now()

    for task in tasks:
        task_id = task.get("id")

        if not task_id or task.get("completed", False):
            continue

        if task_id in notified_tasks:
            continue

        due = parse_due(task)

        if due is None:
            continue

        if timedelta(0) <= now - due <= timedelta(minutes=15):
            notified_tasks.add(task_id)

            messagebox.showinfo(
                "A little reminder",
                f"It's time for:\n\n{task.get('title', 'Your task')}\n\n"
                f"Due at {task.get('time', '')}"
            )

    app.after(15000, check_reminders)


# ==========================================================
# STARTUP
# ==========================================================

def close_app():
    global timer_running, timer_after_id

    timer_running = False

    if timer_after_id is not None:
        try:
            app.after_cancel(timer_after_id)
        except tk.TclError:
            pass

    try:
        if pygame_ready:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
    except Exception:
        pass

    save_tasks()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", close_app)

initialize_music()
refresh_music()
refresh_tasks()
update_timer_display()

app.after(15000, check_reminders)

app.mainloop()