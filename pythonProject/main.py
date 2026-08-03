import base64
import copy
import json
import random
import re
import time
import urllib.parse
from pathlib import Path
import os

import streamlit as st
from streamlit_js_eval import streamlit_js_eval


st.set_page_config(
    page_title="First Aid Heroes",
    page_icon="🩹",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent

# DEBUG: Print what files are in the directory
print("=" * 50)
print(f"BASE_DIR: {BASE_DIR}")
print(f"Files in BASE_DIR: {[f for f in os.listdir(BASE_DIR) if f.endswith('.png')]}")
print("=" * 50)

BROWSER_STORAGE_PREFIX = "first_aid_heroes_progress_v3"
PLAYER_QUERY_KEY = "player"
PUZZLE_RESULT_STORAGE_KEY = "first_aid_heroes_pending_puzzle_result"
PUZZLE_NAV_STORAGE_KEY = "first_aid_heroes_pending_navigation"
NO_BROWSER_SAVE = "__NO_FIRST_AID_SAVE__"
DIFFICULTIES = ["Easy", "Medium", "Hard"]




def normalise_player_id(value):
    """Create a safe, consistent ID for one player profile."""

    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-_")
    return value[:40]


def current_player_id():
    """Return the active player ID for this browser session."""

    return normalise_player_id(
        st.session_state.get("player_id")
        or st.query_params.get(PLAYER_QUERY_KEY, "")
    )


def current_player_name():
    """Return the display name shown in the game UI."""

    return str(
        st.session_state.get("player_name")
        or st.query_params.get("player_name", "")
        or current_player_id()
        or "Player"
    )


def browser_storage_key():
    """Use a separate Local Storage key for every player profile."""

    player_id = current_player_id()
    return f"{BROWSER_STORAGE_PREFIX}::{player_id}"


def game_query_url(screen_name, level_index=None):
    """Build an in-app URL without losing the active player profile."""

    query_values = {
        PLAYER_QUERY_KEY: current_player_id(),
        "player_name": current_player_name(),
        "screen": str(screen_name),
    }

    if level_index is not None:
        query_values["level"] = str(int(level_index))

    return "?" + urllib.parse.urlencode(query_values)


def clear_runtime_game_state():
    """Remove game state before switching to another player."""

    keys_to_clear = [
        "screen", "selected_level", "difficulty", "score",
        "completed_modes", "mode_stars", "layout", "previous_layout",
        "previous_sequence", "moves", "start_time", "decision_answers",
        "pending_decision", "result", "show_hint", "sort_key",
        "slot_warning", "browser_progress_loaded", "attempt_restored",
        "custom_attempt_id", "selected_picture_card",
        "pending_browser_action", "pending_browser_payload",
        "browser_action_revision",
    ]

    # Also clear statistics keys
    stats_keys = [key for key in st.session_state.keys() if key.startswith("stats_level_")]
    keys_to_clear.extend(stats_keys)
    
    # Clear last played keys
    last_played_keys = [key for key in st.session_state.keys() if key.startswith("last_played_level_")]
    keys_to_clear.extend(last_played_keys)

    for key in keys_to_clear:
        st.session_state.pop(key, None)


def render_player_login():
    """Ask each learner for a Player ID before loading their save."""

    st.markdown(
        """
        <style>
        .player-login-card {
            max-width: 680px; margin: 70px auto 20px auto; padding: 28px;
            background: #fffaf0; border: 5px solid #202124;
            border-radius: 18px; box-shadow: 9px 9px 0 #202124;
        }
        .player-login-title {
            font-size: 2.4rem; font-weight: 900; margin-bottom: 8px;
        }
        </style>
        <div class="player-login-card">
            <div class="player-login-title">FIRST AID HEROES</div>
            <p>Enter your own Player ID to load your saved stars, score and unfinished attempt.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("player_login_form", clear_on_submit=False):
        display_name = st.text_input(
            "Player name",
            placeholder="Example: Anna",
            max_chars=30,
        )
        player_code = st.text_input(
            "Player ID",
            placeholder="Example: anna-01",
            max_chars=40,
            help=(
                "Use the same Player ID next time to continue. "
                "Each Player ID has a separate save on this browser."
            ),
        )
        submitted = st.form_submit_button(
            "LOAD MY GAME",
            use_container_width=True,
        )

    if submitted:
        clean_id = normalise_player_id(player_code)
        clean_name = str(display_name or player_code).strip()[:30]

        if len(clean_id) < 2:
            st.error("Enter a Player ID with at least 2 letters or numbers.")
        else:
            clear_runtime_game_state()
            st.session_state.player_id = clean_id
            st.session_state.player_name = clean_name or clean_id
            st.query_params.clear()
            st.query_params[PLAYER_QUERY_KEY] = clean_id
            st.query_params["player_name"] = clean_name or clean_id
            st.rerun()

    st.caption(
        "Progress is saved separately for each Player ID in this browser. "
        "Use the same device, browser and Player ID to continue."
    )

LEVELS = [
    {
        "title": "Nosebleed",
        "setting": "Classroom",
        "story": "A student suddenly develops a nosebleed during class.",
        "correct_cards": ["L1_E_1", "L1_E_2", "L1_E_3", "L1_E_4", "L1_M_1", "L1_M_2", "L1_M_3", "L1_M_4", "L1_M_5", "L1_M_6", "L1_H_1", "L1_H_2", "L1_H_3", "L1_H_4", "L1_H_5", "L1_H_6", "L1_H_7", "L1_H_8"],
        "wrong_cards": ["L1_H_W1", "L1_H_W2"],
        "cards": {
            # ============================================================
            # EASY MODE CARDS (first 4) - 4 cards total
            # ============================================================
            "L1_E_1": "Notify a teacher",
            "L1_E_2": "Pinch the bridge of the nose",
            "L1_E_3": "Continue pinching",
            "L1_E_4": "Check for any bleeding",
            
            # ============================================================
            # MEDIUM MODE CARDS (6 total) - Easy cards + 2 more
            # ============================================================
            "L1_M_1": "Student realises",
            "L1_M_2": "Notify a teacher",
            "L1_M_3": "Pinch the bridge of the nose",
            "L1_M_4": "Retrieve ice pack",
            "L1_M_5": "Apply ice pack",
            "L1_M_6": "Check for any bleeding",
            
            # ============================================================
            # HARD MODE CARDS (8 total) - Medium cards + 3 more
            # ============================================================
            "L1_H_1": "Student realises",
            "L1_H_2": "Friend seeks help",
            "L1_H_3": "Notify the teacher",
            "L1_H_4": "Pinch bridge of the nose",
            "L1_H_5": "Retrieve ice pack",
            "L1_H_6": "Squeeze ice pack",
            "L1_H_7": "Apply ice pack on bridge of the nose",
            "L1_H_8": "Check for any bleeding",
            
            # ============================================================
            # WRONG CARDS (2 total) - Only appear in Hard mode
            # ============================================================
            "L1_H_W1": "Open the ice pack",
            "L1_H_W2": "Tilt head back",
        },
        "decisions": [
            # ============================================================
            # EASY MODE DECISIONS (1 decision)
            # ============================================================
            {
                "id": "easy_pinching_place",
                "difficulty": "Easy",
                "trigger": "L1_E_2",
                "question": "Where do you pinch the nose?",
                "options": [
                    "Below bridge of the nose",
                    "On the hard bone of the nose",
                ],
                "correct": "Below bridge of the nose",
            },
            
            # ============================================================
            # MEDIUM MODE DECISIONS (1 decision)
            # ============================================================
            {
                "id": "medium_compress",
                "difficulty": "Medium",
                "trigger": "L1_M_1",
                "question": "What compress do you use?",
                "options": ["Warm", "Hot", "Cold", "Cool"],
                "correct": "Cool",
            },
            
            # ============================================================
            # HARD MODE DECISIONS (3 decisions)
            # ============================================================
            {
                "id": "hard_ask_teacher",
                "difficulty": "Hard",
                "trigger": "L1_H_3",
                "question": "What do you ask the teacher to bring?",
                "options": ["AED", "First Aid Bag", "Nothing"],
                "correct": "First Aid Bag",
            },
            {
                "id": "hard_pinching_time",
                "difficulty": "Hard",
                "trigger": "L1_H_4",
                "question": "How long do you pinch the nose?",
                "options": ["5-10 mins", "10-15 mins", "20-30 mins"],
                "correct": "10-15 mins",
            },
            {
                "id": "hard_compress_time",
                "difficulty": "Hard",
                "trigger": "L1_H_7",
                "question": "How long do you put the cool compress?",
                "options": ["5-10 mins", "10-15 mins", "20-30 mins"],
                "correct": "10-15 mins",
            },
        ],
        "hint": (
            "Sit upright, lean slightly forward, pinch below the bridge "
            "of the nose for 10-15 minutes and use a cool compress."
        ),
    },
    {
        "title": "Student Falls",
        "setting": "School Corridor",
        "story": "A student trips in the school corridor and falls.",
        "correct_cards": ["L2_E_1", "L2_E_2", "L2_E_3", "L2_E_4", "L2_M_1", "L2_M_2", "L2_M_3", "L2_M_4", "L2_M_5", "L2_M_6", "L2_H_1", "L2_H_2", "L2_H_3", "L2_H_4", "L2_H_5", "L2_H_6", "L2_H_7", "L2_H_8"],
        "wrong_cards": ["L2_H_W1", "L2_H_W2"],
        "cards": {
            # ============================================================
            # EASY MODE CARDS (first 4) - 4 cards total
            # ============================================================
            "L2_E_1": "Student trips and falls",
            "L2_E_2": "Check the area is safe",
            "L2_E_3": "Check the student before moving",
            "L2_E_4": "Inform the teacher",
            
            # ============================================================
            # MEDIUM MODE CARDS (6 total) - Easy cards + 2 more
            # ============================================================
            "L2_M_1": "Student trips and falls",
            "L2_M_2": "Check the area is safe",
            "L2_M_3": "Check the student before moving",
            "L2_M_4": "Inform the teacher",
            "L2_M_5": "Clean the wound with clean materials",
            "L2_M_6": "Apply a clean dressing",
            
            # ============================================================
            # HARD MODE CARDS (8 total) - Medium cards + 3 more
            # ============================================================
            "L2_H_1": "Student trips and falls",
            "L2_H_2": "Check the area is safe",
            "L2_H_3": "Check the student before moving",
            "L2_H_4": "Inform the teacher",
            "L2_H_5": "Clean the wound with clean materials",
            "L2_H_6": "Apply a clean dressing",
            "L2_H_7": "Monitor the student",
            "L2_H_8": "Provide reassurance",
            
            # ============================================================
            # WRONG CARDS (2 total) - Only appear in Hard mode
            # ============================================================
            "L2_H_W1": "Pull the student up immediately",
            "L2_H_W2": "Leave the student alone",
        },
        "decisions": [
            # ============================================================
            # EASY MODE DECISIONS (1 decision)
            # ============================================================
            {
                "id": "easy_fall_move",
                "difficulty": "Easy",
                "trigger": "L2_E_3",
                "question": "Should the student be moved immediately?",
                "options": [
                    "No, check for injury first",
                    "Yes, pull the student up",
                ],
                "correct": "No, check for injury first",
            },
            
            # ============================================================
            # MEDIUM MODE DECISIONS (1 decision)
            # ============================================================
            {
                "id": "medium_fall_clean",
                "difficulty": "Medium",
                "trigger": "L2_M_5",
                "question": "What should be used to clean the wound?",
                "options": [
                    "Clean water and clean materials",
                    "Dirty tissue",
                ],
                "correct": "Clean water and clean materials",
            },
            
            # ============================================================
            # HARD MODE DECISIONS (3 decisions)
            # ============================================================
            {
                "id": "hard_fall_assess",
                "difficulty": "Hard",
                "trigger": "L2_H_3",
                "question": "What should you check before moving the student?",
                "options": [
                    "Consciousness and movement",
                    "Ignore and move quickly",
                ],
                "correct": "Consciousness and movement",
            },
            {
                "id": "hard_fall_clean_time",
                "difficulty": "Hard",
                "trigger": "L2_H_5",
                "question": "How should the wound be cleaned?",
                "options": [
                    "With clean water and gentle pressure",
                    "With a dirty tissue",
                ],
                "correct": "With clean water and gentle pressure",
            },
            {
                "id": "hard_fall_cover",
                "difficulty": "Hard",
                "trigger": "L2_H_6",
                "question": "What should be used to cover the wound?",
                "options": [
                    "A clean dressing",
                    "A dirty cloth",
                ],
                "correct": "A clean dressing",
            },
        ],
        "hint": (
            "Check safety, assess the student, "
            "get adult help and use clean materials."
        ),
    },
    {
        "title": "Fainting",
        "setting": "School Canteen",
        "story": "A student feels dizzy and suddenly faints in the canteen.",
        "correct_cards": ["L3_E_1", "L3_E_2", "L3_E_3", "L3_E_4", "L3_M_1", "L3_M_2", "L3_M_3", "L3_M_4", "L3_M_5", "L3_M_6", "L3_H_1", "L3_H_2", "L3_H_3", "L3_H_4", "L3_H_5", "L3_H_6", "L3_H_7", "L3_H_8"],
        "wrong_cards": ["L3_H_W1", "L3_H_W2"],
        "cards": {
            # ============================================================
            # EASY MODE CARDS (first 4) - 4 cards total
            # ============================================================
            "L3_E_1": "Student feels dizzy",
            "L3_E_2": "Student faints",
            "L3_E_3": "Check responsiveness",
            "L3_E_4": "Call for help",
            
            # ============================================================
            # MEDIUM MODE CARDS (6 total) - Easy cards + 2 more
            # ============================================================
            "L3_M_1": "Student feels dizzy",
            "L3_M_2": "Student faints",
            "L3_M_3": "Check responsiveness",
            "L3_M_4": "Call for help",
            "L3_M_5": "Do not give food or drink",
            "L3_M_6": "Stay and monitor the student",
            
            # ============================================================
            # HARD MODE CARDS (8 total) - Medium cards + 3 more
            # ============================================================
            "L3_H_1": "Student feels dizzy",
            "L3_H_2": "Student faints",
            "L3_H_3": "Check responsiveness",
            "L3_H_4": "Call for help",
            "L3_H_5": "Do not give food or drink",
            "L3_H_6": "Stay and monitor the student",
            "L3_H_7": "Check breathing",
            "L3_H_8": "Keep the student safe",
            
            # ============================================================
            # WRONG CARDS (2 total) - Only appear in Hard mode
            # ============================================================
            "L3_H_W1": "Give food or drink while unconscious",
            "L3_H_W2": "Leave the student alone",
        },
        "decisions": [
            # ============================================================
            # EASY MODE DECISIONS (1 decision)
            # ============================================================
            {
                "id": "easy_faint_response",
                "difficulty": "Easy",
                "trigger": "L3_E_3",
                "question": "What should you check first?",
                "options": [
                    "Responsiveness",
                    "Check for injuries",
                ],
                "correct": "Responsiveness",
            },
            
            # ============================================================
            # MEDIUM MODE DECISIONS (1 decision)
            # ============================================================
            {
                "id": "medium_faint_food",
                "difficulty": "Medium",
                "trigger": "L3_M_5",
                "question": "Should food or drink be given while unconscious?",
                "options": ["No", "Yes"],
                "correct": "No",
            },
            
            # ============================================================
            # HARD MODE DECISIONS (3 decisions)
            # ============================================================
            {
                "id": "hard_faint_breathing",
                "difficulty": "Hard",
                "trigger": "L3_H_7",
                "question": "What should you check after responsiveness?",
                "options": [
                    "Breathing",
                    "Blood pressure",
                ],
                "correct": "Breathing",
            },
            {
                "id": "hard_faint_position",
                "difficulty": "Hard",
                "trigger": "L3_H_6",
                "question": "What should you do if the student is unconscious?",
                "options": [
                    "Stay and monitor",
                    "Leave to get help",
                ],
                "correct": "Stay and monitor",
            },
            {
                "id": "hard_faint_safe",
                "difficulty": "Hard",
                "trigger": "L3_H_8",
                "question": "How should you keep the student safe?",
                "options": [
                    "Stay with them and monitor",
                    "Leave them alone",
                ],
                "correct": "Stay with them and monitor",
            },
        ],
        "hint": (
            "Check responsiveness and breathing, "
            "call for help and continue monitoring."
        ),
    },
]


BASE_TARGETS = [
    {
        "three_time": 60,
        "three_moves": 12,
        "two_time": 90,
        "two_moves": 18,
    },
    {
        "three_time": 50,
        "three_moves": 10,
        "two_time": 80,
        "two_moves": 15,
    },
    {
        "three_time": 70,
        "three_moves": 14,
        "two_time": 100,
        "two_moves": 20,
    },
]


DIFFICULTY_RULES = {
    "Easy": {
        "time_multiplier": 1.30,
        "move_multiplier": 1.25,
        "wrong_cards": 0,
    },
    "Medium": {
        "time_multiplier": 1.00,
        "move_multiplier": 1.00,
        "wrong_cards": 0,
    },
    "Hard": {
        "time_multiplier": 0.75,
        "move_multiplier": 0.85,
        "wrong_cards": 2,
    },
}



def empty_progress():
    """Return a clean progress structure for a new browser user."""

    return {
        "score": 0,
        "completed_modes": set(),
        "mode_stars": {},
        "attempt": None,
        "last_screen": "home",
        "selected_level": 0,
        "difficulty": "Easy",
    }


def sanitise_progress(raw_value):
    """Convert Local Storage data into safe Python values."""

    if raw_value in (None, "", NO_BROWSER_SAVE):
        return empty_progress()

    try:
        data = (
            json.loads(raw_value)
            if isinstance(raw_value, str)
            else raw_value
        )

        if not isinstance(data, dict):
            return empty_progress()

        score = max(
            0,
            int(data.get("score", 0)),
        )

        completed_modes = {
            str(item)
            for item in data.get(
                "completed_modes",
                [],
            )
            if isinstance(
                item,
                (str, int),
            )
        }

        mode_stars = {}
        raw_stars = data.get(
            "mode_stars",
            {},
        )

        if isinstance(raw_stars, dict):
            for key, value in raw_stars.items():
                try:
                    mode_stars[str(key)] = max(
                        0,
                        min(
                            3,
                            int(value),
                        ),
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

        try:
            selected_level = int(
                data.get(
                    "selected_level",
                    0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            selected_level = 0

        selected_level = max(
            0,
            min(
                len(LEVELS) - 1,
                selected_level,
            ),
        )

        difficulty = str(
            data.get(
                "difficulty",
                "Easy",
            )
        )

        if difficulty not in DIFFICULTIES:
            difficulty = "Easy"

        last_screen = str(
            data.get(
                "last_screen",
                "home",
            )
        )

        allowed_screens = {
            "home",
            "map",
            "difficulty",
            "scenario",
            "puzzle",
            "result",
            "score",
            "achievements",
        }

        if last_screen not in allowed_screens:
            last_screen = "home"

        attempt = data.get(
            "attempt"
        )

        if not isinstance(
            attempt,
            dict,
        ):
            attempt = None

        return {
            "score": score,
            "completed_modes": completed_modes,
            "mode_stars": mode_stars,
            "attempt": attempt,
            "last_screen": last_screen,
            "selected_level": selected_level,
            "difficulty": difficulty,
        }

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return empty_progress()


def read_browser_progress():
    """Read progress belonging only to the current browser."""

    storage_key_json = json.dumps(
        browser_storage_key()
    )

    fallback_json = json.dumps(
        NO_BROWSER_SAVE
    )

    return streamlit_js_eval(
        js_expressions=(
            "window.localStorage.getItem("
            f"{storage_key_json}"
            ") ?? "
            f"{fallback_json}"
        ),
        want_output=True,
        key=f"load_first_aid_browser_progress_{current_player_id()}",
    )


def serialisable_layout(layout):
    """Return a safe copy of the drag-and-drop layout."""

    if not isinstance(
        layout,
        list,
    ):
        return None

    cleaned = []

    for container in layout:
        if not isinstance(
            container,
            dict,
        ):
            return None

        header = str(
            container.get(
                "header",
                "",
            )
        )

        items = container.get(
            "items",
            [],
        )

        if not isinstance(
            items,
            list,
        ):
            return None

        cleaned.append(
            {
                "header": header,
                "items": [
                    str(item)
                    for item in items
                ],
            }
        )

    return cleaned


def build_attempt_payload():
    """Build the current unfinished attempt for browser saving."""

    layout = serialisable_layout(
        st.session_state.get(
            "layout"
        )
    )

    start_time = st.session_state.get(
        "start_time"
    )

    if (
        layout is None
        or start_time is None
        or st.session_state.get(
            "screen"
        ) != "puzzle"
    ):
        return None

    elapsed_seconds = max(
        0,
        int(
            time.time()
            - float(start_time)
        ),
    )

    return {
        "level_index": int(
            st.session_state.get(
                "selected_level",
                0,
            )
        ),
        "difficulty": str(
            st.session_state.get(
                "difficulty",
                "Easy",
            )
        ),
        "layout": layout,
        "previous_layout": serialisable_layout(
            st.session_state.get(
                "previous_layout"
            )
        ),
        "previous_sequence": list(
            st.session_state.get(
                "previous_sequence",
                [None] * 6,
            )
        ),
        "moves": max(
            0,
            int(
                st.session_state.get(
                    "moves",
                    0,
                )
            )
        ),
        "elapsed_seconds": elapsed_seconds,
        "decision_answers": dict(
            st.session_state.get(
                "decision_answers",
                {},
            )
        ),
        "pending_decision": st.session_state.get(
            "pending_decision"
        ),
        "show_hint": bool(
            st.session_state.get(
                "show_hint",
                False,
            )
        ),
        "selected_picture_card": st.session_state.get(
            "selected_picture_card"
        ),
    }


def build_progress_payload():
    """Create the complete save file for this browser user."""

    data = {
        "player_id": current_player_id(),
        "player_name": current_player_name(),
        "saved_at": int(time.time()),
        "score": int(
            st.session_state.get(
                "score",
                0,
            )
        ),
        "completed_modes": sorted(
            st.session_state.get(
                "completed_modes",
                set(),
            )
        ),
        "mode_stars": {
            str(key): int(value)
            for key, value
            in st.session_state.get(
                "mode_stars",
                {},
            ).items()
        },
        "last_screen": str(
            st.session_state.get(
                "screen",
                "home",
            )
        ),
        "selected_level": int(
            st.session_state.get(
                "selected_level",
                0,
            )
        ),
        "difficulty": str(
            st.session_state.get(
                "difficulty",
                "Easy",
            )
        ),
        "attempt": build_attempt_payload(),
    }

    return json.dumps(
        data,
        separators=(",", ":"),
    )


def save_progress():
    """Queue an automatic save in this browser's Local Storage."""

    st.session_state.pending_browser_action = "save"
    st.session_state.pending_browser_payload = (
        build_progress_payload()
    )
    st.session_state.browser_action_revision = (
        int(
            st.session_state.get(
                "browser_action_revision",
                0,
            )
        )
        + 1
    )


def flush_pending_browser_action():
    """Write a queued save/reset into Local Storage."""

    action = st.session_state.get(
        "pending_browser_action"
    )

    if action not in {
        "save",
        "reset",
    }:
        return

    revision = int(
        st.session_state.get(
            "browser_action_revision",
            0,
        )
    )

    storage_key_json = json.dumps(
        browser_storage_key()
    )

    if action == "save":
        payload_json = json.dumps(
            st.session_state.get(
                "pending_browser_payload",
                "",
            )
        )

        javascript = (
            "window.localStorage.setItem("
            f"{storage_key_json}, "
            f"{payload_json}"
            "); true"
        )

    else:
        javascript = (
            "window.localStorage.removeItem("
            f"{storage_key_json}"
            "); true"
        )

    streamlit_js_eval(
        js_expressions=javascript,
        want_output=False,
        key=(
            "first_aid_browser_action_"
            f"{revision}"
        ),
    )

    st.session_state.pending_browser_action = None
    st.session_state.pending_browser_payload = ""


def reset_saved_progress():
    """Reset progress only for the current browser user."""

    st.session_state.score = 0
    st.session_state.completed_modes = set()
    st.session_state.mode_stars = {}
    st.session_state.layout = None
    st.session_state.previous_layout = None
    st.session_state.previous_sequence = [None] * 6
    st.session_state.moves = 0
    st.session_state.start_time = None
    st.session_state.decision_answers = {}
    st.session_state.pending_decision = None
    st.session_state.result = None
    st.session_state.show_hint = False
    st.session_state.selected_picture_card = None
    st.session_state.screen = "home"

    # Clear statistics
    stats_keys = [key for key in st.session_state.keys() if key.startswith("stats_level_")]
    for key in stats_keys:
        st.session_state.pop(key, None)
    
    # Clear last played keys
    last_played_keys = [key for key in st.session_state.keys() if key.startswith("last_played_level_")]
    for key in last_played_keys:
        st.session_state.pop(key, None)

    st.session_state.pending_browser_action = "reset"
    st.session_state.pending_browser_payload = ""
    st.session_state.browser_action_revision = (
        int(
            st.session_state.get(
                "browser_action_revision",
                0,
            )
        )
        + 1
    )


def mode_key(
    level_index,
    difficulty,
):
    return (
        f"{int(level_index)}"
        f"::{difficulty}"
    )


# ============================================================
# STATISTICS FUNCTIONS - Differentiated by Level
# ============================================================

def get_stats_key(level_index):
    """Get the storage key for statistics of a specific level."""
    return f"stats_level_{int(level_index)}"


def update_stats(level_index, time_taken, moves_used):
    """Update the average time and moves for a level."""
    stats_key = get_stats_key(level_index)
    
    # Initialize stats if not exists
    if stats_key not in st.session_state:
        st.session_state[stats_key] = {
            "attempts": 0,
            "total_time": 0,
            "total_moves": 0,
            "best_time": None,
            "best_moves": None,
            "completed": False
        }
    
    stats = st.session_state[stats_key]
    stats["attempts"] += 1
    stats["total_time"] += time_taken
    stats["total_moves"] += moves_used
    
    if stats["best_time"] is None or time_taken < stats["best_time"]:
        stats["best_time"] = time_taken
    if stats["best_moves"] is None or moves_used < stats["best_moves"]:
        stats["best_moves"] = moves_used


def get_average_stats(level_index):
    """Get the average time and moves for a level."""
    stats_key = get_stats_key(level_index)
    
    if stats_key not in st.session_state:
        return None, None, None, None, None
    
    stats = st.session_state[stats_key]
    attempts = stats["attempts"]
    
    if attempts == 0:
        return None, None, None, None, None
    
    avg_time = stats["total_time"] // attempts
    avg_moves = stats["total_moves"] // attempts
    
    return avg_time, avg_moves, stats["best_time"], stats["best_moves"], attempts


# ============================================================
# LAST PLAYED TRACKING
# ============================================================

def update_last_played(level_index):
    """Update the last played timestamp for a level."""
    last_played_key = f"last_played_level_{int(level_index)}"
    st.session_state[last_played_key] = time.time()


def get_last_played(level_index):
    """Get the last played timestamp for a level."""
    last_played_key = f"last_played_level_{int(level_index)}"
    if last_played_key in st.session_state:
        return st.session_state[last_played_key]
    return None


def format_last_played(timestamp):
    """Format the timestamp as a readable string."""
    if timestamp is None:
        return "Never"
    dt = time.localtime(timestamp)
    return time.strftime("%b %d, %Y at %I:%M %p", dt)


# ============================================================


def initialise_state(saved_progress):
    """Initialise the game and restore the last unfinished attempt."""

    # If we already have valid data (score > 0 or completed modes), don't reset
    if st.session_state.get("score", 0) > 0 or len(st.session_state.get("completed_modes", set())) > 0:
        # Only set missing keys, don't overwrite existing ones
        defaults = {
            "screen": saved_progress.get("last_screen", "home"),
            "selected_level": saved_progress.get("selected_level", 0),
            "difficulty": saved_progress.get("difficulty", "Easy"),
            "layout": None,
            "previous_layout": None,
            "previous_sequence": [None] * 6,
            "moves": 0,
            "start_time": None,
            "decision_answers": {},
            "pending_decision": None,
            "result": None,
            "show_hint": False,
            "sort_key": 0,
            "slot_warning": False,
            "browser_progress_loaded": True,
            "pending_browser_action": None,
            "pending_browser_payload": "",
            "browser_action_revision": 0,
            "attempt_restored": False,
            "custom_attempt_id": "",
            "picture_component_revision": None,
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = copy.deepcopy(value)
        return

    # Otherwise, initialize from saved progress
    defaults = {
        "screen": saved_progress["last_screen"],
        "selected_level": saved_progress["selected_level"],
        "difficulty": saved_progress["difficulty"],
        "score": saved_progress["score"],
        "completed_modes": saved_progress["completed_modes"],
        "mode_stars": saved_progress["mode_stars"],
        "layout": None,
        "previous_layout": None,
        "previous_sequence": [None] * 6,
        "moves": 0,
        "start_time": None,
        "decision_answers": {},
        "pending_decision": None,
        "result": None,
        "show_hint": False,
        "sort_key": 0,
        "slot_warning": False,
        "browser_progress_loaded": True,
        "pending_browser_action": None,
        "pending_browser_payload": "",
        "browser_action_revision": 0,
        "attempt_restored": False,
        "custom_attempt_id": "",
        "picture_component_revision": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = (
                copy.deepcopy(value)
            )
        elif key in ["score", "completed_modes", "mode_stars", "selected_level", "difficulty", "screen"]:
            # Don't overwrite these if they already exist
            pass
        else:
            st.session_state[key] = copy.deepcopy(value)

    if not isinstance(
        st.session_state.completed_modes,
        set,
    ):
        st.session_state.completed_modes = set(
            st.session_state.completed_modes
        )

    if not isinstance(
        st.session_state.mode_stars,
        dict,
    ):
        st.session_state.mode_stars = {}

    attempt = saved_progress.get(
        "attempt"
    )

    if (
        not st.session_state.attempt_restored
        and isinstance(
            attempt,
            dict,
        )
    ):
        try:
            level_index = int(
                attempt.get(
                    "level_index",
                    0,
                )
            )

            difficulty = str(
                attempt.get(
                    "difficulty",
                    "Easy",
                )
            )

            layout = serialisable_layout(
                attempt.get(
                    "layout"
                )
            )

            previous_layout = serialisable_layout(
                attempt.get(
                    "previous_layout"
                )
            )

            if (
                0 <= level_index < len(LEVELS)
                and difficulty in DIFFICULTIES
                and layout is not None
                and len(layout) >= 5
            ):
                st.session_state.selected_level = (
                    level_index
                )
                st.session_state.difficulty = (
                    difficulty
                )
                st.session_state.layout = (
                    copy.deepcopy(layout)
                )
                st.session_state.previous_layout = (
                    copy.deepcopy(
                        previous_layout
                        if previous_layout is not None
                        else layout
                    )
                )

                expected_slots = max(1, len(layout) - 1)

                previous_sequence = attempt.get(
                    "previous_sequence",
                    [None] * expected_slots,
                )

                if not isinstance(previous_sequence, list):
                    previous_sequence = [None] * expected_slots

                st.session_state.previous_sequence = (
                    list(previous_sequence[:expected_slots])
                    + [None] * expected_slots
                )[:expected_slots]

                st.session_state.moves = max(
                    0,
                    int(
                        attempt.get(
                            "moves",
                            0,
                        )
                    ),
                )

                elapsed_seconds = max(
                    0,
                    int(
                        attempt.get(
                            "elapsed_seconds",
                            0,
                        )
                    ),
                )

                st.session_state.start_time = (
                    time.time()
                    - elapsed_seconds
                )

                answers = attempt.get(
                    "decision_answers",
                    {},
                )

                st.session_state.decision_answers = (
                    dict(answers)
                    if isinstance(
                        answers,
                        dict,
                    )
                    else {}
                )

                st.session_state.pending_decision = (
                    attempt.get(
                        "pending_decision"
                    )
                )

                st.session_state.show_hint = bool(
                    attempt.get(
                        "show_hint",
                        False,
                    )
                )

                restored_selected = attempt.get("selected_picture_card")
                st.session_state.selected_picture_card = (
                    str(restored_selected) if restored_selected else None
                )

                st.session_state.screen = "puzzle"
                st.session_state.sort_key += 1

        except (
            TypeError,
            ValueError,
        ):
            pass

        st.session_state.attempt_restored = True



def navigate(
    screen_name,
    level_index=None,
):
    """Navigate without losing the active player profile."""

    active_player_id = current_player_id()
    active_player_name = current_player_name()

    st.session_state.screen = screen_name

    # Rebuild the URL with the player details included. This is important on
    # Streamlit Community Cloud because opening a raw ?screen=... link may
    # create a fresh session. Without the player parameter, the fresh session
    # would return to the login page.
    st.query_params.clear()
    st.query_params[PLAYER_QUERY_KEY] = active_player_id
    st.query_params["player_name"] = active_player_name
    st.query_params["screen"] = screen_name

    if level_index is not None:
        st.session_state.selected_level = int(level_index)
        st.query_params["level"] = str(int(level_index))

    save_progress()
    st.rerun()


def mode_completed(
    level_index,
    difficulty,
):
    return (
        mode_key(
            level_index,
            difficulty,
        )
        in st.session_state.completed_modes
    )


def difficulty_unlocked(
    level_index,
    difficulty,
):
    if difficulty == "Easy":
        return True

    if difficulty == "Medium":
        return mode_completed(
            level_index,
            "Easy",
        )

    if difficulty == "Hard":
        return mode_completed(
            level_index,
            "Medium",
        )

    return False


def level_unlocked(level_index):
    """
    Level 1 is available from the beginning.

    Every later level unlocks only after the player completes
    Easy mode of the immediately previous level:
    Level 2 <- Level 1 Easy
    Level 3 <- Level 2 Easy
    """

    level_index = int(level_index)

    if level_index == 0:
        return True

    return mode_completed(
        level_index - 1,
        "Easy",
    )


def total_stars():
    return sum(
        int(value)
        for value
        in st.session_state.mode_stars.values()
    )


def level_star_total(level_index):
    return sum(
        int(
            st.session_state.mode_stars.get(
                mode_key(
                    level_index,
                    difficulty,
                ),
                0,
            )
        )
        for difficulty
        in DIFFICULTIES
    )



def difficulty_code(difficulty):
    return {
        "Easy": "E",
        "Medium": "M",
        "Hard": "H",
    }.get(difficulty, "E")


def slot_count_for(level_index, difficulty):
    """Easy uses 4 slots. Medium uses 6 slots. Hard uses 8 slots for Level 1."""

    if int(level_index) == 0:
        if difficulty == "Easy":
            return 4
        elif difficulty == "Hard":
            return 8
        else:  # Medium
            return 6

    return 6


def correct_cards_for(level_index, level, difficulty):
    """Return the correct sequence required for this difficulty."""

    if int(level_index) == 0 and difficulty == "Easy":
        return level["correct_cards"][:4]
    
    if int(level_index) == 0 and difficulty == "Hard":
        # Hard mode uses 8 correct cards
        return level["correct_cards"][:8]

    return level["correct_cards"][:6]


def decisions_for(level, difficulty):
    """Only return questions belonging to the selected difficulty."""

    return [
        decision
        for decision in level.get("decisions", [])
        if decision.get("difficulty") in (None, difficulty)
    ]


def find_image_path(filename_without_extension):
    """
    Load an image using the exact filename.

    Expected examples:
        L1_E_1.png
        L1_E_2.png
        L1_M_5.png
        L1_H_3.png
    """

    # Get the current working directory
    cwd = Path.cwd()
    
    # Try multiple possible locations
    possible_locations = [
        BASE_DIR,  # Same folder as main.py
        cwd,  # Current working directory
        Path("/mount/src/pythonprojectgithub/pythonProject"),  # Streamlit Cloud path
        Path("/mount/src/pythonprojectgithub"),  # Streamlit Cloud root
        Path("/app"),  # Another common Streamlit Cloud path
        Path("/app/pythonProject"),  # Another common Streamlit Cloud path
    ]

    # Also try to find the images folder anywhere in the current directory tree
    for root in [BASE_DIR, cwd] + list(BASE_DIR.parents) + list(cwd.parents):
        if (root / "images").exists():
            possible_locations.append(root / "images")
        if (root / "assets").exists():
            possible_locations.append(root / "assets")

    # Try all possible extensions and cases
    extensions = [".png", ".PNG", ".jpg", ".JPG", ".jpeg", ".JPEG", ".webp", ".WEBP"]
    
    for location in possible_locations:
        if not location or not location.exists():
            continue
        for extension in extensions:
            candidate = location / f"{filename_without_extension}{extension}"
            if candidate.exists():
                print(f"✅ Found image: {candidate}")
                return candidate

    print(f"❌ Image not found: {filename_without_extension}")
    return None


def image_path_for_card(level_index, difficulty, card_id):
    """
    Find the image by using the card ID directly.

    The card ID already matches the image filename without its extension:
        L1_E_1  -> L1_E_1.png
        L1_M_5  -> L1_M_5.png
        L1_H_3  -> L1_H_3.png
        L1_H_W1 -> L1_H_W1.png
    """

    return find_image_path(str(card_id).strip())

def card_html(level_index, difficulty, level, card_id):
    """Create the draggable item, using the matching picture when available."""

    description = level["cards"].get(card_id, card_id)
    image_path = image_path_for_card(
        level_index,
        difficulty,
        card_id,
    )

    hidden_id = f'<span style="display:none">CARD_ID:{card_id}</span>'

    if image_path is None:
        return (
            f'<div class="sortable-picture-card">'
            f'<strong>{card_id}</strong><br>{description}'
            f'{hidden_id}</div>'
        )

    image_uri = image_data_uri(image_path)

    return (
        f'<div class="sortable-picture-card">'
        f'<img src="{image_uri}" alt="{card_id}" '
        f'style="width:150px;max-width:100%;height:150px;'
        f'object-fit:contain;border-radius:10px;display:block;margin:auto;">'
        f'<div style="font-size:0.85rem;text-align:center;margin-top:8px;font-weight:700;color:#202124;background:#fffaf0;padding:4px 8px;border-radius:6px;border:2px solid #202124;">'
        f'{description}</div>{hidden_id}</div>'
    )



def card_text(
    level,
    card_id,
    level_index=None,
    difficulty=None,
):
    if level_index is None:
        level_index = st.session_state.get("selected_level", 0)

    if difficulty is None:
        difficulty = st.session_state.get("difficulty", "Easy")

    return card_html(
        level_index,
        difficulty,
        level,
        card_id,
    )


def extract_card_id(item):
    if not isinstance(item, str):
        return ""

    match = re.search(r"CARD_ID:([A-Za-z0-9-]+)", item)
    if match:
        return match.group(1)

    if " | " in item:
        return item.split(" | ", 1)[0]

    return item.strip()


def start_puzzle():
    level_index = st.session_state.selected_level
    difficulty = st.session_state.difficulty
    level = LEVELS[level_index]

    correct_ids = correct_cards_for(
        level_index,
        level,
        difficulty,
    )

    wrong_count = (
        2
        if level_index == 0 and difficulty == "Hard"
        else DIFFICULTY_RULES[difficulty]["wrong_cards"]
    )

    card_ids = correct_ids.copy()
    card_ids.extend(level["wrong_cards"][:wrong_count])
    random.shuffle(card_ids)

    layout = [
        {
            "header": "CARD TRAY",
            "items": list(card_ids),
        }
    ]

    slot_count = slot_count_for(level_index, difficulty)

    for slot_number in range(1, slot_count + 1):
        layout.append(
            {
                "header": f"SLOT {slot_number}",
                "items": [],
            }
        )

    st.session_state.layout = copy.deepcopy(layout)
    st.session_state.previous_layout = copy.deepcopy(layout)
    st.session_state.previous_sequence = [None] * slot_count
    st.session_state.moves = 0
    st.session_state.start_time = time.time()
    st.session_state.decision_answers = {}
    st.session_state.pending_decision = None
    st.session_state.result = None
    st.session_state.show_hint = False
    st.session_state.slot_warning = False
    st.session_state.selected_picture_card = None
    st.session_state.sort_key += 1
    st.session_state.custom_attempt_id = (
        f"{level_index}-{difficulty}-{time.time_ns()}"
    )
    st.session_state.selected_picture_card = None

    result_key_json = json.dumps(
        PUZZLE_RESULT_STORAGE_KEY
    )

    streamlit_js_eval(
        js_expressions=(
            "window.localStorage.removeItem("
            f"{result_key_json}"
            "); true"
        ),
        want_output=False,
        key=(
            "clear_pending_result_when_starting_"
            f"{st.session_state.custom_attempt_id}"
        ),
    )

    storage_key_json = json.dumps(
        PUZZLE_RESULT_STORAGE_KEY
    )

    streamlit_js_eval(
        js_expressions=(
            "window.localStorage.removeItem("
            f"{storage_key_json}"
            "); true"
        ),
        want_output=False,
        key=(
            "clear_result_before_new_puzzle_"
            f"{st.session_state.sort_key}"
        ),
    )

    navigation_key_json = json.dumps(
        PUZZLE_NAV_STORAGE_KEY
    )

    streamlit_js_eval(
        js_expressions=(
            "window.localStorage.removeItem("
            f"{navigation_key_json}"
            "); true"
        ),
        want_output=False,
        key=(
            "clear_navigation_before_new_puzzle_"
            f"{st.session_state.sort_key}"
        ),
    )

    navigate("puzzle", level_index)

def sequence_from_layout(layout):
    if not isinstance(layout, list) or len(layout) < 2:
        return []

    sequence = []

    for slot in layout[1:]:
        items = slot.get("items", []) if isinstance(slot, dict) else []

        if len(items) == 1:
            sequence.append(extract_card_id(items[0]))
        else:
            sequence.append(None)

    return sequence


def slots_complete(layout):
    if not isinstance(layout, list) or len(layout) < 2:
        return False

    return all(
        isinstance(container, dict)
        and len(container.get("items", [])) == 1
        for container in layout[1:]
    )


def limit_one_card_per_slot(layout):
    if not isinstance(layout, list):
        return (
            copy.deepcopy(st.session_state.layout),
            False,
        )

    corrected = copy.deepcopy(layout)
    previous = st.session_state.previous_layout
    returned_cards = []
    changed = False

    for slot_index in range(1, len(corrected)):
        items = list(corrected[slot_index].get("items", []))

        if len(items) <= 1:
            continue

        changed = True
        card_to_keep = None

        if (
            isinstance(previous, list)
            and len(previous) > slot_index
            and previous[slot_index].get("items", [])
        ):
            previous_item = previous[slot_index]["items"][0]
            if previous_item in items:
                card_to_keep = previous_item

        if card_to_keep is None:
            card_to_keep = items[0]

        kept_once = False
        extras = []

        for item in items:
            if item == card_to_keep and not kept_once:
                kept_once = True
            else:
                extras.append(item)

        corrected[slot_index]["items"] = [card_to_keep]
        returned_cards.extend(extras)

    for item in returned_cards:
        if item not in corrected[0]["items"]:
            corrected[0]["items"].append(item)

    return corrected, changed


def detect_new_decision(
    level,
    old_sequence,
    new_sequence,
):
    old_cards = {
        card
        for card
        in old_sequence
        if card
    }

    new_cards = {
        card
        for card
        in new_sequence
        if card
    }

    newly_added_cards = (
        new_cards - old_cards
    )

    for decision in decisions_for(level, st.session_state.difficulty):
        if (
            decision["trigger"]
            in newly_added_cards
            and decision["id"]
            not in st.session_state.decision_answers
        ):
            return decision["id"]

    return None


def get_decision(
    level,
    decision_id,
):
    for decision in decisions_for(level, st.session_state.difficulty):
        if (
            decision["id"]
            == decision_id
        ):
            return decision

    return None


def decisions_complete(level):
    return all(
        decision["id"] in st.session_state.decision_answers
        for decision in decisions_for(
            level,
            st.session_state.difficulty,
        )
    )


def targets(
    level_index,
    difficulty,
):
    base = BASE_TARGETS[
        level_index
    ]

    rule = DIFFICULTY_RULES[
        difficulty
    ]

    return {
        "three_time": round(
            base["three_time"]
            * rule["time_multiplier"]
        ),
        "three_moves": round(
            base["three_moves"]
            * rule["move_multiplier"]
        ),
        "two_time": round(
            base["two_time"]
            * rule["time_multiplier"]
        ),
        "two_moves": round(
            base["two_moves"]
            * rule["move_multiplier"]
        ),
    }


def evaluate_level():
    level_index = (
        st.session_state.selected_level
    )

    difficulty = (
        st.session_state.difficulty
    )

    level = LEVELS[
        level_index
    ]

    start_time = (
        st.session_state.start_time
    )

    if start_time is None:
        elapsed = 0

    else:
        elapsed = max(
            0,
            int(
                time.time()
                - start_time
            ),
        )

    sequence = sequence_from_layout(
        st.session_state.layout
    )

    required_sequence = correct_cards_for(
        level_index,
        level,
        difficulty,
    )

    sequence_correct = (
        sequence == required_sequence
    )

    decision_results = [
        st.session_state.decision_answers.get(
            decision["id"]
        )
        == decision["correct"]
        for decision
        in decisions_for(level, difficulty)
    ]

    passed = (
        sequence_correct
        and all(decision_results)
    )

    target = targets(
        level_index,
        difficulty,
    )

    if (
        passed
        and elapsed
        <= target["three_time"]
        and st.session_state.moves
        <= target["three_moves"]
    ):
        stars = 3

    elif (
        passed
        and elapsed
        <= target["two_time"]
        and st.session_state.moves
        <= target["two_moves"]
    ):
        stars = 2

    elif passed:
        stars = 1

    else:
        stars = 0

    current_mode_key = mode_key(
        level_index,
        difficulty,
    )

    previous_best = int(
        st.session_state.mode_stars.get(
            current_mode_key,
            0,
        )
    )

    new_points = 0

    if passed:
        st.session_state.completed_modes.add(
            current_mode_key
        )

        if stars > previous_best:
            gained_stars = (
                stars - previous_best
            )

            new_points = (
                gained_stars * 10
            )

            st.session_state.score += (
                new_points
            )

            st.session_state.mode_stars[
                current_mode_key
            ] = stars

        elif (
            current_mode_key
            not in st.session_state.mode_stars
        ):
            st.session_state.mode_stars[
                current_mode_key
            ] = stars

        # Force immediate save
        save_progress()
        flush_pending_browser_action()

    # Record statistics for this attempt (by level only)
    update_stats(level_index, elapsed, st.session_state.moves)
    
    # Update last played
    update_last_played(level_index)

    st.session_state.result = {
        "passed": passed,
        "sequence_correct": (
            sequence_correct
        ),
        "time": elapsed,
        "moves": st.session_state.moves,
        "stars": stars,
        "points": new_points,
        "difficulty": difficulty,
        "level_index": level_index,
    }

    st.session_state.show_hint = False

    navigate(
        "result",
        level_index,
    )


def image_data_uri(path):
    mime_type = "image/png"

    if path.suffix.lower() in {
        ".jpg",
        ".jpeg",
    }:
        mime_type = "image/jpeg"

    elif path.suffix.lower() == ".webp":
        mime_type = "image/webp"

    encoded_image = base64.b64encode(
        path.read_bytes()
    ).decode(
        "utf-8"
    )

    return (
        f"data:{mime_type};base64,"
        f"{encoded_image}"
    )



def encode_image_for_html(path):
    """Return a data URI for a local image path, or an empty string."""

    if path is None or not path.exists():
        return ""

    return image_data_uri(path)


def custom_puzzle_cards(level_index, difficulty, level):
    """Build the exact card list required for the selected mode."""

    correct_ids = correct_cards_for(
        level_index,
        level,
        difficulty,
    )

    wrong_count = (
        2
        if level_index == 0 and difficulty == "Hard"
        else DIFFICULTY_RULES[difficulty]["wrong_cards"]
    )

    card_ids = correct_ids.copy()
    card_ids.extend(level["wrong_cards"][:wrong_count])
    random.shuffle(card_ids)

    cards = []

    for card_id in card_ids:
        image_path = image_path_for_card(
            level_index,
            difficulty,
            card_id,
        )

        cards.append(
            {
                "id": card_id,
                "label": level["cards"].get(card_id, card_id),
                "image": encode_image_for_html(image_path),
            }
        )

    return cards


def submit_custom_result(payload):
    """Evaluate a result sent back from the custom HTML puzzle."""

    level_index = st.session_state.selected_level
    difficulty = st.session_state.difficulty
    level = LEVELS[level_index]

    # Accept the completed payload after the iframe reloads the main app.
    # The pending result is cleared when a new puzzle starts and again after
    # processing, so an attempt-ID comparison is unnecessary and would reject
    # valid results after a full page reload.
    sequence = payload.get("sequence", [])
    answers = payload.get("answers", {})
    moves = max(0, int(payload.get("moves", 0)))
    elapsed = max(0, int(payload.get("elapsed", 0)))

    required_sequence = correct_cards_for(
        level_index,
        level,
        difficulty,
    )

    sequence_correct = sequence == required_sequence

    relevant_decisions = decisions_for(
        level,
        difficulty,
    )

    decisions_correct = all(
        answers.get(decision["id"]) == decision["correct"]
        for decision in relevant_decisions
    )

    passed = sequence_correct and decisions_correct

    target = targets(
        level_index,
        difficulty,
    )

    if (
        passed
        and elapsed <= target["three_time"]
        and moves <= target["three_moves"]
    ):
        stars = 3
    elif (
        passed
        and elapsed <= target["two_time"]
        and moves <= target["two_moves"]
    ):
        stars = 2
    elif passed:
        stars = 1
    else:
        stars = 0

    current_mode_key = mode_key(
        level_index,
        difficulty,
    )

    previous_best = int(
        st.session_state.mode_stars.get(
            current_mode_key,
            0,
        )
    )

    new_points = 0

    if passed:
        st.session_state.completed_modes.add(
            current_mode_key
        )

        if stars > previous_best:
            gained_stars = stars - previous_best
            new_points = gained_stars * 10
            st.session_state.score += new_points
            st.session_state.mode_stars[current_mode_key] = stars
        elif current_mode_key not in st.session_state.mode_stars:
            st.session_state.mode_stars[current_mode_key] = stars

        # Force immediate save
        save_progress()
        flush_pending_browser_action()

    # Record statistics for this attempt (by level only)
    update_stats(level_index, elapsed, moves)
    
    # Update last played
    update_last_played(level_index)

    st.session_state.moves = moves
    st.session_state.start_time = time.time() - elapsed
    st.session_state.decision_answers = dict(answers)
    st.session_state.result = {
        "passed": passed,
        "sequence_correct": sequence_correct,
        "time": elapsed,
        "moves": moves,
        "stars": stars,
        "points": new_points,
        "difficulty": difficulty,
        "level_index": level_index,
    }
    st.session_state.show_hint = False
    st.session_state.custom_attempt_id = ""
    st.session_state.selected_picture_card = None
    st.session_state.screen = "result"

    active_player_id = current_player_id()
    active_player_name = current_player_name()

    st.query_params.clear()
    st.query_params[PLAYER_QUERY_KEY] = active_player_id
    st.query_params["player_name"] = active_player_name
    st.query_params["screen"] = "result"
    st.query_params["level"] = str(level_index)

    save_progress()
    flush_pending_browser_action()
    st.rerun()



# -----------------------------------------------------------------------------
# Picture layout helpers
# -----------------------------------------------------------------------------
def normalise_picture_layout(layout):
    cleaned = serialisable_layout(layout)
    if cleaned is None:
        return None
    for container in cleaned:
        container["items"] = [extract_card_id(item) for item in container["items"]]
    return cleaned


@st.dialog("DECISION QUESTION", width="medium")
def show_decision_question_dialog(level, pending_id):
    """Display the current decision question as a centred overlay popup."""

    decision = get_decision(level, pending_id)
    if decision is None:
        st.session_state.pending_decision = None
        return

    st.markdown(
        f"<div style='font-size:1.2rem;font-weight:800;margin-bottom:12px;'>"
        f"{decision['question']}</div>",
        unsafe_allow_html=True,
    )

    selected_answer = st.radio(
        "Choose your answer",
        decision["options"],
        index=None,
        key=f"decision_dialog_answer_{pending_id}",
        label_visibility="collapsed",
    )

    if st.button(
        "CONFIRM ANSWER",
        key=f"confirm_dialog_decision_{pending_id}",
        use_container_width=True,
    ):
        if selected_answer is None:
            st.warning("Choose one answer first.")
        else:
            st.session_state.decision_answers[pending_id] = selected_answer
            st.session_state.pending_decision = None
            save_progress()
            st.rerun()


def render_custom_image_puzzle():
    """Reliable native Streamlit picture-placement game.

    The player selects a picture and then presses PLACE HERE in a slot.
    This avoids iframe drag/drop restrictions on Streamlit Community Cloud.
    """

    level_index = st.session_state.selected_level
    difficulty = st.session_state.difficulty
    level = LEVELS[level_index]

    if st.session_state.layout is None:
        start_puzzle()
        return

    st.session_state.layout = normalise_picture_layout(st.session_state.layout)
    if st.session_state.previous_layout is not None:
        st.session_state.previous_layout = normalise_picture_layout(
            st.session_state.previous_layout
        )

    if "selected_picture_card" not in st.session_state:
        st.session_state.selected_picture_card = None

    def card_image(card_id):
        return image_path_for_card(level_index, difficulty, card_id)

    def render_clickable_picture(card_id, location_key, compact=False):
        """Show a reliable image-only card with a small select control.

        Streamlit Cloud does not consistently render local data-URI images as
        CSS button backgrounds. Using st.image keeps the scenario pictures
        visible on every rerun while preserving the comic card theme.
        """

        image_path = card_image(card_id)
        if image_path is None:
            st.info(f"Image missing: {card_id}")
            return

        selected = st.session_state.selected_picture_card == card_id
        safe_location = re.sub(r"[^A-Za-z0-9_]", "_", location_key)
        container_key = f"picture_card_{safe_location}"
        button_key = (
            f"select_picture_{safe_location}_"
            f"{st.session_state.custom_attempt_id}"
        )

        border_colour = "#ffca28" if selected else "#202124"
        background_colour = "#fff0ae" if selected else "#ffffff"
        image_width = 150 if compact else 175

        st.markdown(
            f"""
            <style>
            .st-key-{container_key} {{
                position: relative;
                background: {background_colour};
                border: 5px solid {border_colour};
                border-radius: 16px;
                box-shadow: 5px 5px 0 #202124;
                padding: 10px 10px 8px 10px;
                margin-bottom: 12px;
                overflow: visible;
            }}
            .st-key-{container_key} [data-testid="stImage"] {{
                display: flex;
                justify-content: center;
                margin: 0;
            }}
            .st-key-{container_key} [data-testid="stImage"] img {{
                border-radius: 10px;
                object-fit: contain;
                max-height: {145 if compact else 170}px;
            }}
            .st-key-{container_key} div.stButton > button {{
                min-height: 2.35rem !important;
                height: 2.35rem !important;
                padding: 0 !important;
                margin-top: 6px !important;
                background: {'#ffca28' if selected else '#20a43a'} !important;
                color: {'#202124' if selected else '#ffffff'} !important;
                border: 4px solid #202124 !important;
                border-radius: 9px !important;
                box-shadow: 4px 4px 0 #202124 !important;
                font-size: 1.15rem !important;
                line-height: 1 !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Get the description text for this card
        description = level["cards"].get(card_id, card_id)

        with st.container(key=container_key):
            st.image(image_path, width=image_width)
            # Show description text below the image
            st.markdown(
                f"""
                <div style="font-size:0.85rem;text-align:center;margin-top:6px;font-weight:700;color:#202124;background:#fffaf0;padding:4px 8px;border-radius:6px;border:2px solid #202124;">
                {description}
                </div>
                """,
                unsafe_allow_html=True,
            )
            button_label = "✓ SELECTED" if selected else "✓"
            if st.button(
                button_label,
                key=button_key,
                help="Select this picture",
                use_container_width=True,
            ):
                current = st.session_state.get("selected_picture_card")
                st.session_state.selected_picture_card = (
                    None if current == card_id else card_id
                )
                st.rerun()


    # ---------------------- STATUS AT THE TOP ---------------------
    status_1, status_2, status_3 = st.columns(3)
    with status_1:
        st.markdown(
            '<div class="stat-box"><div>DIFFICULTY</div>'
            f'<span>{difficulty}</span></div>',
            unsafe_allow_html=True,
        )
    with status_2:
        st.markdown(
            '<div class="stat-box"><div>MOVES</div>'
            f'<span>{st.session_state.moves}</span></div>',
            unsafe_allow_html=True,
        )
    with status_3:
        live_timer()

    # Show the decision question over the game as a centred popup.
    pending_id = st.session_state.pending_decision
    if pending_id:
        show_decision_question_dialog(level, pending_id)

    def move_selected_to(target_index):
        selected = st.session_state.get("selected_picture_card")
        if not selected:
            st.warning("Select one picture first.")
            return

        layout = copy.deepcopy(st.session_state.layout)
        old_sequence = sequence_from_layout(layout)

        source_index = None
        for index, container in enumerate(layout):
            if selected in container.get("items", []):
                source_index = index
                break

        if source_index is None:
            st.session_state.selected_picture_card = None
            st.warning("That picture is no longer available. Select it again.")
            return

        if source_index == target_index:
            st.session_state.selected_picture_card = None
            st.rerun()

        # A slot accepts only one picture. Return its old picture to the tray.
        if target_index > 0 and layout[target_index].get("items"):
            old_card = layout[target_index]["items"][0]
            if old_card != selected and old_card not in layout[0]["items"]:
                layout[0]["items"].append(old_card)
            layout[target_index]["items"] = []

        layout[source_index]["items"] = [
            item for item in layout[source_index].get("items", [])
            if item != selected
        ]

        if selected not in layout[target_index]["items"]:
            layout[target_index]["items"].append(selected)

        new_sequence = sequence_from_layout(layout)
        new_decision = detect_new_decision(level, old_sequence, new_sequence)

        st.session_state.layout = layout
        st.session_state.previous_layout = copy.deepcopy(layout)
        st.session_state.previous_sequence = list(new_sequence)
        st.session_state.moves += 1
        st.session_state.selected_picture_card = None

        if new_decision is not None and st.session_state.pending_decision is None:
            st.session_state.pending_decision = new_decision

        save_progress()
        st.rerun()

    # ---------------- HORIZONTAL CARD TRAY ----------------
    st.markdown('<div class="comic-panel">', unsafe_allow_html=True)
    st.markdown("### TRAY OF SCENARIOS")
    st.caption("Press the ✓ button below a picture, then press PLACE HERE in the correct story slot.")

    tray_ids = list(st.session_state.layout[0].get("items", []))

    if not tray_ids:
        st.success("All pictures have been placed.")
    else:
        tray_columns = st.columns(min(4, len(tray_ids)), gap="medium")

        for card_position, card_id in enumerate(tray_ids):
            with tray_columns[card_position % len(tray_columns)]:
                render_clickable_picture(
                    card_id,
                    f"tray_{card_position}_{card_id}",
                    compact=False,
                )

    selected_card = st.session_state.get("selected_picture_card")
    if selected_card:
        st.success("Picture selected. Choose a story slot below.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- SMALLER STORY SLOTS ----------------
    st.markdown("### STORY SEQUENCE")
    slot_total = len(st.session_state.layout) - 1

    for row_start in range(1, slot_total + 1, 3):
        slot_columns = st.columns(3, gap="medium")

        for offset in range(3):
            slot_index = row_start + offset
            if slot_index > slot_total:
                continue

            with slot_columns[offset]:
                st.markdown(
                    f"<div class='comic-panel' style='padding:12px;margin-bottom:12px;'>"
                    f"<h3 style='margin:0 0 7px 0;'>SCENARIO {slot_index}</h3>",
                    unsafe_allow_html=True,
                )

                slot_items = st.session_state.layout[slot_index].get("items", [])

                if slot_items:
                    card_id = slot_items[0]
                    render_clickable_picture(
                        card_id,
                        f"slot_{slot_index}_{card_id}",
                        compact=True,
                    )

                    if st.button(
                        "RETURN TO TRAY",
                        key=f"return_slot_{slot_index}_{st.session_state.custom_attempt_id}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_picture_card = card_id
                        move_selected_to(0)
                else:
                    st.markdown(
                        "<div style='height:115px;display:flex;align-items:center;"
                        "justify-content:center;border:4px dashed #202124;"
                        "border-radius:14px;font-weight:900;font-size:0.9rem;'>"
                        "EMPTY SCENARIO</div>",
                        unsafe_allow_html=True,
                    )

                if st.button(
                    "PLACE HERE",
                    key=f"place_slot_{slot_index}_{st.session_state.custom_attempt_id}",
                    use_container_width=True,
                    disabled=not bool(st.session_state.get("selected_picture_card")),
                ):
                    move_selected_to(slot_index)

                st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------- CONTROLS -------------------------
    control_back, control_restart, control_done = st.columns(3)
    with control_back:
        if st.button("BACK", key="puzzle_back_to_map", use_container_width=True):
            st.session_state.layout = None
            st.session_state.previous_layout = None
            st.session_state.previous_sequence = [None] * 6
            st.session_state.start_time = None
            st.session_state.pending_decision = None
            st.session_state.decision_answers = {}
            st.session_state.custom_attempt_id = ""
            st.session_state.selected_picture_card = None
            navigate("map")

    with control_restart:
        if st.button("RESTART", key="puzzle_restart", use_container_width=True):
            st.session_state.selected_picture_card = None
            start_puzzle()

    with control_done:
        if st.button("DONE", key="puzzle_done", use_container_width=True):
            if st.session_state.pending_decision is not None:
                st.warning("Confirm the current popup answer before pressing DONE.")
            elif not slots_complete(st.session_state.layout):
                st.warning("Place one picture in every scenario slot.")
            elif not decisions_complete(level):
                unanswered = [
                    d for d in decisions_for(level, difficulty)
                    if d["id"] not in st.session_state.decision_answers
                ]
                if unanswered:
                    st.session_state.pending_decision = unanswered[0]["id"]
                    st.warning("Answer all decision questions before pressing DONE.")
                    st.rerun()
            else:
                evaluate_level()



# -----------------------------------------------------------------------------
# PLAYER PROFILE GATE
# Every Player ID receives its own browser save and unfinished-attempt record.
# -----------------------------------------------------------------------------
query_player = normalise_player_id(st.query_params.get(PLAYER_QUERY_KEY, ""))

if not st.session_state.get("player_id") and query_player:
    st.session_state.player_id = query_player
    st.session_state.player_name = str(
        st.query_params.get("player_name", query_player)
    )[:30]

if not current_player_id():
    render_player_login()
    st.stop()


# Keep the active profile in the URL. This allows a new Streamlit Cloud
# session created by a page link or browser refresh to restore the same player
# instead of showing the login form again.
active_player_id = current_player_id()
active_player_name = current_player_name()

if st.query_params.get(PLAYER_QUERY_KEY) != active_player_id:
    st.query_params[PLAYER_QUERY_KEY] = active_player_id

if st.query_params.get("player_name") != active_player_name:
    st.query_params["player_name"] = active_player_name


browser_loaded = st.session_state.get(
    "browser_progress_loaded",
    False,
)

if not browser_loaded:
    browser_value = read_browser_progress()

    # streamlit-js-eval may temporarily return None on Streamlit Cloud,
    # especially after navigation creates a new page session. Do not stop
    # the whole app on a permanent loading screen. Continue with a clean
    # state for this session; saved progress can still be written normally
    # after the app has loaded.
    if browser_value is None:
        initialise_state(
            empty_progress()
        )
    else:
        initialise_state(
            sanitise_progress(
                browser_value
            )
        )

else:
    # State is already present in the active Streamlit session. Passing
    # defaults here does not overwrite existing values because
    # initialise_state only creates missing keys.
    initialise_state(
        empty_progress()
    )

flush_pending_browser_action()


query_screen = st.query_params.get(
    "screen"
)

query_level = st.query_params.get(
    "level"
)



custom_submit_value = st.query_params.get("puzzle_submit")

if custom_submit_value:
    try:
        padding = "=" * (-len(custom_submit_value) % 4)
        decoded = base64.urlsafe_b64decode(
            custom_submit_value + padding
        ).decode("utf-8")

        payload = json.loads(decoded)
        st.query_params.pop("puzzle_submit", None)
        st.session_state.screen = "puzzle"
        submit_custom_result(payload)

    except Exception as error:
        st.query_params.pop("puzzle_submit", None)
        st.error(
            "The puzzle result could not be processed. "
            "Please try the level again."
        )


VALID_SCREENS = {
    "home",
    "map",
    "difficulty",
    "scenario",
    "puzzle",
    "result",
    "score",
    "achievements",
}


if query_screen in VALID_SCREENS:
    st.session_state.screen = query_screen
elif query_screen is None and not st.query_params:
    # A clean localhost/cloud URL opens the main page.
    # Saved scores and stars remain available.
    st.session_state.screen = "home"


if query_level is not None:
    try:
        requested_level = int(
            query_level
        )

        if (
            0
            <= requested_level
            < len(LEVELS)
        ):
            st.session_state.selected_level = (
                requested_level
            )

    except ValueError:
        pass

    # Do not rerun here. The level number remains in the URL, so an
    # unconditional st.rerun() would create an endless rerun loop whenever
    # a player clicks a numbered level on the progress map. Continue directly
    # to render the selected level's difficulty page instead.


CSS = """
<style>
@import url(
'https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@400;700&display=swap'
);

:root {
    --dark: #202124;
    --green: #20a43a;
    --yellow: #ffca28;
    --red: #ef3e3e;
    --blue: #1565c0;
    --cream: #fffaf0;
}

.stApp {
    background:
        radial-gradient(
            circle at 12px 12px,
            rgba(32, 33, 36, 0.08) 2px,
            transparent 2px
        ),
        linear-gradient(
            180deg,
            #bfeaff 0%,
            #fff8dc 58%,
            #b9e99d 100%
        );

    background-size:
        28px 28px,
        cover;

    color: var(--dark);

    font-family:
        "Comic Neue",
        cursive;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stToolbar"] {
    visibility: hidden;
}

/* Hide the invisible JavaScript helper frames used for browser saving. */
iframe[title*="streamlit_js_eval"],
iframe[title*="streamlit-js-eval"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    border: 0 !important;
}

div[data-testid="stCustomComponentV1"]:has(
    iframe[title*="streamlit_js_eval"]
),
div[data-testid="stCustomComponentV1"]:has(
    iframe[title*="streamlit-js-eval"]
) {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Extra protection for zero-height helper component containers. */
div[data-testid="stCustomComponentV1"] iframe[height="0"] {
    display: none !important;
}

.block-container {
    max-width: 1180px;
    padding-top: 1rem;
    padding-bottom: 4rem;
}

h1,
h2,
h3 {
    font-family:
        "Bangers",
        cursive !important;

    letter-spacing: 2px;
}

.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;

    background: var(--blue);
    color: white;

    border: 5px solid var(--dark);
    border-radius: 16px;

    padding: 14px 20px;

    box-shadow:
        8px 8px 0
        var(--dark);

    margin-bottom: 22px;

    font-weight: 900;
}

.status-pill {
    display: inline-block;

    background: white;
    color: var(--dark);

    border: 4px solid var(--dark);
    border-radius: 10px;

    padding: 9px 15px;
    margin-left: 8px;

    box-shadow:
        4px 4px 0
        var(--dark);

    font-weight: 900;
}

.comic-panel {
    background: var(--cream);

    border: 5px solid var(--dark);
    border-radius: 18px;

    padding: 22px;

    box-shadow:
        9px 9px 0
        var(--dark);

    margin-bottom: 20px;
}

.comic-label {
    display: inline-block;

    background: var(--yellow);

    border: 4px solid var(--dark);
    border-radius: 10px;

    padding: 8px 18px;

    box-shadow:
        5px 5px 0
        var(--dark);

    font-family:
        "Bangers",
        cursive;

    font-size: 2rem;
    letter-spacing: 2px;

    margin-bottom: 16px;
}

.mode-card {
    background: var(--cream);

    border: 5px solid var(--dark);
    border-radius: 18px;

    padding: 22px;
    min-height: 220px;

    box-shadow:
        9px 9px 0
        var(--dark);

    margin-bottom: 16px;

    text-align: center;
}

.mode-card.locked {
    opacity: 0.42;
    filter: grayscale(1);
}

.mode-stars {
    font-size: 2rem;
    margin-top: 16px;
}

.lock-message {
    background: #eeeeee;

    border: 4px solid var(--dark);
    border-radius: 12px;

    padding: 12px;

    text-align: center;
    font-weight: 900;

    box-shadow:
        5px 5px 0
        var(--dark);

    margin-bottom: 12px;
}

.stat-box,
.result-card {
    width: 100%;

    background: white;
    color: var(--dark);

    border: 4px solid var(--dark);
    border-radius: 10px;

    box-shadow:
        4px 4px 0
        var(--dark);

    box-sizing: border-box;

    font-weight: 900;
    text-align: center;

    padding: 15px;
    margin-bottom: 12px;
}

.stat-box span {
    display: block;
    font-size: 1.7rem;
    margin-top: 4px;
}

.popup-question,
.hint-card {
    background: #fff0ae;
    color: #202124 !important;

    border: 4px solid var(--dark);
    border-radius: 14px;

    padding: 18px;

    box-shadow:
        6px 6px 0
        var(--dark);

    font-weight: 700;
    margin-bottom: 18px;
}

.popup-question,
.popup-question *,
.hint-card,
.hint-card * {
    color: #202124 !important;
}

.correct-title,
.wrong-title {
    font-family:
        "Bangers",
        cursive;

    font-size:
        clamp(
            4rem,
            9vw,
            7rem
        );

    -webkit-text-stroke:
        3px
        var(--dark);

    letter-spacing: 4px;
    text-align: center;
}

.correct-title {
    color: var(--green);

    text-shadow:
        6px 6px 0
        var(--yellow);
}

.wrong-title {
    color: var(--red);

    text-shadow:
        6px 6px 0
        white;
}

.big-stars {
    text-align: center;
    font-size: 4.2rem;
    letter-spacing: 8px;
    margin: 12px 0;
}

div.stButton > button {
    width: 100%;
    min-height: 3.8rem;

    border: 5px solid var(--dark);
    border-radius: 10px;

    background: var(--green);
    color: white;

    box-shadow:
        7px 7px 0
        var(--dark);

    font-family:
        "Bangers",
        cursive;

    font-size: 1.35rem;
    letter-spacing: 2px;
}

div.stButton > button:hover {
    background:
        var(--yellow)
        !important;

    color:
        var(--dark)
        !important;

    border-color:
        var(--dark)
        !important;
}

div.stButton > button:disabled {
    background:
        #bdbdbd
        !important;

    color:
        #5e5e5e
        !important;

    opacity:
        1
        !important;
}

.main-menu-wrap {
    position: relative;
    width: 100%;

    border: 7px solid var(--dark);
    border-radius: 20px;

    overflow: hidden;
    box-sizing: border-box;

    box-shadow:
        13px 13px 0
        var(--dark);
}

.main-menu-wrap img {
    display: block;
    width: 100%;
    height: auto;
}

.menu-hotspot {
    position: absolute;
    display: block;
    z-index: 1000;

    cursor: pointer;
    text-decoration: none;

    border-radius: 18px;

    background:
        rgba(
            255,
            255,
            255,
            0.001
        );
}

.menu-hotspot:hover {
    background:
        rgba(
            255,
            255,
            255,
            0.16
        );

    box-shadow:
        inset
        0 0 0 5px
        rgba(
            255,
            255,
            255,
            0.75
        );
}

.start-hotspot {
    left: 31.5%;
    top: 64.5%;
    width: 37%;
    height: 13%;
}

.achievement-hotspot {
    left: 14%;
    top: 82.5%;
    width: 33%;
    height: 14%;
}

.score-hotspot {
    left: 53%;
    top: 82.5%;
    width: 33%;
    height: 14%;
}

.progress-map-wrapper {
    position: relative;
    width: 100%;

    overflow: hidden;

    border: 7px solid var(--dark);
    border-radius: 24px;

    box-shadow:
        13px 13px 0
        var(--dark);

    background: white;

    margin-bottom: 26px;
}

.progress-map-wrapper img {
    display: block;
    width: 100%;
    height: auto;
}

.map-level-hotspot {
    position: absolute;
    z-index: 80;
    display: block;
    border-radius: 50%;
    text-decoration: none;
    box-sizing: border-box;
    background: rgba(255, 255, 255, 0.001);
}

/* Only unlocked levels behave like clickable buttons. */
.map-level-hotspot.unlocked {
    cursor: pointer;
}

.map-level-hotspot.unlocked:hover {
    background: rgba(255, 255, 255, 0.10);
    box-shadow: inset 0 0 0 5px rgba(255, 255, 255, 0.35);
}

/* Locked levels are not links and cannot be clicked. */
.map-level-hotspot.locked {
    cursor: not-allowed;
    pointer-events: none;
    background: transparent;
}

/*
Invisible hotspot positions aligned to the five circular level nodes
in progress_map.png. Percentages keep the alignment responsive.
*/
.map-level-1 {
    left: 7.2%;
    top: 45.0%;
    width: 12.0%;
    aspect-ratio: 1 / 1;
}

.map-level-2 {
    left: 26.0%;
    top: 37.0%;
    width: 12.0%;
    aspect-ratio: 1 / 1;
}

.map-level-3 {
    left: 44.4%;
    top: 25.8%;
    width: 12.0%;
    aspect-ratio: 1 / 1;
}

.map-level-4 {
    left: 62.8%;
    top: 7.4%;
    width: 12.0%;
    aspect-ratio: 1 / 1;
}

.map-level-5 {
    left: 85.0%;
    top: 5.8%;
    width: 12.0%;
    aspect-ratio: 1 / 1;
}

/* Do not place extra labels or total boxes over the artwork. */
.map-level-badge,
.map-progress-pill {
    display: none !important;
}

@media (max-width: 800px) {
    .top-bar {
        display: block;
        text-align: center;
    }

    .map-level-badge {
        font-size: 0.55rem;
        padding: 2px 4px;
    }

    .map-progress-pill {
        font-size: 0.9rem;
        padding: 5px 8px;
    }
}

.sortable-picture-card {
    min-width: 160px;
    max-width: 180px;
    padding: 8px;
    background: white;
    border: 3px solid #202124;
    border-radius: 12px;
    text-align: center;
    box-sizing: border-box;
}

[data-testid="stImage"] img {
    border-radius: 12px;
}

</style>
"""


st.markdown(
    CSS,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown(f"### Player: {current_player_name()}")
    st.caption(f"ID: {current_player_id()}")
    st.caption("Your progress and unfinished attempt are saved under this Player ID.")
    
    # Show save status
    save_key = browser_storage_key()
    st.caption(f"💾 Save key: `{save_key[:30]}...`")
    
    if st.session_state.get("layout") is not None and st.session_state.get("start_time") is not None:
        st.info("📌 You have an unfinished game")
    
    if st.button("SWITCH PLAYER", use_container_width=True):
        clear_runtime_game_state()
        st.session_state.pop("player_id", None)
        st.session_state.pop("player_name", None)
        st.query_params.clear()
        st.rerun()


def show_top_bar():
    top_bar_html = (
        '<div class="top-bar">'
        '<div>FIRST AID HEROES</div>'
        '<div>'
        f'<span class="status-pill">'
        f'Player: {current_player_name()}'
        f'</span>'
        f'<span class="status-pill">'
        f'Score: {st.session_state.score}'
        f'</span>'
        f'<span class="status-pill">'
        f'Stars: {total_stars()} / 27'
        f'</span>'
        '</div>'
        '</div>'
    )

    st.markdown(
        top_bar_html,
        unsafe_allow_html=True,
    )


def render_home():
    cover_path = (
        BASE_DIR
        / "main_cover.png"
    )

    if cover_path.exists():
        cover_uri = image_data_uri(
            cover_path
        )

        start_url = game_query_url("map")
        achievements_url = game_query_url("achievements")
        score_url = game_query_url("score")

        menu_html = (
            '<div class="main-menu-wrap">'
            f'<img src="{cover_uri}" '
            'alt="First Aid Heroes">'
            '<a '
            'class="menu-hotspot start-hotspot" '
            f'href="{start_url}" '
            'target="_self" '
            'aria-label="Start">'
            '</a>'
            '<a '
            'class="menu-hotspot achievement-hotspot" '
            f'href="{achievements_url}" '
            'target="_self" '
            'aria-label="Achievements">'
            '</a>'
            '<a '
            'class="menu-hotspot score-hotspot" '
            f'href="{score_url}" '
            'target="_self" '
            'aria-label="Score">'
            '</a>'
            '</div>'
        )

        st.markdown(
            menu_html,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            (
                '<div class="comic-panel" '
                'style="text-align:center;">'
                '<div class="comic-label">'
                'FIRST AID HEROES'
                '</div>'
                '<h2>'
                'Save a Life Through Learning'
                '</h2>'
                '<p>'
                'Add <b>main_cover.png</b> beside '
                'main.py to use your custom cover.'
                '</p>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        # Check if there's an unfinished attempt
        if st.session_state.get("layout") is not None and st.session_state.get("start_time") is not None:
            st.markdown(
                """
                <div style="text-align:center;padding:15px;margin-bottom:15px;
                            background:#fff0ae;border:4px solid #202124;border-radius:14px;
                            box-shadow:6px 6px 0 #202124;">
                    <span style="font-size:1.2rem;font-weight:bold;">⏳ You have an unfinished game!</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            continue_col1, continue_col2 = st.columns([1, 1])
            with continue_col1:
                if st.button("▶ CONTINUE GAME", use_container_width=True):
                    # Restore the game state
                    level_index = st.session_state.selected_level
                    navigate("puzzle", level_index)
            
            with continue_col2:
                if st.button("🗑 DISCARD AND START FRESH", use_container_width=True):
                    st.session_state.layout = None
                    st.session_state.previous_layout = None
                    st.session_state.previous_sequence = [None] * 6
                    st.session_state.start_time = None
                    st.session_state.pending_decision = None
                    st.session_state.decision_answers = {}
                    st.session_state.selected_picture_card = None
                    save_progress()
                    st.rerun()

        column_1, column_2, column_3 = (
            st.columns(3)
        )

        with column_1:
            if st.button(
                "START",
                use_container_width=True,
            ):
                navigate("map")

        with column_2:
            if st.button(
                "ACHIEVEMENTS",
                use_container_width=True,
            ):
                navigate(
                    "achievements"
                )

        with column_3:
            if st.button(
                "SCORE",
                use_container_width=True,
            ):
                navigate("score")


def render_map():
    map_path = BASE_DIR / "progress_map.png"

    if map_path.exists():
        map_uri = image_data_uri(map_path)
        hotspot_parts = []

        for level_index in range(len(LEVELS)):
            unlocked = level_unlocked(level_index)
            level_number = level_index + 1
            
            # Get stars for this level
            stars = level_star_total(level_index)
            
            # Create star display string
            if stars == 0:
                star_display = "☆☆☆"
            else:
                star_display = "⭐" * stars + "☆" * (3 - stars)

            if unlocked:
                # Only unlocked levels are real clickable links.
                hotspot_parts.append(
                    (
                        f'<a '
                        f'class="map-level-hotspot unlocked '
                        f'map-level-{level_number}" '
                        f'href="{game_query_url("difficulty", level_index)}" '
                        f'target="_self" '
                        f'title="Level {level_number}: {star_display}" '
                        f'aria-label="Open Level {level_number}">'
                        f'<span style="position:absolute;bottom:-30px;left:50%;transform:translateX(-50%);'
                        f'background:rgba(32,33,36,0.9);color:white;padding:3px 10px;border-radius:8px;'
                        f'font-size:0.75rem;white-space:nowrap;font-family:Arial,sans-serif;'
                        f'border:2px solid #ffca28;box-shadow:0 2px 8px rgba(0,0,0,0.3);">'
                        f'{star_display}'
                        f'</span>'
                        f'</a>'
                    )
                )
            else:
                # Locked levels are decorative only and cannot be pressed.
                hotspot_parts.append(
                    (
                        f'<div '
                        f'class="map-level-hotspot locked '
                        f'map-level-{level_number}" '
                        f'title="Complete Easy mode of Level '
                        f'{level_number - 1} to unlock">'
                        f'<span style="position:absolute;bottom:-30px;left:50%;transform:translateX(-50%);'
                        f'background:rgba(100,100,100,0.9);color:white;padding:3px 10px;border-radius:8px;'
                        f'font-size:0.7rem;white-space:nowrap;font-family:Arial,sans-serif;'
                        f'border:2px solid #666;box-shadow:0 2px 8px rgba(0,0,0,0.3);">'
                        f'🔒 LOCKED'
                        f'</span>'
                        f'</div>'
                    )
                )

        map_html = (
            '<div class="progress-map-wrapper" style="margin-bottom:60px;">'
            f'<img src="{map_uri}" alt="School Progress Map">'
            + "".join(hotspot_parts)
            + "</div>"
        )

        st.markdown(
            map_html,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            (
                '<div class="comic-panel">'
                '<div class="comic-label">'
                'PROGRESS MAP IMAGE MISSING'
                '</div>'
                '<p>'
                'Save your map beside main.py using the exact name '
                '<b>progress_map.png</b>.'
                '</p>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        columns = st.columns(len(LEVELS))

        for level_index, column in enumerate(columns):
            unlocked = level_unlocked(level_index)
            stars = level_star_total(level_index)

            with column:
                st.markdown(
                    (
                        '<div class="comic-panel" '
                        f'style="text-align:center;opacity:'
                        f'{1 if unlocked else 0.5};">'
                        f'<h2>LEVEL {level_index + 1}</h2>'
                        f'<p>{LEVELS[level_index]["title"]}</p>'
                        f'<div style="font-size:1.5rem;">'
                        f'{"⭐" * stars}{"☆" * (3 - stars)}'
                        f'</div>'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

                if st.button(
                    f"OPEN LEVEL {level_index + 1}",
                    key=f"fallback_level_{level_index}",
                    use_container_width=True,
                    disabled=not unlocked,
                ):
                    navigate("difficulty", level_index)

    if st.button(
        "BACK HOME",
        use_container_width=True,
    ):
        navigate("home")


if hasattr(
    st,
    "fragment",
):

    @st.fragment(
        run_every="1s"
    )
    def live_timer():
        elapsed = 0

        if (
            st.session_state.start_time
            is not None
        ):
            elapsed = max(
                0,
                int(
                    time.time()
                    - st.session_state.start_time
                ),
            )
        
        # Get time targets for color coding
        level_index = st.session_state.selected_level
        difficulty = st.session_state.difficulty
        target = targets(level_index, difficulty)
        
        # Determine color based on time relative to targets
        if elapsed <= target["three_time"]:
            color = "#20a43a"  # Green - good
        elif elapsed <= target["two_time"]:
            color = "#ffca28"  # Yellow - okay
        else:
            color = "#ef3e3e"  # Red - too slow
        
        # Add target times display
        target_text = f"Target: {target['two_time']}s / {target['three_time']}s"

        st.markdown(
            (
                f'<div class="stat-box" style="border-color:{color};">'
                '<div>TIME</div>'
                f'<span style="color:{color};font-size:2rem;">{elapsed}s</span>'
                f'<div style="font-size:0.7rem;margin-top:4px;color:#666;">{target_text}</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

else:

    def live_timer():
        elapsed = 0

        if (
            st.session_state.start_time
            is not None
        ):
            elapsed = max(
                0,
                int(
                    time.time()
                    - st.session_state.start_time
                ),
            )
        
        # Get time targets for color coding
        level_index = st.session_state.selected_level
        difficulty = st.session_state.difficulty
        target = targets(level_index, difficulty)
        
        # Determine color based on time relative to targets
        if elapsed <= target["three_time"]:
            color = "#20a43a"  # Green - good
        elif elapsed <= target["two_time"]:
            color = "#ffca28"  # Yellow - okay
        else:
            color = "#ef3e3e"  # Red - too slow
        
        # Add target times display
        target_text = f"Target: {target['two_time']}s / {target['three_time']}s"

        st.markdown(
            (
                f'<div class="stat-box" style="border-color:{color};">'
                '<div>TIME</div>'
                f'<span style="color:{color};font-size:2rem;">{elapsed}s</span>'
                f'<div style="font-size:0.7rem;margin-top:4px;color:#666;">{target_text}</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )


if hasattr(
    st,
    "dialog",
):

    @st.dialog(
        "Decision Point",
        width="small",
    )
    def decision_popup(decision):
        popup_image = image_path_for_card(
            st.session_state.selected_level,
            st.session_state.difficulty,
            decision["trigger"],
        )

        if popup_image is not None:
            st.image(
                str(popup_image),
                use_container_width=True,
            )

        st.markdown(
            (
                '<div class="popup-question">'
                f'{decision["question"]}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        widget_key = (
            f'popup_{decision["id"]}'
        )

        answer = st.radio(
            "Choose one answer:",
            decision["options"],
            index=None,
            key=widget_key,
        )

        st.caption(
            "The result will only be shown "
            "after you press DONE."
        )

        if st.button(
            "CONFIRM ANSWER",
            use_container_width=True,
        ):
            if answer is None:
                st.warning(
                    "Choose one answer first."
                )

            else:
                st.session_state.decision_answers[
                    decision["id"]
                ] = answer

                st.session_state.pending_decision = (
                    None
                )

                st.session_state.pop(
                    widget_key,
                    None,
                )

                save_progress()
                st.rerun()

else:

    def decision_popup(decision):
        st.error(
            "Please update Streamlit to use "
            "the decision popup."
        )



if hasattr(st, "fragment"):

    @st.fragment(run_every="250ms")
    def poll_custom_puzzle_result():
        """
        Check whether the custom drag-and-drop iframe submitted a result.
        This avoids blocked iframe navigation and opens the result page
        automatically after DONE is pressed.
        """

        storage_key_json = json.dumps(
            PUZZLE_RESULT_STORAGE_KEY
        )

        pending_result = streamlit_js_eval(
            js_expressions=(
                "window.localStorage.getItem("
                f"{storage_key_json}"
                ")"
            ),
            want_output=True,
            key="poll_custom_puzzle_result",
        )

        navigation_key_json = json.dumps(
            PUZZLE_NAV_STORAGE_KEY
        )

        pending_navigation = streamlit_js_eval(
            js_expressions=(
                "window.localStorage.getItem("
                f"{navigation_key_json}"
                ")"
            ),
            want_output=True,
            key="poll_custom_puzzle_navigation",
        )

        if pending_navigation:
            try:
                navigation_data = json.loads(
                    pending_navigation
                )

                navigation_attempt_id = str(
                    navigation_data.get(
                        "attempt_id",
                        "",
                    )
                )

                current_attempt_id = str(
                    st.session_state.get(
                        "custom_attempt_id",
                        "",
                    )
                )

                if (
                    not navigation_attempt_id
                    or navigation_attempt_id != current_attempt_id
                ):
                    streamlit_js_eval(
                        js_expressions=(
                            "window.localStorage.removeItem("
                            f"{navigation_key_json}"
                            "); true"
                        ),
                        want_output=False,
                        key=(
                            "clear_stale_custom_puzzle_navigation_"
                            f"{int(time.time())}"
                        ),
                    )
                    return

                target_screen = str(
                    navigation_data.get(
                        "screen",
                        "scenario",
                    )
                )

                target_level = int(
                    navigation_data.get(
                        "level",
                        st.session_state.selected_level,
                    )
                )

                streamlit_js_eval(
                    js_expressions=(
                        "window.localStorage.removeItem("
                        f"{navigation_key_json}"
                        "); true"
                    ),
                    want_output=False,
                    key=(
                        "clear_custom_puzzle_navigation_"
                        f"{int(time.time())}"
                    ),
                )

                navigate(
                    target_screen,
                    target_level,
                )

            except (
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ):
                streamlit_js_eval(
                    js_expressions=(
                        "window.localStorage.removeItem("
                        f"{navigation_key_json}"
                        "); true"
                    ),
                    want_output=False,
                    key=(
                        "clear_bad_custom_puzzle_navigation_"
                        f"{int(time.time())}"
                    ),
                )

        if pending_result:
            try:
                payload = json.loads(
                    pending_result
                )

                streamlit_js_eval(
                    js_expressions=(
                        "window.localStorage.removeItem("
                        f"{storage_key_json}"
                        "); true"
                    ),
                    want_output=False,
                    key="clear_custom_puzzle_result_after_submit",
                )

                submit_custom_result(
                    payload
                )

            except (
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ):
                streamlit_js_eval(
                    js_expressions=(
                        "window.localStorage.removeItem("
                        f"{storage_key_json}"
                        "); true"
                    ),
                    want_output=False,
                    key=(
                        "clear_bad_custom_puzzle_result_"
                        f"{int(time.time())}"
                    ),
                )


else:

    def poll_custom_puzzle_result():
        pass



screen = st.session_state.screen
if screen == "home":
    render_home()


elif screen == "map":
    show_top_bar()
    render_map()


elif screen == "difficulty":
    level_index = st.session_state.selected_level

    # Block users from opening a locked level by manually changing the URL.
    if not level_unlocked(level_index):
        st.warning(
            "This level is locked. Complete Easy mode of the previous level first."
        )

        if st.button(
            "BACK TO MAP",
            use_container_width=True,
        ):
            navigate("map")

        st.stop()

    show_top_bar()

    level = LEVELS[
        level_index
    ]

    st.markdown(
        (
            '<div class="comic-panel">'
            '<div class="comic-label">'
            'CHOOSE DIFFICULTY'
            '</div>'
            f'<h2>'
            f'LEVEL {level_index + 1}: '
            f'{level["title"]}'
            f'</h2>'
            f'<p>'
            f'{level["story"]}'
            f'</p>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    descriptions = {
        "Easy": (
            "Complete Easy to unlock Medium "
            "and the next level."
        ),
        "Medium": (
            "Complete Easy first "
            "to unlock Medium."
        ),
        "Hard": (
            "Complete Medium first "
            "to unlock Hard."
        ),
    }

    difficulty_columns = (
        st.columns(3)
    )

    for column, difficulty in zip(
        difficulty_columns,
        DIFFICULTIES,
    ):
        unlocked = difficulty_unlocked(
            level_index,
            difficulty,
        )

        stars = int(
            st.session_state.mode_stars.get(
                mode_key(
                    level_index,
                    difficulty,
                ),
                0,
            )
        )

        card_class = (
            "mode-card"
            if unlocked
            else "mode-card locked"
        )

        with column:
            st.markdown(
                (
                    f'<div class="{card_class}">'
                    f'<h2>'
                    f'{difficulty}'
                    f'</h2>'
                    f'<p>'
                    f'{descriptions[difficulty]}'
                    f'</p>'
                    f'<div class="mode-stars">'
                    f'{"★" * stars}'
                    f'{"☆" * (3 - stars)}'
                    f'</div>'
                    f'</div>'
                ),
                unsafe_allow_html=True,
            )

            if not unlocked:
                requirement = (
                    "EASY"
                    if difficulty == "Medium"
                    else "MEDIUM"
                )

                st.markdown(
                    (
                        '<div class="lock-message">'
                        f'🔒 COMPLETE {requirement}'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

            button_label = (
                f"CHOOSE {difficulty.upper()}"
                if unlocked
                else (
                    f"{difficulty.upper()} "
                    f"LOCKED"
                )
            )

            if st.button(
                button_label,
                key=(
                    f"choose_"
                    f"{level_index}_"
                    f"{difficulty}"
                ),
                use_container_width=True,
                disabled=not unlocked,
            ):
                st.session_state.difficulty = (
                    difficulty
                )

                navigate(
                    "scenario",
                    level_index,
                )

    if st.button(
        "BACK TO MAP",
        use_container_width=True,
    ):
        navigate("map")


elif screen == "scenario":
    show_top_bar()

    level_index = (
        st.session_state.selected_level
    )

    level = LEVELS[
        level_index
    ]

    st.markdown(
        (
            '<div class="comic-panel">'
            '<div class="comic-label">'
            'MISSION BRIEFING'
            '</div>'
            f'<h1>'
            f'{level["title"]}'
            f'</h1>'
            f'<p>'
            f'<b>Location:</b> '
            f'{level["setting"]}'
            f'</p>'
            f'<p>'
            f'<b>Difficulty:</b> '
            f'{st.session_state.difficulty}'
            f'</p>'
            f'<div class="result-card">'
            f'{level["story"]}'
            f'</div>'
            '<p>'
            'Arrange one card in each slot '
            'and answer every decision popup.'
            '</p>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    back_column, start_column = (
        st.columns(2)
    )

    with back_column:
        if st.button(
            "BACK",
            use_container_width=True,
        ):
            navigate(
                "difficulty",
                level_index,
            )

    with start_column:
        if st.button(
            "START MISSION",
            use_container_width=True,
        ):
            start_puzzle()


elif screen == "puzzle":
    show_top_bar()

    level_index = st.session_state.selected_level
    level = LEVELS[level_index]

    st.markdown(
        (
            '<div class="comic-panel">'
            '<div class="comic-label">'
            'ARRANGE THE STORY'
            '</div>'
            f'<h2>{level["title"]}</h2>'
            '<p>'
            'Click a picture to select it, then press PLACE HERE in the correct slot. '
            'Decision questions will appear after certain pictures are placed.'
            '</p>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    render_custom_image_puzzle()


elif screen == "result":
    show_top_bar()

    level_index = (
        st.session_state.selected_level
    )

    level = LEVELS[
        level_index
    ]

    result = (
        st.session_state.result
    )

    if result is None:
        st.warning(
            "No result is available."
        )

        if st.button(
            "BACK TO MAP",
            use_container_width=True,
        ):
            navigate("map")

    else:
        if result["passed"]:
            st.markdown(
                (
                    '<div class="correct-title">'
                    'CORRECT!'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                (
                    '<div class="big-stars">'
                    f'{"★" * result["stars"]}'
                    f'{"☆" * (3 - result["stars"])}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

            st.success(
                "Progress saved automatically."
            )

        else:
            st.markdown(
                (
                    '<div class="wrong-title">'
                    'WRONG!'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                (
                    '<div class="big-stars">'
                    '☆☆☆'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        result_values = [
            (
                "Difficulty",
                result["difficulty"],
            ),
            (
                "Sequence",
                (
                    "Correct"
                    if result["sequence_correct"]
                    else "Incorrect"
                ),
            ),
            (
                "Time",
                f'{result["time"]} sec',
            ),
            (
                "Moves",
                str(
                    result["moves"]
                ),
            ),
        ]

        result_columns = st.columns(
            len(result_values)
        )

        for column, result_item in zip(
            result_columns,
            result_values,
        ):
            title, value = result_item

            with column:
                st.markdown(
                    (
                        '<div class="result-card">'
                        f'<b>{title}</b>'
                        '<br>'
                        f'{value}'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

        # Add score animation if points were earned
        if result["passed"] and result["points"] > 0:
            st.balloons()
            st.markdown(
                f"""
                <div style="text-align:center;padding:20px;margin:10px 0;
                            background:#ffca28;border:5px solid #202124;border-radius:18px;
                            box-shadow:8px 8px 0 #202124;animation:pulse 1.5s ease-in-out;">
                    <div style="font-family:'Bangers',cursive;font-size:3rem;color:#202124;">
                        +{result['points']} POINTS!
                    </div>
                    <div style="font-size:1rem;color:#202124;">
                        ⭐ {result['stars']} stars earned!
                    </div>
                </div>
                <style>
                @keyframes pulse {{
                    0% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.05); }}
                    100% {{ transform: scale(1); }}
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )

        # Show statistics comparison (by level)
        avg_time, avg_moves, best_time, best_moves, attempts = get_average_stats(
            level_index
        )
        
        if attempts is not None and attempts > 0:
            st.markdown(
                (
                    '<div class="comic-panel" style="margin-top:20px;">'
                    '<h3 style="margin-top:0;">📊 LEVEL STATISTICS</h3>'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )
            
            stat_cols = st.columns(4)
            
            with stat_cols[0]:
                st.metric(
                    "Your Time",
                    f"{result['time']}s",
                    delta=f"{avg_time - result['time']}s vs avg" if result['time'] < avg_time else None,
                    delta_color="normal" if result['time'] < avg_time else "inverse"
                )
            
            with stat_cols[1]:
                st.metric(
                    "Your Moves",
                    f"{result['moves']}",
                    delta=f"{avg_moves - result['moves']} vs avg" if result['moves'] < avg_moves else None,
                    delta_color="normal" if result['moves'] < avg_moves else "inverse"
                )
            
            with stat_cols[2]:
                if best_time is not None:
                    st.metric(
                        "Best Time",
                        f"{best_time}s",
                        delta="🏆" if result['time'] == best_time else None
                    )
            
            with stat_cols[3]:
                if best_moves is not None:
                    st.metric(
                        "Best Moves",
                        f"{best_moves}",
                        delta="🏆" if result['moves'] == best_moves else None
                    )
            
            st.caption(f"Total attempts for this level: {attempts}")
            
            # Show last played
            last_played = get_last_played(level_index)
            if last_played:
                st.caption(f"Last played: {format_last_played(last_played)}")

        if result["passed"]:
            if (
                result["difficulty"]
                == "Easy"
            ):
                st.success(
                    "Medium mode and the next "
                    "level are now unlocked."
                )

            elif (
                result["difficulty"]
                == "Medium"
            ):
                st.success(
                    "Hard mode is now unlocked."
                )

            else:
                st.success(
                    "Hard mode completion "
                    "has been saved."
                )

            retry_column, map_column, next_column = (
                st.columns(3)
            )

            with retry_column:
                if st.button(
                    "TRY AGAIN",
                    key="passed_result_retry",
                    use_container_width=True,
                ):
                    start_puzzle()

            with map_column:
                if st.button(
                    "MAP",
                    key="passed_result_map",
                    use_container_width=True,
                ):
                    navigate("map")

            with next_column:
                if (
                    result["difficulty"]
                    == "Easy"
                ):
                    next_button_label = (
                        "PLAY MEDIUM"
                    )

                    next_difficulty = (
                        "Medium"
                    )

                elif (
                    result["difficulty"]
                    == "Medium"
                ):
                    next_button_label = (
                        "PLAY HARD"
                    )

                    next_difficulty = (
                        "Hard"
                    )

                else:
                    next_button_label = (
                        "NEXT LEVEL"
                    )

                    next_difficulty = None

                if st.button(
                    next_button_label,
                    key="passed_result_next",
                    use_container_width=True,
                ):
                    if next_difficulty is not None:
                        st.session_state.difficulty = (
                            next_difficulty
                        )

                        navigate(
                            "scenario",
                            level_index,
                        )

                    else:
                        next_level = (
                            level_index + 1
                        )

                        if next_level < len(
                            LEVELS
                        ):
                            st.session_state.selected_level = (
                                next_level
                            )

                            navigate(
                                "difficulty",
                                next_level,
                            )

                        else:
                            navigate("map")

        else:
            home_column, hint_column, retry_column = (
                st.columns(3)
            )

            with home_column:
                if st.button(
                    "HOME",
                    key="failed_result_home",
                    use_container_width=True,
                ):
                    navigate("home")

            with hint_column:
                if st.button(
                    "HINT",
                    key="failed_result_hint",
                    use_container_width=True,
                ):
                    st.session_state.show_hint = (
                        True
                    )

                    st.rerun()

            with retry_column:
                if st.button(
                    "TRY AGAIN",
                    key="failed_result_retry",
                    use_container_width=True,
                ):
                    start_puzzle()

            if st.session_state.show_hint:
                st.markdown(
                    (
                        '<div class="hint-card">'
                        '<b>Hint:</b> '
                        f'{level["hint"]}'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )


elif screen == "score":
    show_top_bar()

    st.markdown(
        (
            '<div class="comic-panel" '
            'style="text-align:center;">'
            '<div class="comic-label">'
            'SCORE & STATISTICS'
            '</div>'
            f'<h1>'
            f'{st.session_state.score} POINTS'
            f'</h1>'
            f'<h2>'
            f'{total_stars()} / 27 STARS'
            f'</h2>'
            f'<p>'
            f'Completed modes: '
            f'{len(st.session_state.completed_modes)} '
            f'/ 9'
            f'</p>'
            '<p>'
            'Progress is automatically saved for '
            '<b>this browser user</b>.'
            '</p>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    for level_index, level in enumerate(
        LEVELS
    ):
        # Get statistics for this level (combined across all difficulties)
        avg_time, avg_moves, best_time, best_moves, attempts = get_average_stats(
            level_index
        )
        
        st.markdown(
            (
                '<div class="comic-panel">'
                f'<h2>'
                f'LEVEL {level_index + 1}: '
                f'{level["title"]}'
                f'</h2>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )
        
        # Show level statistics
        if attempts is not None and attempts > 0:
            st.markdown(
                (
                    f'<div style="text-align:center;padding:12px;margin-bottom:12px;'
                    f'background:#e3f2fd;border-radius:12px;border:3px solid #1565c0;">'
                    f'<b>📊 LEVEL STATISTICS</b><br>'
                    f'Average Time: <b>{avg_time}s</b> | '
                    f'Average Moves: <b>{avg_moves}</b><br>'
                    f'Best Time: <b>{best_time}s</b> | '
                    f'Best Moves: <b>{best_moves}</b><br>'
                    f'Total Attempts: <b>{attempts}</b>'
                    f'</div>'
                ),
                unsafe_allow_html=True,
            )
            
            # Show last played
            last_played = get_last_played(level_index)
            if last_played:
                st.caption(f"Last played: {format_last_played(last_played)}")
        else:
            st.markdown(
                (
                    f'<div style="text-align:center;padding:12px;margin-bottom:12px;'
                    f'color:#999;font-style:italic;">'
                    f'No attempts recorded for this level yet'
                    f'</div>'
                ),
                unsafe_allow_html=True,
            )

        mode_columns = st.columns(
            3
        )

        for column, difficulty in zip(
            mode_columns,
            DIFFICULTIES,
        ):
            stars = int(
                st.session_state.mode_stars.get(
                    mode_key(
                        level_index,
                        difficulty,
                    ),
                    0,
                )
            )

            completed = mode_completed(
                level_index,
                difficulty,
            )

            unlocked = (
                level_unlocked(
                    level_index
                )
                and difficulty_unlocked(
                    level_index,
                    difficulty,
                )
            )

            if completed:
                status = "✅ Completed"
            elif unlocked:
                status = "🔓 Unlocked"
            else:
                status = "🔒 Locked"

            with column:
                st.markdown(
                    (
                        '<div class="result-card">'
                        f'<b>'
                        f'{difficulty}'
                        f'</b>'
                        '<br>'
                        f'{"★" * stars}'
                        f'{"☆" * (3 - stars)}'
                        '<br>'
                        f'{status}'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

    back_column, reset_column = (
        st.columns(2)
    )

    with back_column:
        if st.button(
            "BACK HOME",
            use_container_width=True,
        ):
            navigate("home")

    with reset_column:
        if st.button(
            "RESET ALL PROGRESS",
            use_container_width=True,
        ):
            reset_saved_progress()

            st.success(
                "All saved progress "
                "has been reset."
            )

            st.rerun()


elif screen == "achievements":
    show_top_bar()

    completed_mode_count = len(
        st.session_state.completed_modes
    )

    achievements = [
        (
            "FIRST STEP",
            completed_mode_count >= 1,
        ),
        (
            "HELPER HERO",
            completed_mode_count >= 3,
        ),
        (
            "LIFE SAVER",
            completed_mode_count >= 6,
        ),
        (
            "FIRST AID LEGEND",
            completed_mode_count >= 9,
        ),
        (
            "STAR COLLECTOR",
            total_stars() >= 18,
        ),
        (
            "PERFECT HERO",
            total_stars() >= 27,
        ),
    ]

    st.markdown(
        (
            '<div class="comic-label">'
            'ACHIEVEMENTS'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    achievement_columns = (
        st.columns(2)
    )

    for index, achievement in enumerate(
        achievements
    ):
        name, unlocked = achievement

        with achievement_columns[
            index % 2
        ]:
            st.markdown(
                (
                    '<div class="comic-panel" '
                    'style="text-align:center;">'
                    f'<h2>'
                    f'{name}'
                    f'</h2>'
                    f'<p>'
                    f'{"UNLOCKED" if unlocked else "LOCKED"}'
                    f'</p>'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

    if st.button(
        "BACK HOME",
        use_container_width=True,
    ):
        navigate("home")
