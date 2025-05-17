#=============== IMPORTAÇÕES ===============
import pygame
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Tuple, List, Optional
from math import sin, pi, cos
from enum import Enum, auto
import random
from jogos import GerenciadorJogos, Jogo

#=============== CONFIGURAÇÕES INICIAIS ===============
pygame.init()
pygame.joystick.init()
pygame.mixer.init()

# Configuração de diretórios
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"

# Cria diretórios se não existirem
(ASSETS_DIR / "fonts").mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "sounds").mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "images").mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "covers").mkdir(parents=True, exist_ok=True)

# Configuração da tela
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PS2 Launcher Premium HD")

#=============== EFEITOS VISUAIS ===============
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        self.speed = random.uniform(1, 3)
        self.angle = random.uniform(0, 2 * pi)
        self.life = random.randint(30, 60)
    
    def update(self):
        self.x += cos(self.angle) * self.speed
        self.y += sin(self.angle) * self.speed
        self.life -= 1
        return self.life > 0
    
    def draw(self, surface):
        alpha = min(255, self.life * 4)
        color = (*self.color[:3], alpha)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)

#=============== CONTROLE PS2 ===============
class PS2Controller:
    class Button(Enum):
        CROSS = 0; CIRCLE = 1; SQUARE = 2; TRIANGLE = 3
        L1 = 4; R1 = 5; SELECT = 8; START = 9; L3 = 10; R3 = 11
    
    class Axis(Enum):
        LEFT_X = 0; LEFT_Y = 1; RIGHT_X = 2; RIGHT_Y = 3
        L2 = 4; R2 = 5
    
    def __init__(self):
        self.joystick = None
        self._setup()
    
    def _setup(self):
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controle conectado: {self.joystick.get_name()}")
    
    def get_button_pressed(self, button: Button) -> bool:
        return self.joystick.get_button(button.value) if self.joystick else False
    
    def get_dpad(self) -> Tuple[int, int]:
        return self.joystick.get_hat(0) if self.joystick and self.joystick.get_numhats() > 0 else (0, 0)

#=============== SISTEMA DE ÁUDIO ===============
class AudioSystem:
    def __init__(self):
        self.sounds = self._load_sounds()
        self.sound_volume = 0.7
    
    def _load_sounds(self) -> Dict[str, pygame.mixer.Sound]:
        sounds = {}
        for name in ["navigate", "confirm", "back", "select"]:
            try:
                path = ASSETS_DIR / "sounds" / f"{name}.wav"
                if path.exists():
                    sounds[name] = pygame.mixer.Sound(path)
            except: pass
        return sounds
    
    def play(self, sound_name: str):
        if sound_name in self.sounds:
            self.sounds[sound_name].set_volume(self.sound_volume)
            self.sounds[sound_name].play()

