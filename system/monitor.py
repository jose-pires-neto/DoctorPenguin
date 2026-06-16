import os
import ctypes
import threading
import time
import psutil
import urllib.request
from ctypes import wintypes

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64)
    ]

class SystemMonitor:
    def __init__(self):
        self._temp_size = 0
        self._temp_scanning = False
        self._last_temp_scan = 0
        
        # Inicia a primeira varredura de temporários em background
        self.trigger_temp_scan_async()

    def get_ram_info(self):
        """Retorna (porcentagem_ram, nome_processo_pesado, ram_processo_pesado_mb)"""
        try:
            virtual_mem = psutil.virtual_memory()
            ram_percent = virtual_mem.percent
            
            # Encontra o processo que consome mais memória física (rss)
            top_process = None
            max_rss = 0
            
            for proc in psutil.process_iter():
                try:
                    name = proc.name()
                    mem = proc.memory_info()
                    rss = mem.rss
                    if rss > max_rss:
                        # Ignora processos do sistema que não podemos/devemos fechar
                        if name.lower() not in ['system', 'registry', 'idle', 'lsass.exe', 'csrss.exe', 'explorer.exe']:
                            max_rss = rss
                            top_process = proc
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, PermissionError, OSError):
                    continue
                    
            if top_process and max_rss > 0:
                try:
                    top_process_name = top_process.name()
                    top_process_ram_mb = max_rss / (1024 * 1024)
                    return ram_percent, top_process_name, top_process_ram_mb
                except:
                    pass
                
            return ram_percent, "Nenhum", 0.0
        except Exception as e:
            print(f"[Monitor] Erro ao obter dados de RAM: {e}")
            return 0.0, "Erro", 0.0

    def get_recycle_bin_info(self):
        """Retorna (quantidade_de_itens, tamanho_em_bytes) na Lixeira do Windows"""
        try:
            info = SHQUERYRBINFO(cbSize=ctypes.sizeof(SHQUERYRBINFO))
            res = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
            if res == 0:
                return info.i64NumItems, info.i64Size
            return 0, 0
        except Exception as e:
            print(f"[Monitor] Erro ao ler lixeira: {e}")
            return 0, 0

    def get_temp_info(self):
        """Retorna o tamanho acumulado da pasta Temp do usuário.
        Dispara uma varredura em segundo plano se o cache tiver mais de 30 segundos."""
        now = time.time()
        if now - self._last_temp_scan > 30 and not self._temp_scanning:
            self.trigger_temp_scan_async()
        return self._temp_size

    def trigger_temp_scan_async(self):
        """Dispara a varredura da pasta Temp em segundo plano."""
        if self._temp_scanning:
            return
            
        def scan_job():
            self._temp_scanning = True
            temp_dir = os.environ.get("TEMP", "")
            total_size = 0
            if temp_dir and os.path.exists(temp_dir):
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        fp = os.path.join(root, file)
                        try:
                            total_size += os.path.getsize(fp)
                        except:
                            pass
            self._temp_size = total_size
            self._last_temp_scan = time.time()
            self._temp_scanning = False

        thread = threading.Thread(target=scan_job, daemon=True)
        thread.start()

    def check_battery(self):
        """Retorna (porcentagem, carregando) ou (None, None) se for desktop"""
        if not hasattr(psutil, "sensors_battery"):
            return None, None
        battery = psutil.sensors_battery()
        if battery:
            return battery.percent, battery.power_plugged
        return None, None
        
    def check_internet(self):
        """Retorna True se estiver conectado à internet"""
        try:
            # Conecta a um site real que responda a requisições HTTP rápidas
            urllib.request.urlopen('http://www.google.com', timeout=2)
            return True
        except:
            return False
