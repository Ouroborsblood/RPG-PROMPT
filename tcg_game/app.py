#================ app.py =================
import streamlit as st
import os
from core.player import Player
from core.battle import Battle
from core.ai.warrior_ai import WarriorAI
from core.ai.mage_ai import MageAI
from core.logger import BattleLogger

# ------------------ Paths ------------------
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
HERO_FILE = os.path.join(BASE_PATH, "data/test2.json")
ENEMY_FILE = os.path.join(BASE_PATH, "data/cards_enemy.json")

# Cek file
if not os.path.exists(HERO_FILE) or not os.path.exists(ENEMY_FILE):
    st.error("JSON file hero atau enemy tidak ditemukan! Pastikan ada di folder 'data/'")
    st.stop()

# ------------------ Session State ------------------
if "hero" not in st.session_state:
    st.session_state.hero = Player("Hero", HERO_FILE)

if "enemy" not in st.session_state:
    st.session_state.enemy = Player("Enemy", ENEMY_FILE)

if "logger" not in st.session_state:
    st.session_state.logger = BattleLogger()

if "battle" not in st.session_state:
    st.session_state.battle = Battle(
        st.session_state.hero, 
        st.session_state.enemy, 
        logger=st.session_state.logger
    )

if "ai" not in st.session_state:
    st.session_state.ai = WarriorAI()  # bisa diganti MageAI()

# ------------------ Run Battle ------------------
st.title("🃏 RPG TCG Streamlit Minimal")

if st.button("Start / Next Turn"):
    battle = st.session_state.battle
    hero = st.session_state.hero
    enemy = st.session_state.enemy
    ai = st.session_state.ai

    # Jalankan turn AI vs Hero
    # Hero main otomatis 1 kartu pertama dari hand
    if hero.deck.hand:
        card = hero.deck.hand.pop(0)
        battle.combat.effects.apply(hero, enemy, card)
        st.session_state.logger.log(f"{hero.name} played {card.get('name')}!")

    # Enemy turn
    enemy_cards = ai.choose_actions(enemy, hero, combos=[])
    for c in enemy_cards:
        battle.combat.effects.apply(enemy, hero, c)
    st.session_state.logger.log(f"{enemy.name} finished its turn.")

# ------------------ Show Log ------------------
st.write("### Game Log")
for line in st.session_state.logger.logs:
    st.text(line)

# ------------------ Show Status ------------------
st.write("---")
st.write(f"**Hero**: HP {hero.hp}/{hero.max_hp} | Shield {hero.shield} | MP {hero.mp}/{hero.max_mp}")
st.write(f"**Enemy**: HP {enemy.hp}/{enemy.max_hp} | Shield {enemy.shield}")
