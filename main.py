import pygame
import time
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, INVISIBLE_COLOR, RAM_THRESHOLD, RECYCLE_BIN_THRESHOLD, TEMP_THRESHOLD
from core.window import setup_transparent_window, set_window_interactivity, get_mouse_pos
from entities.penguin import Penguin
from system.monitor import SystemMonitor
from system.cleaner import Cleaner

def main():
    screen, hwnd = setup_transparent_window("DoctorPenguin")
    
    # Inicializa Entidades
    penguin = Penguin(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    monitor = SystemMonitor()
    cleaner = Cleaner()
    
    clock = pygame.time.Clock()
    running = True
    
    last_monitor_time = 0
    cooldown_until = 0
    clickable_active = False
    
    # Callback do pinguim
    def on_checkup():
        nonlocal last_monitor_time
        last_monitor_time = 0 # Força o checkup
        
    def on_exit():
        nonlocal running
        running = False
        
    penguin.on_checkup_request = on_checkup
    penguin.on_exit_request = on_exit

    print("Doctor Penguin iniciado com sucesso! Pinguim visível andando na tela e monitorando...")

    while running:
        now = time.time()
        
        # 1. MONITORAMENTO DO SISTEMA (a cada 10s se não estiver ocupado)
        if now - last_monitor_time > 10 and now > cooldown_until and penguin.state == "WANDERING":
            last_monitor_time = now
            alert_text = None
            alert_buttons = []
            
            # Checa RAM
            ram_percent, proc_name, proc_ram = monitor.get_ram_info()
            if ram_percent > RAM_THRESHOLD:
                alert_text = f"ALERTA CRÍTICO! Sua RAM está em {ram_percent:.1f}%!\nO processo '{proc_name}' está devorando {proc_ram:.1f} MB!\nQuer que eu encerre ele para você?"
                alert_buttons = [
                    {'text': 'Encerrar', 'callback': lambda: handle_clean("RAM", proc_name)},
                    {'text': 'Ignorar', 'callback': lambda: handle_ignore()}
                ]
            else:
                # Checa Lixeira
                items, size_mb = monitor.get_recycle_bin_info()
                if items >= RECYCLE_BIN_THRESHOLD:
                    alert_text = f"Sua Lixeira está acumulando lixo!\nTem {items} itens ocupando {size_mb:.1f} MB de espaço.\nPosso esvaziar a lixeira para você?"
                    alert_buttons = [
                        {'text': 'Esvaziar', 'callback': lambda: handle_clean("TRASH", None)},
                        {'text': 'Ignorar', 'callback': lambda: handle_ignore()}
                    ]
                else:
                    # Checa Temporários
                    temp_mb = monitor.get_temp_info() / (1024 * 1024)
                    if temp_mb > (TEMP_THRESHOLD / (1024 * 1024)):
                        alert_text = f"Seu PC tem muito lixo temporário!\nEstimo mais de {temp_mb:.1f} MB de arquivos que não servem para nada na pasta Temp.\nPosso limpar?"
                        alert_buttons = [
                            {'text': 'Limpar', 'callback': lambda: handle_clean("TEMP", None)},
                            {'text': 'Ignorar', 'callback': lambda: handle_ignore()}
                        ]
                        
            if alert_text:
                penguin.set_alert(alert_text, alert_buttons)
                
        # Callbacks locais das ações do alerta
        def handle_clean(type, target):
            nonlocal cooldown_until
            penguin.set_state("CLEANING")
            penguin.bubble.set_text("Trabalhando nisso... faxina em progresso!")
            penguin.bubble.add_buttons([])
            
            if type == "RAM":
                cleaner.kill_process(target)
            elif type == "TRASH":
                cleaner.empty_recycle_bin()
            elif type == "TEMP":
                cleaner.clean_temp_files()
                
            # Mostra mensagem de sucesso
            penguin.set_state("HAPPY")
            penguin.bubble.set_text("Problema resolvido! Seu PC está respirando melhor agora.")
            penguin.bubble.add_buttons([
                {'text': 'Ok', 'callback': lambda: handle_ignore()}
            ])
            cooldown_until = time.time() + 30 # 30s sem encher o saco
            
        def handle_ignore():
            nonlocal cooldown_until
            penguin.set_state("GRUMPY")
            penguin.bubble.set_text("Humph! Você ignorou meu conselho. Não reclame depois se o PC travar...")
            penguin.bubble.add_buttons([])
            penguin.substate_expire_time = pygame.time.get_ticks() + 3000 # 3s rabugento
            cooldown_until = time.time() + 60 # 60s sem incomodar

        # 2. CAPTURA DE EVENTOS
        mouse_pos = get_mouse_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Passa evento para o pinguim e para a UI (se o pinguim tratar, ele retorna True)
            penguin.handle_event(event, mouse_pos)

        # 3. ATUALIZA ESTADOS (Pinguim, UI, Física)
        penguin.update(mouse_pos)

        # 4. GESTÃO DE JANELA INTERATIVA vs CLICK-THROUGH
        hitboxes = penguin.get_ui_hitboxes()
        mouse_over_ui = any(r.collidepoint(mouse_pos) for r in hitboxes)
        
        if mouse_over_ui:
            if not clickable_active:
                set_window_interactivity(hwnd, True)
                clickable_active = True
        else:
            if clickable_active:
                set_window_interactivity(hwnd, False)
                clickable_active = False

        # 5. RENDERIZAÇÃO
        screen.fill(INVISIBLE_COLOR)
        penguin.draw(screen, mouse_pos)
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
