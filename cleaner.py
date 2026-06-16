import os
import ctypes
import threading
import psutil

class Cleaner:
    @staticmethod
    def empty_recycle_bin():
        """Esvazia a Lixeira do Windows silenciosamente. Retorna True se bem sucedido."""
        try:
            # Flags: SHERB_NOCONFIRMATION (1) | SHERB_NOPROGRESSUI (2) | SHERB_NOSOUND (4) = 7
            res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            return res == 0
        except Exception as e:
            print(f"[Cleaner] Erro ao esvaziar lixeira: {e}")
            return False

    @staticmethod
    def clean_temp_files_async(on_finish_callback=None):
        """Limpa arquivos temporários do usuário em background para não travar a GUI."""
        def thread_target():
            temp_dir = os.environ.get("TEMP", "")
            if not temp_dir or not os.path.exists(temp_dir):
                if on_finish_callback:
                    on_finish_callback(0)
                return
                
            cleaned_bytes = 0
            # topdown=False permite apagar arquivos antes de tentar remover as pastas vazias
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for file in files:
                    fp = os.path.join(root, file)
                    try:
                        size = os.path.getsize(fp)
                        os.remove(fp)
                        cleaned_bytes += size
                    except:
                        # Ignora com segurança se o arquivo estiver bloqueado ou em uso
                        pass
                        
                for directory in dirs:
                    dp = os.path.join(root, directory)
                    try:
                        os.rmdir(dp)
                    except:
                        pass
            
            if on_finish_callback:
                on_finish_callback(cleaned_bytes)
                
        thread = threading.Thread(target=thread_target, daemon=True)
        thread.start()

    @staticmethod
    def terminate_process_by_name(process_name, on_finish_callback=None):
        """Busca e encerra o processo correspondente ao nome de forma assíncrona."""
        def thread_target():
            success = False
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == process_name.lower():
                        proc.terminate()
                        # Aguarda até 3 segundos para ver se encerra amigavelmente
                        try:
                            proc.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            proc.kill() # Força o encerramento se não fechar
                        success = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if on_finish_callback:
                on_finish_callback(success)
                
        thread = threading.Thread(target=thread_target, daemon=True)
        thread.start()
