import pygame
import time
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, INVISIBLE_COLOR, RAM_THRESHOLD, RECYCLE_BIN_THRESHOLD, TEMP_THRESHOLD, BATTERY_THRESHOLD, ALERT_COOLDOWN
from core.window import setup_transparent_window, get_mouse_pos
from entities.penguin import Penguin
from entities.fish_drop import FishDrop
from entities.egg import Egg, BabyPenguin
from system.monitor import SystemMonitor
from system.cleaner import Cleaner
from system.save_manager import SaveManager

def main():
    screen, hwnd = setup_transparent_window("DoctorPenguin")
    
    # Inicializa Entidades
    save_manager = SaveManager()
    penguin = Penguin(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, save_manager)
    monitor = SystemMonitor()
    cleaner = Cleaner()
    
    clock = pygame.time.Clock()
    running = True
    
    last_monitor_time = 0
    cooldown_until = 0
    
    app_start_time = time.time()
    last_fish_spawn = time.time()
    active_fish = None
    
    last_egg_spawn = time.time()
    active_egg = None
    baby_penguin = None
    
    # Callback do pinguim
    def on_checkup():
        nonlocal last_monitor_time
        last_monitor_time = 0 # Força o checkup
        
    def on_exit():
        nonlocal running
        running = False
        
    def on_snooze():
        nonlocal cooldown_until
        cooldown_until = time.time() + 3600 # 1 hora
        
    penguin.on_checkup_request = on_checkup
    penguin.on_exit_request = on_exit
    penguin.on_snooze_request = on_snooze

    print("Doctor Penguin iniciado com sucesso! Pinguim visível andando na tela e monitorando...")

    while running:
        now = time.time()
        
        # 1. MONITORAMENTO DO SISTEMA (a cada 10s se não estiver ocupado)
        if now - last_monitor_time > 10 and now > cooldown_until and penguin.state == "WANDERING":
            last_monitor_time = now
            alert_text = None
            alert_buttons = []
            alert_type = None
            alert_target = None
            
            # 0. Checa Saúde Humana (a cada 2 horas)
            if now - app_start_time > 7200: # 7200 segundos = 2 horas
                alert_text = "Mestre! Você está há muito tempo focado...\nBeba uma água e alongue as costas para não bugar sua coluna!"
                alert_buttons = [
                    {'text': 'Já bebi!', 'callback': lambda: handle_human_health()}
                ]
                alert_type = "HUMAN"
            else:
                # 1. Checa RAM
                ram_percent, proc_name, proc_ram = monitor.get_ram_info()
                if ram_percent > RAM_THRESHOLD and proc_name and not save_manager.is_ignored(proc_name):
                    alert_text = f"Sua RAM chegou a {ram_percent:.1f}%!\nO processo '{proc_name}' usa {proc_ram:.1f} MB!\nQuer que eu feche ele para aliviar o PC?"
                    alert_buttons = [
                        {'text': 'Encerrar', 'callback': lambda: handle_clean("RAM", proc_name)},
                        {'text': 'Ignorar', 'callback': lambda: handle_ignore("RAM", proc_name)}
                    ]
                    alert_type = "RAM"
                    alert_target = proc_name
                    penguin.prop = "STETHOSCOPE"
                else:
                    # Checa Bateria
                    batt_percent, batt_plugged = monitor.check_battery()
                    if batt_percent is not None and batt_percent <= BATTERY_THRESHOLD and not batt_plugged:
                        alert_text = f"Mestre, socorro! Bateria em {batt_percent}%!\nPor favor, conecte o carregador antes que eu apague!"
                        alert_buttons = [
                            {'text': 'Ok, já vou', 'callback': lambda: handle_dismiss()}
                        ]
                        alert_type = "BATT"
                    else:
                        # Checa Internet
                        if not monitor.check_internet():
                            alert_text = "Ei! A internet caiu! Não consigo contatar minha família na Antártida!\nVerifique seu roteador!"
                            alert_buttons = [
                                {'text': 'Ok', 'callback': lambda: handle_dismiss()}
                            ]
                            alert_type = "NET"
                        else:
                            # Checa Lixeira
                            items, size_mb = monitor.get_recycle_bin_info()
                            if items >= RECYCLE_BIN_THRESHOLD:
                                alert_text = f"Sua Lixeira está fedendo!\nTem {items} itens ocupando {size_mb:.1f} MB de espaço.\nPosso esvaziar a lixeira para você?"
                                alert_buttons = [
                                    {'text': 'Esvaziar', 'callback': lambda: handle_clean("TRASH", None)},
                                    {'text': 'Ignorar', 'callback': lambda: handle_ignore("TRASH", None)}
                                ]
                                alert_type = "TRASH"
                                penguin.prop = "BROOM"
                            else:
                                # Checa Temporários
                                temp_mb = monitor.get_temp_info() / (1024 * 1024)
                                if temp_mb > (TEMP_THRESHOLD / (1024 * 1024)):
                                    alert_text = f"Estimo mais de {temp_mb:.1f} MB de arquivos inúteis na pasta Temp.\nPosso fazer a faxina?"
                                    alert_buttons = [
                                        {'text': 'Limpar', 'callback': lambda: handle_clean("TEMP", None)},
                                        {'text': 'Ignorar', 'callback': lambda: handle_ignore("TEMP", None)}
                                    ]
                                    alert_type = "TEMP"
                                    penguin.prop = "BROOM"
                        
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
                {'text': 'Ok', 'callback': lambda: handle_dismiss()}
            ])
            penguin.substate_expire_time = pygame.time.get_ticks() + 5000
            cooldown_until = time.time() + 30 # 30s sem encher o saco
            
        def handle_human_health():
            nonlocal app_start_time
            app_start_time = time.time() # Reseta o tempo
            penguin.set_state("HAPPY")
            penguin.happiness = min(100, penguin.happiness + 20)
            penguin.bubble.set_text("Isso aí! Corpo são, PC são!")
            penguin.bubble.add_buttons([])
            penguin.substate_expire_time = pygame.time.get_ticks() + 4000
            
        def handle_dismiss():
            penguin.set_state("WANDERING")
            
        def handle_ignore(type="UNKNOWN", target=None):
            nonlocal cooldown_until
            if type == "RAM" and target:
                save_manager.ignore_process(target, hours=2)
                penguin.bubble.set_text(f"Ok, vou ignorar o '{target}' por um tempo. Mas fique de olho!")
            else:
                penguin.bubble.set_text("Humph! Você ignorou meu conselho. Depois não reclame!")
            
            penguin.set_state("GRUMPY")
            penguin.bubble.add_buttons([])
            penguin.substate_expire_time = pygame.time.get_ticks() + 3000 # 3s rabugento
            cooldown_until = time.time() + (ALERT_COOLDOWN / 1000.0) # 15 minutos sem incomodar por outras coisas
            
        penguin.on_alert_ignored = lambda: handle_ignore("TIMEOUT", None)

        # 2. CAPTURA DE EVENTOS
        mouse_pos = get_mouse_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # Se a janela perder o foco (ex: usuário clicou fora da área opaca da janela), fecha o menu
            if event.type == pygame.WINDOWFOCUSLOST or event.type == getattr(pygame, 'ACTIVEEVENT', -1):
                penguin.menu.hide()
                
            # Checa clique no peixe
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Checa clique no ovo
                if active_egg and active_egg.check_click(mouse_pos):
                    penguin.audio.play('beep')
                    if active_egg.hatched:
                        baby_penguin = BabyPenguin(active_egg.x, active_egg.y)
                        penguin.audio.play('quack') # Nasceu!
                        active_egg = None
                        penguin.bubble.set_text("Meu filhote nasceu!! Obrigado por cuidar do ovo!")
                        penguin.bubble.add_buttons([])
                        penguin.substate_expire_time = pygame.time.get_ticks() + 4000
                
                # Checa clique no peixe
                if active_fish and active_fish.check_click(mouse_pos):
                    save_manager.add_fish()
                    penguin.audio.play('beep') # Toca um sonzinho
                    active_fish = None
                    
            # Passa evento para o pinguim e para a UI (se o pinguim tratar, ele retorna True)
            penguin.handle_event(event, mouse_pos)

        # 3. ATUALIZA ESTADOS (Pinguim, UI, Física)
        penguin.update(mouse_pos)
        
        if baby_penguin:
            baby_penguin.update(penguin.x, penguin.y)
            
        # Spawn do Ovo (Apenas um por sessão, ou bem raro)
        if not baby_penguin and not active_egg and now - last_egg_spawn > random.randint(300, 600):
            if random.random() < 0.5: # 50% de chance de botar quando timer expira
                active_egg = Egg(penguin.x, penguin.y)
                penguin.audio.play('boing')
            last_egg_spawn = now
        
        # Sistema de Pesca Aleatória (A cada 3 a 8 minutos)
        if active_fish is None and now - last_fish_spawn > random.randint(180, 480):
            active_fish = FishDrop(SCREEN_WIDTH)
            last_fish_spawn = now
            
        if active_fish:
            active_fish.update(SCREEN_HEIGHT)
            if not active_fish.active:
                active_fish = None

        # 4. RENDERIZAÇÃO
        screen.fill(INVISIBLE_COLOR)
        if active_fish:
            active_fish.draw(screen)
            
        if active_egg:
            active_egg.draw(screen)
            
        if baby_penguin:
            baby_penguin.draw(screen, mouse_pos)
            
        penguin.draw(screen, mouse_pos)
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
