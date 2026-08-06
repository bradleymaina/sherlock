
import sqlite3
import pytest

from sherlock import database as db


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """
    Redirects get_db() to a throwaway sqlite file for the duration of each test,
    so tests never touch your real lecturer.db and are fully isolated from each other.
    """
    db_path = tmp_path / "test_lecturer.db"

    def fake_get_db():
        connection = sqlite3.connect(db_path)
        return connection, connection.cursor()

    monkeypatch.setattr(db, "get_db", fake_get_db)
    db.create_table()
    yield db_path


# ---------- create_table ----------

def test_create_table_is_idempotent(temp_db):
    # Calling create_table() twice should not raise (IF NOT EXISTS)
    db.create_table()
    db.create_table()


# ---------- add_lecturer ----------

def test_add_lecturer_success(temp_db):
    result = db.add_lecturer("john", "doe", "0712345678")

    assert result["status"] == "success"
    assert result["data"]["first_name"] == "John"
    assert result["data"]["last_name"] == "Doe"
    assert result["data"]["phone_number"] == "0712345678"
    assert result["data"]["id"] == 1


def test_add_lecturer_strips_and_title_cases_names(temp_db):
    result = db.add_lecturer("  jANE  ", "  sMITH ", "0798765432")

    assert result["data"]["first_name"] == "Jane"
    assert result["data"]["last_name"] == "Smith"


def test_add_lecturer_strips_phone_whitespace(temp_db):
    result = db.add_lecturer("Amy", "Lee", "  0711111111  ")

    assert result["status"] == "success"
    assert result["data"]["phone_number"] == "0711111111"


def test_add_lecturer_duplicate_phone_number(temp_db):
    db.add_lecturer("John", "Doe", "0712345678")
    result = db.add_lecturer("Jane", "Doe", "0712345678")

    assert result["status"] == "error"
    assert "already exists" in result["message"]


def test_add_lecturer_phone_too_short(temp_db):
    result = db.add_lecturer("John", "Doe", "12345")

    assert result["status"] == "error"
    assert "10 digits" in result["message"]


def test_add_lecturer_phone_too_long(temp_db):
    result = db.add_lecturer("John", "Doe", "071234567890")

    assert result["status"] == "error"
    assert "10 digits" in result["message"]


def test_add_lecturer_phone_non_numeric(temp_db):
    result = db.add_lecturer("John", "Doe", "07abcd5678")

    assert result["status"] == "error"
    assert "10 digits" in result["message"]


def test_add_lecturer_phone_with_plus_sign_rejected(temp_db):
    # e.g. "+254712345678" is 13 chars and isdigit() is False for '+'
    result = db.add_lecturer("John", "Doe", "+254712345")

    assert result["status"] == "error"


def test_add_lecturer_same_name_different_phone_allowed(temp_db):
    first = db.add_lecturer("John", "Doe", "0712345678")
    second = db.add_lecturer("John", "Doe", "0798765432")

    assert first["status"] == "success"
    assert second["status"] == "success"
    assert first["data"]["id"] != second["data"]["id"]


# ---------- lecturer_lookup ----------

def test_lookup_by_first_name(temp_db):
    db.add_lecturer("John", "Doe", "0712345678")

    result = db.lecturer_lookup("john")

    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["data"][0]["phone_number"] == "0712345678"


def test_lookup_by_last_name(temp_db):
    db.add_lecturer("John", "Doe", "0712345678")

    result = db.lecturer_lookup("doe")

    assert result["status"] == "success"
    assert result["count"] == 1


def test_lookup_partial_match(temp_db):
    db.add_lecturer("Jonathan", "Doe", "0712345678")

    result = db.lecturer_lookup("jon")

    assert result["status"] == "success"
    assert result["count"] == 1


def test_lookup_is_case_insensitive(temp_db):
    db.add_lecturer("John", "Doe", "0712345678")

    result = db.lecturer_lookup("JOHN")

    assert result["status"] == "success"
    assert result["count"] == 1


def test_lookup_no_match_returns_error(temp_db):
    db.add_lecturer("John", "Doe", "0712345678")

    result = db.lecturer_lookup("nonexistent")

    assert result["status"] == "error"


def test_lookup_multiple_results(temp_db):
    db.add_lecturer("John", "Doe", "0712345678")
    db.add_lecturer("Johnny", "Smith", "0798765432")

    result = db.lecturer_lookup("john")

    assert result["status"] == "success"
    assert result["count"] == 2


def test_lookup_matches_across_first_and_last_name(temp_db):
    # "doe" should match Doe as a last name, and also match nobody's first name here
    db.add_lecturer("John", "Doe", "0712345678")
    db.add_lecturer("Jane", "Doevski", "0798765432")

    result = db.lecturer_lookup("doe")

    assert result["status"] == "success"
    assert result["count"] == 2


def test_lookup_empty_database_returns_error(temp_db):
    result = db.lecturer_lookup("anyone")

    assert result["status"] == "error"