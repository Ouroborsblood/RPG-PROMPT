from core.player import Player
from core.battle import Battle
from core.ai.warrior_ai import WarriorAI
from core.ai.mage_ai import MageAI


if __name__ == "__main__":
    p1 = Player("Hero", "data/test2.json")
    p2 = Player("Enemy", "data/cards_enemy.json")

    ai = WarriorAI()  # 🔁 Ganti di sini: WarriorAI() / MageAI() / BaseAI()

    battle = Battle(p1, p2)
    battle.start()
