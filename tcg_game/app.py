# app.py
import streamlit as st
import os
from core.player import Player
from core.battle import Battle
from core.ai.warrior_ai import WarriorAI
from core.ai.mage_ai import MageAI
from core.utils import load_json

st.set_page_config(page_title="TGC Battle", layout="wide")

# ---------------------------------------
# Base path & data files
# ---------------------------------------
BASE_PATH = os.path.dirname(__file__)
HERO_FILE = os.path.join(BASE_PATH, "data", "test2.json")
ENEMY_FILE = os.path.join(BASE_PATH, "data", "cards_enemy.json")
COMBO_FILE = os.path.join(BASE_PATH, "data", "combos.json")

# Debug check
st.text(f"BASE PATH: {BASE_PATH}")
st.text(f"Hero file exists: {os.path.exists(HERO_FILE)}")
st.text(f"Enemy file exists: {os.path.exists(ENEMY_FILE)}")

# ---------------------------------------
# Session State: Player & AI init
# ---------------------------------------
if "hero" not in st.session_state:
    st.session_state.hero = Player("Hero", HERO_FILE)
    st.session_state.hero.start_game()

if "enemy" not in st.session_state:
    st.session_state.enemy = Player("Enemy", ENEMY_FILE)
    st.session_state.enemy.start_game()

if "battle" not in st.session_state:
    st.session_state.battle = Battle(st.session_state.hero, st.session_state.enemy)

if "ai" not in st.session_state:
    # bisa pilih WarriorAI / MageAI
    st.session_state.ai = WarriorAI()

# Load combos
if "combos" not in st.session_state:
    st.session_state.combos = load_json(COMBO_FILE)

# ---------------------------------------
# Show Hero hand (click box)
# ---------------------------------------
st.header("Your Hand")
hero_hand = st.session_state.hero.deck.hand
hand_options = [f"{c['name']} ({c['type']}, {c.get('power', 0)})" for c in hero_hand]
selected = st.multiselect("Select cards to play (max 2):", hand_options, max_selections=2)

# Map selected strings back to card objects
selected_cards = []
for s in selected:
    for c in hero_hand:
        desc = f"{c['name']} ({c['type']}, {c.get('power', 0)})"
        if s == desc:
            selected_cards.append(c)

# ---------------------------------------
# Process Turn
# ---------------------------------------
if st.button("Next Turn"):
    hero = st.session_state.hero
    enemy = st.session_state.enemy
    ai = st.session_state.ai
    combos = st.session_state.combos
    battle = st.session_state.battle

    # Hero play selected cards
    hero_played = []
    for c in selected_cards:
        hero.deck.play_card_by_obj(c)
        hero_played.append(c)
    enemy_played = ai.choose_actions(enemy, hero, combos)

    # Resolve turn
    battle.combat.resolve_turn(hero, enemy, hero_played, enemy_played)

    # End of turn effects
    hero.end_of_turn_effects()
    enemy.end_of_turn_effects()
    hero.begin_turn()
    enemy.begin_turn()

    # Clear selected for next turn
    selected.clear()
    st.experimental_rerun()

# ---------------------------------------
# Display Status
# ---------------------------------------
st.subheader("Hero Status")
st.write(f"HP: {st.session_state.hero.hp}/{st.session_state.hero.max_hp}")
st.write(f"MP: {st.session_state.hero.mp}/{st.session_state.hero.max_mp}")
st.write(f"Shield: {st.session_state.hero.shield}")
st.write("Effects:", st.session_state.hero.effects)

st.subheader("Enemy Status")
st.write(f"HP: {st.session_state.enemy.hp}/{st.session_state.enemy.max_hp}")
st.write(f"MP: {st.session_state.enemy.mp}/{st.session_state.enemy.max_mp}")
st.write(f"Shield: {st.session_state.enemy.shield}")
st.write("Effects:", st.session_state.enemy.effects)

# ---------------------------------------
# Show Hero Hand
# ---------------------------------------
st.subheader("Hero Hand")
for i, c in enumerate(st.session_state.hero.deck.hand):
    st.write(f"{i+1}. {c['name']} ({c['type']}, {c.get('power', 0)})")
