import os

base_path = os.path.dirname(__file__)
hero_file = os.path.join(base_path, "data", "test2.json")
enemy_file = os.path.join(base_path, "data", "cards_enemy.json")

print("BASE PATH:", base_path)
print("Hero file exists:", os.path.exists(hero_file))
print("Enemy file exists:", os.path.exists(enemy_file))
