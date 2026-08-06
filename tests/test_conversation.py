import pytest

from sherlock.conversation import (
    process_message,
    get_state,
    sessions,
    MENU,
    WAITING_FOR_FIRST_NAME,
    WAITING_FOR_LAST_NAME,
    WAITING_FOR_PHONE_NUMBER,
    WAITING_FOR_LECTURER_NAME,
)


@pytest.fixture(autouse=True)
def clear_sessions():
    """
    Give every test a clean conversation state.
    """
    sessions.clear()
    yield
    sessions.clear()


# ---------------------------------------------------------
# Initial state
# ---------------------------------------------------------

def test_new_user_starts_at_menu():
    wa_id = "0712345678"

    response = process_message(wa_id, "hello")

    assert response is not None
    assert get_state(wa_id) == MENU


# ---------------------------------------------------------
# Add lecturer flow
# ---------------------------------------------------------

def test_add_lecturer_starts_flow():
    wa_id = "0712345678"

    response = process_message(wa_id, "add_lecturer")

    assert response == "Please enter the lecturer's first name."
    assert get_state(wa_id) == WAITING_FOR_FIRST_NAME


def test_first_name_moves_to_last_name():
    wa_id = "0712345678"

    process_message(wa_id, "add_lecturer")

    response = process_message(wa_id, "Bradley")

    assert response == "Please enter the lecturer's last name."
    assert get_state(wa_id) == WAITING_FOR_LAST_NAME


def test_last_name_moves_to_phone_number():
    wa_id = "0712345678"

    process_message(wa_id, "add_lecturer")
    process_message(wa_id, "Bradley")

    response = process_message(wa_id, "Maina")

    assert response == "Please enter the lecturer's phone number."
    assert get_state(wa_id) == WAITING_FOR_PHONE_NUMBER


def test_phone_number_completes_add_lecturer_flow():
    wa_id = "0712345678"

    process_message(wa_id, "add_lecturer")
    process_message(wa_id, "Bradley")
    process_message(wa_id, "Maina")

    response = process_message(wa_id, "0712345678")

    assert response is not None
    assert get_state(wa_id) == MENU


# ---------------------------------------------------------
# Search lecturer flow
# ---------------------------------------------------------

def test_search_lecturer_starts_flow():
    wa_id = "0712345678"

    response = process_message(wa_id, "search_lecturer")

    assert response is not None
    assert get_state(wa_id) == WAITING_FOR_LECTURER_NAME


def test_search_lecturer_accepts_search_term():
    wa_id = "0712345678"

    process_message(wa_id, "search_lecturer")

    response = process_message(wa_id, "Bradley")

    assert response is not None


# ---------------------------------------------------------
# Unknown input
# ---------------------------------------------------------

def test_unknown_command_does_not_crash():
    wa_id = "0712345678"

    response = process_message(wa_id, "this_is_not_a_command")

    assert response is not None


# ---------------------------------------------------------
# Session isolation
# ---------------------------------------------------------

def test_users_have_independent_sessions():
    user_a = "0711111111"
    user_b = "0722222222"

    process_message(user_a, "add_lecturer")
    process_message(user_b, "search_lecturer")

    assert get_state(user_a) == WAITING_FOR_FIRST_NAME
    assert get_state(user_b) == WAITING_FOR_LECTURER_NAME



# ---------------------------------------------------------
# Repeated users / existing session
# ---------------------------------------------------------

def test_existing_session_continues_from_current_state():
    wa_id = "0712345678"

    process_message(wa_id, "add_lecturer")

    assert get_state(wa_id) == WAITING_FOR_FIRST_NAME

    process_message(wa_id, "Bradley")

    assert get_state(wa_id) == WAITING_FOR_LAST_NAME