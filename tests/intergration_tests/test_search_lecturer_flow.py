"""
Integration tests for the "search for a lecturer" flow.

Same approach as test_add_lecturer_flow.py: nothing is mocked except the
outbound WhatsApp send call. The webhook route, the conversation state
machine, and a real (temp-file) sqlite database are all wired together for
real, so these tests catch bugs that only appear once the pieces talk to
each other.
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from sherlock import api
from sherlock import database as db_module
from sherlock.conversation import sessions


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point the real database module at a throwaway sqlite file."""
    db_path = tmp_path / "test_lecturer.db"

    def fake_get_db():
        connection = sqlite3.connect(db_path)
        return connection, connection.cursor()

    monkeypatch.setattr(db_module, "get_db", fake_get_db)
    db_module.create_table()
    yield db_path


@pytest.fixture(autouse=True)
def clear_sessions():
    """Give every test a clean conversation state, like test_conversation.py does."""
    sessions.clear()
    yield
    sessions.clear()


@pytest.fixture
def sent_messages(monkeypatch):
    """Capture outbound WhatsApp replies instead of calling the real Meta API."""
    sent = []

    def fake_send(wa_id, message):
        sent.append({"wa_id": wa_id, "message": message})

        class FakeResponse:
            status_code = 200
        return FakeResponse()

    monkeypatch.setattr(api, "send_whatsapp_message", fake_send)
    return sent


@pytest.fixture
def client():
    # raise_server_exceptions=False so a 500 comes back as a normal response
    # instead of blowing up the test process — needed to assert on crashes.
    return TestClient(api.app, raise_server_exceptions=False)


def _text_message(wa_id, body):
    """Build a webhook payload shaped like a real incoming WhatsApp text message."""
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": wa_id,
                        "type": "text",
                        "text": {"body": body},
                    }]
                }
            }]
        }],
    }


def _send(client, wa_id, body):
    return client.post("/webhook", json=_text_message(wa_id, body))


def _seed_lecturer(first_name, last_name, phone_number):
    """Write directly via the real database module, bypassing the chat flow."""
    result = db_module.add_lecturer(first_name, last_name, phone_number)
    assert result["status"] == "success"
    return result


# ---------------------------------------------------------------------
# search_lecturer prompt
# ---------------------------------------------------------------------

def test_search_lecturer_starts_flow_and_prompts_for_name(client, temp_db, sent_messages):
    wa_id = "254712345678"

    response = _send(client, wa_id, "search_lecturer")

    assert response.status_code == 200
    assert sent_messages[-1]["message"] == "Please enter the lecturer's name you want to search for."
    assert sessions[wa_id]["state"] == "WAITING_FOR_LECTURER_NAME"


# ---------------------------------------------------------------------
# Not-found path (this one actually works correctly end to end)
# ---------------------------------------------------------------------

def test_search_for_nonexistent_lecturer_returns_not_found(client, temp_db, sent_messages):
    wa_id = "254711111111"
    _seed_lecturer("John", "Doe", "0712345678")

    _send(client, wa_id, "search_lecturer")
    response = _send(client, wa_id, "nobodyhere")

    assert response.status_code == 200
    assert sent_messages[-1]["message"] == "A lecturer by that name does not exist! "


def test_not_found_search_keeps_session_open_for_retry(client, temp_db, sent_messages):
    """
    Unlike a successful search (see the bug section below), a not-found
    result doesn't delete the session — the user stays in
    WAITING_FOR_LECTURER_NAME and can immediately try another name.
    """
    wa_id = "254711111111"
    _seed_lecturer("John", "Doe", "0712345678")

    _send(client, wa_id, "search_lecturer")
    _send(client, wa_id, "nobodyhere")

    assert sessions[wa_id]["state"] == "WAITING_FOR_LECTURER_NAME"


def test_search_is_case_insensitive_and_matches_partial_names(client, temp_db, sent_messages):
    wa_id = "254711111111"
    _seed_lecturer("Jonathan", "Doe", "0712345678")

    # "JON" shouldn't match anything if searched with wrong case+substring
    # in a case-sensitive engine, but sqlite LIKE is case-insensitive, and
    # this is a substring search — confirm that survives the full pipeline.
    # (We only assert the *not-found* shape here since any real match hits
    # the crash bug documented below — see test_search_flow_crash tests.)
    _send(client, wa_id, "search_lecturer")
    response = _send(client, wa_id, "zzz_no_match_zzz")

    assert response.status_code == 200
    assert sent_messages[-1]["message"] == "A lecturer by that name does not exist! "


