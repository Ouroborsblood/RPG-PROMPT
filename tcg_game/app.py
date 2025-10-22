#==================== app_interactive.py ====================
import streamlit as st
import json
import os
from core.player import Player
from core.battle import Battle
from core.ai.warrior_ai import WarriorAI

# ----------------- Load combos -----------------
base_path = os.path.dirname(__file__)
combos_path = os.path.join(base_path, "data/combos.json")
with open(combos_path, "r", encoding="utf-8") as f:
    combos = json.load(f)

# ----------------- Inisialisasi Player -----------------
if "hero" not in st.session_state:
    st.session_state.hero = Player("Hero", os.path.join(base_path, "data/test2.json"))
    st.session_state.enemy = Player("Enemy", os.path.join(base_path, "data/cards_enemy.json"))
    st.session_state.hero.start_game()
    st.session_state.enemy.start_game()

hero = st.session_state.hero
enemy = st.session_state.enemy

# ----------------- AI -----------------
ai = WarriorAI()
enemy_cards = ai.choose_actions(enemy, hero, combos)

st.title("🃏 TCG Battle Simulator")

# ----------------- Pilih kartu Hero -----------------
st.subheader("Pilih kartu Hero untuk dimainkan:")
selected_indices = []
for i, c in enumerate(hero.deck.hand):
    if st.checkbox(f"{c['name']} ({c['type']}, power {c.get('power',0)})", key=i):
        selected_indices.append(i)

# ----------------- Jalankan turn -----------------
if st.button("Resolve Turn"):
    if not selected_indices:
        st.warning("Pilih minimal 1 kartu untuk dimainkan!")
    else:
        # Ambil kartu yang dipilih
        player_cards = [hero.deck.hand[i] for i in selected_indices]
        # Remove dari hand & tambahkan ke discard
        for i in sorted(selected_indices, reverse=True):
            hero.deck.play_card(i)

        # Resolve turn
        battle = Battle(hero, enemy)
        battle.combat.resolve_turn(hero, enemy, player_cards, enemy_cards)

        # Tampilkan hasil
        st.success("Turn selesai!")
        st.write(f"**{hero.name} HP:** {hero.hp} | Shield: {hero.shield}")
        st.write(f"**{enemy.name} HP:** {enemy.hp} | Shield: {enemy.shield}")

        # Tampilkan sisa hand
        st.subheader("Sisa hand Hero:")
        for c in hero.deck.hand:
            st.write(f"- {c['name']} ({c['type']}, power {c.get('power',0)})")
