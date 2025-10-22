from core.ai.base_ai import BaseAI
from colorama import Fore, Style
import random

class WarriorAI(BaseAI):
    def __init__(self):
        super().__init__()
        self.name = "WarriorAI"

    def choose_actions(self, enemy, player, combos):
        chosen = []
        hand = enemy.deck.hand
        available_combos = self.check_combos(hand, combos)

        # Prioritas: gunakan combo ofensif dulu
        offensive = [c for c in available_combos if "damage" in c["effect"]]
        healing = [c for c in available_combos if "heal" in c["effect"]]

        for _ in range(2):
            if player.hp < 20 and healing:
                combo = random.choice(healing)
            elif offensive:
                combo = random.choice(offensive)
            else:
                combo = None

            if combo:
                print(f"{Fore.MAGENTA}{enemy.name} mengaktifkan {combo['name']}!{Style.RESET_ALL}")
                for req, amt in combo["require"].items():
                    enemy.deck.remove_card_by_name(req, amt)
                chosen.append({
                    "name": combo["name"],
                    "type": "combo",
                    "effect": combo["effect"]
                })
            elif hand:
                chosen.append(hand.pop(0))
        return chosen
