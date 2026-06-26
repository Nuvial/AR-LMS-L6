import string
from unittest.mock import patch

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from routes.employees import _validate_employee_fields
from routes.leave import _validate_leave_request
from routes.users import _validate_username
from routes.models.users import validate_password


_ALNUM = string.ascii_letters + string.digits
_NAME_CHARS = string.ascii_letters + " -"
_SYMBOLS = "!@#$%^&*()_=+.,/\\?<>{}[]|"
_BAD_FOR_USERNAME = _SYMBOLS # Usernames allow letters and digits, so only symbols are disallowed.
_BAD_FOR_NAME = string.digits + _SYMBOLS # Names allow letters, spaces and hyphens only, so digits are disallowed too.



class TestUsernameProperties:

    @given(st.text(alphabet=_ALNUM, min_size=3, max_size=25))
    def test_any_alphanumeric_3_to_25_is_accepted(self, username):
        assert _validate_username(username) is None

    @given(st.text(alphabet=_ALNUM, min_size=1, max_size=2))
    def test_any_alphanumeric_under_3_is_rejected_for_length(self, username):
        assert _validate_username(username) == "Username must be between 3 and 25 characters."

    @given(st.text(alphabet=_ALNUM, min_size=26, max_size=60))
    def test_any_alphanumeric_over_25_is_rejected_for_length(self, username):
        assert _validate_username(username) == "Username must be between 3 and 25 characters."

    @given(
        head=st.text(alphabet=_ALNUM, min_size=1, max_size=10),
        bad=st.sampled_from(_BAD_FOR_USERNAME),
        tail=st.text(alphabet=_ALNUM, min_size=1, max_size=10),
    )
    def test_any_username_with_a_disallowed_char_is_rejected(self, head, bad, tail):
        username = head + bad + tail
        assert _validate_username(username) == "Username must be alphanumeric."

    @given(st.text())
    def test_return_is_always_none_or_str(self, username):
        result = _validate_username(username)
        assert result is None or isinstance(result, str)



class TestEmployeeNameProperties:

    @given(st.text(alphabet=_NAME_CHARS, min_size=1, max_size=32))
    def test_valid_name_characters_within_length_are_accepted(self, name):
        stripped = name.strip()
        assume(stripped != "" and 1 <= len(stripped) <= 32)
        assert _validate_employee_fields({"first_name": name}, require_all=False) is None

    @given(
        head=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
        bad=st.sampled_from(_BAD_FOR_NAME),
        tail=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    )
    def test_name_with_disallowed_char_is_rejected(self, head, bad, tail):
        name = head + bad + tail
        err = _validate_employee_fields({"first_name": name}, require_all=False)
        assert err == "First name must be 1-32 letters, spaces or hyphens only"

    @given(st.text(alphabet=string.ascii_letters, min_size=33, max_size=80))
    def test_name_over_32_chars_is_rejected(self, name):
        err = _validate_employee_fields({"last_name": name}, require_all=False)
        assert err == "Last name must be 1-32 letters, spaces or hyphens only"



class TestEmployeeBalanceProperties:

    @given(st.floats(min_value=0, max_value=5000, allow_nan=False, allow_infinity=False))
    def test_in_range_balance_is_accepted(self, value):
        assert _validate_employee_fields(
            {"default_leave_balance": value}, require_all=False
        ) is None

    @given(st.floats(min_value=5000.01, max_value=1e9, allow_nan=False, allow_infinity=False))
    def test_above_range_balance_is_rejected(self, value):
        err = _validate_employee_fields({"default_leave_balance": value}, require_all=False)
        assert err == "Default leave balance must be between 0 and 5000 hours"

    @given(st.floats(min_value=-1e9, max_value=-0.01, allow_nan=False, allow_infinity=False))
    def test_negative_balance_is_rejected(self, value):
        err = _validate_employee_fields({"default_leave_balance": value}, require_all=False)
        assert err == "Default leave balance must be between 0 and 5000 hours"



class TestPasswordLengthProperties:

    @settings(max_examples=50)
    @given(st.text(min_size=15, max_size=128))
    def test_any_15_to_128_char_password_is_accepted(self, password):
        with patch("routes.models.users._check_hibp", return_value=0):
            assert validate_password(password) == []

    @given(st.text(min_size=1, max_size=14))
    def test_any_password_under_15_chars_is_rejected(self, password):
        errors = validate_password(password)
        assert errors, "Sub-minimum password must be rejected"
        assert any("15" in e for e in errors)

    @given(st.text(min_size=129, max_size=400))
    def test_any_password_over_128_chars_is_rejected(self, password):
        errors = validate_password(password)
        assert any("128" in e for e in errors)

    @given(st.text())
    def test_return_is_always_a_list(self, password):
        with patch("routes.models.users._check_hibp", return_value=0):
            assert isinstance(validate_password(password), list)



class TestLeaveHoursProperties:

    def _request(self, hours):
        return {
            "leave_type": "Annual Leave",
            "start_date": "2025-06-01",
            "end_date": "2025-06-05",
            "hours_requested": hours,
        }

    @given(st.floats(max_value=0, allow_nan=False, allow_infinity=False))
    def test_non_positive_hours_always_rejected(self, hours):
        assert _validate_leave_request(self._request(hours)) == \
            "Hours requested must be greater than 0"

    @given(st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False))
    def test_reasonable_positive_hours_accepted(self, hours):
        assert _validate_leave_request(self._request(hours)) is None

    @given(st.floats(min_value=10000.01, max_value=1e9, allow_nan=False, allow_infinity=False))
    def test_excessive_hours_rejected(self, hours):
        assert _validate_leave_request(self._request(hours)) == \
            "Hours requested is unreasonably large"
