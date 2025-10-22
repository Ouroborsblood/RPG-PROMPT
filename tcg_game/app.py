#===================== app.py =====================
import streamlit as st
import os
from core.player import Player
from core.battle import Battle
from core.ai.warrior_ai import WarriorAI
from core.effects import EffectEngine
from core.logger import BattleLogger

# -----------------------
# Setup path
# -----------------------
base_path = os.path.dirname(__file__)
hero_file = os.path.join(base_path, "data", "test2.json")
enemy_file = os.path.join(base_path, "data", "cards_enemy.json")

# -----------------------
# Initialize session state
# -----------------------
if "hero" not in st.session_state:
    st.session_state.hero = Player("Hero", hero_file)
    st.session_state.hero.start_game()

if "enemy" not in st.session_state:
    st.session_state.enemy = Player("Enemy", enemy_file)
    st.session_state.enemy.start_game()

if "log" not in st.session_state:
    st.session_state.log = []

# -----------------------
# Battle and effects
# -----------------------
effects = EffectEngine()
logger = BattleLogger()
ai = WarriorAI()

# -----------------------
# Sidebar: show stats
# -----------------------
st.sidebar.header("Stats")
st.sidebar.text(f"HP: {st.session_state.hero.hp}/{st.session_state.hero.max_hp}")
st.sidebar.text(f"MP: {st.session_state.hero.mp}/{st.session_state.hero.max_mp}")
st.sidebar.text(f"Shield: {st.session_state.hero.shield}")
st.sidebar.text(f"Effects: {st.session_state.hero.effects}")

st.sidebar.markdown("---")
st.sidebar.text(f"Enemy HP: {st.session_state.enemy.hp}/{st.session_state.enemy.max_hp}")
st.sidebar.text(f"Enemy Shield: {st.session_state.enemy.shield}")
st.sidebar.text(f"Enemy Effects: {st.session_state.enemy.effects}")

# -----------------------
# Show hand with checkboxes
# -----------------------
st.header("Pilih Kartu yang Akan Digunakan")
hand = st.session_state.hero.deck.hand
selected_indices = []

for i, card in enumerate(hand):
    checked = st.checkbox(f"{card['name']} ({card['type']}, power {card.get('power',0)})", key=f"card_{card['id']}")
    if checked:
        selected_indices.append(i)

# -----------------------
# Next Turn button
# -----------------------
if st.button("Next Turn"):
    hero = st.session_state.hero
    enemy = st.session_state.enemy

    # Hero plays selected cards
    hero_cards = [hero.deck.play_card_by_obj(hand[i]) for i in selected_indices]
    hero.begin_turn()  # regen MP, draw cards, apply hot/dot
    enemy_cards = ai.choose_actions(enemy, hero, combos=[])  # combos empty for now

    # Combat resolution
    battle = Battle(hero, enemy)
    battle.combat.resolve_turn(hero, enemy, hero_cards, enemy_cards)

    # End-of-turn effects
    hero.end_of_turn_effects()
    enemy.end_of_turn_effects()

    # Log update
    st.session_state.log.extend(logger.logs)
    logger.logs.clear()

# -----------------------
# Show battle log
# -----------------------
st.header("Battle Log")
for msg in st.session_state.log[-20:]:
    st.write(msg)

# -----------------------
# Show current hand
# -----------------------
st.header("Hand saat ini")
for c in st.session_state.hero.deck.hand:
    st.write(f"{c['name']} ({c['type']}, power {c.get('power',0)})")
