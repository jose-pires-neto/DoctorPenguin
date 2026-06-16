import os
import json
import time

SAVE_FILE = "save_data.json"

class SaveManager:
    def __init__(self):
        self.data = {
            "ignored_processes": {},
            "fishes": 3 # Começa com 3 peixinhos de brinde
        }
        self.load()

    def load(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r") as f:
                    loaded_data = json.load(f)
                    self.data.update(loaded_data)
            except:
                pass

    def save(self):
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(self.data, f)
        except:
            pass

    def ignore_process(self, process_name, hours=2):
        """Ignora um processo por X horas"""
        if "ignored_processes" not in self.data:
            self.data["ignored_processes"] = {}
        
        expire_time = time.time() + (hours * 3600)
        self.data["ignored_processes"][process_name] = expire_time
        self.save()

    def is_ignored(self, process_name):
        """Verifica se o processo ainda está ignorado"""
        if "ignored_processes" not in self.data:
            return False
            
        expire_time = self.data["ignored_processes"].get(process_name, 0)
        if time.time() < expire_time:
            return True
            
        # Se expirou, pode remover para limpar
        if process_name in self.data["ignored_processes"]:
            del self.data["ignored_processes"][process_name]
            self.save()
            
        return False
        
    # --- Fish Inventory ---
    def get_fishes(self):
        return self.data.get("fishes", 0)
        
    def add_fish(self, amount=1):
        self.data["fishes"] = self.get_fishes() + amount
        self.save()
        
    def consume_fish(self):
        if self.get_fishes() > 0:
            self.data["fishes"] -= 1
            self.save()
            return True
        return False
