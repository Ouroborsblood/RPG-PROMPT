# app.py
import os
import streamlit as st
from core.player import Player
from core.battle import Battle
from core.ai.warrior_ai import WarriorAI
from core.ai.mage_ai import MageAI
from core.logger import BattleLogger
from core.utils import load_json

# ----------------------
# Paths
# ----------------------
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
HERO_FILE = os.path.join(BASE_PATH, "data/test2.json")
ENEMY_FILE = os.path.join(BASE_PATH, "data/cards_enemy.json")
COMBO_FILE = os.path.join(BASE_PATH, "data/combos.json")

# ----------------------
# Load combos
# ----------------------
try:
    combos = load_json("data/combos.json")
except Exception:
    combos = []

# ----------------------
# Session state
# ----------------------
if "logger" not in st.session_state:
    st.session_state.logger = BattleLogger()

if "hero" not in st.session_state:
    st.session_state.hero = Player("Hero", HERO_FILE)

if "enemy" not in st.session_state:
    st.session_state.enemy = Player("Enemy", ENEMY_FILE)

if "ai" not in st.session_state:
    st.session_state.ai = WarriorAI()

if "battle" not in st.session_state:
    st.session_state.battle = Battle(
        st.session_state.hero,
        st.session_state.enemy
    )

if "turn" not in st.session_state:
    st.session_state.turn = 1

# ----------------------
# Streamlit layout
# ----------------------
st.title("RPG TCG Battle")
st.subheader(f"Turn: {st.session_state.turn}")

hero = st.session_state.hero
enemy = st.session_state.enemy
battle = st.session_state.battle
ai = st.session_state.ai
logger = st.session_state.logger

# ----------------------
# Show status
# ----------------------
st.markdown(f"**Hero:** HP={hero.hp}/{hero.max_hp}, MP={hero.mp}/{hero.max_mp}, Shield={hero.shield}")
st.markdown(f"**Enemy:** HP={enemy.hp}/{enemy.max_hp}, MP={enemy.mp}/{enemy.max_mp}, Shield={enemy.shield}")

# ----------------------
# Hero hand
# ----------------------
st.markdown("### Hero Hand")
for i, card in enumerate(hero.deck.hand):
    st.markdown(f"{i+1}. {card['name']} ({card['type']}, Power={card.get('power',0)})")

# ----------------------
# Player selects card
# ----------------------
card_idx = st.selectbox("Pilih kartu untuk dimainkan (Hero)", list(range(len(hero.deck.hand))), format_func=lambda x: hero.deck.hand[x]['name'] if hero.deck.hand else "Kosong")

if st.button("Next Turn"):
    # Hero plays
    if hero.deck.hand:
        card_obj = hero.deck.hand[card_idx]
        hero.deck.play_card_by_obj(card_obj)
        battle.effect_engine.apply(hero, enemy, card_obj)

    # Enemy AI plays
    enemy_cards = ai.choose_actions(enemy, hero, combos)
    for c in enemy_cards:
        battle.effect_engine.apply(enemy, hero, c)

    # End of turn effects
    hero.end_of_turn_effects()
    enemy.end_of_turn_effects()

    # Begin next turn
    hero.begin_turn()
    enemy.begin_turn()
    st.session_state.turn += 1

# ----------------------
# Show last logs
# ----------------------
st.markdown("### Battle Log")
for log_entry in logger.logs[-10:]:
    st.text(log_entry)
