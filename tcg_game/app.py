import streamlit as st
from core.player import Player
from core.battle import Battle
from core.ai.warrior_ai import WarriorAI
from core.effects import EffectEngine
from core.combat_manager import CombatManager
from core.logger import BattleLogger

st.set_page_config(page_title="TCG RPG Streamlit", layout="wide")
st.title("🃏 RPG TCG Turn-Based Demo")

# -----------------------
# INIT (run once)
# -----------------------
if "initialized" not in st.session_state:
    st.session_state.hero = Player("Hero", "data/test2.json")
    st.session_state.enemy = Player("Enemy", "data/cards_enemy.json")
    st.session_state.logger = BattleLogger()
    st.session_state.effects = EffectEngine(st.session_state.logger)
    st.session_state.combat = CombatManager(st.session_state.effects, st.session_state.logger)
    st.session_state.ai = WarriorAI()  # Enemy AI
    st.session_state.turn = 1
    st.session_state.log_lines = []
    st.session_state.hero.start_game()
    st.session_state.enemy.start_game()
    st.session_state.initialized = True

hero = st.session_state.hero
enemy = st.session_state.enemy
logger = st.session_state.logger
combat = st.session_state.combat
ai = st.session_state.ai

# -----------------------
# Sidebar: Player stats
# -----------------------
st.sidebar.header(f"{hero.name} Status")
st.sidebar.text(f"HP: {hero.hp}/{hero.max_hp}")
st.sidebar.text(f"MP: {hero.mp}/{hero.max_mp}")
st.sidebar.text(f"Shield: {hero.shield}")
st.sidebar.text(f"Effects: {hero.effects}")

st.sidebar.header(f"{enemy.name} Status")
st.sidebar.text(f"HP: {enemy.hp}/{enemy.max_hp}")
st.sidebar.text(f"Shield: {enemy.shield}")
st.sidebar.text(f"Effects: {enemy.effects}")

# -----------------------
# Player action
# -----------------------
st.subheader(f"Turn {st.session_state.turn} - Pilih kartu untuk dimainkan")
hand_options = {f"{i+1}. {c.get('name')} ({c.get('type')})": c for i, c in enumerate(hero.deck.hand)}

selected_card_name = st.selectbox("Pilih kartu:", list(hand_options.keys()))
play_button = st.button("Mainkan kartu")

if play_button:
    # Ambil kartu yang dipilih
    card_to_play = hand_options[selected_card_name]
    hero.deck.play_card_by_obj(card_to_play)
    st.session_state.log_lines.append(f"{hero.name} memainkan {card_to_play.get('name')}")

    # Enemy AI pilih kartu
    enemy_cards = ai.choose_actions(enemy, hero, combos)
    enemy.deck.play_card_by_obj(enemy_card)
    st.session_state.log_lines.append(f"{enemy.name} memainkan {enemy_card.get('name')}")

    # Jalankan combat manager
    combat.resolve_turn(hero, enemy, [card_to_play], [enemy_card])

    # Begin next turn
    hero.begin_turn()
    enemy.begin_turn()
    st.session_state.turn += 1

# -----------------------
# Show Hand
# -----------------------
st.subheader("Kartu di tangan:")
for c in hero.deck.hand:
    st.text(f"- {c.get('name')} ({c.get('type')}, Power {c.get('power')})")

# -----------------------
# Show Log
# -----------------------
st.subheader("Log Battle")
for line in logger.logs:
    st.text(line)
