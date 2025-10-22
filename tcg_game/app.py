#====================== app.py ======================
import streamlit as st
import os
from core.player import Player
from core.battle import Battle
from core.ai.warrior_ai import WarriorAI
from core.ai.mage_ai import MageAI

# -----------------------
# Setup paths
# -----------------------
BASE_PATH = os.getcwd()
HERO_FILE = os.path.join(BASE_PATH, "data", "test2.json")
ENEMY_FILE = os.path.join(BASE_PATH, "data", "cards_enemy.json")

st.write("BASE PATH:", BASE_PATH)
st.write("HERO FILE EXISTS:", os.path.exists(HERO_FILE))
st.write("ENEMY FILE EXISTS:", os.path.exists(ENEMY_FILE))

if not os.path.exists(HERO_FILE) or not os.path.exists(ENEMY_FILE):
    st.error("JSON file hero atau enemy tidak ditemukan! Pastikan ada di folder 'data/'")
    st.stop()

# -----------------------
# Initialize session state
# -----------------------
if "hero" not in st.session_state:
    st.session_state.hero = Player("Hero", HERO_FILE)
    st.session_state.hero.start_game()

if "enemy" not in st.session_state:
    st.session_state.enemy = Player("Enemy", ENEMY_FILE)
    st.session_state.enemy.start_game()

if "battle" not in st.session_state:
    st.session_state.battle = Battle(st.session_state.hero, st.session_state.enemy)

# -----------------------
# AI Setup
# -----------------------
AI_CHOICE = st.radio("Pilih AI musuh:", ("WarriorAI", "MageAI"))
if "ai" not in st.session_state or st.session_state.ai_name != AI_CHOICE:
    if AI_CHOICE == "WarriorAI":
        st.session_state.ai = WarriorAI()
    else:
        st.session_state.ai = MageAI()
    st.session_state.ai_name = AI_CHOICE

# -----------------------
# Display hands
# -----------------------
st.subheader("Kartu Hero")
hero_hand = st.session_state.hero.deck.hand
selected_indices = st.multiselect("Pilih kartu yang akan dimainkan:", list(range(len(hero_hand))),
                                  format_func=lambda i: f"{i+1}. {hero_hand[i]['name']} ({hero_hand[i]['type']})")

st.subheader("Kartu Musuh")
enemy_hand = st.session_state.enemy.deck.hand
st.write([f"{c['name']} ({c['type']})" for c in enemy_hand])

# -----------------------
# Next Turn Button
# -----------------------
if st.button("Next Turn"):
    hero = st.session_state.hero
    enemy = st.session_state.enemy
    ai = st.session_state.ai

    # -------------------
    # Pilih kartu Hero
    # -------------------
    hero_cards = [hero_hand[i] for i in selected_indices]

    # -------------------
    # Pilih kartu AI
    # -------------------
    combos = {}  # bisa diisi combo data jika ada
    enemy_cards = ai.choose_actions(enemy, hero, combos)

    # -------------------
    # Resolve turn
    # -------------------
    st.session_state.battle.resolve_turn(hero, enemy, hero_cards, enemy_cards)

    # -------------------
    # End turn effects
    # -------------------
    hero.end_of_turn_effects()
    enemy.end_of_turn_effects()

    # -------------------
    # Refill hands
    # -------------------
    hero.begin_turn()
    enemy.begin_turn()

    # -------------------
    # Status update
    # -------------------
    st.write(f"Hero HP: {hero.hp} | Shield: {hero.shield} | MP: {hero.mp}")
    st.write(f"Enemy HP: {enemy.hp} | Shield: {enemy.shield} | MP: {enemy.mp}")

