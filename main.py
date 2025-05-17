import os
import sys
import ctypes
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import pygame
import pygame.joystick
import subprocess
import threading
import time
import math
from io import BytesIO
import traceback
import json
import hashlib

# ====================== CONFIGURAÇÕES ======================
class Config:
    WIDTH, HEIGHT = 1280, 720
    CARD_WIDTH, CARD_HEIGHT = 300, 420
    FPS = 60
    
    # Cores
    BG_COLOR = "#0a0a1a"
    MENU_COLOR = "#16213E"
    SELECTED_COLOR = "#00b4d8"
    TEXT_COLOR = "#ffffff"
    ACCENT_COLOR = "#ff9e00"
    CARD_BG = "#1a1a2e"
    DOWNLOAD_BTN_COLOR = "#ff2d75"
    
    # Caminhos
    DOWNLOADS_DIR = "downloads"
    ASSETS_DIR = "assets"
    CONFIG_FILE = "config.json"
    
    # Sons
    SOUNDS = {
        "startup": "audio/startup.wav",
        "select": "audio/select.wav",
        "confirm": "audio/confirm.wav",
        "back": "audio/back.wav",
        "navigate": "audio/navigate.wav"
    }

# ====================== UTILITÁRIOS ======================
class Utils:
    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def run_as_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, None, 1)
        sys.exit()

    @staticmethod
    def hsv_to_rgb(h, s, v):
        h_i = int(h*6)
        f = h*6 - h_i
        p = v * (1 - s)
        q = v * (1 - f*s)
        t = v * (1 - (1 - f)*s)
        
        if h_i == 0: r, g, b = v, t, p
        elif h_i == 1: r, g, b = q, v, p
        elif h_i == 2: r, g, b = p, v, t
        elif h_i == 3: r, g, b = p, q, v
        elif h_i == 4: r, g, b = t, p, v
        else: r, g, b = v, p, q
            
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    @staticmethod
    def md5(file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

# ====================== GERENCIADOR DE ÁUDIO ======================
class AudioManager:
    def __init__(self):
        self.sounds = {}
        self.setup_audio()

    def setup_audio(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            
            for name, path in Config.SOUNDS.items():
                full_path = os.path.join(Config.ASSETS_DIR, path)
                if os.path.exists(full_path):
                    self.sounds[name] = pygame.mixer.Sound(full_path)
                    self.sounds[name].set_volume(0.7)
                else:
                    self._create_fallback_sound(name)
        except Exception as e:
            print(f"Erro ao inicializar áudio: {e}")
            self._create_all_fallback_sounds()

    def _create_fallback_sound(self, name):
        samples = []
        duration = 0.3
        
        if name == "startup": freq = 523.25
        elif name == "confirm": freq = 783.99
        elif name == "back": freq = 392.00
        else: freq = 659.25
            
        for i in range(int(22050 * duration)):
            value = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / 22050))
            samples.append(value)
        
        self.sounds[name] = pygame.mixer.Sound(buffer=bytearray(samples))

    def _create_all_fallback_sounds(self):
        for name in Config.SOUNDS.keys():
            self._create_fallback_sound(name)

    def play(self, sound_name):
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass

# ====================== GERENCIADOR DE JOGOS ======================
class GameManager:
    def __init__(self):
        self.games = self._load_games()
        self.create_directories()

    def _load_games(self):
        try:
            with open(os.path.join(Config.ASSETS_DIR, "games.json"), "r") as f:
                return json.load(f)
        except:
            return [
                {
                    "title": "Jogo de Teste",
                    "image": "games/test_game.jpg",
                    "size": "10 MB",
                    "exe_name": "ChromeSetup.exe",
                    "download_url": "https://drive.usercontent.google.com/download?id=1sbAijvGUPPnt5nG2kv_6Cp0DSCCZGtNV&export=download&authuser=0",
                    "md5": "d41d8cd98f00b204e9800998ecf8427e"
                }
            ]

    def create_directories(self):
        os.makedirs(Config.DOWNLOADS_DIR, exist_ok=True)
        os.makedirs(os.path.join(Config.ASSETS_DIR, "audio"), exist_ok=True)
        os.makedirs(os.path.join(Config.ASSETS_DIR, "games"), exist_ok=True)

    def is_game_installed(self, exe_name):
        exe_path = os.path.join(Config.DOWNLOADS_DIR, exe_name)
        return os.path.exists(exe_path)

    def verify_game_integrity(self, exe_name, expected_md5):
        exe_path = os.path.join(Config.DOWNLOADS_DIR, exe_name)
        if not os.path.exists(exe_path):
            return False
            
        return Utils.md5(exe_path) == expected_md5

