import json
import os
import random

def roll(chance):
    return random.random() < chance

def load_json(path):
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    full_path = os.path.join(base_path, path)
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)
