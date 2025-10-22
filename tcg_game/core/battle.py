# core/battle.py
# Battle loop v2: MP regen model, combo-as-option (require-count), multi-play while MP remains.
import random
from colorama import Fore, Style, init
from core.utils import load_json
from core.effects import EffectEngine
from core.logger import BattleLogger
from core.combat_manager import CombatManager

init(autoreset=True)

class Battle:
    def __init__(self, player, enemy, ai=None):
        self.player = player
        self.enemy = enemy
        self.ai = ai
        # combos.json expected to contain list of combos with "require", "effect", and optional "mp_cost"
        self.combos = load_json("data/combos.json") if self._try_load_combo() else []
        self.logger = BattleLogger()
        self.effects = EffectEngine(logger=self.logger)
        self.combat = CombatManager(self.effects, logger=self.logger)

    def _try_load_combo(self):
        try:
            load_json("data/combos.json")
            return True
        except Exception:
            return False

    # ================================
    # MAIN BATTLE LOOP
    # ================================
    def start(self):
        self.logger.log(f"\n{Fore.CYAN}⚔️  Battle Start!{Style.RESET_ALL}")
        turn = 1
        self.player.start_game()
        self.enemy.start_game()

        while self.player.hp > 0 and self.enemy.hp > 0:
            
            self.player.begin_turn()
            self.enemy.begin_turn()
            
            self.logger.log(f"\n=== TURN {turn} ===")
            self.show_status()

            # begin turn (MP regen & refill handled inside player.begin_turn)
            #self.player.begin_turn()
            #self.enemy.begin_turn()

            # player actions: now allow multiple plays until MP exhausted or player stops
            player_cards = self.player_select_actions()
            enemy_cards = self.enemy_select_actions()

            self.logger.log(f"\n{Fore.YELLOW}--- Resolving turn ---{Style.RESET_ALL}")
            # resolve with CombatManager - it expects lists of card dicts
            self.combat.resolve_turn(self.player, self.enemy, player_cards, enemy_cards)

            # end of turn effects processing (dot/hot decrement, etc.)
            self.player.end_of_turn_effects()
            self.enemy.end_of_turn_effects()
            turn += 1

        self.logger.log("\n=== Battle End ===")
        if self.player.hp <= 0 and self.enemy.hp <= 0:
            self.logger.log("⚖️  Draw!")
        elif self.player.hp <= 0:
            self.logger.log(f"{Fore.RED}{self.enemy.name} wins!{Style.RESET_ALL}")
        else:
            self.logger.log(f"{Fore.GREEN}{self.player.name} wins!{Style.RESET_ALL}")

    # ================================
    # STATUS DISPLAY (kept similar)
    # ================================
    def show_status(self):
        def eff_string(effects):
            parts = []
            for e in effects:
                kind = e.get("kind")
                power = e.get("power")
                stat = e.get("stat", "")
                turns = int(e.get("turns", 0) or 0)
                ratio = e.get("ratio", None)

                color_map = {
                    "buff": Fore.YELLOW,
                    "hot": Fore.GREEN,
                    "dot": Fore.RED,
                    "reduce": Fore.CYAN,
                    "reflect": Fore.MAGENTA,
                    "counter": Fore.MAGENTA,
                }
                color = color_map.get(kind, Fore.WHITE)
                inner = kind
                if kind == "counter":
                    if turns:
                        inner += f", {turns}t"
                elif ratio is not None:
                    pct = int(float(ratio) * 100)
                    inner += f", {pct}%"
                    if turns:
                        inner += f", {turns}t"
                elif stat and power is not None:
                    inner += f", {stat}+{power}"
                    if turns:
                        inner += f", {turns}t"
                elif power is not None:
                    inner += f", {power}"
                    if turns:
                        inner += f", {turns}t"

                parts.append(f"{color}{inner}{Style.RESET_ALL}")
            return " | ".join(parts) if parts else "-"

        self.logger.log(
            f"\n{Fore.CYAN}{self.player.name}:{Style.RESET_ALL} {Fore.GREEN}{self.player.hp} HP{Style.RESET_ALL} "
            f"{Fore.WHITE}| Shield {self.player.shield}{Style.RESET_ALL} | MP {self.player.mp}/{self.player.max_mp} | {eff_string(self.player.effects)}"
        )
        self.logger.log(
            f"{Fore.RED}{self.enemy.name}:{Style.RESET_ALL} {Fore.GREEN}{self.enemy.hp} HP{Style.RESET_ALL} "
            f"{Fore.WHITE}| Shield {self.enemy.shield}{Style.RESET_ALL} | MP {self.enemy.mp}/{self.enemy.max_mp} | {eff_string(self.enemy.effects)}"
        )

    # ====================================================
    # PLAYER ACTION SELECTION (multi-play while MP)
    # ====================================================
    def player_select_actions(self):
        chosen = []
        # loop until player decides to stop or MP exhausted or no playable cards
        while True:
            # build current available combos based on hand counts
            combos = self.check_available_combos(self.player.deck.hand)
            # show prompt and available choices
            card = self.select_action_once(len(chosen) + 1, combos_available=combos)
            # if None returned => stop selection
            if card is None:
                break

            # card chosen might be a combo dict or a normal card dict
            cost = int(card.get("mp_cost", card.get("cost", 0)))
            if cost > self.player.mp:
                print(f"{Fore.RED}MP tidak cukup untuk {card.get('name')} ({cost} MP){Style.RESET_ALL}")
                # if we popped from hand earlier, return it back handled in select_action_once
                # continue selection
                continue

           # if this is a combo, we must consume required cards from hand (player.deck.remove_card_by_name)
            if card.get("type") == "combo" and "require" in card:
                for req_name, qty in card["require"].items():
                    removed_cards = self.player.deck.play_card_by_name(req_name, amount=qty)
                    if len(removed_cards) < qty:
                        print(f"{Fore.RED}Error: not enough {req_name} cards in hand for combo.{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.GREEN}Combo '{card['name']}' aktif! Mengonsumsi {qty}x {req_name}.{Style.RESET_ALL}")
                # record combo in history as one played item
                self.player.turn_history.append(card.get("name"))
                # deduct MP
                self.player.mp -= cost
                chosen.append(card)

            else:
                # normal card; remove it from hand and record history
                # select_action_once already removed the card from hand when returning it (see implementation)
                self.player.turn_history.append(card.get("name"))
                self.player.mp -= cost
                chosen.append(card)

            # stop conditions
            if self.player.mp <= 0:
                print("MP habis.")
                break
            if not self.player.deck.hand:
                print("Tidak ada kartu tersisa di tangan.")
                break

            # allow player to stop anytime
            cont = input("Main kartu lagi? (y/n): ").strip().lower()
            if cont != "y":
                break

        return chosen

    def select_action_once(self, index, combos_available=None):
        """
        Shows hand + combos (if any). Returns:
         - dict for normal card (it will remove it from hand here if playable)
         - dict for combo (constructed with type 'combo') but DO NOT remove required cards here,
           removing is handled later when combo is actually confirmed to be played.
         - None to indicate stop/invalid
        """
        hand = self.player.deck.hand
        combos = combos_available or self.check_available_combos(hand)

        print(f"\nPilih aksi ke-{index}: (MP tersisa: {self.player.mp})")
        for i, c in enumerate(hand, 1):
            name = c.get("name", "Unknown")
            ctype = c.get("type", "unknown")
            power = c.get("power", 0)
            stat = c.get("stat", "")
            ratio = c.get("ratio", None)
            turns = int(c.get("turns", 0) or 0)
            desc = c.get("description", "")
            cost = c.get("mp_cost", c.get("cost", 0))

            # color mapping (same as before)
            color_map = {
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
            }
            color = color_map.get(ctype, Fore.WHITE)

            # detail string
            detail = f"{ctype}"
            if ctype == "dot" and turns > 0:
                tick_count = max(1, turns - 1)
                detail += f", {power} dmg, {tick_count}x tick"
            elif ctype == "hot" and turns > 0:
                tick_count = max(1, turns - 1)
                detail += f", {power} HP, {tick_count}x tick"
            elif ctype == "reduce" and ratio is not None:
                pct = int(float(ratio) * 100)
                detail += f", {pct}%, {turns}t"
            elif ctype == "reflect" and ratio is not None:
                pct = int(float(ratio) * 100)
                detail += f", {pct}%, {turns}t"
            elif ctype == "buff":
                if stat:
                    detail += f", {stat}+{power}, {turns}t"
                else:
                    detail += f", +{power}, {turns}t"
            elif ctype == "counter":
                label = "time" if turns == 1 else "times"
                detail += f", {turns}{label}"
            elif turns > 0:
                detail += f", {turns}t"
            else:
                detail += f", power {power}"

            print(f"  {color}{i}. {name}{Style.RESET_ALL} (cost {cost} MP) - {detail} - {desc}")

        # show combos as extra options
        if combos:
            print(f"\n{Fore.MAGENTA}--- Combo tersedia ---{Style.RESET_ALL}")
            for j, combo in enumerate(combos, 1):
                mp_cost = combo.get("mp_cost", combo.get("cost", 0))
                print(f"{Fore.MAGENTA}{len(hand)+j}. ✨ {combo['name']} (cost {mp_cost} MP){Style.RESET_ALL} - {combo.get('effect', {}).get('description','')}")


        # read input
        try:
            choice = input("Pilih nomor kartu (atau tekan Enter untuk selesai): ").strip()
            if choice == "":
                return None
            choice = int(choice)
        except ValueError:
            print("Input tidak valid.")
            return None

        # normal card chosen
        if 1 <= choice <= len(hand):
            sel_idx = choice - 1
            card = hand[sel_idx]
            cost = int(card.get("mp_cost", card.get("cost", 0)))
            if cost > self.player.mp:
                print(f"{Fore.RED}MP tidak cukup untuk kartu ini ({cost} MP).{Style.RESET_ALL}")
                return None
            # remove card from hand and return it
            return hand.pop(sel_idx)

        # combo chosen
        elif combos and len(hand) < choice <= len(hand) + len(combos):
            combo = combos[choice - len(hand) - 1]
            mp_cost = int(combo.get("mp_cost", combo.get("cost", 0)))
            if mp_cost > self.player.mp:
                print(f"{Fore.RED}MP tidak cukup untuk combo {combo['name']} ({mp_cost} MP).{Style.RESET_ALL}")
                return None
            # return a shallow combo dict (do not consume required cards here)
            combo_copy = combo.copy()
            combo_copy["type"] = "combo"
            return combo_copy
        else:
            print("Pilihan tidak valid.")
            return None

    # ====================================================
    # ENEMY ACTION SELECTION (AI-aware, plays until MP exhausted)
    # ====================================================
    def enemy_select_actions(self):
        if self.ai:
            # AI must be updated to use MP model; fallback to ai.choose_actions
            return self.ai.choose_actions(self.enemy, self.player, self.combos)

        chosen = []
        hand = self.enemy.deck.hand

        # simple AI: greedily play highest power cards/combo while MP available
        while True:
            # get combos available to enemy
            combos = self.check_available_combos(hand)
            played = False
            # try use combo if enemy has enough MP and combo is available
            for combo in combos:
                cost = int(combo.get("mp_cost", combo.get("cost", 0)))
                if cost <= self.enemy.mp:
                    # consume required cards
                    for req, amt in combo["require"].items():
                        for _ in range(amt):
                            self.enemy.deck.remove_card_by_name(req)
                    self.enemy.mp -= cost
                    chosen.append({"name": combo["name"], "type": "combo", "effect": combo["effect"], "mp_cost": cost})
                    played = True
                    break
            if played:
                # update hand reference after consumption
                hand = self.enemy.deck.hand
                continue

            # otherwise, play highest-power card that fits MP
            playable = [c for c in hand if int(c.get("mp_cost", c.get("cost", 0))) <= self.enemy.mp]
            if not playable:
                break
            # choose highest power (ties arbitrary)
            play_card = max(playable, key=lambda c: c.get("power", 0))
            # remove and play
            try:
                hand.remove(play_card)
            except ValueError:
                pass
            cost = int(play_card.get("mp_cost", play_card.get("cost", 0)))
            self.enemy.mp -= cost
            chosen.append(play_card)

            # continue until no MP or no playable cards
            if self.enemy.mp <= 0 or not hand:
                break

        return chosen

    # ====================================================
    # COMBO CHECKER (unchanged logic - require based)
    # ====================================================
    def check_available_combos(self, hand):
        combos_available = []
        hand_names = [c["name"] for c in hand]
        for combo in self.combos:
            valid = True
            for req, amt in combo["require"].items():
                if hand_names.count(req) < amt:
                    valid = False
                    break
            if valid:
                combos_available.append(combo)
        return combos_available
