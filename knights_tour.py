import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkFont
import time
import os

# Try importing pygame for audio
try:
    import pygame
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

class KnightsTourGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Knight's Tour")
        
        # Default Game State
        self.n = 8
        self.m = 8
        self.cell_size = 60
        self.history = [] 
        self.visited = set() 
        self.planned_solution = [] 
        self.is_solving = False 
        self.is_playing = False 
        self.is_fullscreen = False
        
        # Centering and Panning
        self.offset_x = 0
        self.offset_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        
        # Audio State Flags & Base Volumes
        self.victory_played = False
        self.gameover_played = False
        self.bgm_loaded = False
        self.sfx_base_vols = {
            "click.wav": 0.5,      
            "victory.wav": 1.0,
            "gameover.wav": 1.0
        }
        
        # Mode Toggles & Variables
        self.show_counts_mode = tk.BooleanVar(value=False)
        self.show_hint_mode = tk.BooleanVar(value=False)
        self.show_max_path_mode = tk.BooleanVar(value=False)
        self.speed_var = tk.DoubleVar(value=0.05) 
        
        # Audio Mute & Volume Variables
        self.mute_bgm_var = tk.BooleanVar(value=False)
        self.mute_sfx_var = tk.BooleanVar(value=False)
        self.bgm_vol_var = tk.DoubleVar(value=1.0) 
        self.sfx_vol_var = tk.DoubleVar(value=1.0)
        
        # Dynamic Fonts for UI Scaling
        self.ui_font_size = 11
        self.title_font_size = 32
        
        self.title_font = tkFont.Font(family="Old English Text MT", size=self.title_font_size, weight="bold")
        self.ui_font = tkFont.Font(family="Georgia", size=self.ui_font_size)
        self.ui_bold_font = tkFont.Font(family="Georgia", size=self.ui_font_size, weight="bold")
        self.status_font = tkFont.Font(family="Georgia", size=self.ui_font_size + 2, weight="bold")
        
        self.init_audio()
        self.setup_ui()
        self.apply_size()
        
        # Key Bindings
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        
        # Global Ctrl+Scroll dispatcher
        self.root.bind("<Control-MouseWheel>", self.on_ctrl_scroll)
        self.root.bind("<Control-Button-4>", self.on_ctrl_scroll)
        self.root.bind("<Control-Button-5>", self.on_ctrl_scroll)

    def init_audio(self):
        self.sounds = {}
        if not HAS_AUDIO:
            return
        try:
            pygame.mixer.init()
            if os.path.exists("bgm.wav"):
                pygame.mixer.music.load("bgm.wav")
                pygame.mixer.music.set_volume(self.bgm_vol_var.get())
                pygame.mixer.music.play(-1)
                self.bgm_loaded = True
                
            sfx_files = ["click.wav", "victory.wav", "gameover.wav"]
            for sfx in sfx_files:
                if os.path.exists(sfx):
                    self.sounds[sfx] = pygame.mixer.Sound(sfx)
            self.update_sfx_volume()
        except Exception:
            pass

    def update_bgm_volume(self, val=None):
        if HAS_AUDIO and self.bgm_loaded:
            pygame.mixer.music.set_volume(self.bgm_vol_var.get())

    def update_sfx_volume(self, val=None):
        if HAS_AUDIO:
            master_sfx_vol = self.sfx_vol_var.get()
            for sfx_name, sound_obj in self.sounds.items():
                base_vol = self.sfx_base_vols.get(sfx_name, 1.0)
                sound_obj.set_volume(master_sfx_vol * base_vol)

    def toggle_bgm(self):
        if HAS_AUDIO and self.bgm_loaded:
            if self.mute_bgm_var.get():
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
            
    def play_sound(self, sound_name):
        if HAS_AUDIO and not self.mute_sfx_var.get() and sound_name in self.sounds:
            self.sounds[sound_name].play()

    def get_margin(self):
        return self.cell_size * 0.6

    def get_col_label(self, c):
        label = ""
        while True:
            label = chr(65 + (c % 26)) + label
            c = c // 26 - 1
            if c < 0:
                break
        return label

    # --- Animation Logistics ---
    
    def toggle_top(self):
        self.top_collapsed = not self.top_collapsed
        self.top_toggle_btn.config(text="▼" if self.top_collapsed else "▲")
        self.animate_top()

    def animate_top(self):
        target = 0 if self.top_collapsed else self.top_req_height
        speed = max(15, self.top_req_height // 8)
        
        diff = target - self.top_current_height
        if abs(diff) <= speed:
            self.top_current_height = target
            self.top_container.config(height=self.top_current_height)
            self.top_ui_frame.place(relwidth=1, y=self.top_current_height - self.top_req_height)
            return
            
        self.top_current_height += speed if diff > 0 else -speed
        self.top_container.config(height=self.top_current_height)
        self.top_ui_frame.place(relwidth=1, y=self.top_current_height - self.top_req_height)
        self.root.after(16, self.animate_top)

    def toggle_bottom(self):
        self.bottom_collapsed = not self.bottom_collapsed
        self.bottom_toggle_btn.config(text="▲ About the Game ▲" if self.bottom_collapsed else "▼ Close ▼")
        self.animate_bottom()

    def animate_bottom(self):
        target = 0 if self.bottom_collapsed else self.bottom_req_height
        speed = max(15, self.bottom_req_height // 8)
        
        diff = target - self.bottom_current_height
        if abs(diff) <= speed:
            self.bottom_current_height = target
            self.bottom_container.config(height=self.bottom_current_height)
            self.bottom_ui_frame.place(relwidth=1, y=0)
            return
            
        self.bottom_current_height += speed if diff > 0 else -speed
        self.bottom_container.config(height=self.bottom_current_height)
        self.bottom_ui_frame.place(relwidth=1, y=0)
        self.root.after(16, self.animate_bottom)

    def trigger_ui_resize(self):
        """Updates internal heights when the UI changes organically (e.g. Solution buttons reveal)"""
        self.root.update_idletasks()
        self.top_req_height = self.top_ui_frame.winfo_reqheight()
        if not self.top_collapsed:
            self.top_current_height = self.top_req_height
            self.top_container.config(height=self.top_current_height)
            self.top_ui_frame.place(relwidth=1, y=0)

    # --- UI Setup ---

    def setup_ui(self):
        # 1. Medieval Title (Stays static at the top)
        tk.Label(self.root, text="Knight's Tour", font=self.title_font, fg="#2c3e50").pack(side=tk.TOP, pady=(10, 0))

        # 2. Top Collapsible Wrapper
        self.top_wrapper = tk.Frame(self.root)
        self.top_wrapper.pack(side=tk.TOP, fill=tk.X)
        
        self.top_container = tk.Frame(self.top_wrapper)
        self.top_container.pack(side=tk.TOP, fill=tk.X)
        
        self.top_ui_frame = tk.Frame(self.top_container, padx=10, pady=10)
        self.top_ui_frame.pack(side=tk.TOP, fill=tk.X) 
        
        # --- Game Controls (Inside Top UI) ---
        game_frame = tk.Frame(self.top_ui_frame)
        game_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        tk.Label(game_frame, text="Rows (n):", font=self.ui_font).grid(row=0, column=0, padx=2, pady=5)
        self.n_entry = tk.Entry(game_frame, width=5, font=self.ui_font)
        self.n_entry.insert(0, str(self.n))
        self.n_entry.grid(row=0, column=1, padx=2)
        
        tk.Label(game_frame, text="Cols (m):", font=self.ui_font).grid(row=0, column=2, padx=2)
        self.m_entry = tk.Entry(game_frame, width=5, font=self.ui_font)
        self.m_entry.insert(0, str(self.m))
        self.m_entry.grid(row=0, column=3, padx=2)
        
        tk.Button(game_frame, text="Set Size / Restart", command=self.apply_size, bg="#e0e0e0", font=self.ui_font).grid(row=0, column=4, padx=10)
        tk.Button(game_frame, text="Reset", command=self.reset, bg="#ffcccc", font=self.ui_font).grid(row=0, column=5, padx=5)
        tk.Button(game_frame, text="Undo", command=self.undo, bg="#ffffcc", font=self.ui_font).grid(row=0, column=6, padx=5)
        tk.Button(game_frame, text="Give Solution", command=self.solve, bg="#ccffcc", font=self.ui_font).grid(row=0, column=7, padx=5)
        
        tk.Checkbutton(game_frame, text="Show Next Path Counts", variable=self.show_counts_mode, command=self.draw_board, font=self.ui_font).grid(row=1, column=0, columnspan=3, sticky="w", pady=5)
        tk.Checkbutton(game_frame, text="Hint: Max paths from cell", variable=self.show_hint_mode, command=self.draw_board, font=self.ui_font).grid(row=1, column=3, columnspan=3, sticky="w")
        tk.Checkbutton(game_frame, text="Show Global Max Paths", variable=self.show_max_path_mode, command=self.draw_board, font=self.ui_font).grid(row=1, column=6, columnspan=3, sticky="w")
        
        self.solution_frame = tk.Frame(game_frame, bd=2, relief=tk.GROOVE, padx=5, pady=5)
        self.solution_frame.grid(row=2, column=0, columnspan=9, sticky="w", pady=5)
        
        self.play_btn = tk.Button(self.solution_frame, text="▶", command=self.play_solution, bg="#b3e5fc", width=4, font=self.ui_bold_font)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.solution_frame, text="Speed Delay:", font=self.ui_font).pack(side=tk.LEFT)
        self.speed_scale = tk.Scale(self.solution_frame, variable=self.speed_var, from_=0.0, to=0.5, resolution=0.01, orient=tk.HORIZONTAL, length=150, showvalue=True, font=self.ui_font)
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        
        self.prev_btn = tk.Button(self.solution_frame, text="Previous", command=self.step_backward, bg="#ffccbc", width=8, font=self.ui_font)
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = tk.Button(self.solution_frame, text="Next", command=self.step_forward, bg="#dcedc8", width=8, font=self.ui_font)
        self.next_btn.pack(side=tk.LEFT, padx=5)

        self.solution_frame.grid_remove()

        # --- Audio Controls (Inside Top UI) ---
        audio_frame = tk.Frame(self.top_ui_frame, bd=2, relief=tk.GROOVE, padx=10, pady=5)
        audio_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(audio_frame, text="Audio Controls", font=self.ui_bold_font).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        tk.Checkbutton(audio_frame, text="Mute BGM", variable=self.mute_bgm_var, command=self.toggle_bgm, font=self.ui_font).grid(row=1, column=0, sticky="w")
        self.bgm_scale = tk.Scale(audio_frame, variable=self.bgm_vol_var, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, length=100, showvalue=False, command=self.update_bgm_volume)
        self.bgm_scale.grid(row=1, column=1, padx=(5, 0))

        tk.Checkbutton(audio_frame, text="Mute SFX", variable=self.mute_sfx_var, font=self.ui_font).grid(row=2, column=0, sticky="w", pady=(5,0))
        self.sfx_scale = tk.Scale(audio_frame, variable=self.sfx_vol_var, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, length=100, showvalue=False, command=self.update_sfx_volume)
        self.sfx_scale.grid(row=2, column=1, padx=(5, 0), pady=(5,0))

        # Top Slide Toggle Button
        self.top_toggle_btn = tk.Button(self.top_wrapper, text="▲", command=self.toggle_top, font=("Arial", 9), bg="#dcdcdc", relief=tk.FLAT, pady=0)
        self.top_toggle_btn.pack(side=tk.TOP, fill=tk.X)

        # 3. Status Panel (Stays visible below Top UI)
        self.status_var = tk.StringVar()
        self.max_path_var = tk.StringVar()
        
        status_frame = tk.Frame(self.root, padx=10)
        status_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        tk.Label(status_frame, textvariable=self.status_var, font=self.status_font, fg="red").pack(side=tk.LEFT)
        tk.Label(status_frame, textvariable=self.max_path_var, font=self.status_font, fg="blue").pack(side=tk.LEFT, padx=(20, 0))
        tk.Label(status_frame, text="(F11 Fullscreen, Ctrl+Scroll Zoom)", fg="gray", font=self.ui_font).pack(side=tk.RIGHT, padx=5)

        # 4. Bottom Collapsible Wrapper (About Section)
        self.bottom_wrapper = tk.Frame(self.root)
        self.bottom_wrapper.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.bottom_toggle_btn = tk.Button(self.bottom_wrapper, text="▲ About the Game ▲", command=self.toggle_bottom, font=("Arial", 9), bg="#dcdcdc", relief=tk.FLAT, pady=0)
        self.bottom_toggle_btn.pack(side=tk.TOP, fill=tk.X)
        
        self.bottom_container = tk.Frame(self.bottom_wrapper)
        self.bottom_container.pack(side=tk.TOP, fill=tk.X)
        
        self.bottom_ui_frame = tk.Frame(self.bottom_container, bg="#fdfbf7", bd=2, relief=tk.SUNKEN)
        self.bottom_ui_frame.pack(side=tk.TOP, fill=tk.X)
        
        about_text = """HOW TO PLAY:
1. Select the board size and click 'Set Size / Restart'.
2. Click any square to place your first Knight.
3. Click on the green highlighted squares to move in an "L" shape.
4. The goal is to visit every square on the board exactly once!
5. Tip: You can click on any previously visited square's number to Undo back to that exact move.

HISTORY:
The Knight's Tour is a classic mathematical problem dating back to the 9th century in Arabic manuscripts. 
It was extensively analyzed by the famous mathematician Leonhard Euler in 1759. 
Finding a full path is a classic example of computing a Hamiltonian path in graph theory."""
        
        tk.Label(self.bottom_ui_frame, text=about_text, justify=tk.LEFT, font=self.ui_font, bg="#fdfbf7", padx=15, pady=15).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Initialize Container Heights for Animations
        self.root.update_idletasks()
        
        # Setup Top Animation variables
        self.top_req_height = self.top_ui_frame.winfo_reqheight()
        self.top_current_height = self.top_req_height
        self.top_container.pack_propagate(False)
        self.top_container.config(height=self.top_req_height)
        self.top_ui_frame.pack_forget()
        self.top_ui_frame.place(relwidth=1, y=0)
        self.top_collapsed = False
        
        # Setup Bottom Animation variables
        self.bottom_req_height = self.bottom_ui_frame.winfo_reqheight()
        self.bottom_current_height = 0
        self.bottom_container.pack_propagate(False)
        self.bottom_container.config(height=0)
        self.bottom_ui_frame.pack_forget()
        self.bottom_ui_frame.place(relwidth=1, y=0)
        self.bottom_collapsed = True

        # 5. Game Canvas with Scrollbars (Center)
        self.canvas_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.canvas_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)
        
        self.v_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        
        self.h_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", highlightthickness=0, 
                                yscrollcommand=self.v_scroll.set,
                                xscrollcommand=self.h_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        
        # Mouse Interactions
        self.canvas.bind("<MouseWheel>", self.on_mousewheel_v) 
        self.canvas.bind("<Button-4>", self.on_mousewheel_v)   
        self.canvas.bind("<Button-5>", self.on_mousewheel_v)   
        
        self.canvas.bind("<Shift-MouseWheel>", self.on_mousewheel_h)
        self.canvas.bind("<Shift-Button-4>", self.on_mousewheel_h)
        self.canvas.bind("<Shift-Button-5>", self.on_mousewheel_h)
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Configure>", lambda e: self.draw_board())

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)

    def on_ctrl_scroll(self, event):
        if str(event.widget) == str(self.canvas):
            self.zoom_board(event)
        else:
            self.zoom_ui(event)

    def zoom_ui(self, event):
        if getattr(event, 'num', 0) == 4 or getattr(event, 'delta', 0) > 0:
            self.ui_font_size = min(24, self.ui_font_size + 1)
        elif getattr(event, 'num', 0) == 5 or getattr(event, 'delta', 0) < 0:
            self.ui_font_size = max(8, self.ui_font_size - 1)
            
        self.ui_font.configure(size=self.ui_font_size)
        self.ui_bold_font.configure(size=self.ui_font_size, weight="bold")
        self.status_font.configure(size=self.ui_font_size + 2, weight="bold")
        
        self.title_font_size = self.ui_font_size + 21
        self.title_font.configure(size=self.title_font_size)
        
        # Dynamically Adjust Containers so it scales beautifully while zooming
        self.root.update_idletasks()
        
        new_top_req = self.top_ui_frame.winfo_reqheight()
        if not self.top_collapsed:
            self.top_current_height = new_top_req
            self.top_container.config(height=self.top_current_height)
            self.top_ui_frame.place(relwidth=1, y=0)
        self.top_req_height = new_top_req
        
        new_bottom_req = self.bottom_ui_frame.winfo_reqheight()
        if not self.bottom_collapsed:
            self.bottom_current_height = new_bottom_req
            self.bottom_container.config(height=self.bottom_current_height)
            self.bottom_ui_frame.place(relwidth=1, y=0)
        self.bottom_req_height = new_bottom_req

    def zoom_board(self, event):
        if getattr(event, 'num', 0) == 4 or getattr(event, 'delta', 0) > 0:
            self.cell_size = min(250, self.cell_size + 5)
        elif getattr(event, 'num', 0) == 5 or getattr(event, 'delta', 0) < 0:
            self.cell_size = max(20, self.cell_size - 5)
        self.draw_board()

    def on_mousewheel_v(self, event):
        if event.state & 0x0004: return # Ignore if Ctrl is held
        dir = -1 if event.num == 4 or getattr(event, 'delta', 0) > 0 else 1
        self.canvas.yview_scroll(dir, "units")

    def on_mousewheel_h(self, event):
        if event.state & 0x0004: return 
        dir = -1 if event.num == 4 or getattr(event, 'delta', 0) > 0 else 1
        self.canvas.xview_scroll(dir, "units")

    def on_press(self, event):
        if self.is_playing: return
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = False
        self.canvas.scan_mark(event.x, event.y)

    def on_drag(self, event):
        if self.is_playing: return
        if abs(event.x - self.drag_start_x) > 3 or abs(event.y - self.drag_start_y) > 3:
            self.is_dragging = True
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_release(self, event):
        if self.is_playing: return
        if not self.is_dragging:
            margin = self.get_margin()
            real_x = self.canvas.canvasx(event.x)
            real_y = self.canvas.canvasy(event.y)
            c = int(real_x - self.offset_x - margin) // self.cell_size
            r = int(real_y - self.offset_y - margin) // self.cell_size
            self.handle_click(r, c)

    def handle_click(self, r, c):
        if not (0 <= r < self.n and 0 <= c < self.m):
            return
            
        if (r, c) in self.history:
            idx = self.history.index((r, c))
            if idx < len(self.history) - 1:
                self.history = self.history[:idx + 1]
                self.visited = set(self.history)
                self.hide_solution_controls()
                self.victory_played = False
                self.gameover_played = False
                self.play_sound("click.wav")
                self.draw_board()
            return
            
        curr = self.history[-1] if self.history else None
        
        if not curr:
            self.hide_solution_controls()
            self.history.append((r, c))
            self.visited.add((r, c))
            self.play_sound("click.wav")
            self.draw_board()
            return
            
        valid_moves = self.get_valid_moves(curr[0], curr[1], self.visited)
        if (r, c) in valid_moves:
            self.hide_solution_controls() 
            self.history.append((r, c))
            self.visited.add((r, c))
            
            moves = self.get_valid_moves(r, c, self.visited)
            is_victory = len(self.history) == self.n * self.m
            is_gameover = not moves
            
            if not is_victory and not is_gameover:
                self.play_sound("click.wav")
                
            self.draw_board()

    def apply_size(self):
        try:
            new_n = int(self.n_entry.get())
            new_m = int(self.m_entry.get())
            if new_n < 3 or new_m < 3:
                messagebox.showerror("Error", "Board dimensions should be at least 3x3")
                return
            self.n = new_n
            self.m = new_m
            self.reset()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integers for N and M")

    def hide_solution_controls(self):
        self.is_playing = False
        self.is_solving = False
        self.planned_solution = []
        self.play_btn.config(text="▶")
        self.solution_frame.grid_remove()
        self.trigger_ui_resize()

    def reset(self):
        self.history.clear()
        self.visited.clear()
        self.victory_played = False
        self.gameover_played = False
        self.hide_solution_controls()
        self.draw_board()

    def undo(self):
        self.hide_solution_controls()
        self.victory_played = False
        self.gameover_played = False
        if self.history:
            last_move = self.history.pop()
            self.visited.remove(last_move)
            self.draw_board()

    def get_valid_moves(self, r, c, visited_set):
        moves = [
            (r-2, c-1), (r-2, c+1), (r-1, c-2), (r-1, c+2),
            (r+1, c-2), (r+1, c+2), (r+2, c-1), (r+2, c+1)
        ]
        return [(nr, nc) for nr, nc in moves if 0 <= nr < self.n and 0 <= nc < self.m and (nr, nc) not in visited_set]

    def warnsdorff_sort(self, moves, visited_set):
        return sorted(moves, key=lambda m: len(self.get_valid_moves(m[0], m[1], visited_set)))

    def solve(self):
        if len(self.history) == self.n * self.m:
            return
            
        self.hide_solution_controls()
        self.planned_solution = []
        
        temp_history = list(self.history)
        temp_visited = set(self.visited)
        
        if not temp_history:
            best_r, best_c = 0, 0
            best_max = 0
            for r in range(self.n):
                for c in range(self.m):
                    l = self._simulate_warnsdorff(r, c, set())
                    if l > best_max:
                        best_max = l
                        best_r, best_c = r, c
            
            self.planned_solution.append((best_r, best_c))
            temp_history.append((best_r, best_c))
            temp_visited.add((best_r, best_c))

        while len(temp_history) < self.n * self.m:
            curr = temp_history[-1]
            moves = self.get_valid_moves(curr[0], curr[1], temp_visited)
            
            if not moves:
                break 
                
            moves = self.warnsdorff_sort(moves, temp_visited)
            best_move = moves[0]
            
            temp_history.append(best_move)
            temp_visited.add(best_move)
            self.planned_solution.append(best_move)
            
        self.solution_frame.grid()
        self.trigger_ui_resize()

    def play_solution(self):
        if self.is_playing:
            self.is_playing = False
            self.play_btn.config(text="▶")
            return
            
        self.is_playing = True
        self.play_btn.config(text="⏸")
        self.is_solving = True 
        
        while self.is_playing and self.planned_solution:
            self.next_step()
            self.draw_board() 
            self.root.update()
            
            delay = self.speed_var.get()
            if delay > 0:
                time.sleep(delay)

        self.is_solving = False
        self.is_playing = False
        self.play_btn.config(text="▶")
        self.draw_board() 

    def step_forward(self):
        self.is_playing = False
        self.is_solving = False 
        self.play_btn.config(text="▶")
        self.next_step()
        self.draw_board()

    def step_backward(self):
        self.is_playing = False
        self.is_solving = False 
        self.play_btn.config(text="▶")
        self.prev_step()
        self.draw_board()

    def next_step(self):
        if self.planned_solution:
            nxt = self.planned_solution.pop(0)
            self.history.append(nxt)
            self.visited.add(nxt)
            
            moves = self.get_valid_moves(nxt[0], nxt[1], self.visited)
            is_victory = len(self.history) == self.n * self.m
            is_gameover = not moves and not self.planned_solution
            
            if not is_victory and not is_gameover:
                self.play_sound("click.wav")

    def prev_step(self):
        if self.history:
            last_move = self.history.pop()
            self.visited.remove(last_move)
            self.planned_solution.insert(0, last_move)
            self.play_sound("click.wav")

    def get_heuristic_max_path_length(self):
        if not self.history:
            best_max = 0
            for r in range(self.n):
                for c in range(self.m):
                    best_max = max(best_max, self._simulate_warnsdorff(r, c, set()))
            return best_max
        else:
            curr = self.history[-1]
            return self._simulate_warnsdorff(curr[0], curr[1], self.visited)

    def _simulate_warnsdorff(self, start_r, start_c, visited_set):
        temp_visited = set(visited_set)
        temp_visited.add((start_r, start_c))
        
        length = len(temp_visited)
        curr = (start_r, start_c)
        
        while True:
            moves = self.get_valid_moves(curr[0], curr[1], temp_visited)
            if not moves:
                break
            moves = self.warnsdorff_sort(moves, temp_visited)
            curr = moves[0]
            temp_visited.add(curr)
            length += 1
            
        return length

    def update_status(self):
        curr = self.history[-1] if self.history else None
        
        if not curr:
            self.status_var.set("Click any square to start.")
        else:
            moves = self.get_valid_moves(curr[0], curr[1], self.visited)
            if len(self.history) == self.n * self.m:
                self.status_var.set("Victory! Board Completed!")
                if not self.victory_played:
                    self.play_sound("victory.wav")
                    self.victory_played = True
            elif not moves and not self.planned_solution:
                self.status_var.set("Game Over! No available moves left.")
                if not self.gameover_played:
                    self.play_sound("gameover.wav")
                    self.gameover_played = True
            else:
                self.status_var.set(f"Move {len(self.history)}. Select next path.")
            
        if self.show_max_path_mode.get():
            max_len = self.get_heuristic_max_path_length()
            self.max_path_var.set(f"Global Max Path: {max_len} moves")
        else:
            self.max_path_var.set("")

    def draw_board(self):
        self.canvas.delete("all")
        
        win_w = self.canvas.winfo_width()
        win_h = self.canvas.winfo_height()
        
        margin = self.get_margin()
        board_w = self.m * self.cell_size
        board_h = self.n * self.cell_size
        
        total_w = board_w + 2 * margin
        total_h = board_h + 2 * margin
        
        self.offset_x = max(0, (win_w - total_w) // 2) if win_w > 1 else 0
        self.offset_y = max(0, (win_h - total_h) // 2) if win_h > 1 else 0
        
        start_x = self.offset_x + margin
        start_y = self.offset_y + margin

        curr = self.history[-1] if self.history else None
        valid_moves = self.get_valid_moves(curr[0], curr[1], self.visited) if curr else []
        
        trail_length = 6
        trail_colors = ["#ffeb3b", "#ffc107", "#ff9800", "#ff5722", "#f44336", "#e91e63"]
        
        # Draw Chessboard Algebraic Notation Labels
        label_font_size = max(8, int(self.cell_size * 0.35))
        label_font = ("Georgia", label_font_size, "bold")
        
        for c in range(self.m):
            col_text = self.get_col_label(c)
            cx = start_x + c * self.cell_size + self.cell_size / 2
            self.canvas.create_text(cx, self.offset_y + margin / 2, text=col_text, font=label_font, fill="#555555")
            self.canvas.create_text(cx, start_y + board_h + margin / 2, text=col_text, font=label_font, fill="#555555")
            
        for r in range(self.n):
            row_text = str(r + 1)
            cy = start_y + r * self.cell_size + self.cell_size / 2
            self.canvas.create_text(self.offset_x + margin / 2, cy, text=row_text, font=label_font, fill="#555555")
            self.canvas.create_text(start_x + board_w + margin / 2, cy, text=row_text, font=label_font, fill="#555555")
        
        for r in range(self.n):
            for c in range(self.m):
                x1 = start_x + c * self.cell_size
                y1 = start_y + r * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                bg_color = "white" if (r + c) % 2 == 0 else "#e8e8e8"
                
                if (r, c) == curr:
                    bg_color = trail_colors[0] 
                elif self.is_solving and (r, c) in self.history[-trail_length:-1]:
                    dist = self.history[::-1].index((r, c))
                    bg_color = trail_colors[min(dist, len(trail_colors)-1)]
                elif (r, c) in valid_moves:
                    bg_color = "#b2ffb2" 
                elif not self.history:
                    bg_color = "#e6f7ff"
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=bg_color, outline="#cccccc")
                
                base_font_size = max(8, self.cell_size // 4)
                main_font_size = max(10, self.cell_size // 3)
                
                if (r, c) in self.history:
                    idx = self.history.index((r, c)) + 1
                    self.canvas.create_text(x1 + self.cell_size/2, y1 + self.cell_size/2, 
                                            text=str(idx), font=("Georgia", main_font_size, "bold"), fill="black")
                else:
                    if self.show_counts_mode.get() or self.show_hint_mode.get():
                        count_y = y1 + self.cell_size / 2
                        max_y = y1 + self.cell_size / 2
                        
                        if self.show_counts_mode.get() and self.show_hint_mode.get():
                            count_y -= base_font_size
                            max_y += base_font_size
                            
                        if self.show_counts_mode.get():
                            count = len(self.get_valid_moves(r, c, self.visited))
                            self.canvas.create_text(x1 + self.cell_size/2, count_y, 
                                                    text=str(count), font=("Georgia", main_font_size, "bold"), fill="#bfbfbf")
                            
                        if self.show_hint_mode.get():
                            max_len = self._simulate_warnsdorff(r, c, self.visited)
                            self.canvas.create_text(x1 + self.cell_size/2, max_y, 
                                                    text=str(max_len), font=("Georgia", base_font_size, "bold"), fill="#6ca0dc")

        if self.is_solving and len(self.history) > 1:
            points = [(start_x + c * self.cell_size + self.cell_size/2, 
                       start_y + r * self.cell_size + self.cell_size/2) 
                      for r, c in self.history[-trail_length:]]
            
            for i in range(len(points)-1):
                px1, py1 = points[i]
                px2, py2 = points[i+1]
                w = max(1, (i + 2) * (self.cell_size / 60)) 
                self.canvas.create_line(px1, py1, px2, py2, fill="#d32f2f", width=w, capstyle=tk.ROUND)
                
        bbox = self.canvas.bbox("all")
        if bbox:
            pad = 10
            self.canvas.config(scrollregion=(bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad))
            
        self.update_status()

if __name__ == "__main__":
    root = tk.Tk()
    app = KnightsTourGame(root)
    root.resizable(True, True)
    root.minsize(1050, 650)
    root.mainloop()