# ====================== INTERFACE GRÁFICA ======================
class GameLauncherUI:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.audio = AudioManager()
        self.game_manager = GameManager()
        self.joystick = None
        
        self.current_screen = "main"
        self.menu_items = ["Jogos", "Sair"]
        self.selected_index = 0
        self.game_cards = []
        self.selected_card_index = 0
        self.running = True
        
        self.setup_joystick()
        self.setup_main_menu()
        self.start_control_loop()
        
        self.audio.play("startup")
        self.animate_title()

    def setup_window(self):
        self.root.title("Game Launcher Premium")
        self.root.geometry(f"{Config.WIDTH}x{Config.HEIGHT}")
        self.root.configure(bg=Config.BG_COLOR)
        
        # Centraliza
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - Config.WIDTH) // 2
        y = (screen_height - Config.HEIGHT) // 2
        self.root.geometry(f"+{x}+{y}")

    def setup_joystick(self):
        try:
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
        except Exception as e:
            print(f"Erro no controle: {e}")

    def setup_main_menu(self):
        self.main_canvas = tk.Canvas(self.root, bg=Config.BG_COLOR, highlightthickness=0)
        self.main_canvas.pack(fill="both", expand=True)
        
        # Título
        self.title_text = self.main_canvas.create_text(
            Config.WIDTH//2, Config.HEIGHT//4,
            text="GAME LAUNCHER",
            font=("Arial", 48, "bold"),
            fill=Config.SELECTED_COLOR,
            tags="title")
        
        # Itens do menu
        self.menu_rects = []
        self.menu_texts = []
        
        for i, item in enumerate(self.menu_items):
            y_pos = Config.HEIGHT//2 + i*80
            
            rect = self.main_canvas.create_rectangle(
                Config.WIDTH//2 - 250, y_pos - 35,
                Config.WIDTH//2 + 250, y_pos + 35,
                fill=Config.MENU_COLOR,
                outline="",
                width=0,
                tags=f"menu_{i}")
            
            text = self.main_canvas.create_text(
                Config.WIDTH//2, y_pos,
                text=item,
                font=("Arial", 24),
                fill=Config.TEXT_COLOR,
                tags=f"menu_text_{i}")
            
            self.menu_rects.append(rect)
            self.menu_texts.append(text)
        
        self.update_selection()

    def animate_title(self):
        for i in range(0, 360, 5):
            if not self.running: return
            color = Utils.hsv_to_rgb(i/360, 0.8, 1)
            self.main_canvas.itemconfig("title", fill=color)
            self.root.update()
            time.sleep(0.05)

    def setup_games_menu(self):
        self.games_canvas = tk.Canvas(self.root, bg=Config.BG_COLOR, highlightthickness=0)
        self.games_canvas.pack(fill="both", expand=True)
        
        # Título
        self.games_canvas.create_text(
            Config.WIDTH//2, 60,
            text="JOGOS DISPONÍVEIS",
            font=("Arial", 36, "bold"),
            fill=Config.SELECTED_COLOR)
        
        # Frame para os cards
        self.cards_frame = tk.Frame(self.games_canvas, bg=Config.BG_COLOR)
        self.cards_frame.place(x=0, y=120, width=Config.WIDTH, height=Config.HEIGHT-180)
        
        self.create_game_cards()
        
        # Botão de voltar
        self.back_btn = tk.Label(self.games_canvas, text="VOLTAR", 
                               font=("Arial", 18, "bold"), 
                               fg=Config.TEXT_COLOR, bg=Config.ACCENT_COLOR,
                               padx=20, pady=10,
                               relief="raised",
                               borderwidth=3)
        self.back_btn.place(x=50, y=Config.HEIGHT-80)
        self.back_btn.bind("<Button-1>", lambda e: self.back_to_main())
        self.back_btn.bind("<Enter>", lambda e: self.back_btn.config(bg="#ffb733"))
        self.back_btn.bind("<Leave>", lambda e: self.back_btn.config(bg=Config.ACCENT_COLOR))

    def create_game_cards(self):
        self.game_cards = []
        padding = 40
        start_x = (Config.WIDTH - (3 * (Config.CARD_WIDTH + padding))) // 2
        
        for i, game in enumerate(self.game_manager.games):
            row = i // 3
            col = i % 3
            
            x = start_x + col * (Config.CARD_WIDTH + padding)
            y = row * (Config.CARD_HEIGHT + padding)
            
            # Frame do card
            card_frame = tk.Frame(self.cards_frame, bg=Config.CARD_BG, 
                                 width=Config.CARD_WIDTH, height=Config.CARD_HEIGHT,
                                 relief="raised", borderwidth=3)
            card_frame.place(x=x, y=y)
            
            # Imagem do jogo
            try:
                img_path = os.path.join(Config.ASSETS_DIR, game["image"])
                img = Image.open(img_path)
                img = img.resize((Config.CARD_WIDTH-20, int(Config.CARD_HEIGHT*0.6)), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
            except:
                img = Image.new('RGB', (Config.CARD_WIDTH-20, int(Config.CARD_HEIGHT*0.6)), '#333333')
                img_tk = ImageTk.PhotoImage(img)
            
            img_label = tk.Label(card_frame, image=img_tk, bg=Config.CARD_BG)
            img_label.image = img_tk
            img_label.pack(pady=10)
            
            # Título do jogo
            title_label = tk.Label(card_frame, text=game["title"], 
                                 font=("Arial", 16, "bold"), 
                                 fg=Config.TEXT_COLOR, bg=Config.CARD_BG,
                                 wraplength=Config.CARD_WIDTH-20)
            title_label.pack(pady=5)
            
            # Tamanho do jogo
            size_label = tk.Label(card_frame, text=f"Tamanho: {game['size']}", 
                                font=("Arial", 12), 
                                fg=Config.TEXT_COLOR, bg=Config.CARD_BG)
            size_label.pack(pady=5)
            
            # Botão de ação
            installed = self.game_manager.is_game_installed(game["exe_name"])
            btn_text = "▶ JOGAR" if installed else "⬇ DOWNLOAD"
            btn_color = Config.DOWNLOAD_BTN_COLOR if installed else "#4CAF50"
            
            action_btn = tk.Label(card_frame, text=btn_text, 
                                font=("Arial", 14, "bold"), 
                                fg=Config.TEXT_COLOR, bg=btn_color,
                                padx=15, pady=5,
                                relief="raised",
                                borderwidth=2)
            action_btn.pack(pady=10)
            
            # Efeitos hover
            if installed:
                action_btn.bind("<Enter>", lambda e, b=action_btn: b.config(bg="#ff4f8d"))
                action_btn.bind("<Leave>", lambda e, b=action_btn: b.config(bg=Config.DOWNLOAD_BTN_COLOR))
                action_btn.bind("<Button-1>", lambda e, exe=game["exe_name"]: self.launch_game(exe))
            else:
                action_btn.bind("<Enter>", lambda e, b=action_btn: b.config(bg="#5cbf5c"))
                action_btn.bind("<Leave>", lambda e, b=action_btn: b.config(bg="#4CAF50"))
                action_btn.bind("<Button-1>", lambda e, g=game: self.start_download(g))
            
            self.game_cards.append({
                "frame": card_frame,
                "action_btn": action_btn,
                "installed": installed
            })
        
        if self.game_cards:
            self.selected_card_index = 0
            self.highlight_selected_card()

    def launch_game(self, exe_name):
        """Executa o jogo com múltiplos métodos de fallback"""
        try:
            exe_path = os.path.abspath(os.path.join(Config.DOWNLOADS_DIR, exe_name))
            
            if not os.path.exists(exe_path):
                messagebox.showerror("Erro", f"Arquivo não encontrado:\n{exe_path}")
                return
            
            # Verifica integridade do arquivo
            game = next((g for g in self.game_manager.games if g["exe_name"] == exe_name), None)
            if game and "md5" in game:
                if not self.game_manager.verify_game_integrity(exe_name, game["md5"]):
                    messagebox.showerror("Erro", "Arquivo do jogo corrompido. Por favor, baixe novamente.")
                    return
            
            # Tenta diferentes métodos de execução
            methods = [
                self._launch_with_subprocess,
                self._launch_with_os_startfile,
                self._launch_with_shellexecute
            ]
            
            for method in methods:
                if method(exe_path):
                    return
                
            messagebox.showerror("Erro", "Não foi possível iniciar o jogo com nenhum método disponível.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao executar o jogo:\n{str(e)}")

    def _launch_with_subprocess(self, exe_path):
        try:
            subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
            return True
        except:
            return False

    def _launch_with_os_startfile(self, exe_path):
        try:
            os.startfile(exe_path)
            return True
        except:
            return False

    def _launch_with_shellexecute(self, exe_path):
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "open", exe_path, None, os.path.dirname(exe_path), 1)
            return True
        except:
            return False

    def start_download(self, game):
        """Inicia o download do jogo"""
        try:
            download_window = tk.Toplevel(self.root)
            download_window.title(f"Download - {game['title']}")
            download_window.geometry("500x200")
            download_window.resizable(False, False)
            
            tk.Label(download_window, text=f"Baixando {game['title']}...", 
                   font=("Arial", 16)).pack(pady=10)
            
            progress = ttk.Progressbar(download_window, length=400, mode="determinate")
            progress.pack(pady=10)
            
            threading.Thread(target=self._download_game, args=(game, progress, download_window), daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar download: {str(e)}")

    def _download_game(self, game, progress, window):
        try:
            exe_path = os.path.join(Config.DOWNLOADS_DIR, game["exe_name"])
            
            # Verifica se já existe e remove
            if os.path.exists(exe_path):
                os.remove(exe_path)
            
            with requests.get(game["download_url"], stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                
                with open(exe_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not self.running:  # Permite cancelar
                            if os.path.exists(exe_path):
                                os.remove(exe_path)
                            return
                            
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress_value = int((downloaded / total_size) * 100)
                        progress["value"] = progress_value
                        window.update()
            
            # Verifica se o download foi completado
            if os.path.exists(exe_path) and os.path.getsize(exe_path) > 0:
                self.root.after(0, self._download_complete, game, window)
            else:
                self.root.after(0, self._download_failed, "Download incompleto ou arquivo corrompido", window)
            
        except Exception as e:
            self.root.after(0, self._download_failed, str(e), window)

    def _download_complete(self, game, window):
        window.destroy()
        
        for i, g in enumerate(self.game_manager.games):
            if g["title"] == game["title"]:
                card = self.game_cards[i]
                card["action_btn"].config(text="▶ JOGAR", bg=Config.DOWNLOAD_BTN_COLOR)
                card["action_btn"].bind("<Button-1>", lambda e, exe=game["exe_name"]: self.launch_game(exe))
                card["action_btn"].bind("<Enter>", lambda e, b=card["action_btn"]: b.config(bg="#ff4f8d"))
                card["action_btn"].bind("<Leave>", lambda e, b=card["action_btn"]: b.config(bg=Config.DOWNLOAD_BTN_COLOR))
                card["installed"] = True
                break
        
        messagebox.showinfo("Sucesso", f"{game['title']} instalado com sucesso!")

    def _download_failed(self, error, window):
        window.destroy()
        messagebox.showerror("Erro", f"Falha no download: {error}")

    def back_to_main(self):
        self.current_screen = "main"
        self.games_canvas.pack_forget()
        self.setup_main_menu()

    def update_selection(self):
        for i in range(len(self.menu_items)):
            color = Config.SELECTED_COLOR if i == self.selected_index else Config.MENU_COLOR
            font = ("Arial", 22, "bold") if i == self.selected_index else ("Arial", 20)
            self.main_canvas.itemconfig(self.menu_rects[i], fill=color)
            self.main_canvas.itemconfig(self.menu_texts[i], font=font)

    def highlight_selected_card(self):
        for i, card in enumerate(self.game_cards):
            border_color = Config.SELECTED_COLOR if i == self.selected_card_index else Config.CARD_BG
            card["frame"].config(highlightbackground=border_color, highlightthickness=3)

    def move_selection(self, direction):
        if self.current_screen == "main":
            self.move_menu_selection(direction)
        else:
            self.move_card_selection(direction)

    def move_menu_selection(self, direction):
        new_index = (self.selected_index - 1) % len(self.menu_items) if direction == "up" else (self.selected_index + 1) % len(self.menu_items)
        self.selected_index = new_index
        self.update_selection()
        self.audio.play("navigate")

    def move_card_selection(self, direction):
        if not self.game_cards:
            return
            
        if direction == "up":
            new_index = max(0, self.selected_card_index - 3)
        elif direction == "down":
            new_index = min(len(self.game_cards) - 1, self.selected_card_index + 3)
        elif direction == "left":
            new_index = max(0, self.selected_card_index - 1)
        else:  # right
            new_index = min(len(self.game_cards) - 1, self.selected_card_index + 1)
        
        if new_index != self.selected_card_index:
            self.selected_card_index = new_index
            self.highlight_selected_card()
            self.audio.play("navigate")

    def select_item(self):
        self.audio.play("confirm")
        
        if self.current_screen == "main":
            if self.menu_items[self.selected_index] == "Jogos":
                self.show_games_menu()
            else:
                self.quit_app()
        else:
            card = self.game_cards[self.selected_card_index]
            for child in card["frame"].winfo_children():
                if isinstance(child, tk.Label) and child.cget("text") in ["▶ JOGAR", "⬇ DOWNLOAD"]:
                    child.event_generate("<Button-1>")
                    break

    def show_games_menu(self):
        self.current_screen = "games"
        self.main_canvas.pack_forget()
        self.setup_games_menu()

    def back_action(self):
        self.audio.play("back")
        if self.current_screen == "games":
            self.back_to_main()

    def start_control_loop(self):
        """Inicia o loop de controle usando root.after para evitar problemas de threading"""
        self.process_joystick_events()
        if self.running:
            self.root.after(10, self.start_control_loop)

    def process_joystick_events(self):
        """Processa eventos do joystick e teclado"""
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 1:  # Eixo Y
                    if event.value < -0.7:
                        self.move_selection("up")
                    elif event.value > 0.7:
                        self.move_selection("down")
                elif event.axis == 0:  # Eixo X
                    if event.value < -0.7:
                        self.move_selection("left")
                    elif event.value > 0.7:
                        self.move_selection("right")
            
            elif event.type == pygame.JOYHATMOTION:
                if event.value[1] == 1:  # Cima
                    self.move_selection("up")
                elif event.value[1] == -1:  # Baixo
                    self.move_selection("down")
                elif event.value[0] == -1:  # Esquerda
                    self.move_selection("left")
                elif event.value[0] == 1:  # Direita
                    self.move_selection("right")
            
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # X
                    self.select_item()
                elif event.button == 1:  # Circle
                    self.back_action()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.move_selection("up")
                elif event.key == pygame.K_DOWN:
                    self.move_selection("down")
                elif event.key == pygame.K_LEFT:
                    self.move_selection("left")
                elif event.key == pygame.K_RIGHT:
                    self.move_selection("right")
                elif event.key == pygame.K_RETURN:
                    self.select_item()
                elif event.key == pygame.K_ESCAPE:
                    self.back_action()

    def quit_app(self):
        self.running = False
        pygame.quit()
        self.root.destroy()

if __name__ == "__main__":
    if not Utils.is_admin():
        Utils.run_as_admin()
    
    try:
        pygame.init()
        root = tk.Tk()
        app = GameLauncherUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Erro fatal: {e}")
        traceback.print_exc()
        input("Pressione Enter para sair...")