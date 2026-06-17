import pygame
import random
import time
import math
from core.window import get_mouse_pos, get_floor_y
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from entities.drawer import PenguinDrawer
from ui.components import DialogueBubble
from ui.menu import ContextMenu
from ui.props import draw_broom, draw_zzz, draw_stethoscope, draw_glasses
from core.audio import AudioSystem
import win32api
import datetime

# Constantes de Movimentação e Física
WANDER_MIN_TIME = 2000
WANDER_MAX_TIME = 6000
SPEED = 1.5
GRAVITY = 0.5
BOUNCE_DAMPING = 0.6
FRICTION = 0.95

class Penguin:
    def __init__(self, x, y, save_manager, ai_manager, monitor):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.save_manager = save_manager
        self.ai_manager = ai_manager
        self.monitor = monitor
        
        # Estado e visual
        self.state = "WANDERING" # WANDERING, SITTING, HAPPY, CLEANING, TALKING, GRUMPY, HELD, THROWN, POMODORO, REVOLTED, IDLE
        self.wander_substate = "IDLE_STANDING"
        self.prop = None # None, "BROOM", "ZZZ", "STETHOSCOPE", "GLASSES"
        self.color = self.save_manager.get_penguin_color()
        self.drawer = PenguinDrawer(body_color=self.color)
        self.audio = AudioSystem()
        self.bubble = DialogueBubble("", x, y, 280, 100, audio_system=self.audio)
        self.menu = ContextMenu()
        
        # Atributos de Tamagotchi
        self.happiness = 100
        
        # Estados: WANDERING, HELD, THROWN, ALERT, POKED, IDLE, GRUMPY, HAPPY, CLEANING, POMODORO, REVOLTED
        self.substate_expire_time = pygame.time.get_ticks() + random.randint(WANDER_MIN_TIME, WANDER_MAX_TIME)
        
        self.pomodoro_end = 0
        
        self.direction_idx = 0
        self.dest_x = x
        self.dest_y = y
        
        # Física
        self.is_held = False
        self.hold_offset_x = 0
        self.hold_offset_y = 0
        self.last_mouse_pos = (x, y)
        
        # Controle de cutucadas e idle
        self.last_action_time = time.time()
        
        # Callbacks (definidos pelo main)
        self.on_checkup_request = None
        self.on_exit_request = None

    def get_app_context(self):
        context_str = ""
        try:
            now = datetime.datetime.now()
            
            # Formata Data e Hora
            meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            data_str = f"{now.day} de {meses[now.month]}"
            
            context_str += f" [Nota de Sistema: Hoje é {data_str}, e agora são exatamente {now.strftime('%H:%M')}."
        except:
            context_str += " [Nota de Sistema:"
            
        if not hasattr(self, 'monitor') or not self.monitor: 
            return context_str + "]"
            
        # Puxa o clima do Monitor
        if hasattr(self.monitor, 'weather_info') and self.monitor.weather_info != "Desconhecido":
            context_str += f" Clima local: {self.monitor.weather_info}."
            
        proc, title = self.monitor.get_active_window_info()
        if proc and title:
            context_str += f" O usuário está usando a janela '{title}' do aplicativo '{proc}'.]"
        else:
            context_str += "]"
            
        return context_str

    def _on_ai_response(self, text):
        """Callback usado quando o Ollama retorna uma resposta."""
        self.bubble.set_text(text)
        # Garante no mínimo 7 segundos na tela após a IA responder
        self.substate_expire_time = max(self.substate_expire_time, pygame.time.get_ticks() + 7000)
        
    def reload_color(self):
        """Atualiza o drawer com a nova cor recarregada do save manager"""
        self.color = self.save_manager.get_penguin_color()
        self.drawer = PenguinDrawer(body_color=self.color)

    def set_alert(self, text, buttons):
        """Inicia um alerta do sistema"""
        self.state = "ALERT"
        self.bubble.set_text(text)
        self.bubble.add_buttons(buttons)
        self.substate_expire_time = pygame.time.get_ticks() + 15000 # 15s para interagir
        
    def set_state(self, new_state):
        self.state = new_state
        if new_state in ["THROWN", "HELD"]:
            self.bubble.set_text("")
            self.bubble.buttons.clear()
            
    def poke(self):
        """Reação ao clique rápido"""
        self.state = "POKED"
        self.happiness = max(0, self.happiness - 5)
        self.audio.play('quack')
        phrases = [
            "Pare com isso!",
            "Isso dói, sabia?",
            "Estou trabalhando, humano!",
            "Mais um clique e eu formato o PC!",
            "Por que você me cutuca?!"
        ]
        
        if self.ai_manager.is_enabled:
            self.bubble.set_text("...")
            self.ai_manager.request_dialogue(
                event_context=f"O usuário acabou de me dar uma cutucada (clique) dolorida com o mouse. Minha felicidade atual é de {self.happiness}/100." + self.get_app_context(),
                callback=self._on_ai_response,
                fallback=random.choice(phrases)
            )
        else:
            self.bubble.set_text(random.choice(phrases))
            
        self.bubble.add_buttons([])
        self.last_action_time = time.time()
        self.substate_expire_time = pygame.time.get_ticks() + 3000 # Volta a passear depois de 3 segundos

    def handle_event(self, event, mouse_pos):
        hitbox = self.drawer.get_hitbox(self.x, self.y)
        mouse_over = hitbox.collidepoint(mouse_pos)
        
        # 1. Trata clique na Bubble
        if self.state in ["ALERT", "POKED", "GRUMPY", "HAPPY", "CLEANING", "IDLE"]:
            if self.bubble.handle_event(event, mouse_pos):
                return True # Evento consumido
                
        # 2. Trata clique no Menu
        if self.menu.handle_event(event, mouse_pos):
            return True
            
        # 3. Trata interações físicas com o Pinguim
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Clique Esquerdo
                if mouse_over:
                    if self.state == "POMODORO":
                        self.bubble.set_text("Shhh! Estou focado trabalhando! Não me distraia!")
                        self.bubble.add_buttons([])
                        self.substate_expire_time = pygame.time.get_ticks() + 3000
                        return True
                        
                    self.is_held = True
                    self.state = "HELD"
                    self.hold_offset_x = self.x - mouse_pos[0]
                    self.hold_offset_y = self.y - mouse_pos[1]
                    self.vx = 0
                    self.vy = 0
                    
                    if self.ai_manager.is_enabled:
                        self.bubble.set_text("...")
                        self.ai_manager.request_dialogue(
                            event_context=f"O usuário acabou de me segurar e me levantar com o mouse do computador! Estou pendurado! Felicidade: {self.happiness}/100." + self.get_app_context(),
                            callback=self._on_ai_response,
                            fallback=random.choice(["Me solta!", "Socorro!", "Eu tenho labirintite!"])
                        )
                    else:
                        self.bubble.set_text(random.choice(["Me solta!", "Socorro!", "Eu tenho labirintite!"]))
                        
                    self.bubble.add_buttons([])
                    self.menu.hide()
                    return True
            elif event.button == 3: # Clique Direito
                if mouse_over:
                    fishes = self.save_manager.get_fishes()
                    if self.state == "POMODORO":
                        self.menu.show(mouse_pos[0], mouse_pos[1], [
                            {'text': 'Cancelar Foco', 'callback': self._cancel_pomodoro}
                        ])
                    else:
                        ai_text = 'Desativar IA' if self.save_manager.is_ai_enabled() else 'Ativar IA'
                        mute_text = 'Desmutar Som' if self.audio.muted else 'Mutar Som'
                        options = [
                            {
                                'text': '▶️ Ações ►',
                                'submenu': [
                                    {'text': 'Soneca', 'callback': self._snooze},
                                    {'text': 'Fazer Checkup', 'callback': self._trigger_checkup}
                                ]
                            },
                            {
                                'text': '🍅 Foco/Saúde ►',
                                'submenu': [
                                    {'text': 'Focar (25 min)', 'callback': self._start_pomodoro}
                                ]
                            },
                            {
                                'text': '🎨 Interagir ►',
                                'submenu': [
                                    {'text': 'Mudar Cor', 'callback': self._change_color},
                                    {'text': 'Fazer Carinho', 'callback': self._pet},
                                    {'text': f'Dar Peixe ({fishes}x)', 'callback': self._feed}
                                ]
                            },
                            {
                                'text': '🤖 IA ►',
                                'submenu': [
                                    {'text': ai_text, 'callback': self._toggle_ai}
                                ]
                            },
                            {
                                'text': '⚙️ Opções ►',
                                'submenu': [
                                    {'text': mute_text, 'callback': self._toggle_mute},
                                    {'text': 'Sair do App', 'callback': self._trigger_exit}
                                ]
                            }
                        ]
                        self.menu.show(mouse_pos[0], mouse_pos[1], options)
                    return True
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_held:
                self.is_held = False
                
                # Se mal se moveu e soltou rápido, é um poke!
                speed = math.hypot(self.vx, self.vy)
                if speed < 2.0:
                    self.poke()
                else:
                    self.state = "THROWN"
                    if self.ai_manager.is_enabled:
                        self.bubble.set_text("...")
                        self.ai_manager.request_dialogue(
                            event_context=f"O usuário acabou de me arremessar na tela do computador e eu estou voando! Felicidade: {self.happiness}/100." + self.get_app_context(),
                            callback=self._on_ai_response,
                            fallback="WAAAHHH!"
                        )
                    else:
                        self.bubble.set_text("WAAAHHH!")
                return True
                
        return False

    def _trigger_checkup(self):
        self.menu.hide()
        if self.happiness < 20:
            self.set_state("GRUMPY")
            self.bubble.set_text("Estou com fome e triste! Me dê um peixe antes de pedir favores!")
            self.bubble.add_buttons([])
            self.substate_expire_time = pygame.time.get_ticks() + 4000
            return
            
        if self.on_checkup_request:
            self.on_checkup_request()
            
    def _start_pomodoro(self):
        self.menu.hide()
        self.set_state("POMODORO")
        self.prop = "GLASSES"
        self.pomodoro_end = pygame.time.get_ticks() + 25 * 60 * 1000 # 25 minutes
        self.bubble.set_text("Modo Foco ativado! Bora trabalhar!")
        self.bubble.add_buttons([])
        self.substate_expire_time = pygame.time.get_ticks() + 3000
        
    def _cancel_pomodoro(self):
        self.menu.hide()
        self.set_state("WANDERING")
        self.prop = None
        self.bubble.set_text("Foco cancelado... Que pena!")
        self.bubble.add_buttons([])
        self.substate_expire_time = pygame.time.get_ticks() + 3000
            
    def _snooze(self):
        self.menu.hide()
        self.set_state("HAPPY")
        self.prop = "ZZZ"
        self.bubble.set_text("Modo silencioso ativado! Vou só brincar por aqui pelas próximas horas.")
        self.bubble.add_buttons([])
        self.substate_expire_time = pygame.time.get_ticks() + 4000
        # O main cuidará do Snooze global
        if hasattr(self, 'on_snooze_request') and self.on_snooze_request:
            self.on_snooze_request()
            
    def _feed(self):
        self.menu.hide()
        if self.save_manager.consume_fish():
            self.happiness = min(100, self.happiness + 30)
            self.set_state("HAPPY")
            self.audio.play('quack')
            
            if self.ai_manager.is_enabled:
                self.bubble.set_text("...")
                self.ai_manager.request_dialogue(
                    event_context=f"O usuário acabou de me dar um peixe delicioso! Eu amo peixes! Felicidade: {self.happiness}/100." + self.get_app_context(),
                    callback=self._on_ai_response,
                    fallback="Nham nham! Delícia! Obrigado, mestre!"
                )
            else:
                self.bubble.set_text("Nham nham! Delícia! Obrigado, mestre!")
        else:
            self.set_state("GRUMPY")
            self.audio.play('quack')
            self.bubble.set_text("Você não tem peixes! Espere eu pescar algum ou procure na tela.")
            
        self.bubble.add_buttons([])
        self.substate_expire_time = pygame.time.get_ticks() + 4000
        
    def _pet(self):
        self.menu.hide()
        self.happiness = min(100, self.happiness + 15)
        self.set_state("HAPPY")
        
        if self.ai_manager.is_enabled:
            self.bubble.set_text("...")
            self.ai_manager.request_dialogue(
                event_context=f"O usuário está fazendo um carinho muito bom em mim. Felicidade: {self.happiness}/100." + self.get_app_context(),
                callback=self._on_ai_response,
                fallback="hehe... isso faz cosquinha!"
            )
        else:
            self.bubble.set_text("hehe... isso faz cosquinha!")
            
        self.bubble.add_buttons([])
        self.substate_expire_time = pygame.time.get_ticks() + 4000
            
    def _trigger_exit(self):
        self.menu.hide()
        if self.on_exit_request:
            self.on_exit_request()
            
    def _toggle_ai(self):
        self.menu.hide()
        current = self.save_manager.is_ai_enabled()
        self.save_manager.set_ai_enabled(not current)
        self.ai_manager.enable(not current)
        
        self.set_state("HAPPY")
        if not current:
            self.bubble.set_text("IA Ativada! Cérebro nativo ativando...")
        else:
            self.bubble.set_text("IA Desativada. Voltando a ser um pinguim simples.")
        self.bubble.add_buttons([])
        self.substate_expire_time = pygame.time.get_ticks() + 4000
            
    def _toggle_mute(self):
        self.menu.hide()
        is_muted = self.audio.toggle_mute()
        self.set_state("HAPPY")
        if not is_muted:
            self.audio.play('quack')
        self.bubble.set_text("Mudo ativado!" if is_muted else "Sons ativados!")
        self.bubble.add_buttons([])
        self.substate_expire_time = pygame.time.get_ticks() + 3000
            
    def _change_color(self):
        self.menu.hide()
        # Sorteia uma nova cor aleatória vibrante
        new_color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        self.save_manager.set_penguin_color(new_color)
        self.reload_color()
        self.set_state("HAPPY")
        self.audio.play('quack')
        self.bubble.set_text("Wow! Estou de visual novo!!")
        self.bubble.add_buttons([])
        self.substate_expire_time = pygame.time.get_ticks() + 4000

    def update(self, mouse_pos):
        now = pygame.time.get_ticks()
        
        # 1. Atualiza Física (Arrastar e Arremessar)
        if self.is_held:
            # Segue o mouse
            new_x = mouse_pos[0] + self.hold_offset_x
            new_y = mouse_pos[1] + self.hold_offset_y
            # Calcula velocidade baseada no movimento do mouse
            self.vx = (new_x - self.x) * 0.5
            self.vy = (new_y - self.y) * 0.5
            self.x = new_x
            self.y = new_y
            
            # Limita a tela
            self.x = max(40, min(self.x, SCREEN_WIDTH - 40))
            self.y = max(40, min(self.y, SCREEN_HEIGHT - 40))
            
            # Animação de desespero (muda frame rapidamente)
            self.direction_idx = (now // 100) % 8
            
        elif self.state == "THROWN":
            # Aplica gravidade e inércia
            self.vy += GRAVITY
            self.x += self.vx
            self.y += self.vy
            
            # Atrito horizontal
            self.vx *= 0.99
            
            # Quica nas bordas
            floor_y = get_floor_y(self.x, self.y) - 40
            if self.y >= floor_y:
                if self.vy > 2: self.audio.play('boing')
                self.y = floor_y
                self.vy = -self.vy * BOUNCE_DAMPING
                self.vx *= FRICTION # Atrito no chão
                self.happiness = max(0, self.happiness - 1)
            if self.x <= 40:
                if abs(self.vx) > 2: self.audio.play('boing')
                self.x = 40
                self.vx = -self.vx * BOUNCE_DAMPING
                self.happiness = max(0, self.happiness - 1)
            elif self.x >= SCREEN_WIDTH - 40:
                if abs(self.vx) > 2: self.audio.play('boing')
                self.x = SCREEN_WIDTH - 40
                self.vx = -self.vx * BOUNCE_DAMPING
                self.happiness = max(0, self.happiness - 1)
                
            # Gira loucamente enquanto cai rápido
            if abs(self.vx) > 3 or abs(self.vy) > 3:
                self.direction_idx = (now // 100) % 8
            else:
                self.direction_idx = 0 # Olha pra frente
                
            # Se parar quase totalmente, volta a passear
            floor_y = get_floor_y(self.x, self.y) - 45
            if abs(self.vx) < 0.5 and abs(self.vy) < 0.5 and self.y >= floor_y:
                if self.happiness == 0 and time.time() - getattr(self, 'last_revolt_time', 0) > 120:
                    self.state = "REVOLTED"
                    if self.ai_manager.is_enabled:
                        self.bubble.set_text("...")
                        self.ai_manager.request_dialogue(
                            event_context=f"Acabei de cair no chão depois de ser arremessado. Minha felicidade chegou a ZERO. Estou revoltado com o usuário e vou ameaçá-lo!" + self.get_app_context(),
                            callback=self._on_ai_response,
                            fallback="ESTOU REVOLTADO!!"
                        )
                    else:
                        self.bubble.set_text("ESTOU REVOLTADO!!")
                else:
                    self.state = "WANDERING"
                self.vx = 0
                self.vy = 0
                self.last_action_time = time.time()
                
        # 1.5. Lógica Pomodoro
        elif self.state == "POMODORO":
            # Pinguim fica sentado lendo exatamente onde está
            self.wander_substate = "SITTING"
            
            time_left = max(0, (self.pomodoro_end - now) // 1000)
            mins = time_left // 60
            secs = time_left % 60
            
            if not self.bubble.is_typing:
                self.bubble.set_text_instant(f"Modo Foco ativado! Bora trabalhar!\nTempo Restante: {mins:02d}:{secs:02d}")
            
            if now > self.pomodoro_end:
                self.state = "HAPPY"
                self.prop = None
                self.audio.play('beep')
                self.bubble.set_text("Pomodoro finalizado! Bom trabalho, mestre! Ganhou um peixe!")
                self.save_manager.add_fish()
                self.bubble.add_buttons([])
                self.substate_expire_time = now + 5000
                
        # 1.6. Lógica REVOLTED (Física do Mouse)
        elif self.state == "REVOLTED":
            # Persegue o mouse agressivamente
            dx = mouse_pos[0] - self.x
            dy = mouse_pos[1] - self.y
            dist = math.hypot(dx, dy)
            
            # Movimentação super rápida
            if dist > 30:
                self.x += (dx / dist) * 4.0
                self.y += (dy / dist) * 4.0
                
                # Face direction towards mouse
                angle = math.degrees(math.atan2(-dy, dx))
                if angle < 0: angle += 360
                sector = int(((angle + 22.5) % 360) / 45)
                sector_to_idx = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0, 7: 7}
                self.direction_idx = sector_to_idx.get(sector, 0)
            else:
                # Encostou no mouse! Joga o mouse pro lado
                try:
                    current_mouse_x, current_mouse_y = win32api.GetCursorPos()
                    # Empurra o mouse pra longe do pinguim
                    push_x = 50 if dx < 0 else -50
                    push_y = 50 if dy < 0 else -50
                    win32api.SetCursorPos((current_mouse_x + push_x, current_mouse_y + push_y))
                    self.audio.play('boing')
                except:
                    pass
                    
                # Dá o golpe e foge (Cooldown de 2 minutos antes do próximo ataque)
                self.state = "WANDERING"
                self.last_revolt_time = time.time()
                if self.ai_manager.is_enabled:
                    self.ai_manager.request_dialogue(
                        event_context=f"Acabei de atacar o mouse do usuário porque estava irritado. Vou dar um aviso para ele cuidar melhor de mim." + self.get_app_context(),
                        callback=self._on_ai_response,
                        fallback="Me dê atenção ou eu ataco de novo daqui a pouco!!"
                    )
                else:
                    self.bubble.set_text("Me dê atenção ou eu ataco de novo daqui a pouco!!")
                self.substate_expire_time = now + 4000
                
        # 2. Atualiza Lógica de Passeio (Wandering)
        elif self.state == "WANDERING":
            if now > self.substate_expire_time:
                # Sorteia próximo subestado
                r = random.random()
                if r < 0.5:
                    self.wander_substate = "WANDERING"
                    self.dest_x = random.randint(100, SCREEN_WIDTH - 100)
                    floor_y = get_floor_y(self.dest_x, self.y) - 40
                    self.dest_y = random.randint(100, int(floor_y))
                elif r < 0.8:
                    self.wander_substate = "IDLE_STANDING"
                else:
                    self.wander_substate = "SITTING"
                self.substate_expire_time = now + random.randint(WANDER_MIN_TIME, WANDER_MAX_TIME)
                
            if self.wander_substate == "WANDERING":
                dx = self.dest_x - self.x
                dy = self.dest_y - self.y
                dist = math.hypot(dx, dy)
                
                if dist > SPEED:
                    move_x = (dx / dist) * SPEED
                    move_y = (dy / dist) * SPEED
                    self.x += move_x
                    self.y += move_y
                    
                    angle = math.degrees(math.atan2(-dy, dx))
                    if angle < 0:
                        angle += 360
                    # angle 0 is Right(East).
                    # sprite columns: 0:S, 1:SW, 2:W, 3:NW, 4:N, 5:NE, 6:E, 7:SE
                    sector = int(((angle + 22.5) % 360) / 45)
                    sector_to_idx = {
                        0: 6, 1: 5, 2: 4, 3: 3,
                        4: 2, 5: 1, 6: 0, 7: 7
                    }
                    self.direction_idx = sector_to_idx.get(sector, 0)
                else:
                    self.wander_substate = "IDLE_STANDING"
                    
            # Chance de dormir ou dar dica
            if self.wander_substate in ["IDLE_STANDING", "SITTING"] and time.time() - self.last_action_time > 10:
                if random.random() < 0.05:
                    self.state = "IDLE"
                    
                    phrases = [
                        "Zzz...", 
                        "Dica: Reiniciar resolve 90% dos problemas.",
                        "Lembre de beber água!",
                        "Eu sou open source, sabia?"
                    ]
                    
                    if self.ai_manager.is_enabled:
                        self.bubble.set_text("...")
                        ideias = [
                            "Conte uma piada bem curta e engraçada.",
                            "Dê um conselho engraçado ou inútil.",
                            "Reclame sobre estar com tédio.",
                            "Faça uma piada ou comentário atrevido sobre o aplicativo ou aba que o usuário está usando no momento (leia a nota de contexto).",
                            "Faça uma analogia maluca do aplicativo que o usuário está usando com gelo ou peixes.",
                            "Dê uma dica rápida de produtividade para o usuário."
                        ]
                        ideia_escolhida = random.choice(ideias)
                        self.ai_manager.request_dialogue(
                            event_context=f"Estou ocioso no computador sem fazer nada. Felicidade: {self.happiness}/100. Sua tarefa agora é: {ideia_escolhida}" + self.get_app_context(),
                            callback=self._on_ai_response,
                            fallback=random.choice(phrases)
                        )
                    else:
                        self.bubble.set_text(random.choice(phrases))
                        
                    self.last_action_time = time.time()
                    self.substate_expire_time = now + 6000
                    
        elif self.state in ["IDLE", "POKED", "GRUMPY", "HAPPY", "CLEANING", "ALERT"]:
            if now > self.substate_expire_time and not self.bubble.is_typing:
                if self.state == "ALERT":
                    if hasattr(self, 'on_alert_ignored') and self.on_alert_ignored:
                        self.on_alert_ignored()
                else:
                    if self.happiness == 0:
                        self.state = "REVOLTED"
                    else:
                        self.state = "WANDERING"
                    self.prop = None
                    self.last_action_time = time.time()
                    
        elif self.state == "POMODORO":
            # Permanece sentado olhando para a tela (Sul)
            self.direction_idx = 0
            self.vx = 0
            
            # Aplica física de gravidade se estiver caindo
            floor_y = get_floor_y(self.x, self.y) - 40
            if self.y < floor_y:
                self.vy += GRAVITY
                self.y += self.vy
            else:
                self.y = floor_y
                self.vy = 0
                
            # Fim do Pomodoro
            if now > self.pomodoro_end:
                self.state = "HAPPY"
                self.prop = None
                self.audio.play('beep')
                self.bubble.set_text("Pomodoro concluído! Hora de uma pausa!")
                self.substate_expire_time = now + 5000

        # 3. Atualiza interface (Balão e Botões)
        # Posiciona balão dinamicamente
        ideal_bx = self.x - self.bubble.width / 2
        ideal_by = self.y - self.bubble.max_height - 90
        
        ideal_bx = max(10, min(ideal_bx, SCREEN_WIDTH - self.bubble.width - 10))
        ideal_by = max(10, min(ideal_by, SCREEN_HEIGHT - self.bubble.max_height - 10))
        
        self.bubble.x = ideal_bx
        self.bubble.y = ideal_by
        self.bubble.update(mouse_pos)
        
        self.menu.update(mouse_pos)
        
        self.last_mouse_pos = mouse_pos

    def is_ui_active(self):
        """Retorna True se tiver um balão interativo ou menu aberto."""
        return (self.state in ["ALERT", "POKED", "GRUMPY", "HAPPY", "CLEANING", "IDLE"] and self.bubble.current_text != "") or self.menu.is_open

    def get_ui_hitboxes(self):
        hitboxes = [self.drawer.get_hitbox(self.x, self.y)]
        if self.is_ui_active():
            if self.bubble.current_text != "":
                hitboxes.append(self.bubble.get_hitbox())
            if self.menu.is_open:
                hitboxes.append(self.menu.get_hitbox())
        return hitboxes

    def draw(self, screen, mouse_pos):
        now_ms = pygame.time.get_ticks()
        
        # Transforma o estado do Penguin no estado visual do Drawer
        visual_state = self.state
        if self.state == "WANDERING":
            visual_state = self.wander_substate
        elif self.state == "IDLE" and self.prop == "ZZZ":
            visual_state = "SITTING"
        elif self.state == "HELD" or self.state == "THROWN":
            visual_state = "WANDERING" # Usa quadros de caminhada
            
        self.drawer.draw(screen, self.x, self.y, visual_state, mouse_pos, self.direction_idx)
        
        # Desenhar Props por cima do pinguim dependendo do estado/prop
        if self.state == "CLEANING" or self.prop == "BROOM":
            draw_broom(screen, self.x, self.y, now_ms)
        elif self.prop == "STETHOSCOPE":
            draw_stethoscope(screen, self.x, self.y)
        elif self.prop == "ZZZ":
            draw_zzz(screen, self.x, self.y, now_ms)
        elif self.prop == "GLASSES":
            draw_glasses(screen, self.x, self.y)
            
        if self.bubble.current_text != "":
            self.bubble.draw(screen)
            
        if self.menu.is_open:
            self.menu.draw(screen)
