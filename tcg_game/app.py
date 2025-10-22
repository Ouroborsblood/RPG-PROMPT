#====================== app.py ======================
import streamlit as st
import os
from core.player import Player
from core.battle import Battle
from core.ai.warrior_ai import WarriorAI
from core.ai.mage_ai import MageAI

# -------------------- Setup Paths --------------------
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
HERO_FILE = os.path.join(BASE_PATH, "data/test2.json")
ENEMY_FILE = os.path.join(BASE_PATH, "data/cards_enemy.json")

# Pastikan file ada
if not os.path.exists(HERO_FILE) or not os.path.exists(ENEMY_FILE):
    st.error("JSON file hero atau enemy tidak ditemukan! Pastikan ada di folder 'data/'")
    st.stop()

# -------------------- Session State --------------------
if "hero" not in st.session_state:
    st.session_state.hero = Player("Hero", HERO_FILE)

if "enemy" not in st.session_state:
    st.session_state.enemy = Player("Enemy", ENEMY_FILE)

if "battle" not in st.session_state:
    st.session_state.battle = Battle(st.session_state.hero, st.session_state.enemy)

if "ai" not in st.session_state:
    # Pilih AI yang diinginkan
    st.session_state.ai = WarriorAI()  # bisa diganti MageAI()

if "log" not in st.session_state:
    st.session_state.log = []

# -------------------- Helper --------------------
def add_log(msg):
    st.session_state.log.append(msg)
    st.experimental_rerun()  # refresh UI supaya log tampil

def show_hand_with_click(player):
    st.write(f"### {player.name}'s Hand (MP: {player.mp}/{player.max_mp})")
    hand = player.deck.hand
    if not hand:
        st.write("*(Kosong)*")
        return None

    choices = []
    for i, c in enumerate(hand):
        name = c.get("name")
        cost = c.get("power")  # asumsi power = MP cost
        ctype = c.get("type")
        desc = c.get("description", "")
        label = f"{name} ({ctype}, power {cost}) - {desc}"
        choices.append(label)

    selected_index = st.radio("Pilih kartu untuk dimainkan:", list(range(len(hand))), format_func=lambda x: choices[x])
    return selected_index

# -------------------- Main UI --------------------
st.title("🃏 RPG TCG Streamlit")

# Tampilkan HP, Shield, Effects
hero = st.session_state.hero
enemy = st.session_state.enemy

st.write(f"**Hero**: HP {hero.hp}/{hero.max_hp} | Shield {hero.shield} | MP {hero.mp}/{hero.max_mp}")
st.write(f"**Enemy**: HP {enemy.hp}/{enemy.max_hp} | Shield {enemy.shield}")

st.write("---")

# -------------------- Hero Turn --------------------
selected_card_index = show_hand_with_click(hero)

if st.button("Play Selected Card") and selected_card_index is not None:
    try:
        card = hero.deck.play_card(selected_card_index)
        # Terapkan efek (langsung ke enemy)
        st.session_state.battle.combat.effects.apply(hero, enemy, card)
        hero.turn_history.append(card.get("name"))
        add_log(f"{hero.name} played {card.get('name')}!")
    except Exception as e:
        st.error(f"Error saat memainkan kartu: {e}")

# -------------------- Enemy Turn --------------------
if st.button("Enemy Turn"):
    ai = st.session_state.ai
    enemy_cards = ai.choose_actions(enemy, hero, combos=[])  # combos kosong jika belum ada
    for c in enemy_cards:
        st.session_state.battle.combat.effects.apply(enemy, hero, c)
    add_log(f"{enemy.name} finished its turn.")

# -------------------- Game Log --------------------
st.write("### Game Log")
for msg in st.session_state.log:
    st.write(msg)

# -------------------- End Turn --------------------
if st.button("End Turn"):
    hero.end_of_turn_effects()
    enemy.end_of_turn_effects()
    hero.begin_turn()
    enemy.begin_turn()
    add_log("→ New Turn begins")

