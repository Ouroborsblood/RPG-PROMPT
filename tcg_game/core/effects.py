# core/effects.py
# Overwrite this file

from colorama import Fore, Style


class EffectEngine:
    def __init__(self, logger=None):
        self.logger = logger if logger is not None else self

    def log(self, msg):
        # logger has `.log()` in BattleLogger; fallback to print
        if hasattr(self.logger, "log"):
            self.logger.log(msg)
        else:
            print(msg)

    def color_name(self, actor, self_ref=True):
        name = actor.name
        if name.lower() == "hero":
            return f"{Fore.CYAN}{name}{Style.RESET_ALL}"
        elif name.lower() == "enemy":
            return f"{Fore.RED}{name}{Style.RESET_ALL}"
        return f"{Fore.WHITE}{name}{Style.RESET_ALL}"

    def color_num(self, num, kind="damage"):
        if kind == "heal":
            return f"{Fore.GREEN}{num}{Style.RESET_ALL}"
        elif kind == "shield":
            return f"{Fore.CYAN}{num}{Style.RESET_ALL}"
        return f"{Fore.RED}{num}{Style.RESET_ALL}"

    # -------------------------
    # Main apply entry
    # -------------------------
    def apply(self, user, target, card):
        """
        Central dispatcher for cards.
        card fields: type, power (int), ratio (float 0..1), turns (int), stat (str), name (str)
        """
        ctype = card.get("type")
        name = card.get("name", ctype.title())
        power = card.get("power", 0)
        turns = card.get("turns", 0)
        stat = card.get("stat", "")
        ratio = card.get("ratio", None)

        # handle combos that wrap effects
        if ctype == "combo":
            eff = card.get("effect", {})
            if "type" in eff:
                pseudo = {"name": card.get("name"), **eff}
                return self._dispatch(user, target, pseudo)
            else:
                # support multiple keys in combo
                if "damage" in eff:
                    self._dispatch(user, target, {"type": "attack", "name": card.get("name"), "power": eff["damage"]})
                if "heal" in eff:
                    self._dispatch(user, target, {"type": "heal", "name": card.get("name"), "power": eff["heal"]})
                if "buff_damage" in eff:
                    self._dispatch(user, target, {"type": "buff", "name": card.get("name"), "stat": "damage", "power": eff["buff_damage"], "turns": eff.get("turns", 2)})
                if "hot" in eff:
                    hot = eff["hot"]
                    self._dispatch(user, target, {"type": "hot", "name": card.get("name"), "power": hot.get("power"), "turns": hot.get("turns", 2)})
                return

        # normal dispatch
        return self._dispatch(user, target, card)

    def _dispatch(self, user, target, card):
        fn = getattr(self, f"_do_{card.get('type')}", None)
        if fn:
            return fn(user, target, card)
        else:
            self.log(f"[EffectEngine] Unknown card type: {card.get('type')}")

    # -------------------------
    # Handlers
    # -------------------------
    def _do_attack(self, user, target, card):
        base = card.get("power", 0)
        bonus = getattr(user, "total_buff_damage", lambda: 0)()
        dmg = base + bonus
        name = card.get("name", "Attack")

        # Log attacker action
        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] menyerang {self.color_name(target, False)}")

        # Apply damage via centralized handler
        self._apply_damage_with_effects(user, target, dmg)

    def _do_attack_true(self, user, target, card):
        base = card.get("power", 0)
        bonus = getattr(user, "total_buff_damage", lambda: 0)()
        dmg = base + bonus
        name = card.get("name", "True Strike")

        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] menyerang {self.color_name(target, False)} (True)")
        self._apply_damage_with_effects(user, target, dmg, true=True)

    def _do_lifesteal(self, user, target, card):
        power = card.get("power", 0)
        ratio = float(card.get("ratio", 0.5))
        name = card.get("name", "Life Steal")
        
        # LOG serangan dulu, biar kelihatan seperti attack normal
        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] menyerang {self.color_name(target, False)}")

        # Terapkan damage seperti serangan biasa
        damage_dealt = self._apply_damage_with_effects(user, target, card.get("power",0), return_damage=True)

        if damage_dealt > 0:
            heal_amount = int(damage_dealt * ratio)
            if heal_amount > 0:
                user.heal(heal_amount)
                self.log(f"→ {self.color_name(user)} menyerap energi musuh dan memulihkan {heal_amount} HP")
            else:
                self.log("→ Damage terlalu kecil untuk diserap.")
        else:
            self.log("→ Damage terlalu kecil untuk diserap.")

    def _do_heal(self, user, target, card):
        amt = card.get("power", 0)
        name = card.get("name", "Heal")
        healed = user.heal(amt)
        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}]")
        self.log(f"→ {self.color_name(user)} memulihkan {self.color_num(healed, 'heal')} HP")

    def _do_buff(self, user, target, card):
        power = card.get("power", 0)
        stat = card.get("stat", "damage")
        turns = card.get("turns", 1)
        name = card.get("name", "Buff")
        user.add_effect({"kind": "buff", "stat": stat, "power": power, "turns": turns})
        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] → {stat}+{power} selama {turns} turn")

    def _do_defense(self, user, target, card):
        amt = card.get("power", 0)
        name = card.get("name", "Defend")
        user.add_shield(amt)
        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] → Mendapat {self.color_num(amt, 'shield')} shield")

    def _do_dot(self, user, target, card):
        power = card.get("power", 0)
        turns = card.get("turns", 3)
        name = card.get("name", "Poison")

        target.add_effect({"kind": "dot", "power": power, "turns": turns})

        # Karena tick pertama terjadi di turn berikutnya,
        # kita tampilkan jumlah tick aktual (turns - 1)
        tick_count = max(1, turns - 1)
        self.log(
            f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] → "
            f"{self.color_name(target, False)} mendapat DoT {self.color_num(power)} DMG/turn ({tick_count}x tick)")

    def _do_hot(self, user, target, card):
        power = card.get("power", 0)
        turns = card.get("turns", 2)
        name = card.get("name", "Regeneration")

        # Hitungan tick aktual (1 turn pertama = fase persiapan)
        tick_count = max(1, turns - 1)

        user.add_effect({"kind": "hot", "power": power, "turns": turns})

        self.log(
            f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] → "
            f"Regenerasi {self.color_num(power, 'heal')} HP/turn ({tick_count}x tick)")

    def _do_counter(self, user, target, card):
        # store as full-block-single-instance counter: ratio used for possible partial versions later
        turns = card.get("turns", 1)
        # ratio might be provided (e.g., 1.0 for full). support both 'ratio' and 'power' fields.
        ratio = card.get("ratio", None)
        if ratio is None:
            p = card.get("power", None)
            if p is not None and p > 0:
                ratio = float(p) / 100.0 if p > 1 else float(p)
            else:
                ratio = 1.0
        name = card.get("name", "Counter Stance")
        user.add_effect({"kind": "counter", "mode": "full", "ratio": float(ratio), "used": False, "turns": turns})
        pct = int(float(ratio) * 100)
        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] → COUNTER {pct}% aktif selama {turns} turn")

    def _do_reduce(self, user, target, card):
        turns = card.get("turns", 1)
        ratio = card.get("ratio")
        if ratio is None:
            p = card.get("power")
            if p is not None:
                ratio = p / 100.0 if p > 1 else float(p)
            else:
                ratio = 0.2
        name = card.get("name", "Damage Reduce")

        # Pastikan ratio dalam range benar (0–1)
        ratio = max(0.0, min(1.0, float(ratio)))

        user.add_effect({"kind": "reduce", "ratio": ratio, "turns": turns})
        pct = int(ratio * 100)
        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] → REDUCE {pct}% selama {turns} turn")

    def _do_strip(self, user, target, card):
        name = card.get("name", "Strip")
        targets = card.get("targets", ["buff"])  # default: hanya buff
        if "shield" in targets:
            target.shield = 0
            targets = [t for t in targets if t != "shield"]
        if targets:
            target.remove_effects_by_kind(targets)

        targets_str = ", ".join(targets).replace("buff", "buffs").replace("hot", "regen")
        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] → Menghapus {targets_str} dari {self.color_name(target, False)}")

    def _do_clean(self, user, target, card):
        name = card.get("name", "Cleanse")
        user.remove_effects_by_kind(["dot"])
        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] → Membersihkan efek negatif")

    def _do_reflect(self, user, target, card):
        turns = card.get("turns", 1)
        ratio = card.get("ratio", None)

        # fallback jika tidak ada ratio
        if ratio is None:
            p = card.get("power", None)
            if p is not None and p > 0:
                ratio = float(p) / 100.0 if p > 1 else float(p)
            else:
                ratio = 0.25  # default 25%

        name = card.get("name", "Reflect Aura")
        ratio = max(0.0, min(1.0, float(ratio)))  # pastikan aman antara 0–1

        user.add_effect({"kind": "reflect", "ratio": ratio, "turns": turns})
        pct = int(float(ratio) * 100)
        self.log(f"{self.color_name(user)} menggunakan [{Fore.YELLOW}{name}{Style.RESET_ALL}] → REFLECT {pct}% selama {turns} turn")

    # -------------------------
    # Central damage processing (handles counter/reduce/reflect)
    # -------------------------
    def _apply_damage_with_effects(self, attacker, target, damage, true=False, return_damage=False):
        """
        Central routine:
          1) Check for counter (full-block first-hit) on target -> if present, reflect full (or ratio) back to attacker and mark used -> return (target takes no damage)
          2) Apply reduce effects to compute actual damage
          3) Call target.take_damage(actual_damage, source=attacker, true=true)
          4) After damage applied (HP lost), compute reflect percent(s) and apply reflect to attacker (true damage)
        """
        # 1) Counter: check first
        counter = next((e for e in target.effects if e.get("kind") == "counter" and not e.get("used", False)), None)
        if counter:
            # full-block behavior
            ratio = float(counter.get("ratio", 1.0))
            reflected = int(damage * ratio)
            counter["used"] = True
            # optionally remove if turns == 0; leave end_of_turn to expunge or manual
            self.log(f"{Fore.MAGENTA}→ {self.color_name(target, False)} melakukan COUNTER! {self.color_name(attacker)} kehilangan {self.color_num(reflected)} HP{Style.RESET_ALL}")
            # reflect to attacker as true damage to avoid retriggering counters/shields
            attacker.take_damage(reflected, source=target, true=True)
            return  # target takes no damage

        # 2) Reduce (incoming damage)
        reduces = [e for e in target.effects if e.get("kind") == "reduce"]
        total_reduce = sum(e.get("ratio", 0.0) for e in reduces)
        if total_reduce > 0.9:
            total_reduce = 0.9
        actual = damage if true else int(damage * (1.0 - total_reduce))

        # 3) Apply main damage to target (target.take_damage handles shield/hp)
        lost = target.take_damage(actual, source=attacker, true=true)
        self.log(f"{Fore.RED}→ {self.color_name(target, False)} kehilangan {self.color_num(lost)} HP{Style.RESET_ALL}")

        # 4) Reflect percent buffs (after damage applied)
        reflects = [e for e in target.effects if e.get("kind") == "reflect"]
        total_reflect = sum(e.get("ratio", 0.0) for e in reflects)
        if total_reflect > 1.0:
            total_reflect = 1.0
        if lost > 0 and total_reflect > 0:
            reflected_amt = int(lost * total_reflect)
            if reflected_amt > 0:
                self.log(f"{Fore.MAGENTA}→ Damage dipantulkan! {self.color_name(attacker)} kehilangan {self.color_num(reflected_amt)} HP{Style.RESET_ALL}")
                attacker.take_damage(reflected_amt, source=target, true=True)
            else:
                self.log("→ Damage terlalu kecil untuk dipantulkan.")
            
        if return_damage:
            return lost