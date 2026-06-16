import sys
import time
import random
import math
import threading
import pygame
import win32api
import win32con
import win32gui
import winsound

from config import (
    SCREEN_X, SCREEN_Y, SCREEN_WIDTH, SCREEN_HEIGHT, INVISIBLE_COLOR,
    RAM_THRESHOLD, TEMP_THRESHOLD, RECYCLE_BIN_THRESHOLD,
    MONITOR_CHECK_INTERVAL, ALERT_COOLDOWN, DIALOGUES,
    WALK_SPEED, WANDER_MIN_TIME, WANDER_MAX_TIME,
    IDLE_MIN_TIME, IDLE_MAX_TIME, SITTING_MIN_TIME, SITTING_MAX_TIME
)
from system_monitor import SystemMonitor
from cleaner import Cleaner
from penguin_drawer import PenguinDrawer
from ui_components import DialogueBubble

# --- SOM ASSÍNCRONO PARA NÃO TRAVAR A GUI ---
def play_sound_async(sound_type):
    def thread_target():
        try:
            if sound_type == "alarm":
                for _ in range(3):
                    winsound.Beep(1200, 80)
                    time.sleep(0.04)
                    winsound.Beep(800, 80)
                    time.sleep(0.04)
            elif sound_type == "click":
                winsound.Beep(1000, 50)
            elif sound_type == "clean":
                for f in range(600, 1500, 150):
                    winsound.Beep(f, 30)
            elif sound_type == "happy":
                winsound.Beep(900, 80)
                winsound.Beep(1300, 80)
                winsound.Beep(1700, 150)
            elif sound_type == "grumpy":
                winsound.Beep(400, 100)
                winsound.Beep(300, 150)
        except:
            pass
    threading.Thread(target=thread_target, daemon=True).start()


