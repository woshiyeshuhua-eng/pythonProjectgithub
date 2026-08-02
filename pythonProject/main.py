import base64
import copy
import json
import random
import re
import time
import urllib.parse
from pathlib import Path

import streamlit as st
from streamlit_js_eval import streamlit_js_eval


st.set_page_config(
    page_title="First Aid Heroes",
    page_icon="🩹",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
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
        "correct_cards": ["L1-1", "L1-2", "L1-3", "L1-4", "L1-5", "L1-6"],
        "wrong_cards": ["L1-W1", "L1-W2"],
        "cards": {
            # Easy mode cards (first 4)
            "L1-1": "Notify a teacher",
            "L1-2": "Pinch the bridge of the nose",
            "L1-3": "Continue pinching",
            "L1-4": "Check for any bleeding",
            # Medium mode cards (6 total)
            "L1-5": "Student realises",
            "L1-6": "Retrieve ice pack",
            # Hard mode cards (8 total, including 2 new ones)
            "L1-7": "Friend seeks help",
            "L1-8": "Squeeze ice pack",
            "L1-9": "Apply ice pack on bridge of the nose",
            # Wrong cards
            "L1-W1": "Open the ice pack",
            "L1-W2": "Tilt head back",
        },
        "decisions": [
            {
                "id": "easy_pinching_time",
                "difficulty": "Easy",
                "trigger": "L1-2",
                "question": "How long do you pinch the nose?",
                "options": ["5-10 mins", "10-15 mins", "20-30 mins"],
                "correct": "10-15 mins",
            },
            {
                "id": "easy_pinching_place",
                "difficulty": "Easy",
                "trigger": "L1-2",
                "question": "Where do you pinch the nose?",
                "options": [
                    "Below bridge of the nose",
                    "On the hard bone of the nose",
                ],
                "correct": "Below bridge of the nose",
            },
            {
                "id": "medium_compress",
                "difficulty": "Medium",
                "trigger": "L1-5",
                "question": "What compress do you use?",
                "options": ["Warm", "Hot", "Cold", "Cool"],
                "correct": "Cool",
            },
            {
                "id": "hard_ask_teacher",
                "difficulty": "Hard",
                "trigger": "L1-3",
                "question": "What do you ask the teacher to bring?",
                "options": ["AED", "First Aid Bag", "Nothing"],
                "correct": "First Aid Bag",
            },
            {
                "id": "hard_pinching_time",
                "difficulty": "Hard",
                "trigger": "L1-2",
                "question": "How long do you pinch the nose?",
                "options": ["5-10 mins", "10-15 mins", "20-30 mins"],
                "correct": "10-15 mins",
            },
            {
                "id": "hard_compress_time",
                "difficulty": "Hard",
                "trigger": "L1-7",
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
        "correct_cards": ["L3-1", "L3-2", "L3-3", "L3-4", "L3-5", "L3-6"],
        "wrong_cards": ["L3-W1", "L3-W2", "L3-W3"],
        "cards": {
            "L3-1": "Student trips and falls in the corridor",
            "L3-2": "Helper checks that the area is safe",
            "L3-3": "Helper checks the student before moving them",
            "L3-4": "Teacher is informed",
            "L3-5": "The wound is cleaned with clean materials",
            "L3-6": "A clean dressing is applied",
            "L3-W1": "Helper immediately pulls the student up",
            "L3-W2": "The wound is cleaned with a dirty tissue",
            "L3-W3": "The injured student is left alone",
        },
        "decisions": [
            {
                "id": "fall_move",
                "trigger": "L3-3",
                "question": "Should the student be pulled up immediately?",
                "options": [
                    "No, check for injury first",
                    "Yes, pull the student up",
                ],
                "correct": "No, check for injury first",
            },
            {
                "id": "fall_clean",
                "trigger": "L3-5",
                "question": "What should be used to clean the wound?",
                "options": [
                    "Clean water and clean materials",
                    "Dirty tissue",
                ],
                "correct": "Clean water and clean materials",
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
        "correct_cards": ["L4-1", "L4-2", "L4-3", "L4-4", "L4-5", "L4-6"],
        "wrong_cards": ["L4-W1", "L4-W2", "L4-W3"],
        "cards": {
            "L4-1": "Student feels dizzy",
            "L4-2": "Student faints",
            "L4-3": "Helper checks responsiveness and breathing",
            "L4-4": "No food or drink is given while unconscious",
            "L4-5": "Teacher and school staff are called",
            "L4-6": "Helper stays and monitors the student",
            "L4-W1": "Food is given while the student is unconscious",
            "L4-W2": "The student is left alone",
            "L4-W3": "The student is forced to stand immediately",
        },
        "decisions": [
            {
                "id": "faint_food",
                "trigger": "L4-4",
                "question": "Should food or drink be given while unconscious?",
                "options": ["No", "Yes"],
                "correct": "No",
            },
            {
                "id": "faint_stay",
                "trigger": "L4-6",
                "question": "What should the helper do?",
                "options": [
                    "Stay and monitor",
                    "Leave the student alone",
                ],
                "correct": "Stay and monitor",
            },
        ],
        "hint": (
            "Check responsiveness and breathing, "
            "call for help and continue monitoring."
        ),
    },
    {
        "title": "Chemical Splash",
        "setting": "Science Laboratory",
        "story": (
            "A chemical splashes onto a student's hand "
            "during an experiment."
        ),
        "correct_cards": ["L5-1", "L5-2", "L5-3", "L5-4", "L5-5", "L5-6"],
        "wrong_cards": ["L5-W1", "L5-W2", "L5-W3"],
        "cards": {
            "L5-1": "Chemical splashes onto the student's hand",
            "L5-2": "Student moves away from the chemical",
            "L5-3": "Teacher is informed immediately",
            "L5-4": "The affected area is rinsed with running water",
            "L5-5": "The area is rinsed before it is covered",
            "L5-6": "Teacher continues to monitor the student",
            "L5-W1": "Another chemical is applied",
            "L5-W2": "The area is covered before rinsing",
            "L5-W3": "The chemical is wiped using bare hands",
        },
        "decisions": [
            {
                "id": "chemical_rinse",
                "trigger": "L5-4",
                "question": "What should be used to rinse the chemical?",
                "options": [
                    "Running water",
                    "Another chemical",
                ],
                "correct": "Running water",
            },
            {
                "id": "chemical_cover",
                "trigger": "L5-5",
                "question": "Should the area be covered before rinsing?",
                "options": [
                    "No, rinse first",
                    "Yes, cover it immediately",
                ],
                "correct": "No, rinse first",
            },
        ],
        "hint": (
            "Move away from danger, alert the teacher "
            "and rinse thoroughly with running water."
        ),
    },    {
        "title": "Burn Injury",
        "setting": "School Canteen",
        "story": "A student accidentally touches a hot surface and suffers a minor burn.",
        "correct_cards": ["L5-1", "L5-2", "L5-3", "L5-4", "L5-5", "L5-6"],
        "wrong_cards": ["L5-W1", "L5-W2", "L5-W3"],
        "cards": {
            "L5-1": "Move the student away from the heat source",
            "L5-2": "Inform a teacher or responsible adult",
            "L5-3": "Cool the burn under cool running water",
            "L5-4": "Remove nearby jewellery if it is safe",
            "L5-5": "Cover the burn loosely with a clean dressing",
            "L5-6": "Continue monitoring and seek medical help if needed",
            "L5-W1": "Put ice directly on the burn",
            "L5-W2": "Apply toothpaste or butter",
            "L5-W3": "Break any blisters",
        },
        "decisions": [
            {
                "id": "burn_water",
                "trigger": "L5-3",
                "question": "What should be used to cool a minor burn?",
                "options": ["Cool running water", "Ice directly on the skin"],
                "correct": "Cool running water",
            },
            {
                "id": "burn_cover",
                "trigger": "L5-5",
                "question": "How should the burn be covered?",
                "options": ["Loosely with a clean dressing", "Tightly with a dirty cloth"],
                "correct": "Loosely with a clean dressing",
            },
        ],
        "hint": "Cool the burn with cool running water and cover it loosely with a clean dressing.",
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
    {
        "three_time": 80,
        "three_moves": 15,
        "two_time": 110,
        "two_moves": 22,
    },
    {
        "three_time": 90,
        "three_moves": 16,
        "two_time": 120,
        "two_moves": 24,
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



def initialise_state(saved_progress):
    """Initialise the game and restore the last unfinished attempt."""

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
    Level 4 <- Level 3 Easy
    Level 5 <- Level 4 Easy
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
    """Easy uses 4 slots. Medium and Hard use 6 slots for Level 1."""

    if int(level_index) == 0:
        return 4 if difficulty == "Easy" else 6

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

    Popup questions are NOT determined by the filename.
    They are linked by the internal card ID (trigger),
    so you can safely rename your images to the format above.
    """

    for extension in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = BASE_DIR / f"{filename_without_extension}{extension}"
        if candidate.exists():
            return candidate

    return None


def image_path_for_card(level_index, difficulty, card_id):
    """
    Convert an internal card ID such as L1-2 or L1-W1 into:
    L1_E_2, L1_M_2
