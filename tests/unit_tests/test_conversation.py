from unittest.mock import patch

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
    """Give every test a clean conversation state."""
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


def test_hello_returns_welcome_message_and_list():
    wa_id = "0712345678"

    response = process_message(wa_id, "hello")

    assert len(response) == 2

    # First response: welcome message
    assert response[0]["type"] == "text"
    assert response[0]["body"] == (
        "Welcome to sherlock. I am a virtual assistant "
        "that makes it easy to find lecturers and add "
        "them to the database."
    )

    # Second response: interactive list
    assert response[1]["type"] == "list"
    assert response[1]["body"] == "View Options"
    assert response[1]["button_title"] == "Select an option"

    # List options
    assert response[1]["rows"][0]["id"] == "add_lecturer"
    assert response[1]["rows"][0]["title"] == "Add Lecturer"

    assert response[1]["rows"][1]["id"] == "search_lecturer"
    assert response[1]["rows"][1]["title"] == "Search Lecturer"


# ---------------------------------------------------------
# Add lecturer flow
# ---------------------------------------------------------

def test_add_lecturer_starts_flow():
    wa_id = "0712345678"

    response = process_message(wa_id, "add_lecturer")

    assert response == {
        "type": "text",
        "body": "Please enter the lecturer's first name.",
    }

    assert get_state(wa_id) == WAITING_FOR_FIRST_NAME


def test_first_name_moves_to_last_name():
    wa_id = "0712345678"

    process_message(wa_id, "add_lecturer")

    response = process_message(wa_id, "Bradley")

    assert response == {
        "type": "text",
        "body": "Please enter the lecturer's last name.",
    }

    assert get_state(wa_id) == WAITING_FOR_LAST_NAME


def test_last_name_moves_to_phone_number():
    wa_id = "0712345678"

    process_message(wa_id, "add_lecturer")
    process_message(wa_id, "Bradley")

    response = process_message(wa_id, "Maina")

    assert response == {
        "type": "text",
        "body": "Please enter the lecturer's phone number.",
    }

    assert get_state(wa_id) == WAITING_FOR_PHONE_NUMBER


def test_phone_number_completes_add_lecturer_flow():
    wa_id = "0712345678"

    with patch("sherlock.conversation.add_lecturer") as mock_add:
        mock_add.return_value = {
            "status": "success",
            "data": "Lecturer added successfully.",
        }

        process_message(wa_id, "add_lecturer")
        process_message(wa_id, "Bradley")
        process_message(wa_id, "Maina")

        response = process_message(wa_id, "0712345678")

        mock_add.assert_called_once_with(
            "Bradley",
            "Maina",
            "0712345678",
        )

        assert response == {
            "type": "text",
            "body": (
                "Lecturer Bradley Maina with phone number "
                "0712345678 has been added successfully."
            ),
        }

        assert get_state(wa_id) is None


def test_phone_number_with_add_lecturer_error_does_not_crash():
    """Documents current (buggy) behavior: on an error result, add_lecturer's
    branch has no else clause, so process_message implicitly returns None
    and the session is never cleared. This is a known gap (see TODOs in the
    module) rather than intended behavior -- flagging it here so it gets
    fixed rather than silently regressing further."""
    wa_id = "0712345678"

    with patch("sherlock.conversation.add_lecturer") as mock_add:
        mock_add.return_value = {
            "status": "error",
            "message": "Phone number already exists.",
        }

        process_message(wa_id, "add_lecturer")
        process_message(wa_id, "Bradley")
        process_message(wa_id, "Maina")

        response = process_message(wa_id, "0712345678")

        assert response is None
        # Session is stuck in WAITING_FOR_PHONE_NUMBER since it's never cleared.
        assert get_state(wa_id) == WAITING_FOR_PHONE_NUMBER


# ---------------------------------------------------------
# Search lecturer flow
# ---------------------------------------------------------

def test_search_lecturer_starts_flow():
    wa_id = "0712345678"

    response = process_message(wa_id, "search_lecturer")

    assert response == {
        "type": "text",
        "body": "Please enter the lecturer's name you want to search for.",
    }

    assert get_state(wa_id) == WAITING_FOR_LECTURER_NAME


def test_search_lecturer_accepts_search_term():
    """Documents current (buggy) behavior: on success this branch returns a
    plain string instead of the {"type": "text", "body": ...} dict shape
    used everywhere else -- this is the "Fix the search lecturer function"
    TODO in the module."""
    wa_id = "0712345678"

    with patch("sherlock.conversation.lecturer_lookup") as mock_lookup:
        mock_lookup.return_value = {
            "status": "success",
            "data": [
                {
                    "first_name": "Bradley",
                    "last_name": "Maina",
                    "phone_number": "0712345678",
                }
            ],
        }

        process_message(wa_id, "search_lecturer")

        response = process_message(wa_id, "Bradley")

        mock_lookup.assert_called_once_with("Bradley")

        assert response == "Bradley Maina : 0712345678."

        assert get_state(wa_id) is None


def test_search_lecturer_formats_multiple_results():
    wa_id = "0712345678"

    with patch("sherlock.conversation.lecturer_lookup") as mock_lookup:
        mock_lookup.return_value = {
            "status": "success",
            "data": [
                {
                    "first_name": "Bradley",
                    "last_name": "Maina",
                    "phone_number": "0712345678",
                },
                {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "phone_number": "0798765432",
                },
            ],
        }

        process_message(wa_id, "search_lecturer")

        response = process_message(wa_id, "Doe")

        assert response == (
            "Bradley Maina : 0712345678.\n Jane Doe : 0798765432."
        )

        assert get_state(wa_id) is None


def test_search_lecturer_returns_error_message():
    """On a lookup error, the raw error message is returned as-is (also a
    plain string, not the usual dict shape), and the session is left
    dangling in WAITING_FOR_LECTURER_NAME since it's never cleared."""
    wa_id = "0712345678"

    with patch("sherlock.conversation.lecturer_lookup") as mock_lookup:
        mock_lookup.return_value = {
            "status": "error",
            "message": "No lecturer found with that name.",
        }

        process_message(wa_id, "search_lecturer")

        response = process_message(wa_id, "Nobody")

        assert response == "No lecturer found with that name."
        assert get_state(wa_id) == WAITING_FOR_LECTURER_NAME


# ---------------------------------------------------------
# Unknown input
# ---------------------------------------------------------

def test_unknown_command_does_not_crash():
    wa_id = "0712345678"

    response = process_message(
        wa_id,
        "this_is_not_a_command"
    )

    assert response == {
        "type": "text",
        "body": "Invalid option. Please select a valid option from the menu.",
    }


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
# Existing session
# ---------------------------------------------------------

def test_existing_session_continues_from_current_state():
    wa_id = "0712345678"

    process_message(wa_id, "add_lecturer")

    assert get_state(wa_id) == WAITING_FOR_FIRST_NAME

    process_message(wa_id, "Bradley")

    assert get_state(wa_id) == WAITING_FOR_LAST_NAME