# ---------------------------------------------------------------------
# Session isolation
# ---------------------------------------------------------------------

def test_two_users_searching_stay_isolated(client, temp_db, sent_messages):
    user_a = "254711111111"
    user_b = "254722222222"
    _seed_lecturer("John", "Doe", "0712345678")

    _send(client, user_a, "search_lecturer")
    _send(client, user_b, "search_lecturer")

    _send(client, user_a, "nobodyhere")  # not found -> stays open
    _send(client, user_b, "alsonobody")  # not found -> stays open

    assert sessions[user_a]["state"] == "WAITING_FOR_LECTURER_NAME"
    assert sessions[user_b]["state"] == "WAITING_FOR_LECTURER_NAME"
    assert sessions[user_a]["lecturer_name"] == "nobodyhere"
    assert sessions[user_b]["lecturer_name"] == "alsonobody"


# ---------------------------------------------------------------------
# Known bug surfaced only by wiring conversation.py + database.py together
# ---------------------------------------------------------------------
#
# conversation.py's search step does:
#
#     result = lecturer_lookup(...)
#     if result["status"] == "success":
#          del sessions[wa_id]
#     return result["message"]
#
# but database.lecturer_lookup's *success* dict only ever has "status",
# "count", and "data" keys — there is no "message" key on success (only the
# error dict has one). So finding a real match — the whole point of the
# search feature — raises KeyError('message'), which FastAPI turns into an
# unhandled 500. This is the mirror image of the add-lecturer bug documented
# in test_add_lecturer_flow.py, and again only shows up once the real
# lecturer_lookup return shape meets the real conversation.py code — unit
# tests that mock lecturer_lookup's return value never hit it.
#
# One good side effect worth noting: `del sessions[wa_id]` runs BEFORE the
# crashing `return`, so the session is still cleaned up even though the
# request fails — the user isn't left stuck the way the add-lecturer bug
# leaves them (see test_search_flow_recovers_after_a_crash below).
#
# These tests document the CURRENT (broken) behavior. If you fix
# conversation.py's success branch to return something like result["data"]
# instead, these should start failing — update them then to assert the
# actual match gets returned to the user.

def test_finding_an_existing_lecturer_crashes_the_webhook(client, temp_db, sent_messages):
    wa_id = "254733333333"
    _seed_lecturer("John", "Doe", "0712345678")

    _send(client, wa_id, "search_lecturer")
    response = _send(client, wa_id, "john")

    # BUG: this should ideally be a 200 with John's phone number — instead
    # the whole request blows up because lecturer_lookup's success dict has
    # no "message" key.
    assert response.status_code == 500


def test_finding_multiple_matching_lecturers_also_crashes_the_webhook(client, temp_db, sent_messages):
    wa_id = "254744444444"
    _seed_lecturer("John", "Doe", "0712345678")
    _seed_lecturer("Johnny", "Smith", "0798765432")

    _send(client, wa_id, "search_lecturer")
    response = _send(client, wa_id, "john")

    assert response.status_code == 500


def test_search_flow_recovers_after_a_crash(client, temp_db, sent_messages):
    """
    Despite the crash, the session gets deleted before the failing return,
    so the next message from the same user starts fresh at the main menu
    instead of getting stuck (unlike the add-lecturer duplicate-phone bug).
    """
    wa_id = "254755555555"
    _seed_lecturer("John", "Doe", "0712345678")

    _send(client, wa_id, "search_lecturer")
    crash_response = _send(client, wa_id, "john")
    assert crash_response.status_code == 500

    assert wa_id not in sessions

    recovery_response = _send(client, wa_id, "hello")

    assert recovery_response.status_code == 200
    assert sent_messages[-1]["message"] == (
        "Welcome to sherlock.I am a virtual assistant that makes it easy "
        "to find lecturers and add them to the database."
    )
    assert sessions[wa_id]["state"] == "MENU"