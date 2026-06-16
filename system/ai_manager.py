import threading
import urllib.request
import json
import queue

class AIManager:
    def __init__(self):
        self._is_enabled = False
        self.model = "llama3.2:1b"
        self.api_url = "http://localhost:11434/api/generate"
        
        # Sistema de Fila de Falas
        self.request_queue = queue.Queue()
        self.current_task_id = 0
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        self.system_prompt = (
            "Você é o Doctor Penguin, um pinguim mascote virtual de computador. "
            "Você mora no PC do usuário e ajuda a cuidar do sistema. "
            "Você é fofo, inteligente, prestativo e um pouco atrevido. "
            "Você ama peixes, frio, gelo e a Antártida. "
            "Suas respostas devem ser SEMPRE curtas (no máximo 10 frases), diretas e em português do Brasil (PT-BR). "
            "Aja como o mascote interagindo com seu dono e reaja ao contexto fornecido. Não dê explicações extras, não saia do personagem."
        )

    @property
    def is_enabled(self):
        return self._is_enabled

    def enable(self, state: bool):
        self._is_enabled = state

    def request_dialogue(self, event_context, callback, fallback):
        if not self._is_enabled:
            callback(fallback)
            return

        self.current_task_id += 1
        
        self.request_queue.put({
            'task_id': self.current_task_id,
            'event_context': event_context,
            'callback': callback,
            'fallback': fallback
        })

    def _worker_loop(self):
        while True:
            req = self.request_queue.get()
            
            # Se já tem outra requisição mais nova na fila, descarta esta (evita acúmulo)
            if req['task_id'] != self.current_task_id:
                continue
                
            try:
                prompt = f"Contexto atual do PC ou da interação: {req['event_context']}\nO que você diria para o usuário agora?"
                
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "system": self.system_prompt,
                    "stream": False
                }
                
                data = json.dumps(payload).encode("utf-8")
                http_req = urllib.request.Request(self.api_url, data=data, headers={"Content-Type": "application/json"})
                
                with urllib.request.urlopen(http_req, timeout=30) as response:
                    # Verifica se o usuário engatilhou outra fala enquanto esperávamos a IA pensar
                    if req['task_id'] != self.current_task_id:
                        continue
                        
                    if response.status == 200:
                        resp_data = json.loads(response.read().decode("utf-8"))
                        ai_text = resp_data.get("response", "").strip()
                        # Remove aspas extras que a IA as vezes coloca
                        if ai_text.startswith('"') and ai_text.endswith('"'):
                            ai_text = ai_text[1:-1]
                            
                        if ai_text:
                            req['callback'](ai_text)
                        else:
                            req['callback'](req['fallback'])
                    else:
                        print(f"[AIManager] Erro na API do Ollama (Status {response.status})")
                        req['callback'](req['fallback'])
            except Exception as e:
                # Só executa o fallback de erro se ainda for a task atual
                if req['task_id'] == self.current_task_id:
                    print(f"[AIManager] Erro ao contatar Ollama: {e}")
                    req['callback'](req['fallback'])