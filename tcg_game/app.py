# app.py
import streamlit as st
import os
from core.player import Player
from core.battle import Battle
from core.ai.warrior_ai import WarriorAI
from core.ai.mage_ai import MageAI
from core.utils import load_json

# ----------------------------
# BASE PATH & FILES
# ----------------------------
BASE_PATH = os.path.dirname(__file__)
HERO_FILE = os.path.join(BASE_PATH, "data", "test2.json")
ENEMY_FILE = os.path.join(BASE_PATH, "data", "cards_enemy.json")
COMBO_FILE = os.path.join(BASE_PATH, "data", "combos.json")

st.title("⚔️ RPG TCG Battle")

# ----------------------------
# PASTIKAN FILE ADA
# ----------------------------
st.text(f"Hero file exists: {os.path.exists(HERO_FILE)}")
st.text(f"Enemy file exists: {os.path.exists(ENEMY_FILE)}")
st.text(f"Combo file exists: {os.path.exists(COMBO_FILE)}")

if not (os.path.exists(HERO_FILE) and os.path.exists(ENEMY_FILE)):
    st.error("❌ File JSON tidak ditemukan. Pastikan folder data/ ada di repo.")
    st.stop()

# ----------------------------
# MUAT DATA
# ----------------------------
try:
    combos = load_json("data/combos.json")
except Exception:
    combos = []

# ----------------------------
# INISIALISASI PLAYER
# ----------------------------
if "hero" not in st.session_state:
    st.session_state.hero = Player("Hero", HERO_FILE)
if "enemy" not in st.session_state:
    st.session_state.enemy = Player("Enemy", ENEMY_FILE)

# Pilih AI
ai_choice = st.selectbox("Pilih AI Enemy", ["WarriorAI", "MageAI"])
if ai_choice == "WarriorAI":
    ai = WarriorAI()
else:
    ai = MageAI()

# ----------------------------
# MAIN GAME LOOP
# ----------------------------
def next_turn():
    hero = st.session_state.hero
    enemy = st.session_state.enemy

    # Hero pilih kartu dari hand
    hand = hero.deck.hand
    if not hand:
        st.warning("Hero tidak punya kartu di tangan!")
        return

    card_names = [c["name"] for c in hand]
    selected_name = st.session_state.get("selected_card")
    if selected_name not in card_names:
        selected_name = card_names[0]

    # Temukan kartu yg dipilih
    selected_card = next(c for c in hand if c["name"] == selected_name)

    # Play kartu
    hero.deck.play_card_by_obj(selected_card)
    st.write(f"✅ Hero memainkan [{selected_card['name']}]")

    # Enemy giliran AI
    enemy_cards = ai.choose_actions(st.session_state.enemy, st.session_state.hero, combos)
    st.write(f"⚔️ Enemy memainkan {', '.join([c['name'] for c in enemy_cards])}")

    # Jalankan battle resolution
    battle = Battle(hero, enemy)
    battle.combat.resolve_turn(hero, enemy, [selected_card], enemy_cards)

    # Tampilkan HP & Shield
    st.text(f"Hero: HP={hero.hp}, Shield={hero.shield}")
    st.text(f"Enemy: HP={enemy.hp}, Shield={enemy.shield}")

# ----------------------------
# Pilih kartu via selectbox
# ----------------------------
hero = st.session_state.hero
hand_names = [c["name"] for c in hero.deck.hand]
st.selectbox("Pilih kartu untuk dimainkan", hand_names, key="selected_card")

# Tombol Next
st.button("▶️ Next Turn", on_click=next_turn)
