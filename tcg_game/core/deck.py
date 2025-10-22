# --------------------------- core/deck.py (RPG Style + Verbose Mode) ---------------------------
import json
import random
import os
import uuid
from colorama import Fore, Style


class Deck:
    def __init__(self, card_file):
        base = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(base, card_file) if not os.path.isabs(card_file) else card_file

        with open(path, "r", encoding="utf-8") as f:
            self.cards = json.load(f)[:]  # list of card dicts

        # Tambahkan template ID unik
        for c in self.cards:
            if "template_id" not in c:
                c["template_id"] = str(uuid.uuid4())[:8]

        random.shuffle(self.cards)
        self.hand = []
        self.discard = []

    # -------------------------------------------------
    # Basic deck operations
    # -------------------------------------------------
    def shuffle(self):
        random.shuffle(self.cards)

    def _make_instance(self, card_template):
        inst = card_template.copy()
        inst["id"] = str(uuid.uuid4())[:8]
        return inst

    def draw(self, n=1):
        drawn = []
        for _ in range(n):
            # 🔹 Pastikan ada kartu untuk digacha
            if not self.cards:
                break

            # 🔹 Gunakan rate sebagai bobot (default = 1 kalau tidak ada)
            weights = [c.get("rate", 1) for c in self.cards]
            template = random.choices(self.cards, weights=weights, k=1)[0]

            # 🔹 Buat instance unik kartu
            inst = self._make_instance(template)
            self.hand.append(inst)
            drawn.append(inst)

        return drawn


    def draw_starting(self, n=5):
        return self.draw(n)

    # -------------------------------------------------
    # Play / remove cards
    # -------------------------------------------------
    def play_card(self, index):
        if 0 <= index < len(self.hand):
            card = self.hand.pop(index)
            self.discard.append(card)
            return card
        raise IndexError("card index out of range")

    def play_card_by_obj(self, card_obj):
        if card_obj in self.hand:
            self.hand.remove(card_obj)
            self.discard.append(card_obj)
            return card_obj
        raise ValueError("card object not found in hand")

    def remove_card_by_name(self, name, amount=1):
        removed = 0
        for card in list(self.hand):
            if card.get("name") == name:
                self.hand.remove(card)
                self.discard.append(card)
                removed += 1
                if removed >= amount:
                    break

    def play_card_by_name(self, name, amount=1):
        removed = []
        for card in list(self.hand):
            if card.get("name") == name and len(removed) < amount:
                self.hand.remove(card)
                self.discard.append(card)
                removed.append(card)
        return removed

    # -------------------------------------------------
    # Show hand (RPG-Style + Debug Option)
    # -------------------------------------------------
    def show_hand(self, verbose=False):
        if not self.hand:
            print("  (kosong)")
            return

        print(f"{Fore.LIGHTWHITE_EX}=== Kartu di tangan ==={Style.RESET_ALL}")
        for i, c in enumerate(self.hand, start=1):
            name = c.get("name")
            ctype = c.get("type")
            power = c.get("power", 0)
            desc = c.get("description", "")
            turns = c.get("turns", None)
            ratio = c.get("ratio", None)

            # 🎨 Warna berdasarkan tipe
            color = {
                "attack": Fore.RED,
                "attack_true": Fore.LIGHTRED_EX,
                "defense": Fore.CYAN,
                "heal": Fore.GREEN,
                "hot": Fore.LIGHTGREEN_EX,
                "dot": Fore.MAGENTA,
                "buff": Fore.YELLOW,
                "reduce": Fore.BLUE,
                "reflect": Fore.LIGHTMAGENTA_EX,
                "counter": Fore.LIGHTYELLOW_EX,
                "strip": Fore.LIGHTBLACK_EX,
                "clean": Fore.LIGHTWHITE_EX,
                "lifesteal": Fore.LIGHTRED_EX,
            }.get(ctype, Fore.WHITE)

            # 🧩 Detail tambahan (turns, ratio, dmg/tick)
            detail = ctype
            if ctype in ("dot", "hot") and turns is not None:
                tick_count = max(1, turns - 1)
                detail += f", {power} dmg, {tick_count}x tick"
            elif turns is not None:
                detail += f", {turns}t"
            elif ratio is not None:
                pct = int(float(ratio) * 100)
                detail += f", {pct}%"
            else:
                detail += f", power {power}"

            # ✨ Output gaya RPG-style
            print(f"  {i}. {color}{name}{Style.RESET_ALL} ({detail}) - {desc}")

            # 🧠 Mode verbose: tampilkan info internal
            if verbose:
                cid = c.get("id", "-")
                tid = c.get("template_id", "-")
                print(f"     ↳ ID: {cid} | template: {tid} | turns: {turns}")

        print(f"{Fore.LIGHTWHITE_EX}=======================\n{Style.RESET_ALL}")
