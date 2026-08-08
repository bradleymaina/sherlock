import pytest
from fastapi.testclient import TestClient

from sherlock import api as main
from sherlock.api import WebhookPayload


@pytest.fixture
def client():
    return TestClient(main.app)


# ---------- POST /lecturers ----------

def test_create_lecturer_success(client, monkeypatch):
    monkeypatch.setattr(
        main, "add_lecturer",
        lambda first_name, last_name, phone_number: {
            "status": "success",
            "data": {
                "id": 1,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": phone_number,
            },
        },
    )

    response = client.post("/lecturers", json={
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "0712345678",
    })

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["first_name"] == "John"


def test_create_lecturer_passes_validated_fields_through(client, monkeypatch):
    captured = {}

    def fake_add_lecturer(first_name, last_name, phone_number):
        captured["args"] = (first_name, last_name, phone_number)
        return {"status": "success", "data": {}}

    monkeypatch.setattr(main, "add_lecturer", fake_add_lecturer)

    client.post("/lecturers", json={
        "first_name": "Jane",
        "last_name": "Smith",
        "phone_number": "0198765432",
    })

    assert captured["args"] == ("Jane", "Smith", "0198765432")


def test_create_lecturer_first_name_too_short(client):
    response = client.post("/lecturers", json={
        "first_name": "Jo",
        "last_name": "Doe",
        "phone_number": "0712345678",
    })

    assert response.status_code == 422


def test_create_lecturer_first_name_too_long(client):
    response = client.post("/lecturers", json={
        "first_name": "Abcdefghijk",  # 11 chars, max is 10
        "last_name": "Doe",
        "phone_number": "0712345678",
    })

    assert response.status_code == 422


def test_create_lecturer_first_name_with_digits_rejected(client):
    response = client.post("/lecturers", json={
        "first_name": "John1",
        "last_name": "Doe",
        "phone_number": "0712345678",
    })

    assert response.status_code == 422


def test_create_lecturer_phone_wrong_prefix_rejected(client):
    # Must start with 07 or 01
    response = client.post("/lecturers", json={
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "0512345678",
    })

    assert response.status_code == 422


def test_create_lecturer_phone_wrong_length_rejected(client):
    response = client.post("/lecturers", json={
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "071234567",  # 9 digits
    })

    assert response.status_code == 422


def test_create_lecturer_phone_non_numeric_rejected(client):
    response = client.post("/lecturers", json={
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "07abcd5678",
    })

    assert response.status_code == 422


def test_create_lecturer_missing_field_rejected(client):
    response = client.post("/lecturers", json={
        "first_name": "John",
        "last_name": "Doe",
        # phone_number missing
    })

    assert response.status_code == 422


# ---------- GET /lecturers/search ----------

def test_search_lecturer_success(client, monkeypatch):
    monkeypatch.setattr(
        main, "lecturer_lookup",
        lambda search_name: {
            "status": "success",
            "count": 1,
            "data": [{
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "0712345678"
            }],
        },
    )

    response = client.get(
        "/lecturers/search",
        params={"search_name": "john"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["count"] == 1


def test_search_lecturer_not_found(client, monkeypatch):
    monkeypatch.setattr(
        main, "lecturer_lookup",
        lambda search_name: {
            "status": "error",
            "message": "not found"
        },
    )

    response = client.get(
        "/lecturers/search",
        params={"search_name": "nobody"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "error"


def test_search_lecturer_missing_query_param(client):
    response = client.get("/lecturers/search")

    assert response.status_code == 422


# ---------- GET /webhook (verification) ----------

def test_verify_webhook_success(client):
    response = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "sherlock_webhook_2026",
        "hub.challenge": "12345",
    })

    assert response.status_code == 200
    assert response.text == "12345"


def test_verify_webhook_wrong_token(client):
    response = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "12345",
    })

    assert response.status_code == 403


def test_verify_webhook_wrong_mode(client):
    response = client.get("/webhook", params={
        "hub.mode": "unsubscribe",
        "hub.verify_token": "sherlock_webhook_2026",
        "hub.challenge": "12345",
    })

    assert response.status_code == 403


def test_verify_webhook_missing_params(client):
    response = client.get("/webhook")

    assert response.status_code == 403


# ---------- POST /webhook (incoming messages) ----------

def _text_webhook_payload(wa_id="254712345678", body="hi"):
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


def _button_webhook_payload(wa_id="254712345678"):
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": wa_id,
                        "type": "interactive",
                        "interactive": {
                            "type": "button_reply",
                            "button_reply": {
                                "id": "explore_sherlock",
                                "title": "Explore Sherlock",
                            },
                        },
                    }]
                }
            }]
        }],
    }


def _list_webhook_payload(wa_id="254712345678"):
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": wa_id,
                        "type": "interactive",
                        "interactive": {
                            "type": "list_reply",
                            "list_reply": {
                                "id": "add_lecturer",
                                "title": "Add Lecturer",
                            },
                        },
                    }]
                }
            }]
        }],
    }