#=============== BOTÃO ESTILO PS2 ===============
class PS2Button:
    def __init__(self, x, y, text, icon=None, width=300, height=80):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.icon = self._load_icon(icon) if icon else None
        self.selected = False
        self.anim_progress = 0
        self.particles = []
        self.original_y = y
    
    def _load_icon(self, icon_path: str) -> pygame.Surface:
        try:
            path = ASSETS_DIR / "images" / icon_path if not icon_path.startswith("covers/") else ASSETS_DIR / icon_path
            if path.exists():
                icon = pygame.image.load(str(path)).convert_alpha()
                size = 50 if not icon_path.startswith("covers/") else 80
                return pygame.transform.scale(icon, (size, size))
        except Exception as e:
            print(f"Erro ao carregar ícone: {e}")
        return None
    
    def update(self, dt):
        if self.selected:
            self.anim_progress = min(1, self.anim_progress + dt * 3)
            self.rect.y = self.original_y - sin(self.anim_progress * pi) * 10
            
            if random.random() < 0.3:
                color = (random.randint(100, 200), random.randint(100, 200), 255)
                self.particles.append(Particle(
                    self.rect.centerx + random.randint(-20, 20),
                    self.rect.centery + random.randint(-10, 10),
                    color
                ))
        else:
            self.anim_progress = max(0, self.anim_progress - dt * 3)
            self.rect.y = self.original_y
        
        self.particles = [p for p in self.particles if p.update()]
    
    def draw(self, surface, theme):
        for p in self.particles:
            p.draw(surface)
        
        if self.selected:
            glow_size = int(self.anim_progress * 20)
            glow = pygame.Surface((self.rect.w + glow_size*2, self.rect.h + glow_size*2), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*theme["highlight"], int(self.anim_progress * 100)), 
                            glow.get_rect(), border_radius=20)
            surface.blit(glow, (self.rect.x - glow_size, self.rect.y - glow_size))
        
        color = theme["accent"] if self.selected else theme["button"]
        pygame.draw.rect(surface, color, self.rect, border_radius=15)
        pygame.draw.rect(surface, theme["highlight"], self.rect, 3, border_radius=15)
        
        if self.icon:
            icon_rect = self.icon.get_rect(center=(self.rect.x + 45 if not isinstance(self.icon, str) or not self.icon.startswith("covers/") else self.rect.x + 100, 
                                          self.rect.centery))
            surface.blit(self.icon, icon_rect)
        
        try:
            font = pygame.font.Font(str(ASSETS_DIR / "fonts/ps_bold.ttf"), 32)
            text_pos = (self.rect.centerx + (40 if self.icon and not isinstance(self.icon, str) or not self.icon.startswith("covers/") else 0), 
                       self.rect.centery)
            
            shadow = font.render(self.text, True, (0, 0, 0, 100))
            surface.blit(shadow, (text_pos[0] + 3 - shadow.get_width()//2, text_pos[1] + 3 - shadow.get_height()//2))
            
            text = font.render(self.text, True, theme["text"])
            surface.blit(text, (text_pos[0] - text.get_width()//2, text_pos[1] - text.get_height()//2))
        except:
            font = pygame.font.Font(None, 32)
            text = font.render(self.text, True, theme["text"])
            surface.blit(text, self.rect)

#=============== MENU PRINCIPAL ===============
class MainMenu:
    def __init__(self, audio: AudioSystem, controller: PS2Controller):
        self.audio = audio
        self.controller = controller
        self.gerenciador_jogos = GerenciadorJogos()
        self.tela_atual = "menu"  # menu | jogos | config
        self.buttons_menu = self._criar_menu_principal()
        self.buttons_jogos = self._criar_menu_jogos()
        self.selected_index = 0
        self.last_input_time = 0
        self.input_delay = 0.15
        self.theme = {
            "bg": (20, 20, 40),
            "button": (50, 50, 80),
            "text": (220, 220, 250),
            "accent": (0, 200, 255),
            "highlight": (100, 200, 255)
        }
        self.background = self._create_background()
    
    def _create_background(self):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            alpha = int((y / SCREEN_HEIGHT) * 150)
            color = (20 + alpha//2, 40 + alpha//3, 80 + alpha//4)
            pygame.draw.line(bg, color, (0, y), (SCREEN_WIDTH, y))
        
        for y in range(0, SCREEN_HEIGHT, 2):
            pygame.draw.line(bg, (0, 0, 0, 10), (0, y), (SCREEN_WIDTH, y))
        
        return bg
    
    def _criar_menu_principal(self):
        return [
            PS2Button(SCREEN_WIDTH//2 - 150, 250, "Jogos", "game_icon.png"),
            PS2Button(SCREEN_WIDTH//2 - 150, 350, "Configurações", "settings_icon.png"),
            PS2Button(SCREEN_WIDTH//2 - 150, 450, "Extras", "extras_icon.png"),
            PS2Button(SCREEN_WIDTH//2 - 150, 550, "Sair", "exit_icon.png")
        ]
    
    def _criar_menu_jogos(self):
        buttons = []
        for i, jogo in enumerate(self.gerenciador_jogos.jogos):
            btn = PS2Button(
                x=100 + (i % 3) * 400,
                y=150 + (i // 3) * 180,
                text=jogo.nome,
                icon=f"covers/{jogo.imagem}",
                width=350,
                height=150
            )
            buttons.append(btn)
        return buttons
    
    def _change_selection(self, direction):
        current_buttons = self.buttons_jogos if self.tela_atual == "jogos" else self.buttons_menu
        
        if not current_buttons:
            return
            
        current_buttons[self.selected_index].selected = False
        self.selected_index = (self.selected_index + direction) % len(current_buttons)
        current_buttons[self.selected_index].selected = True
        self.audio.play("navigate")
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
                    self._change_selection(1 if self.tela_atual == "menu" else 3)
                elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
                    self._change_selection(-1 if self.tela_atual == "menu" else -3)
                elif event.key == pygame.K_ESCAPE and self.tela_atual != "menu":
                    self.tela_atual = "menu"
                    self.audio.play("back")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return self._processar_selecao()
        
        # Controle PS2
        current_time = time.time()
        if current_time - self.last_input_time > self.input_delay:
            dpad_x, dpad_y = self.controller.get_dpad()
            
            if dpad_y != 0 or dpad_x != 0:
                direction = dpad_y if self.tela_atual == "menu" else (dpad_x * 3 + dpad_y)
                self._change_selection(direction)
                self.last_input_time = current_time
        
        if self.controller.get_button_pressed(self.controller.Button.CROSS):
            return self._processar_selecao()
        elif self.controller.get_button_pressed(self.controller.Button.CIRCLE) and self.tela_atual != "menu":
            self.tela_atual = "menu"
            self.audio.play("back")
        
        return None
    
    def _processar_selecao(self):
        if self.tela_atual == "menu":
            opcao = self.buttons_menu[self.selected_index].text.lower()
            if opcao == "jogos":
                self.tela_atual = "jogos"
                self.selected_index = 0
                if self.buttons_jogos:
                    self.buttons_jogos[0].selected = True
                self.audio.play("confirm")
            elif opcao == "sair":
                return "quit"
            else:
                self.audio.play("confirm")
                return opcao
        elif self.tela_atual == "jogos" and self.buttons_jogos:
            jogo_selecionado = self.gerenciador_jogos.jogos[self.selected_index]
            self.audio.play("confirm")
            if self.gerenciador_jogos.executar_jogo(jogo_selecionado.nome):
                return "game_started"
        
        return None
    
    def update(self, dt):
        current_buttons = self.buttons_jogos if self.tela_atual == "jogos" else self.buttons_menu
        for btn in current_buttons:
            btn.update(dt)
    
    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        
        if self.tela_atual == "menu":
            self._draw_menu(surface)
        elif self.tela_atual == "jogos":
            self._draw_jogos(surface)
    
    def _draw_menu(self, surface):
        try:
            font = pygame.font.Font(str(ASSETS_DIR / "fonts/ps_bold.ttf"), 72)
            title = font.render("PS2 Launcher HD", True, self.theme["accent"])
            shadow = font.render("PS2 Launcher HD", True, (0, 0, 0, 100))
            surface.blit(shadow, (SCREEN_WIDTH//2 - shadow.get_width()//2 + 5, 105))
            surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        except:
            font = pygame.font.Font(None, 72)
            title = font.render("PS2 Launcher HD", True, self.theme["accent"])
            surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        for btn in self.buttons_menu:
            btn.draw(surface, self.theme)
        
        footer_text = "Use ↑↓/D-Pad para navegar | X/Enter para selecionar"
        font = pygame.font.Font(None, 24)
        footer = font.render(footer_text, True, (150, 150, 150))
        surface.blit(footer, (SCREEN_WIDTH//2 - footer.get_width()//2, SCREEN_HEIGHT - 40))
    
    def _draw_jogos(self, surface):
        font = pygame.font.Font(str(ASSETS_DIR / "fonts/ps_bold.ttf"), 48)
        title = font.render("Biblioteca de Jogos", True, self.theme["accent"])
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        if not self.buttons_jogos:
            font = pygame.font.Font(None, 36)
            msg = font.render("Nenhum jogo encontrado", True, self.theme["text"])
            surface.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, SCREEN_HEIGHT//2))
        else:
            for btn in self.buttons_jogos:
                btn.draw(surface, self.theme)
        
        footer_text = "Pressione ○/ESC para voltar | X/Enter para iniciar"
        font = pygame.font.Font(None, 24)
        footer = font.render(footer_text, True, (150, 150, 150))
        surface.blit(footer, (SCREEN_WIDTH//2 - footer.get_width()//2, SCREEN_HEIGHT - 40))

#=============== LOOP PRINCIPAL ===============
def main():
    audio = AudioSystem()
    controller = PS2Controller()
    menu = MainMenu(audio, controller)
    clock = pygame.time.Clock()
    running = True
    
    # Toca som de inicialização
    if "startup" in audio.sounds:
        audio.play("startup")
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        result = menu.handle_input()
        if result == "quit":
            running = False
        elif result == "game_started":
            # Aqui você pode adicionar lógica enquanto o jogo está rodando
            pass
        
        menu.update(dt)
        menu.draw(screen)
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()