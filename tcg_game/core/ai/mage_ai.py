from core.ai.base_ai import BaseAI

class MageAI(BaseAI):
    def __init__(self):
        super().__init__()
        self.combos = [
            {
                "name": "Meteor Burst",
                "require": {"Fireball": 3},
                "effect": {"type": "attack_true", "power": 30}
            },
            {
                "name": "Arcane Recovery",
                "require": {"Mana Heal": 2},
                "effect": {"type": "hot", "power": 10, "turns": 3}
            }
        ]

    def choose_cards(self, enemy):
        hand_names = [c["name"] for c in enemy.deck.hand]
        for combo in self.combos:
            if all(hand_names.count(n) >= amt for n, amt in combo["require"].items()):
                for n, amt in combo["require"].items():
                    for _ in range(amt):
                        enemy.deck.play_card_by_name(n)

                print(f"\033[91m{enemy.name}\033[0m unleashes combo: {combo['name']}!")

                return [dict(combo["effect"], name=combo["name"], combo=True)]
        return super().choose_cards(enemy)