# ---------- Pydantic interactive payload tests ----------

def test_button_webhook_payload_parses():
    payload = _button_webhook_payload()

    webhook = WebhookPayload(**payload)

    message = webhook.entry[0].changes[0].value.messages[0]

    assert message.type == "interactive"
    assert message.interactive.type == "button_reply"
    assert message.interactive.button_reply.id == "explore_sherlock"
    assert message.interactive.button_reply.title == "Explore Sherlock"


def test_list_webhook_payload_parses():
    payload = _list_webhook_payload()

    webhook = WebhookPayload(**payload)

    message = webhook.entry[0].changes[0].value.messages[0]

    assert message.type == "interactive"
    assert message.interactive.type == "list_reply"
    assert message.interactive.list_reply.id == "add_lecturer"
    assert message.interactive.list_reply.title == "Add Lecturer"


# ---------- Webhook text message ----------

def test_receive_webhook_text_message_success(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "process_message",
        lambda wa_id, msg: "auto-reply"
    )

    sent = {}

    def fake_send(wa_id, message):
        sent["wa_id"] = wa_id
        sent["message"] = message

        class FakeResponse:
            status_code = 200

        return FakeResponse()

    monkeypatch.setattr(
        main,
        "send_whatsapp_message",
        fake_send
    )

    response = client.post(
        "/webhook",
        json=_text_webhook_payload(
            wa_id="254712345678",
            body="find john"
        )
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    assert sent["wa_id"] == "254712345678"
    assert sent["message"] == "auto-reply"


# ---------- Webhook button reply ----------

def test_receive_webhook_button_reply_success(client, monkeypatch):
    received = {}

    def fake_process_message(wa_id, input_value):
        received["wa_id"] = wa_id
        received["input_value"] = input_value
        return "button response"

    monkeypatch.setattr(
        main,
        "process_message",
        fake_process_message
    )

    sent = {}

    def fake_send(wa_id, message):
        sent["wa_id"] = wa_id
        sent["message"] = message

    monkeypatch.setattr(
        main,
        "send_whatsapp_message",
        fake_send
    )

    response = client.post(
        "/webhook",
        json=_button_webhook_payload(
            wa_id="254712345678"
        )
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    assert received["wa_id"] == "254712345678"
    assert received["input_value"] == "explore_sherlock"

    assert sent["wa_id"] == "254712345678"
    assert sent["message"] == "button response"


# ---------- Webhook list reply ----------

def test_receive_webhook_list_reply_success(client, monkeypatch):
    received = {}

    def fake_process_message(wa_id, input_value):
        received["wa_id"] = wa_id
        received["input_value"] = input_value
        return "list response"

    monkeypatch.setattr(
        main,
        "process_message",
        fake_process_message
    )

    sent = {}

    def fake_send(wa_id, message):
        sent["wa_id"] = wa_id
        sent["message"] = message

    monkeypatch.setattr(
        main,
        "send_whatsapp_message",
        fake_send
    )

    response = client.post(
        "/webhook",
        json=_list_webhook_payload(
            wa_id="254712345678"
        )
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    assert received["wa_id"] == "254712345678"
    assert received["input_value"] == "add_lecturer"

    assert sent["wa_id"] == "254712345678"
    assert sent["message"] == "list response"


# ---------- Other webhook cases ----------

def test_receive_webhook_no_entry(client):
    response = client.post("/webhook", json={
        "object": "whatsapp_business_account",
        "entry": [],
    })

    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}


def test_receive_webhook_no_changes(client):
    response = client.post("/webhook", json={
        "object": "whatsapp_business_account",
        "entry": [{"changes": []}],
    })

    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}


def test_receive_webhook_no_messages(client):
    response = client.post("/webhook", json={
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {}}]}],
    })

    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}


def test_receive_webhook_non_text_message(client, monkeypatch):
    # process_message/send_whatsapp_message should NOT be called for non-text
    called = {"process": False, "send": False}

    monkeypatch.setattr(
        main,
        "process_message",
        lambda wa_id, msg: called.__setitem__("process", True)
    )

    monkeypatch.setattr(
        main,
        "send_whatsapp_message",
        lambda wa_id, msg: called.__setitem__("send", True)
    )

    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "254712345678",
                        "type": "image",
                    }]
                }
            }]
        }],
    }

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ignored"
    assert body["reason"] == "non-text message"
    assert called["process"] is False
    assert called["send"] is False


# ---------- send_whatsapp_message ----------

def test_send_whatsapp_message_builds_correct_request(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json

        class FakeResponse:
            status_code = 200

        return FakeResponse()

    monkeypatch.setattr(main.requests, "post", fake_post)

    main.send_whatsapp_message("254712345678", "hello there")

    assert captured["url"].endswith("/messages")
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["json"]["to"] == "254712345678"
    assert captured["json"]["text"]["body"] == "hello there"
    assert captured["json"]["type"] == "text"