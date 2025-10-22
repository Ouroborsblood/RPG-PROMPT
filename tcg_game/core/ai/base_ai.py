import random
from colorama import Fore, Style

class BaseAI:
    def __init__(self):
        self.name = "BaseAI"

    def choose_actions(self, enemy, player, combos):
        """Default AI: pilih kartu random, kadang combo"""
        chosen = []
        hand = enemy.deck.hand

        # cari combo yang bisa dipakai
        available_combos = self.check_combos(hand, combos)

        for _ in range(2):
            use_combo = available_combos and random.random() < 0.3
            if use_combo:
                combo = random.choice(available_combos)
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

    def check_combos(self, hand, combos):
        hand_names = [c["name"] for c in hand]
        available = []
        for combo in combos:
            if all(hand_names.count(req) >= amt for req, amt in combo["require"].items()):
                available.append(combo)
        return available
