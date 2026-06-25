"""
Unit tests — Layer 1 of the test plan (server-side field validators).

These validators were extracted from the request handlers into standalone,
side-effect-free helpers so they can be exercised in isolation:

  - routes.employees._validate_employee_fields  (name / balance / hours rules)
  - routes.leave._validate_leave_request        (leave type / date / hours rules)
  - routes.users._validate_username             (alphanumeric / length rules)

Each returns an error string when input is invalid, or None when it is valid.
Testing them directly is the cheapest place to prove the application's input
contract holds, independent of any route, session or database.
"""
import pytest

from routes.employees import _validate_employee_fields
from routes.leave import _validate_leave_request
from routes.users import _validate_username


# ===========================================================================
# _validate_employee_fields
# ===========================================================================

def _valid_employee():
    """A fully valid employee payload; individual tests mutate one field."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "default_leave_balance": 160,
        "default_sick_leave_balance": 40,
        "contracted_daily_hours": 8,
        "contracted_weekly_hours": 40,
    }


class TestValidateEmployeeFieldsRequired:
    """require_all=True is used by the add-employee route: every field mandatory."""

    def test_complete_payload_is_valid(self):
        assert _validate_employee_fields(_valid_employee(), require_all=True) is None

    @pytest.mark.parametrize(
        "missing_field",
        [
            "first_name",
            "last_name",
            "default_leave_balance",
            "default_sick_leave_balance",
            "contracted_daily_hours",
            "contracted_weekly_hours",
        ],
    )
    def test_any_missing_field_is_rejected(self, missing_field):
        data = _valid_employee()
        del data[missing_field]
        err = _validate_employee_fields(data, require_all=True)
        assert err == "Missing required fields"

    def test_empty_name_treated_as_missing(self):
        data = _valid_employee()
        data["first_name"] = ""
        # Empty string is falsy -> caught by the required-fields guard
        assert _validate_employee_fields(data, require_all=True) == "Missing required fields"

    def test_zero_balance_is_not_treated_as_missing(self):
        """0 is a legitimate balance and must pass the required-fields guard."""
        data = _valid_employee()
        data["default_leave_balance"] = 0
        assert _validate_employee_fields(data, require_all=True) is None


class TestValidateEmployeeFieldsPartial:
    """require_all=False is used by update routes: only present fields validated."""

    def test_empty_dict_is_valid_when_not_requiring_all(self):
        assert _validate_employee_fields({}, require_all=False) is None

    def test_single_valid_field_passes(self):
        assert _validate_employee_fields({"first_name": "Jane"}, require_all=False) is None

    def test_single_invalid_field_is_rejected(self):
        err = _validate_employee_fields({"first_name": "Jane123"}, require_all=False)
        assert err is not None and "First name" in err


class TestValidateEmployeeName:
    """Name rule: 1-32 chars, letters / spaces / hyphens only (regex ^[a-zA-Z\\- ]+$)."""

    @pytest.mark.parametrize("name", ["John", "Mary Jane", "Anne-Marie", "de la Cruz", "A"])
    def test_valid_names_accepted(self, name):
        data = _valid_employee()
        data["first_name"] = name
        assert _validate_employee_fields(data, require_all=True) is None

    @pytest.mark.parametrize("name", ["John2", "O'Brien", "J@ne", "Anne_Marie", "Zoë", "123"])
    def test_names_with_disallowed_characters_rejected(self, name):
        data = _valid_employee()
        data["first_name"] = name
        err = _validate_employee_fields(data, require_all=True)
        assert err == "First name must be 1-32 letters, spaces or hyphens only"

    def test_name_at_32_char_boundary_accepted(self):
        data = _valid_employee()
        data["last_name"] = "A" * 32
        assert _validate_employee_fields(data, require_all=True) is None

    def test_name_over_32_chars_rejected(self):
        data = _valid_employee()
        data["last_name"] = "A" * 33
        err = _validate_employee_fields(data, require_all=True)
        assert err == "Last name must be 1-32 letters, spaces or hyphens only"

    def test_whitespace_only_name_rejected(self):
        """'   ' strips to empty -> caught by the required-fields guard."""
        data = _valid_employee()
        data["first_name"] = "   "
        # falsy after the route reads it? No — '   ' is truthy, so it reaches the regex/length check
        err = _validate_employee_fields(data, require_all=False)
        assert err == "First name must be 1-32 letters, spaces or hyphens only"

    def test_surrounding_whitespace_is_stripped_before_validation(self):
        data = _valid_employee()
        data["first_name"] = "  John  "
        assert _validate_employee_fields(data, require_all=True) is None


class TestValidateEmployeeBalances:
    """Leave / sick balance rule: numeric, 0 <= value <= 5000."""

    @pytest.mark.parametrize("value", [0, 0.0, 250, 5000, "100"])
    def test_valid_leave_balances_accepted(self, value):
        data = _valid_employee()
        data["default_leave_balance"] = value
        assert _validate_employee_fields(data, require_all=True) is None

    @pytest.mark.parametrize("value", [-1, 5000.1, 99999])
    def test_out_of_range_leave_balance_rejected(self, value):
        data = _valid_employee()
        data["default_leave_balance"] = value
        err = _validate_employee_fields(data, require_all=True)
        assert err == "Default leave balance must be between 0 and 5000 hours"

    def test_non_numeric_leave_balance_rejected(self):
        data = _valid_employee()
        data["default_leave_balance"] = "lots"
        err = _validate_employee_fields(data, require_all=True)
        assert err == "Default leave balance must be a number"

    def test_non_numeric_sick_balance_rejected(self):
        data = _valid_employee()
        data["default_sick_leave_balance"] = "n/a"
        err = _validate_employee_fields(data, require_all=True)
        assert err == "Default sick leave balance must be a number"

    def test_out_of_range_sick_balance_rejected(self):
        data = _valid_employee()
        data["default_sick_leave_balance"] = 6000
        err = _validate_employee_fields(data, require_all=True)
        assert err == "Default sick leave balance must be between 0 and 5000 hours"


class TestValidateEmployeeHours:
    """
    Daily hours rule: 0 < value <= 24.
    Weekly hours rule: 0 < value <= 168.
    Zero is rejected here (unlike balances) because a contract of 0 hours is invalid.
    """

    @pytest.mark.parametrize("value", [0.5, 8, 24])
    def test_valid_daily_hours_accepted(self, value):
        data = _valid_employee()
        data["contracted_daily_hours"] = value
        assert _validate_employee_fields(data, require_all=True) is None

    @pytest.mark.parametrize("value", [-1, 24.5, 100])
    def test_out_of_range_daily_hours_rejected(self, value):
        data = _valid_employee()
        data["contracted_daily_hours"] = value
        err = _validate_employee_fields(data, require_all=True)
        assert err == "Contracted daily hours must be between 0 and 24"

    def test_zero_daily_hours_rejected(self):
        """0 fails the strict lower bound (0 < value)."""
        data = _valid_employee()
        # supply 0 directly via partial validation so the required-fields guard
        # (which would also reject 0 as falsy) is not what we are measuring
        err = _validate_employee_fields({"contracted_daily_hours": 0}, require_all=False)
        assert err == "Contracted daily hours must be between 0 and 24"

    @pytest.mark.parametrize("value", [0.5, 40, 168])
    def test_valid_weekly_hours_accepted(self, value):
        data = _valid_employee()
        data["contracted_weekly_hours"] = value
        assert _validate_employee_fields(data, require_all=True) is None

    @pytest.mark.parametrize("value", [-1, 168.5, 200])
    def test_out_of_range_weekly_hours_rejected(self, value):
        data = _valid_employee()
        data["contracted_weekly_hours"] = value
        err = _validate_employee_fields(data, require_all=True)
        assert err == "Contracted weekly hours must be between 0 and 168"

    def test_non_numeric_weekly_hours_rejected(self):
        err = _validate_employee_fields({"contracted_weekly_hours": "full-time"}, require_all=False)
        assert err == "Contracted weekly hours must be a number"



def _valid_leave():
    return {
        "leave_type": "Annual Leave",
        "start_date": "2025-06-01",
        "end_date": "2025-06-05",
        "hours_requested": 40,
    }


class TestValidateLeaveRequestRequired:

    def test_complete_request_is_valid(self):
        assert _validate_leave_request(_valid_leave()) is None

    @pytest.mark.parametrize("field", ["leave_type", "start_date", "end_date", "hours_requested"])
    def test_missing_field_is_rejected(self, field):
        data = _valid_leave()
        del data[field]
        err = _validate_leave_request(data)
        assert err == "Missing required fields: leave_type, start_date, end_date, hours_requested"

    def test_zero_hours_is_not_treated_as_missing(self):
        """hours_requested=0 passes the presence guard but fails the >0 rule."""
        data = _valid_leave()
        data["hours_requested"] = 0
        err = _validate_leave_request(data)
        assert err == "Hours requested must be greater than 0"


class TestValidateLeaveType:

    @pytest.mark.parametrize("leave_type", ["Annual Leave", "Sick Leave", "Time off in Lieu"])
    def test_valid_leave_types_accepted(self, leave_type):
        data = _valid_leave()
        data["leave_type"] = leave_type
        assert _validate_leave_request(data) is None

    @pytest.mark.parametrize("leave_type", ["Holiday", "annual leave", "Vacation", "ANNUAL LEAVE"])
    def test_invalid_leave_type_rejected(self, leave_type):
        data = _valid_leave()
        data["leave_type"] = leave_type
        err = _validate_leave_request(data)
        assert err is not None and err.startswith("Invalid leave type")


class TestValidateLeaveDates:

    def test_bad_start_date_format_rejected(self):
        data = _valid_leave()
        data["start_date"] = "01/06/2025"
        assert _validate_leave_request(data) == "start_date must be in YYYY-MM-DD format"

    def test_bad_end_date_format_rejected(self):
        data = _valid_leave()
        data["end_date"] = "2025-13-40"
        assert _validate_leave_request(data) == "end_date must be in YYYY-MM-DD format"

    def test_start_after_end_rejected(self):
        data = _valid_leave()
        data["start_date"] = "2025-06-10"
        data["end_date"] = "2025-06-05"
        assert _validate_leave_request(data) == "start_date must not be after end_date"

    def test_single_day_leave_accepted(self):
        """Equal start and end dates is a valid one-day request."""
        data = _valid_leave()
        data["start_date"] = "2025-06-05"
        data["end_date"] = "2025-06-05"
        assert _validate_leave_request(data) is None


class TestValidateLeaveHours:

    def test_negative_hours_rejected(self):
        data = _valid_leave()
        data["hours_requested"] = -5
        assert _validate_leave_request(data) == "Hours requested must be greater than 0"

    def test_excessive_hours_rejected(self):
        data = _valid_leave()
        data["hours_requested"] = 10001
        assert _validate_leave_request(data) == "Hours requested is unreasonably large"

    def test_upper_bound_hours_accepted(self):
        data = _valid_leave()
        data["hours_requested"] = 10000
        assert _validate_leave_request(data) is None

    def test_non_numeric_hours_rejected(self):
        data = _valid_leave()
        data["hours_requested"] = "all of them"
        assert _validate_leave_request(data) == "hours_requested must be a number"


# ===========================================================================
# _validate_username
# ===========================================================================

class TestValidateUsername:
    """Username rule: alphanumeric only, 3-25 characters."""

    @pytest.mark.parametrize("username", ["abc", "User123", "A1b2C3", "a" * 25])
    def test_valid_usernames_accepted(self, username):
        assert _validate_username(username) is None

    @pytest.mark.parametrize("username", ["ab", "a", "12"])
    def test_too_short_username_rejected(self, username):
        assert _validate_username(username) == "Username must be between 3 and 25 characters."

    def test_too_long_username_rejected(self):
        assert _validate_username("a" * 26) == "Username must be between 3 and 25 characters."

    @pytest.mark.parametrize("username", ["john_doe", "john doe", "john.doe", "john!", "josé"])
    def test_non_alphanumeric_username_rejected(self, username):
        assert _validate_username(username) == "Username must be alphanumeric."

    @pytest.mark.parametrize("username", ["", None])
    def test_empty_or_none_username_rejected(self, username):
        # Falsy values fail the alphanumeric guard first
        assert _validate_username(username) == "Username must be alphanumeric."

    def test_alphanumeric_check_runs_before_length_check(self):
        """A short, non-alphanumeric username reports the alphanumeric error first."""
        assert _validate_username("a!") == "Username must be alphanumeric."
