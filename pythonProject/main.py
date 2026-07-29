import base64
import copy
import json
import random
import time
from pathlib import Path

import streamlit as st
from streamlit_sortables import sort_items
from streamlit_js_eval import streamlit_js_eval


st.set_page_config(
    page_title="First Aid Heroes",
    page_icon="🩹",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
BROWSER_STORAGE_KEY = "first_aid_heroes_progress_v2"
NO_BROWSER_SAVE = "__NO_FIRST_AID_SAVE__"
DIFFICULTIES = ["Easy", "Medium", "Hard"]


LEVELS = [
    {
        "title": "Sprained Ankle",
        "setting": "Basketball Court",
        "story": "A student lands badly during basketball and injures the ankle.",
        "correct_cards": ["L1-1", "L1-2", "L1-3", "L1-4", "L1-5", "L1-6"],
        "wrong_cards": ["L1-W1", "L1-W2", "L1-W3"],
        "cards": {
            "L1-1": "Student lands badly and injures the ankle",
            "L1-2": "Student sits down and rests",
            "L1-3": "Friend informs the teacher and gets first aid",
            "L1-4": "Friend asks where it hurts",
            "L1-5": "Wrapped ice pack is applied for 15–20 minutes",
            "L1-6": "Elastic bandage is wrapped and the leg is elevated",
            "L1-W1": "Friend twists or pulls the injured ankle",
            "L1-W2": "Ice pack is placed directly on the skin",
            "L1-W3": "Student stands and walks immediately",
        },
        "decisions": [
            {
                "id": "ankle_check",
                "trigger": "L1-4",
                "question": "What should the friend do?",
                "options": ["Ask where it hurts", "Twist or pull the ankle"],
                "correct": "Ask where it hurts",
            },
            {
                "id": "ankle_ice",
                "trigger": "L1-5",
                "question": "How should the ice pack be applied?",
                "options": [
                    "Wrap it in a cloth first",
                    "Place it directly on the skin",
                ],
                "correct": "Wrap it in a cloth first",
            },
        ],
        "hint": (
            "Rest the ankle, use a wrapped cold pack, "
            "apply gentle compression and elevate it."
        ),
    },
    {
        "title": "Nosebleed",
        "setting": "Classroom",
        "story": "A student suddenly develops a nosebleed during class.",
        "correct_cards": ["L2-1", "L2-2", "L2-3", "L2-4", "L2-5", "L2-6"],
        "wrong_cards": ["L2-W1", "L2-W2", "L2-W3"],
        "cards": {
            "L2-1": "Student notices that the nose is bleeding",
            "L2-2": "Student sits upright",
            "L2-3": "Student leans slightly forward",
            "L2-4": "Soft part of the nose is pinched",
            "L2-5": "Pressure is maintained continuously",
            "L2-6": "Teacher monitors the student",
            "L2-W1": "Student tilts the head backwards",
            "L2-W2": "Student lies flat",
            "L2-W3": "Student checks the nose every few seconds",
        },
        "decisions": [
            {
                "id": "nose_position",
                "trigger": "L2-3",
                "question": "How should the student position the head?",
                "options": [
                    "Lean slightly forward",
                    "Tilt the head backwards",
                ],
                "correct": "Lean slightly forward",
            },
            {
                "id": "nose_pressure",
                "trigger": "L2-4",
                "question": "Where should pressure be applied?",
                "options": [
                    "Soft part of the nose",
                    "Bridge of the nose",
                ],
                "correct": "Soft part of the nose",
            },
        ],
        "hint": (
            "Sit upright, lean slightly forward and pinch "
            "the soft part of the nose continuously."
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
        "wrong_cards": 1,
    },
    "Medium": {
        "time_multiplier": 1.00,
        "move_multiplier": 1.00,
        "wrong_cards": 2,
    },
    "Hard": {
        "time_multiplier": 0.75,
        "move_multiplier": 0.85,
        "wrong_cards": 3,
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
        BROWSER_STORAGE_KEY
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
        key="load_first_aid_browser_progress",
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
            ),
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
    }


def build_progress_payload():
    """Create the complete save file for this browser user."""

    data = {
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
        BROWSER_STORAGE_KEY
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
                and len(layout) >= 7
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

                previous_sequence = attempt.get(
                    "previous_sequence",
                    [None] * 6,
                )

                if not isinstance(
                    previous_sequence,
                    list,
                ):
                    previous_sequence = [None] * 6

                st.session_state.previous_sequence = (
                    list(previous_sequence[:6])
                    + [None] * 6
                )[:6]

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
    st.session_state.screen = (
        screen_name
    )

    st.query_params["screen"] = (
        screen_name
    )
    if level_index is not None:
        st.session_state.selected_level = int(
            level_index
        )

        st.query_params["level"] = str(
            level_index
        )

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


def card_text(
    level,
    card_id,
):
    return (
        f"{card_id} | "
        f"{level['cards'][card_id]}"
    )


def extract_card_id(item):
    return item.split(
        " | ",
        1,
    )[0]


def start_puzzle():
    level_index = (
        st.session_state.selected_level
    )

    difficulty = (
        st.session_state.difficulty
    )

    level = LEVELS[
        level_index
    ]

    wrong_count = DIFFICULTY_RULES[
        difficulty
    ]["wrong_cards"]

    card_ids = (
        level["correct_cards"].copy()
    )

    card_ids.extend(
        level["wrong_cards"][
            :wrong_count
        ]
    )

    random.shuffle(
        card_ids
    )

    layout = [
        {
            "header": "CARD TRAY",
            "items": [
                card_text(
                    level,
                    card_id,
                )
                for card_id
                in card_ids
            ],
        }
    ]

    for slot_number in range(
        1,
        7,
    ):
        layout.append(
            {
                "header": (
                    f"SLOT {slot_number}"
                ),
                "items": [],
            }
        )

    st.session_state.layout = (
        copy.deepcopy(layout)
    )

    st.session_state.previous_layout = (
        copy.deepcopy(layout)
    )

    st.session_state.previous_sequence = (
        [None] * 6
    )

    st.session_state.moves = 0
    st.session_state.start_time = time.time()
    st.session_state.decision_answers = {}
    st.session_state.pending_decision = None
    st.session_state.result = None
    st.session_state.show_hint = False
    st.session_state.slot_warning = False
    st.session_state.sort_key += 1

    navigate(
        "puzzle",
        level_index,
    )


def sequence_from_layout(layout):
    sequence = []

    for slot in layout[1:7]:
        if len(slot["items"]) == 1:
            sequence.append(
                extract_card_id(
                    slot["items"][0]
                )
            )

        else:
            sequence.append(None)

    return sequence


def slots_complete(layout):
    if not layout:
        return False

    if len(layout) < 7:
        return False

    return all(
        len(
            layout[index]["items"]
        ) == 1
        for index
        in range(
            1,
            7,
        )
    )


def limit_one_card_per_slot(layout):
    corrected = copy.deepcopy(
        layout
    )

    previous = (
        st.session_state.previous_layout
    )

    returned_cards = []
    changed = False

    for slot_index in range(
        1,
        7,
    ):
        items = list(
            corrected[
                slot_index
            ]["items"]
        )

        if len(items) <= 1:
            continue

        changed = True
        card_to_keep = None

        if (
            previous
            and len(previous) > slot_index
            and previous[
                slot_index
            ]["items"]
        ):
            previous_item = previous[
                slot_index
            ]["items"][0]

            if previous_item in items:
                card_to_keep = (
                    previous_item
                )

        if card_to_keep is None:
            card_to_keep = items[0]

        kept_once = False
        extra_cards = []

        for item in items:
            if (
                item == card_to_keep
                and not kept_once
            ):
                kept_once = True

            else:
                extra_cards.append(
                    item
                )

        corrected[
            slot_index
        ]["items"] = [
            card_to_keep
        ]

        returned_cards.extend(
            extra_cards
        )

    for item in returned_cards:
        if item not in corrected[0]["items"]:
            corrected[0]["items"].append(
                item
            )

    return (
        corrected,
        changed,
    )


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

    for decision in level["decisions"]:
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
    for decision in level["decisions"]:
        if (
            decision["id"]
            == decision_id
        ):
            return decision

    return None


def decisions_complete(level):
    return all(
        decision["id"]
        in st.session_state.decision_answers
        for decision
        in level["decisions"]
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

    sequence_correct = (
        sequence
        == level["correct_cards"]
    )

    decision_results = [
        st.session_state.decision_answers.get(
            decision["id"]
        )
        == decision["correct"]
        for decision
        in level["decisions"]
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

        save_progress()

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


browser_loaded = st.session_state.get(
    "browser_progress_loaded",
    False,
)

if not browser_loaded:
    browser_value = read_browser_progress()

    if browser_value is None:
        st.info(
            "Loading your saved progress..."
        )
        st.stop()

    initialise_state(
        sanitise_progress(
            browser_value
        )
    )

else:
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
    st.session_state.screen = (
        query_screen
    )


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

    border: 4px solid var(--dark);
    border-radius: 14px;

    padding: 18px;

    box-shadow:
        6px 6px 0
        var(--dark);

    font-weight: 700;
    margin-bottom: 18px;
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
    z-index: 40;

    display: block;

    border-radius: 50%;

    text-decoration: none;
    cursor: pointer;

    background:
        rgba(
            255,
            255,
            255,
            0.001
        );
}

.map-level-hotspot:hover {
    background:
        rgba(
            255,
            255,
            255,
            0.20
        );

    box-shadow:
        inset
        0 0 0 7px
        rgba(
            255,
            255,
            255,
            0.85
        );
}

.map-level-hotspot.locked {
    cursor: not-allowed;

    background:
        rgba(
            80,
            80,
            80,
            0.05
        );
}

/* Positions for progress_map.png */

.map-level-1 {
    left: 5.2%;
    top: 48%;
    width: 16%;
    height: 30%;
}

.map-level-2 {
    left: 24%;
    top: 41%;
    width: 15.5%;
    height: 30%;
}

.map-level-3 {
    left: 41%;
    top: 29%;
    width: 15.5%;
    height: 30%;
}

.map-level-4 {
    left: 58%;
    top: 14%;
    width: 15.5%;
    height: 30%;
}

.map-level-5 {
    left: 80.5%;
    top: 11.5%;
    width: 15.5%;
    height: 30%;
}

.map-progress-pill {
    position: absolute;

    left: 3%;
    bottom: 3.5%;

    z-index: 50;

    background:
        rgba(
            255,
            255,
            255,
            0.95
        );

    border: 4px solid var(--dark);
    border-radius: 18px;

    padding: 10px 18px;

    box-shadow:
        5px 5px 0
        var(--dark);

    font-family:
        "Bangers",
        cursive;

    font-size:
        clamp(
            1.2rem,
            2.5vw,
            2.2rem
        );
}

.map-level-badge {
    position: absolute;
    z-index: 55;

    transform:
        translate(
            -50%,
            -50%
        );

    background:
        rgba(
            255,
            255,
            255,
            0.95
        );

    border: 3px solid var(--dark);
    border-radius: 12px;

    padding: 4px 8px;

    box-shadow:
        3px 3px 0
        var(--dark);

    font-weight: 900;

    font-size:
        clamp(
            0.65rem,
            1.2vw,
            1rem
        );

    pointer-events: none;
}

.badge-1 {
    left: 13%;
    top: 79%;
}

.badge-2 {
    left: 31.8%;
    top: 72%;
}

.badge-3 {
    left: 48.8%;
    top: 59.5%;
}

.badge-4 {
    left: 65.8%;
    top: 44.5%;
}

.badge-5 {
    left: 88.3%;
    top: 42%;
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
</style>
"""


st.markdown(
    CSS,
    unsafe_allow_html=True,
)


def show_top_bar():
    top_bar_html = (
        '<div class="top-bar">'
        '<div>FIRST AID HEROES</div>'
        '<div>'
        f'<span class="status-pill">'
        f'Score: {st.session_state.score}'
        f'</span>'
        f'<span class="status-pill">'
        f'Stars: {total_stars()} / 45'
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

        menu_html = (
            '<div class="main-menu-wrap">'
            f'<img src="{cover_uri}" '
            'alt="First Aid Heroes">'
            '<a '
            'class="menu-hotspot start-hotspot" '
            'href="?screen=map" '
            'target="_self" '
            'aria-label="Start">'
            '</a>'
            '<a '
            'class="menu-hotspot achievement-hotspot" '
            'href="?screen=achievements" '
            'target="_self" '
            'aria-label="Achievements">'
            '</a>'
            '<a '
            'class="menu-hotspot score-hotspot" '
            'href="?screen=score" '
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
    map_path = (
        BASE_DIR
        / "progress_map.png"
    )

    if map_path.exists():
        map_uri = image_data_uri(
            map_path
        )

        hotspot_parts = []
        badge_parts = []

        for level_index in range(
            len(LEVELS)
        ):
            unlocked = level_unlocked(
                level_index
            )

            stars = level_star_total(
                level_index
            )

            level_number = (
                level_index + 1
            )

            if unlocked:
                hotspot_parts.append(
                    (
                        f'<a '
                        f'class="map-level-hotspot '
                        f'map-level-{level_number}" '
                        f'href="?screen=difficulty'
                        f'&level={level_index}" '
                        f'target="_self" '
                        f'title="Open Level '
                        f'{level_number}" '
                        f'aria-label="Open Level '
                        f'{level_number}">'
                        f'</a>'
                    )
                )

            else:
                hotspot_parts.append(
                    (
                        f'<div '
                        f'class="map-level-hotspot '
                        f'map-level-{level_number} '
                        f'locked" '
                        f'title="Level '
                        f'{level_number} is locked">'
                        f'</div>'
                    )
                )

            status = (
                "UNLOCKED"
                if unlocked
                else "LOCKED"
            )

            badge_parts.append(
                (
                    f'<div '
                    f'class="map-level-badge '
                    f'badge-{level_number}">'
                    f'L{level_number}: '
                    f'{stars}/9 ★ · '
                    f'{status}'
                    f'</div>'
                )
            )

        map_html = (
            '<div class="progress-map-wrapper">'
            f'<img src="{map_uri}" '
            f'alt="School Progress Map">'
            + "".join(
                hotspot_parts
            )
            + "".join(
                badge_parts
            )
            + (
                f'<div class="map-progress-pill">'
                f'TOTAL: {total_stars()} / 45 ★'
                f'</div>'
            )
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
                'Save your illustrated map beside '
                'main.py using the exact name '
                '<b>progress_map.png</b>.'
                '</p>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        columns = st.columns(
            len(LEVELS)
        )

        for level_index, column in enumerate(
            columns
        ):
            unlocked = level_unlocked(
                level_index
            )

            stars = level_star_total(
                level_index
            )

            with column:
                st.markdown(
                    (
                        '<div class="comic-panel" '
                        f'style="text-align:center; '
                        f'opacity:'
                        f'{1 if unlocked else 0.5};">'
                        f'<h2>'
                        f'LEVEL {level_index + 1}'
                        f'</h2>'
                        f'<p>'
                        f'{LEVELS[level_index]["title"]}'
                        f'</p>'
                        f'<p>'
                        f'{stars} / 9 ★'
                        f'</p>'
                        f'</div>'
                    ),
                    unsafe_allow_html=True,
                )

                if st.button(
                    f"OPEN LEVEL {level_index + 1}",
                    key=(
                        f"fallback_level_"
                        f"{level_index}"
                    ),
                    use_container_width=True,
                    disabled=not unlocked,
                ):
                    navigate(
                        "difficulty",
                        level_index,
                    )

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

        st.markdown(
            (
                '<div class="stat-box">'
                '<div>TIME</div>'
                f'<span>{elapsed}s</span>'
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

        st.markdown(
            (
                '<div class="stat-box">'
                '<div>TIME</div>'
                f'<span>{elapsed}s</span>'
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


screen = st.session_state.screen
if screen == "home":
    render_home()


elif screen == "map":
    show_top_bar()
    render_map()


elif screen == "difficulty":
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
            'ARRANGE THE STORY'
            '</div>'
            f'<h2>'
            f'{level["title"]}'
            f'</h2>'
            '<p>'
            'Drag one card into each '
            'of the six slots.'
            '</p>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    difficulty_column, moves_column, timer_column = (
        st.columns(3)
    )

    with difficulty_column:
        st.markdown(
            (
                '<div class="stat-box">'
                '<div>DIFFICULTY</div>'
                f'<span>'
                f'{st.session_state.difficulty}'
                f'</span>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

    with moves_column:
        st.markdown(
            (
                '<div class="stat-box">'
                '<div>MOVES</div>'
                f'<span>'
                f'{st.session_state.moves}'
                f'</span>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

    with timer_column:
        live_timer()

    new_layout = sort_items(
        st.session_state.layout,
        direction="horizontal",
        multi_containers=True,
        key=(
            f"story_sort_"
            f"{st.session_state.sort_key}"
        ),
    )

    corrected_layout, corrected = (
        limit_one_card_per_slot(
            new_layout
        )
    )

    if corrected:
        st.session_state.layout = (
            copy.deepcopy(
                corrected_layout
            )
        )

        st.session_state.previous_layout = (
            copy.deepcopy(
                corrected_layout
            )
        )

        st.session_state.previous_sequence = (
            sequence_from_layout(
                corrected_layout
            )
        )

        st.session_state.sort_key += 1
        st.session_state.slot_warning = True

        save_progress()
        st.rerun()

    old_sequence = (
        st.session_state.previous_sequence.copy()
    )

    new_sequence = (
        sequence_from_layout(
            corrected_layout
        )
    )

    if (
        corrected_layout
        != st.session_state.previous_layout
    ):
        st.session_state.moves += 1

        decision_id = detect_new_decision(
            level,
            old_sequence,
            new_sequence,
        )

        if decision_id is not None:
            st.session_state.pending_decision = (
                decision_id
            )

        st.session_state.previous_layout = (
            copy.deepcopy(
                corrected_layout
            )
        )

        st.session_state.previous_sequence = (
            new_sequence.copy()
        )

    st.session_state.layout = (
        copy.deepcopy(
            corrected_layout
        )
    )

    save_progress()

    if st.session_state.slot_warning:
        st.warning(
            "Only one card is allowed in each slot. "
            "The extra card returned to the tray."
        )

        st.session_state.slot_warning = False

    back_column, restart_column, done_column = (
        st.columns(3)
    )

    with back_column:
        if st.button(
            "BACK",
            use_container_width=True,
        ):
            navigate(
                "scenario",
                level_index,
            )

    with restart_column:
        if st.button(
            "RESTART",
            use_container_width=True,
        ):
            start_puzzle()

    with done_column:
        if st.button(
            "DONE",
            use_container_width=True,
        ):
            if not slots_complete(
                corrected_layout
            ):
                st.warning(
                    "Place exactly one card "
                    "in every slot."
                )

            elif not decisions_complete(
                level
            ):
                st.warning(
                    "Answer all decision "
                    "questions first."
                )

            else:
                evaluate_level()

    if (
        st.session_state.pending_decision
        is not None
    ):
        decision = get_decision(
            level,
            st.session_state.pending_decision,
        )

        if decision is not None:
            decision_popup(
                decision
            )


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

            home_column, map_column, next_column = (
                st.columns(3)
            )

            with home_column:
                if st.button(
                    "HOME",
                    key="passed_result_home",
                    use_container_width=True,
                ):
                    navigate("home")

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
            'SCORE'
            '</div>'
            f'<h1>'
            f'{st.session_state.score} POINTS'
            f'</h1>'
            f'<h2>'
            f'{total_stars()} / 45 STARS'
            f'</h2>'
            f'<p>'
            f'Completed modes: '
            f'{len(st.session_state.completed_modes)} '
            f'/ 15'
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
                status = "Completed"

            elif unlocked:
                status = "Unlocked"

            else:
                status = "Locked"

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
            completed_mode_count >= 5,
        ),
        (
            "LIFE SAVER",
            completed_mode_count >= 10,
        ),
        (
            "FIRST AID LEGEND",
            completed_mode_count >= 15,
        ),
        (
            "STAR COLLECTOR",
            total_stars() >= 30,
        ),
        (
            "PERFECT HERO",
            total_stars() >= 45,
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