# core/player.py

from core.deck import Deck

class Player:
    def __init__(self, name, card_file, max_hp=50,
                 max_mp=50, mp=20, mp_regen=10):
        """
        Player with regenerative MP model.

        - max_mp: maximum MP the player can store
        - mp: initial/current MP (can be less than max)
        - mp_regen: MP added at begin_turn (capped to max_mp)
        """
        self.name = name
        self.deck = Deck(card_file)
        self.max_hp = int(max_hp)
        self.hp = int(max_hp)
        self.shield = int(0)
        self.effects = []  # list of dicts, e.g. {"kind":"hot","power":2,"turns":2}

        # MP system (regenerative RPG style)
        self.max_mp = int(max_mp)
        self.mp = int(mp)
        self.mp_regen = int(mp_regen)

        # per-turn played card history (names), reset each begin_turn
        self.turn_history = []

    def start_game(self):
        # draw starting hand of 5 (as per new rules)
        try:
            # Deck should provide draw_starting(n)
            self.deck.draw_starting(5)
        except Exception:
            # fallback: old behavior (if draw_starting not available)
            self.deck.draw(5)

    def begin_turn(self):
        # Regen MP (do not reset)
        self.mp = min(self.max_mp, self.mp + self.mp_regen)

        # Apply start-of-turn status effects (dot/hot etc.)
        self.apply_start_of_turn_effects()

        # reset per-turn history (we record order of played cards)
        self.turn_history = []

        # Refill hand up to minimal hand size = 5 (cap at 7)
        try:
            hand_len = len(self.deck.hand)
        except Exception:
            hand_len = 0
        need = max(0, 5 - hand_len)
        if need > 0:
            # Draw only up to max hand size
            cap = max(0, 7 - hand_len)
            to_draw = min(need, cap)
            if to_draw > 0:
                self.deck.draw(to_draw)
    
    def end_of_turn_effects(self):
        still_active = []
        for e in self.effects:
            turns = e.get("turns", 0)
            if turns > 0:
                # efek masih aktif untuk turn ini
                turns -= 1
                e["turns"] = turns

            # efek tetap disimpan kalau belum habis
            if turns > 0:
                still_active.append(e)
            elif turns == 0:
                print(f"  -> {self.name}'s {e.get('kind')} effect expired.")

        self.effects = still_active

    def add_effect(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            ef = args[0].copy()
        else:
            kind = args[0] if args else kwargs.get("kind")
            ef = {"kind": kind}
            ef.update(kwargs)

        if "name" in ef and "kind" not in ef:
            ef["kind"] = ef.pop("name")

        if ef.get("kind") == "counter" and "mode" not in ef:
            ef.setdefault("mode", "full")
            ef.setdefault("used", False)
            ef.setdefault("turns", ef.get("turns", 1))

        self.effects.append(ef)
        return ef

    def remove_effects_by_kind(self, kinds):
        self.effects = [e for e in self.effects if e.get("kind") not in kinds]

    def apply_start_of_turn_effects(self):
        dots = [e for e in self.effects if e.get("kind") == "dot"]
        hots = [e for e in self.effects if e.get("kind") == "hot"]

        total_dot = sum(e.get("power", 0) for e in dots)
        if total_dot > 0:
            self.take_damage(total_dot)
            print(f"  -> {self.name} suffers {total_dot} DOT damage.")

        total_hot = sum(e.get("power", 0) for e in hots)
        if total_hot > 0:
            healed = self.heal(total_hot)
            print(f"  -> {self.name} recovers {healed} HoT HP.")

    # ==============================
    # CORE DAMAGE CALCULATION
    # ==============================
    def take_damage(self, dmg, source=None, true=False):
        """
        Apply incoming damage to this player.

        Note: reduction must be applied before calling this function.
        'true' means bypass shields/reduction when intended by caller.
        """
        if dmg <= 0:
            return 0

        # Shield absorb
        actual_to_hp = dmg
        if not true and self.shield > 0:
            if self.shield >= actual_to_hp:
                self.shield -= actual_to_hp
                return 0
            else:
                actual_to_hp -= self.shield
                self.shield = 0

        # 💥 Izinkan HP negatif sementara agar Overkill bisa dihitung
        actual_to_hp = int(actual_to_hp)
        before = self.hp
        self.hp -= actual_to_hp  # tidak pakai max(0, ...) agar bisa -HP

        # kalau HP jadi negatif, overkill = damage melebihi sisa HP
        lost = actual_to_hp if self.hp < 0 else before - self.hp
        return lost

    def heal(self, amount):
        if amount <= 0:
            return 0
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def add_shield(self, amount):
        if amount <= 0:
            return 0
        self.shield += amount
        return self.shield

    def has_counter(self):
        return [e for e in self.effects if e.get("kind") == "counter"]

    def total_buff_damage(self):
        return sum(
            e.get("power", 0)
            for e in self.effects
            if e.get("kind") == "buff" and e.get("stat") == "damage"
        )

    def __repr__(self):
        return f"<Player {self.name} HP={self.hp} MP={self.mp} SHIELD={self.shield} EFFECTS={self.effects}>"
