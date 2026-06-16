import win32api

# --- RESOLUÇÃO DA TELA (MÚLTIPLOS MONITORES) ---
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

SCREEN_X = win32api.GetSystemMetrics(SM_XVIRTUALSCREEN)
SCREEN_Y = win32api.GetSystemMetrics(SM_YVIRTUALSCREEN)
SCREEN_WIDTH = win32api.GetSystemMetrics(SM_CXVIRTUALSCREEN)
SCREEN_HEIGHT = win32api.GetSystemMetrics(SM_CYVIRTUALSCREEN)

# --- CORES E CONFIGURAÇÕES VISUAIS ---
# Cor usada como chave de transparência (chroma key) no Pygame/Windows
# Usando (1, 1, 1) para que as bordas suavizadas do PNG pareçam sombras escuras (outline) e não fiquem rosas!
INVISIBLE_COLOR = (1, 1, 1)

# Cores da interface HQ/Quadrinhos
BG_COLOR = (250, 250, 250)         # Fundo do balão (Quase branco)
BORDER_COLOR = (15, 15, 15)        # Contorno preto estilo HQ
TEXT_COLOR = (20, 20, 20)          # Texto escuro
BTN_COLOR = (220, 220, 220)        # Fundo do botão cinza claro
BTN_HOVER_COLOR = (180, 180, 180)  # Botão hover mais escuro
BTN_TEXT_COLOR = (15, 15, 15)      # Texto de botão escuro
SHADOW_COLOR = (150, 150, 150, 100)# Sombra leve translucida

# --- LIMITES DE SISTEMA (THRESHOLDS) ---
RAM_THRESHOLD = 85.0            # Alerta se uso de RAM > 85%
TEMP_THRESHOLD = 50 * 1024 * 1024 # Alerta se temporários > 50 MB
RECYCLE_BIN_THRESHOLD = 1        # Alerta se houver 1 ou mais itens na lixeira
BATTERY_THRESHOLD = 20           # Alerta se bateria estiver <= 20%
MONITOR_CHECK_INTERVAL = 3000   # Checar sistema a cada 3 segundos (em ms)
ALERT_COOLDOWN = 900000         # Tempo base de silêncio após alerta ignorado (15 minutos = 900000ms)

# --- TEXTOS E FALAS DO PINGUIM ---
DIALOGUES = {
    "welcome": "Olá, humano! Eu sou o Doctor Penguin. Estou monitorando seu sistema em busca de lixo digital e lentidão. Ficarei em segundo plano, mas se algo der errado, eu apareço!",
    
    "ram_alert": "ALERTA CRÍTICO! Sua RAM está em {ram:.1f}%!\nO processo '{process_name}' está devorando {process_ram:.1f} MB do seu computador!\nQuer que eu passe o rodo e encerre ele para você?",
    
    "temp_alert": "Epa, detectei uma montanha de lixo virtual!\nVocê tem {temp_size:.1f} MB de arquivos temporários entupindo as pastas do Windows.\nPosso fazer uma faxina agora mesmo?",
    
    "trash_alert": "Que desordem! Sua Lixeira tem {trash_items} itens acumulando poeira digital (cerca de {trash_size:.1f} MB).\nQuer que eu esvazie ela em um piscar de olhos?",
    
    "cleaning": "Limpando sistema... Aguarde enquanto eu varro essa bagunça...",
    
    "clean_success": "Faxina concluída com sucesso!\nRecuperei seu precioso espaço e memória.\nDe volta ao modo de monitoramento furtivo!",
    
    "ram_success": "Processo '{process_name}' encerrado com sucesso!\nSua memória respira aliviada agora.\nVoltando a dormir...",
    
    "no_issues": "Tudo limpo por aqui! Seu computador está voando. De volta ao modo de repouso.",
    
    "grumpy": "Humph! Você ignorou meu conselho. Não reclame depois se o PC travar... Estarei de olho."
}

# --- CONFIGURAÇÕES DE MOVIMENTAÇÃO (SPRITES E IA) ---
SPRITESHEET_PATH = "penguin_sprites_aligned.png"
SPRITE_COLS = 8
SPRITE_ROWS = 4
WALK_SPEED = 1.2
WANDER_MIN_TIME = 4000 # tempo mínimo caminhando em uma direção (ms)
WANDER_MAX_TIME = 8000 # tempo máximo caminhando em uma direção (ms)
IDLE_MIN_TIME = 3000   # tempo mínimo parado (ms)
IDLE_MAX_TIME = 6000   # tempo máximo parado (ms)
SITTING_MIN_TIME = 4000 # tempo mínimo sentado (ms)
SITTING_MAX_TIME = 8000 # tempo máximo sentado (ms)

