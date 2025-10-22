from typing import List
from itertools import zip_longest


class CombatManager:
    """Manages the simultaneous turn resolution.


    Strategy used here (simple and deterministic):
        1. Apply all 'status-setting' effects (buffs, hot, dot, counter, defense, clean, strip)
        2. Resolve all immediate effects that deal/restore HP (attack, attack_true, lifesteal, heal)

    This order means counters/buffs applied at step 1 will affect step 2 damage.
    """


    def __init__(self, effects_engine, logger=None):
        self.effects = effects_engine
        self.logger = logger


    def resolve_turn(self, player, enemy, player_cards: List[dict], enemy_cards: List[dict]):
        # split categories
        status_types = {"buff", "hot", "dot", "counter", "defense", "strip", "clean", "reduce", "reflect" }

        p_status = [c for c in player_cards if c.get("type") in status_types or c.get("type") == "combo" and any(k in (c.get("effect") or {}) for k in ("buff_damage","hot","heal"))]
        e_status = [c for c in enemy_cards if c.get("type") in status_types or c.get("type") == "combo" and any(k in (c.get("effect") or {}) for k in ("buff_damage","hot","heal"))]

        p_immediate = [c for c in player_cards if c not in p_status]
        e_immediate = [c for c in enemy_cards if c not in e_status]


        # 1) status abilities applied (both sides)
        # 1️⃣ STATUS ABILITIES (apply simultaneously)
        for ps, es in zip_longest(p_status, e_status):
            if ps:
             self.effects.apply(player, enemy, ps)
            if es:
             self.effects.apply(enemy, player, es)



        # 2) immediate abilities
        # Process in the order they were chosen (player first then enemy) to keep determinism
        for c in p_immediate:
            self.effects.apply(player, enemy, c)
        for c in e_immediate:
            self.effects.apply(enemy, player, c)

        # Setelah semua efek selesai diterapkan:
        p_overkill = max(0, -enemy.hp)
        e_overkill = max(0, -player.hp)

        if p_overkill > 0:
            self.logger.log(f"{player.name} melakukan OVERKILL sebesar {p_overkill}!")
            enemy.hp = 0

        if e_overkill > 0:
            self.logger.log(f"{enemy.name} melakukan OVERKILL sebesar {e_overkill}!")
            player.hp = 0

        # after resolution, handle counter reflection
        # Note: counters are implemented as effects on players: when damage is taken the Player.take_damage
        # implementation may consult counters (see Player code for integration).
