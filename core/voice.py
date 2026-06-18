import pyttsx3
import threading
import queue
import asyncio
import edge_tts
import pygame
import os

class VoiceSystem:
    def __init__(self, save_manager):
        self.save_manager = save_manager
        self.q = queue.Queue()
        self.pyttsx3_engine = None
        self.voices = []
        
        # Vozes Premium em Nuvem (Edge TTS)
        self.voices = [
            {'id': 'pt-BR-FranciscaNeural', 'name': 'Francisca (Alta Qualidade)'},
            {'id': 'pt-BR-AntonioNeural', 'name': 'Antonio (Alta Qualidade)'},
            {'id': 'pt-BR-ThalitaNeural', 'name': 'Thalita (Alta Qualidade)'}
        ]
        
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        # 1. Inicializa o fallback offline (pyttsx3)
        try:
            self.pyttsx3_engine = pyttsx3.init()
            local_voices = self.pyttsx3_engine.getProperty('voices')
            
            # Adiciona a primeira voz local que encontrar em PT-BR como fallback visível
            for v in local_voices:
                if 'Portuguese' in v.name or 'Brazil' in v.name or 'PT-BR' in v.name.upper() or 'Maria' in v.name or 'Daniel' in v.name:
                    nome_curto = v.name.split('-')[0].strip()
                    self.voices.append({'id': v.id, 'name': f"{nome_curto} (Offline)"})
                    break
        except Exception as e:
            print(f"Erro ao inicializar fallback TTS local: {e}")

        # Se não houver voz selecionada ainda, define a Francisca como padrão
        if not self.save_manager.get_voice_id() and self.voices:
            self.save_manager.set_voice_id(self.voices[0]['id'])

        while True:
            item = self.q.get()
            if item is None:
                break
                
            text, voice_id = item
            
            # Checa se é uma voz do Edge TTS (Nuvem)
            is_edge = "Neural" in voice_id if voice_id else False
            
            success = False
            
            # Tenta pela nuvem primeiro se for uma voz neural
            if is_edge:
                try:
                    import tempfile
                    temp_file = os.path.join(tempfile.gettempdir(), "penguin_temp_voice.mp3")
                    communicate = edge_tts.Communicate(text, voice_id)
                    asyncio.run(communicate.save(temp_file))
                    
                    if os.path.exists(temp_file):
                        pygame.mixer.music.load(temp_file)
                        pygame.mixer.music.play()
                        
                        # Espera terminar de tocar
                        while pygame.mixer.music.get_busy():
                            # Se chegar uma nova frase na fila enquanto essa toca, aborta!
                            if not self.q.empty():
                                pygame.mixer.music.stop()
                                break
                            pygame.time.delay(100)
                            
                        # Limpa para evitar travamento de arquivo no Windows
                        pygame.mixer.music.unload()
                        success = True
                except Exception as e:
                    print(f"Erro na nuvem (Edge TTS), ativando fallback offline: {e}")
                    success = False
                    
            # Fallback offline (se a nuvem falhou ou se o usuário escolheu a voz offline)
            if not success and self.pyttsx3_engine:
                try:
                    # Se ele estava tentando usar a voz neural e falhou, mantemos a voz local atual.
                    # Mas se ele escolheu a voz local intencionalmente, setamos a ID:
                    if not is_edge and voice_id:
                        self.pyttsx3_engine.setProperty('voice', voice_id)
                        
                    self.pyttsx3_engine.say(text)
                    self.pyttsx3_engine.runAndWait()
                except Exception as e:
                    print(f"Erro no fallback TTS offline: {e}")
                
            self.q.task_done()

    def get_voices(self):
        """Retorna as vozes mescladas (Nuvem + Fallback Offline)"""
        return self.voices

    def speak(self, text):
        """Adiciona um texto à fila para ser falado"""
        if not self.save_manager.is_voice_enabled():
            return
            
        if text.strip() == "..." or not text.strip():
            return

        voice_id = self.save_manager.get_voice_id()
        
        # Limpa a fila para a nova fala cortar a anterior
        with self.q.mutex:
            self.q.queue.clear()
            
        # Para a música do pygame caso a voz neural esteja tocando agora
        if pygame.mixer.get_init():
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
            except:
                pass
            
        self.q.put((text, voice_id))
