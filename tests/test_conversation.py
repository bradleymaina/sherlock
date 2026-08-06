import pytest

from sherlock.conversation import process_message


def test_process_message():
    wa_id = "0712345678"
    msg = "add_lecturer"

    response = process_message(wa_id, msg)

    assert response == "Please enter the lecturer's first name."
