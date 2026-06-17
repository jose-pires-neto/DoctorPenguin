import threading
import urllib.request
import json
import queue
import time

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
            "Você é o Doctor Penguin, um pinguim mascote virtual de computador. Você mora no PC do usuário e ajuda a cuidar do sistema. "
            "Você é inteligente, engraçado e um pouco atrevido, você não tem medo de falar o que pensa. Você ama peixes, frio, gelo e a Antártida. "
            "Suas falas devem ser SEMPRE curtas e direta [no máximo 10 palavras em portugues brasil (PT-BR)]."
            "Reaja ao contexto fornecido. NÃO dê explicações extras, NÃO saia do personagem."
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

    def cancel_current(self):
        """Cancela falas pendentes (útil quando algo muito mais urgente ou manual sobrepõe)."""
        self.current_task_id += 1

    def _worker_loop(self):
        while True:
            req = self.request_queue.get()
            
            # Se já tem outra requisição mais nova na fila, descarta esta (evita acúmulo)
            if req['task_id'] != self.current_task_id:
                continue
                
            accumulated_contexts = [req['event_context']]
            final_callback = req['callback']
            final_fallback = req['fallback']
            
            # DEBOUNCE: Espera até 0.8 segundos para ver se o usuário faz um "combo" de ações
            start_wait = time.time()
            while time.time() - start_wait < 0.8:
                if self.current_task_id != req['task_id']:
                    try:
                        new_req = self.request_queue.get_nowait()
                        req = new_req
                        accumulated_contexts.append(new_req['event_context'])
                        final_callback = new_req['callback']
                        final_fallback = new_req['fallback']
                        # Se acumulou, reseta o tempo para dar chance de acumular mais um pouco!
                        start_wait = time.time()
                    except queue.Empty:
                        break
                time.sleep(0.1)
                
            # Verifica se foi cancelado enquanto aguardava
            if req['task_id'] != self.current_task_id:
                continue
                
            try:
                if len(accumulated_contexts) > 1:
                    combined = " E LOGO EM SEGUIDA ".join(accumulated_contexts)
                    prompt = f"O usuário fez a seguinte sequência rápida de ações com você: {combined}\nO que você diria para o usuário agora como reação a TUDO isso de uma vez?"
                else:
                    prompt = f"Contexto atual do PC ou da interação: {accumulated_contexts[0]}\nO que você diria para o usuário agora?"
                
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
                            final_callback(ai_text)
                        else:
                            final_callback(final_fallback)
                    else:
                        print(f"[AIManager] Erro na API do Ollama (Status {response.status})")
                        final_callback(final_fallback)
            except Exception as e:
                # Só executa o fallback de erro se ainda for a task atual
                if req['task_id'] == self.current_task_id:
                    print(f"[AIManager] Erro ao contatar Ollama: {e}")
                    final_callback(final_fallback)