def main():
    # --- INICIALIZAÇÃO DO PYGAME ---
    pygame.init()
    pygame.mixer.quit() # Garante que o mixer não cause problemas se não houver driver de áudio
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("Doctor Penguin")
    
    # --- CONFIGURAÇÃO DE TRANSPARÊNCIA E JANELA DO WINDOWS ---
    hwnd = pygame.display.get_wm_info()["window"]
    default_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    
    # Estilo 1: click-through (clique passa direto para a tela de trás)
    click_through_style = default_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST
    # Estilo 2: interativo (recebe cliques nas áreas do pinguim/balão)
    interactive_style = (default_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST) & ~win32con.WS_EX_TRANSPARENT
    
    # Começa em modo click-through
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, click_through_style)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*INVISIBLE_COLOR), 0, win32con.LWA_COLORKEY)
    
    # Força a janela a ficar no topo e cobre toda a tela virtual
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, SCREEN_X, SCREEN_Y, SCREEN_WIDTH, SCREEN_HEIGHT, win32con.SWP_SHOWWINDOW)
    
    # Mantém a janela visível desde o início (Desktop Pet ativo)
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    
    # --- INICIALIZAÇÃO DE COMPONENTES ---
    monitor = SystemMonitor()
    drawer = PenguinDrawer()
    
    # Posição de ancoragem de Alertas do Pinguim (canto inferior direito)
    target_x = SCREEN_WIDTH - 120
    target_y = SCREEN_HEIGHT - 60
    
    # Inicia o Pinguim em uma posição aleatória na tela
    p_x = random.randint(100, SCREEN_WIDTH - 100)
    p_y = random.randint(100, SCREEN_HEIGHT - 100)
    
    # Tamanho e posição base do balão (agora mais compacto e HQ)
    bubble_w = 280
    bubble_h = 100 # Altura inicial, será ajustada dinamicamente
    b_x = target_x - 300
    b_y = target_y - bubble_h - 90
    
    bubble = DialogueBubble("", b_x, b_y, bubble_w, bubble_h)
    
    # --- IA DE MOVIMENTAÇÃO (WANDERING) ---
    wander_substate = "WANDERING" # "WANDERING", "IDLE_STANDING", "SITTING"
    dest_x = random.randint(100, SCREEN_WIDTH - 100)
    dest_y = random.randint(100, SCREEN_HEIGHT - 100)
    substate_expire_time = pygame.time.get_ticks() + random.randint(WANDER_MIN_TIME, WANDER_MAX_TIME)
    direction_idx = 0 # começa olhando para o Sul (0)
    
    # --- ESTADOS DO LOOP PRINCIPAL ---
    # Estados: "MONITORING", "RUNNING_TO_WARNING", "ACTIVE", "CLEANING", "HAPPY", "GRUMPY"
    app_state = "MONITORING"
    
    last_monitor_time = 0
    cooldown_until = 0
    clickable_active = False
    
    # Variáveis de monitoramento do sistema
    current_alert_type = None
    active_start_time = 0
    
    ram_info = {"percent": 0.0, "process": "None", "process_ram": 0.0}
    temp_size_mb = 0.0
    trash_info = {"items": 0, "size_mb": 0.0}
    
    # Variáveis de Glitch e Vibração
    glitch_duration = 0
    shake_amount = 0
    
    clock = pygame.time.Clock()
    running = True
    
    # Mostra mensagem de boas-vindas rápida no console/log
    print("Doctor Penguin iniciado com sucesso! Pinguim visível andando na tela e monitorando...")
    
    # Callback de finalização de limpeza
    cleaning_result_bytes = 0
    cleaning_finished = False
    
    def on_temp_cleaned(bytes_freed):
        nonlocal cleaning_result_bytes, cleaning_finished
        cleaning_result_bytes = bytes_freed
        cleaning_finished = True
        
    def on_ram_cleaned(success):
        nonlocal cleaning_finished
        cleaning_finished = True
        
    while running:
        now_ticks = pygame.time.get_ticks()
        now_time = time.time()
        
        # Processa eventos do Pygame
        mouse_pos = (0, 0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # Trata eventos da UI do balão de diálogo
            if app_state in ["ACTIVE", "HAPPY", "GRUMPY"]:
                abs_mx, abs_my = win32api.GetCursorPos()
                mouse_pos = (abs_mx - SCREEN_X, abs_my - SCREEN_Y)
                bubble.handle_event(event, mouse_pos)

        # Atualiza a posição do mouse e trata hover/click-through para interatividade
        if app_state in ["ACTIVE", "HAPPY", "GRUMPY"]:
            abs_mx, abs_my = win32api.GetCursorPos()
            mouse_pos = (abs_mx - SCREEN_X, abs_my - SCREEN_Y)
            
            p_hitbox = drawer.get_hitbox(p_x, p_y)
            b_hitbox = bubble.get_hitbox()
            
            mouse_over_ui = p_hitbox.collidepoint(mouse_pos) or b_hitbox.collidepoint(mouse_pos)
            
            # Habilita clique apenas se estiver em cima dos elementos da UI
            if mouse_over_ui:
                if not clickable_active:
                    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, interactive_style)
                    clickable_active = True
            else:
                if clickable_active:
                    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, click_through_style)
                    clickable_active = False
        else:
            # Garante modo click-through total enquanto caminha livremente
            if clickable_active:
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, click_through_style)
                clickable_active = False

        # Roda a 60 FPS estáveis para renderizar caminhadas e animações
        clock.tick(60)

        # --- MÁQUINA DE ESTADOS DO PINGUIM ---
        
        # 1. MONITORANDO E VAGANDO (PET MODO)
        if app_state == "MONITORING":
            # A) Checagem periódica do sistema
            if now_ticks - last_monitor_time > MONITOR_CHECK_INTERVAL:
                last_monitor_time = now_ticks
                
                if now_time > cooldown_until:
                    # 1. Checa Lixeira
                    items, size = monitor.get_recycle_bin_info()
                    if items >= RECYCLE_BIN_THRESHOLD:
                        current_alert_type = "TRASH"
                        trash_info["items"] = items
                        trash_info["size_mb"] = size / (1024 * 1024)
                        
                        text = DIALOGUES["trash_alert"].format(
                            trash_items=trash_info["items"],
                            trash_size=trash_info["size_mb"]
                        )
                        bubble.set_text(text)
                        
                        def clean_trash_cb():
                            nonlocal app_state
                            play_sound_async("clean")
                            Cleaner.empty_recycle_bin()
                            app_state = "CLEANING"
                            bubble.set_text(DIALOGUES["cleaning"])
                            pygame.time.set_timer(pygame.USEREVENT + 1, 2000)
                            
                        def ignore_trash_cb():
                            nonlocal app_state, cooldown_until
                            play_sound_async("grumpy")
                            cooldown_until = time.time() + ALERT_COOLDOWN / 1000
                            app_state = "GRUMPY"
                            bubble.set_text(DIALOGUES["grumpy"])
                            pygame.time.set_timer(pygame.USEREVENT + 2, 3000)
                            
                        bubble.add_buttons([
                            {"text": "Limpar Lixeira", "callback": clean_trash_cb},
                            {"text": "Ignorar", "callback": ignore_trash_cb}
                        ])
                        
                        app_state = "ACTIVE"
                        active_start_time = now_ticks
                        play_sound_async("alarm")
                        shake_amount = 15
                        glitch_duration = 30
                        continue
                        
                    # 2. Checa Temp
                    temp_bytes = monitor.get_temp_info()
                    if temp_bytes > TEMP_THRESHOLD:
                        current_alert_type = "TEMP"
                        temp_size_mb = temp_bytes / (1024 * 1024)
                        
                        text = DIALOGUES["temp_alert"].format(temp_size=temp_size_mb)
                        bubble.set_text(text)
                        
                        def clean_temp_cb():
                            nonlocal app_state, cleaning_finished, cleaning_result_bytes
                            play_sound_async("clean")
                            cleaning_finished = False
                            cleaning_result_bytes = 0
                            Cleaner.clean_temp_files_async(on_temp_cleaned)
                            app_state = "CLEANING"
                            bubble.set_text(DIALOGUES["cleaning"])
                            
                        def ignore_temp_cb():
                            nonlocal app_state, cooldown_until
                            play_sound_async("grumpy")
                            cooldown_until = time.time() + ALERT_COOLDOWN / 1000
                            app_state = "GRUMPY"
                            bubble.set_text(DIALOGUES["grumpy"])
                            pygame.time.set_timer(pygame.USEREVENT + 2, 3000)
                            
                        bubble.add_buttons([
                            {"text": "Faxina Geral", "callback": clean_temp_cb},
                            {"text": "Ignorar", "callback": ignore_temp_cb}
                        ])
                        
                        app_state = "ACTIVE"
                        active_start_time = now_ticks
                        play_sound_async("alarm")
                        shake_amount = 15
                        glitch_duration = 30
                        continue
                        
                    # 3. Checa RAM
                    ram_percent, top_proc, top_proc_ram = monitor.get_ram_info()
                    if ram_percent > RAM_THRESHOLD:
                        current_alert_type = "RAM"
                        ram_info["percent"] = ram_percent
                        ram_info["process"] = top_proc
                        ram_info["process_ram"] = top_proc_ram
                        
                        text = DIALOGUES["ram_alert"].format(
                            ram=ram_percent,
                            process_name=top_proc,
                            process_ram=top_proc_ram
                        )
                        bubble.set_text(text)
                        
                        def clean_ram_cb():
                            nonlocal app_state, cleaning_finished
                            play_sound_async("clean")
                            cleaning_finished = False
                            Cleaner.terminate_process_by_name(ram_info["process"], on_ram_cleaned)
                            app_state = "CLEANING"
                            bubble.set_text(DIALOGUES["cleaning"])
                            
                        def ignore_ram_cb():
                            nonlocal app_state, cooldown_until
                            play_sound_async("grumpy")
                            cooldown_until = time.time() + ALERT_COOLDOWN / 1000
                            app_state = "GRUMPY"
                            bubble.set_text(DIALOGUES["grumpy"])
                            pygame.time.set_timer(pygame.USEREVENT + 2, 3000)
                            
                        bubble.add_buttons([
                            {"text": f"Fechar {top_proc[:12]}", "callback": clean_ram_cb},
                            {"text": "Ignorar", "callback": ignore_ram_cb}
                        ])
                        
                        app_state = "ACTIVE"
                        active_start_time = now_ticks
                        play_sound_async("alarm")
                        shake_amount = 15
                        glitch_duration = 30
                        continue

            # B) Atualiza IA de Caminhada
            if wander_substate == "WANDERING":
                dx = dest_x - p_x
                dy = dest_y - p_y
                dist = math.hypot(dx, dy)
                
                # Se chegou próximo ao destino ou excedeu o limite de tempo
                if dist < 8 or now_ticks > substate_expire_time:
                    # Escolhe aleatoriamente se vai ficar de pé ou sentar
                    wander_substate = random.choice(["IDLE_STANDING", "SITTING"])
                    substate_expire_time = now_ticks + random.randint(
                        IDLE_MIN_TIME if wander_substate == "IDLE_STANDING" else SITTING_MIN_TIME,
                        IDLE_MAX_TIME if wander_substate == "IDLE_STANDING" else SITTING_MAX_TIME
                    )
                else:
                    # Move o pinguim
                    vx = (dx / dist) * WALK_SPEED
                    vy = (dy / dist) * WALK_SPEED
                    p_x += vx
                    p_y += vy
                    
                    # Atualiza índice da direção baseado no ângulo do movimento
                    angle = math.degrees(math.atan2(vy, vx))
                    if angle < 0:
                        angle += 360
                    # Mapeia ângulo em graus para o índice de 0 a 7
                    sector_to_idx = [6, 7, 0, 1, 2, 3, 4, 5]
                    direction_idx = sector_to_idx[int(round(angle / 45)) % 8]
                    
            elif wander_substate in ["IDLE_STANDING", "SITTING"]:
                if now_ticks > substate_expire_time:
                    # Escolhe novo destino aleatório e volta a caminhar
                    wander_substate = "WANDERING"
                    dest_x = random.randint(100, SCREEN_WIDTH - 100)
                    dest_y = random.randint(100, SCREEN_HEIGHT - 100)
                    substate_expire_time = now_ticks + random.randint(WANDER_MIN_TIME, WANDER_MAX_TIME)

        # Removido estado RUNNING_TO_WARNING
                
        # 3. ATIVO E DIALOGANDO
        elif app_state == "ACTIVE":
            # Pinguim ativo de alertas olha para frente (Sul = 0)
            direction_idx = 0
            bubble.update(mouse_pos)
            
            # Se o usuário ignorar por 15 segundos, auto-ignorar
            if now_ticks - active_start_time > 15000:
                play_sound_async("grumpy")
                cooldown_until = time.time() + ALERT_COOLDOWN / 1000
                app_state = "GRUMPY"
                bubble.set_text(DIALOGUES["grumpy"])
                pygame.time.set_timer(pygame.USEREVENT + 2, 3000)
            
        # 4. EXECUTANDO A LIMPEZA (ANIMAÇÃO)
        elif app_state == "CLEANING":
            direction_idx = 0
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                    play_sound_async("happy")
                    app_state = "HAPPY"
                    text = DIALOGUES["clean_success"]
                    bubble.set_text(text)
                    pygame.time.set_timer(pygame.USEREVENT + 3, 4000)
            
            if cleaning_finished:
                cleaning_finished = False
                play_sound_async("happy")
                app_state = "HAPPY"
                
                if current_alert_type == "TEMP":
                    freed_mb = cleaning_result_bytes / (1024 * 1024)
                    text = f"Limpeza concluída!\nApaguei todos os arquivos temporários destrancados.\nEconomizei {freed_mb:.1f} MB de espaço!"
                elif current_alert_type == "RAM":
                    text = DIALOGUES["ram_success"].format(process_name=ram_info["process"])
                else:
                    text = DIALOGUES["clean_success"]
                    
                bubble.set_text(text)
                pygame.time.set_timer(pygame.USEREVENT + 3, 4000)
                
        # 5. FELIZ DA VIDA (SUCESSO) OU GRUMPY (IGNORADO)
        elif app_state in ["HAPPY", "GRUMPY"]:
            direction_idx = 0
            bubble.update(mouse_pos)
            for event in pygame.event.get():
                # Quando o temporizador expira, volta a caminhar livremente
                if event.type in [pygame.USEREVENT + 2, pygame.USEREVENT + 3]:
                    pygame.time.set_timer(pygame.USEREVENT + 2, 0)
                    pygame.time.set_timer(pygame.USEREVENT + 3, 0)
                    
                    # Reseta estado para voltar a andar
                    app_state = "MONITORING"
                    current_alert_type = None
                    wander_substate = "WANDERING"
                    dest_x = random.randint(100, SCREEN_WIDTH - 100)
                    dest_y = random.randint(100, SCREEN_HEIGHT - 100)
                    substate_expire_time = now_ticks + random.randint(WANDER_MIN_TIME, WANDER_MAX_TIME)

        # --- RENDERIZAR TELA ---
        screen.fill(INVISIBLE_COLOR)
        
        # Vibração se houver
        sx, sy = 0, 0
        if shake_amount > 0:
            sx = random.randint(-shake_amount, shake_amount)
            sy = random.randint(-shake_amount, shake_amount)
            shake_amount -= 1
            
        # Determina o estado gráfico do pinguim
        draw_state = "IDLE"
        if app_state == "MONITORING":
            if wander_substate == "WANDERING":
                draw_state = "WANDERING"
            elif wander_substate == "SITTING":
                draw_state = "SITTING"
            else:
                draw_state = "IDLE"
        elif app_state == "RUNNING_TO_WARNING":
            draw_state = "WANDERING"
        elif app_state == "ACTIVE":
            draw_state = "TALKING" if bubble.is_typing else "IDLE"
        elif app_state == "CLEANING":
            draw_state = "CLEANING"
        elif app_state == "HAPPY":
            draw_state = "HAPPY"
        elif app_state == "GRUMPY":
            draw_state = "IDLE"
            
        # Desenha Balão de Diálogo (se estiver falando ou agindo)
        if app_state in ["ACTIVE", "CLEANING", "HAPPY", "GRUMPY"]:
            # Posiciona dinamicamente baseado no pinguim
            ideal_bx = p_x - bubble_w / 2
            ideal_by = p_y - bubble.max_height - 90
            
            # Mantém dentro da tela
            ideal_bx = max(10, min(ideal_bx, SCREEN_WIDTH - bubble_w - 10))
            ideal_by = max(10, min(ideal_by, SCREEN_HEIGHT - bubble.max_height - 10))
            
            b_x, b_y = ideal_bx, ideal_by
            bubble.x = b_x + sx
            bubble.y = b_y + sy
            bubble.draw(screen)
            
        # Desenha Pinguim (com a direção de movimento correspondente)
        drawer.draw(screen, p_x + sx, p_y + sy, draw_state, mouse_pos, direction_idx)
            
        # Efeito de Glitch Visual (estética hacker/vírus)
        if glitch_duration > 0:
            glitch_duration -= 1
            if random.random() < 0.3:
                for _ in range(random.randint(2, 6)):
                    gy = random.randint(0, SCREEN_HEIGHT)
                    gx = random.randint(0, SCREEN_WIDTH - 200)
                    gw = random.randint(50, 400)
                    g_color = random.choice([(0, 255, 64, 150), (255, 10, 10, 150)])
                    
                    temp_surf = pygame.Surface((gw, 3), pygame.SRCALPHA)
                    temp_surf.fill(g_color)
                    screen.blit(temp_surf, (gx, gy))
                    
                if app_state in ["ACTIVE", "RUNNING_TO_WARNING"]:
                    g_rect = pygame.Rect(b_x + random.randint(-20, 20), b_y + random.randint(0, bubble_h), bubble_w, random.randint(2, 8))
                    pygame.draw.rect(screen, (0, 255, 64, 100), g_rect)

        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
