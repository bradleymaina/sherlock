"""
Integration tests for the "add a lecturer" flow.

Unlike tests/unit_tests, these do NOT mock add_lecturer, lecturer_lookup, or
process_message. They drive the whole stack the way a real WhatsApp message
would: FastAPI webhook -> conversation state machine -> real sqlite database.

The only thing mocked is the outbound call to Meta's WhatsApp API
(send_whatsapp_message / requests.post) — that's the one true external
boundary, and hitting it for real in tests would require live credentials
and would spam a real phone number.

Everything else — routing, session state, name/phone normalization, and
actual row persistence — is real, so these tests catch bugs that only show
up when the pieces are wired together (unit tests that mock database calls
can't see them).
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
    # raise_server_exceptions=False so a 500 (an unhandled exception in the
    # route) comes back as a normal response instead of blowing up the test
    # process — we want to be able to assert on crashes, not just successes.
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


# ---------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------

def test_full_add_lecturer_flow_persists_to_real_database(client, temp_db, sent_messages):
    wa_id = "254712345678"

    _send(client, wa_id, "add_lecturer")
    _send(client, wa_id, "Bradley")
    _send(client, wa_id, "Maina")
    response = _send(client, wa_id, "0712345678")

    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    replies = [m["message"] for m in sent_messages]
    assert replies == [
        "Please enter the lecturer's first name.",
        "Please enter the lecturer's last name.",
        "Please enter the lecturer's phone number.",
        "Lecturer Bradley Maina with phone number 0712345678 has been added successfully.",
    ]

    # The whole point of an integration test: check the row is really there,
    # written by the real database module, not a mock.
    result = db_module.lecturer_lookup("bradley")
    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["data"][0] == {
        "first_name": "Bradley",
        "last_name": "Maina",
        "phone_number": "0712345678",
    }

    # Session should be cleaned up after a successful add.
    assert wa_id not in sessions


def test_add_lecturer_flow_normalizes_names_end_to_end(client, temp_db, sent_messages):
    """
    Conversation.py passes whatever the user typed straight through — the
    trimming/title-casing happens in database.add_lecturer. This test checks
    that normalization actually survives the full pipeline, not just in
    isolation.
    """
    wa_id = "254711111111"

    _send(client, wa_id, "add_lecturer")
    _send(client, wa_id, "  jANE  ")
    _send(client, wa_id, "  sMITH ")
    _send(client, wa_id, "0798765432")

    result = db_module.lecturer_lookup("jane")
    assert result["status"] == "success"
    assert result["data"][0]["first_name"] == "Jane"
    assert result["data"][0]["last_name"] == "Smith"


def test_two_users_adding_lecturers_stay_isolated(client, temp_db, sent_messages):
    user_a = "254711111111"
    user_b = "254722222222"

    _send(client, user_a, "add_lecturer")
    _send(client, user_b, "add_lecturer")

    _send(client, user_a, "Alice")
    _send(client, user_b, "Bob")

    _send(client, user_a, "Achieng")
    _send(client, user_b, "Otieno")

    _send(client, user_a, "0711112222")
    _send(client, user_b, "0722223333")

    alice = db_module.lecturer_lookup("alice")
    bob = db_module.lecturer_lookup("bob")

    assert alice["data"][0]["last_name"] == "Achieng"
    assert alice["data"][0]["phone_number"] == "0711112222"

    assert bob["data"][0]["last_name"] == "Otieno"
    assert bob["data"][0]["phone_number"] == "0722223333"

    assert user_a not in sessions
    assert user_b not in sessions


def test_add_lecturer_flow_does_not_touch_database_until_all_fields_collected(
    client, temp_db, sent_messages
):
    wa_id = "254733333333"

    _send(client, wa_id, "add_lecturer")
    _send(client, wa_id, "Grace")

    # Only first name has been given so far — nothing should be written yet.
    result = db_module.lecturer_lookup("grace")
    assert result["status"] == "error"


# ---------------------------------------------------------------------
# Known bugs surfaced only by wiring conversation.py + database.py together
# ---------------------------------------------------------------------
#
# conversation.py's phone-number step does:
#
#     result = add_lecturer(...)
#     if result["status"] == "success":
#         ...
#     return result["data"]
#
# but database.add_lecturer's *error* dict only ever has "status" and
# "message" keys — never "data". Any error from add_lecturer (duplicate
# phone, or a malformed phone number, since the chat flow never validates
# the phone format the way the /lecturers REST endpoint does) makes
# conversation.py raise KeyError('data'), which FastAPI turns into an
# unhandled 500 for the whole webhook call. Unit tests that mock
# add_lecturer's return value never exercise the real error shape, so this
# only shows up once the two modules are wired together for real — which is
# exactly what these tests do.
#
# These tests document the CURRENT (broken) behavior. If you fix
# conversation.py to handle the error branch properly, these two tests
# should start failing — update them then to assert the graceful behavior
# instead.

def test_duplicate_phone_number_crashes_the_webhook(client, temp_db, sent_messages):
    wa_id = "254744444444"

    _send(client, wa_id, "add_lecturer")
    _send(client, wa_id, "Bradley")
    _send(client, wa_id, "Maina")
    first = _send(client, wa_id, "0712345678")
    assert first.status_code == 200  # first add succeeds

    sessions.clear()

    _send(client, wa_id, "add_lecturer")
    _send(client, wa_id, "Bradley")
    _send(client, wa_id, "Maina")
    duplicate = _send(client, wa_id, "0712345678")

    # BUG: this should ideally be a 200 with a friendly "already exists"
    # reply (add_lecturer already produces that message!) — instead the
    # whole request blows up.
    assert duplicate.status_code == 500

    # The row from the first, successful add is still just one row.
    result = db_module.lecturer_lookup("bradley")
    assert result["count"] == 1


def test_invalid_phone_number_typed_in_chat_crashes_the_webhook(client, temp_db, sent_messages):
    """
    The /lecturers REST endpoint rejects a bad phone number with a clean 422
    via the Lecturer pydantic model. The chat flow has no equivalent
    validation before calling add_lecturer, so a bad phone number typed in
    WhatsApp hits the same missing-"data"-key bug as the duplicate case.
    """
    wa_id = "254755555555"

    _send(client, wa_id, "add_lecturer")
    _send(client, wa_id, "Bradley")
    _send(client, wa_id, "Maina")
    response = _send(client, wa_id, "12345")  # too short, not 10 digits

    assert response.status_code == 500

    # Nothing should have been (and indeed wasn't) written to the database.
    result = db_module.lecturer_lookup("bradley")
    assert result["status"] == "error"