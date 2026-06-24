"""
Covers pure functions and helpers that require no database or running server
"""
import hashlib
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from flask_bcrypt import Bcrypt

from routes.models.auth import User
from routes.models.users import _check_hibp, validate_password

_bcrypt = Bcrypt()

def _make_hibp_mock(suffix: str, count: int):
    """
    Return a mock urlopen context-manager whose body contains one matching
    line (<suffix>:<count>) and two non-matching lines.
    """
    body = (
        f'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:1\n'
        f'{suffix}:{count}\n'
        f'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB:99'
    ).encode()

    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    mock_resp.read.return_value = body
    return mock_resp


@pytest.fixture()
def make_hash():
    """Return a bcrypt hash for any plaintext string."""
    def _inner(plaintext: str) -> str:
        return _bcrypt.generate_password_hash(plaintext).decode('utf-8')
    return _inner


class TestValidatePasswordLength:
    """
    Minimum 8 characters, maximum 128 characters.
    """

    def test_empty_string_is_rejected(self):
        errors = validate_password('')
        assert errors, 'Empty password must produce at least one error'
        assert any('required' in e.lower() for e in errors)

    def test_none_is_rejected(self):
        # falsy value
        errors = validate_password(None)
        assert errors

    def test_seven_chars_below_minimum_is_rejected(self):
        errors = validate_password('Abc123!')
        assert any('8' in e for e in errors), \
            f'Seven-char password should fail minimum-length check; got: {errors}'

    def test_eight_chars_meets_minimum(self):
        # HIBP mocked to 0 so length is the only variable
        with patch('routes.models.users._check_hibp', return_value=0):
            errors = validate_password('Abc1234!')
        assert errors == [], \
            f'Eight-character password should pass all checks; got: {errors}'

    def test_128_chars_meets_maximum(self):
        pw = 'A' * 120 + 'b1!@#456'
        with patch('routes.models.users._check_hibp', return_value=0):
            errors = validate_password(pw)
        assert errors == [], \
            f'128-character password should pass; got: {errors}'

    def test_129_chars_exceeds_maximum_is_rejected(self):
        pw = 'A' * 121 + 'b1!@#456'
        errors = validate_password(pw)
        assert any('128' in e or 'exceed' in e.lower() for e in errors), \
            f'129-character password should fail max-length check; got: {errors}'

    def test_return_type_is_always_list(self):
        with patch('routes.models.users._check_hibp', return_value=0):
            assert isinstance(validate_password(''), list)
            assert isinstance(validate_password('ValidPass1!'), list)

    def test_multiple_errors_not_returned_for_empty(self):
        # empty check returns immediately with one error
        errors = validate_password('')
        assert len(errors) == 1



class TestValidatePasswordReuse:
    """
    New password must differ from the current password.
    The check is performed against the stored bcrypt hash, not plaintext.
    """

    def test_same_password_as_current_hash_is_rejected(self, make_hash):
        password = 'OriginalPass1!'
        current_hash = make_hash(password)
        errors = validate_password(password, current_hash=current_hash)
        assert errors, 'Re-using the current password must be rejected'
        assert any('different' in e.lower() or 'current' in e.lower() for e in errors)

    def test_different_password_from_current_hash_is_accepted(self, make_hash):
        current_hash = make_hash('OldPass123!')
        with patch('routes.models.users._check_hibp', return_value=0):
            errors = validate_password('NewPass456!', current_hash=current_hash)
        assert errors == [], f'A new password differing from the hash should pass; got: {errors}'

    def test_no_current_hash_skips_reuse_check(self):
        with patch('routes.models.users._check_hibp', return_value=0):
            errors = validate_password('FreshPass1!', current_hash=None)
        assert errors == []

    def test_reuse_check_runs_before_hibp(self, make_hash):
        """
        If the password matches the current hash, no HIBP call should be made
        (errors list is non-empty, short-circuiting the HIBP branch).
        """
        password = 'OriginalPass1!'
        current_hash = make_hash(password)

        with patch('routes.models.users._check_hibp') as mock_hibp:
            validate_password(password, current_hash=current_hash)
            mock_hibp.assert_not_called()




class TestValidatePasswordHIBP:
    """
    Reject passwords appearing in breaches.
    Fail-open policy: if HIBP is unreachable, the password is allowed through.
    """

    def test_breached_password_is_rejected(self):
        # Force the breach check on regardless of the ambient HIBP_ENABLED env
        # (the test suite disables it globally to stay offline).
        with patch('routes.models.users._HIBP_ENABLED', True), \
                patch('routes.models.users._check_hibp', return_value=1):
            errors = validate_password('ValidFormat1!')
        assert errors, 'Password found in breach database must be rejected'
        assert any(
            word in e.lower()
            for e in errors
            for word in ('breach', 'data', 'known')
        )

    def test_breach_count_appears_in_error_message(self):
        with patch('routes.models.users._HIBP_ENABLED', True), \
                patch('routes.models.users._check_hibp', return_value=9_999):
            errors = validate_password('ValidFormat1!')
        assert any('9,999' in e or '9999' in e for e in errors), \
            f'Breach count should appear in the error message; got: {errors}'

    def test_zero_breach_count_means_password_is_accepted(self):
        with patch('routes.models.users._check_hibp', return_value=0):
            errors = validate_password('UniquePass99!')
        assert errors == []

    def test_hibp_unreachable_fails_open(self):
        """
        Unavailability of HIBP must not block a user.
        The application should fail open (allow the password through).
        """
        with patch(
            'routes.models.users._check_hibp',
            side_effect=RuntimeError('HIBP unreachable: timeout'),
        ):
            errors = validate_password('ValidFormat1!')
        assert errors == [], \
            f'HIBP unavailability must not reject the password; got: {errors}'

    def test_hibp_not_called_when_password_too_short(self):
        """HIBP should never be reached if earlier checks already failed."""
        with patch('routes.models.users._check_hibp') as mock_hibp:
            validate_password('short')
            mock_hibp.assert_not_called()

    def test_hibp_not_called_for_empty_password(self):
        with patch('routes.models.users._check_hibp') as mock_hibp:
            validate_password('')
            mock_hibp.assert_not_called()




class TestCheckHIBP:
    """
    Verifies the k-anonymity implementation used to query the HIBP API.
    Only the first 5 hex characters of the SHA-1 hash are sent over the wire;
    matching is performed locally on the remaining 35 characters.
    """

    def test_only_5_char_sha1_prefix_sent_in_url(self):
        """
        The request URL must end with exactly the first 5 uppercase hex characters of the password's SHA-1 hash.
        """
        password = 'TestPassword1!'
        expected_prefix = hashlib.sha1(password.encode()).hexdigest().upper()[:5]
        suffix = hashlib.sha1(password.encode()).hexdigest().upper()[5:]

        with patch('urllib.request.urlopen') as mock_open:
            mock_open.return_value = _make_hibp_mock(suffix, 3)
            _check_hibp(password)

        called_request = mock_open.call_args[0][0]
        assert called_request.full_url.endswith(expected_prefix), (
            f'URL must end with "{expected_prefix}"; '
            f'got "{called_request.full_url}"'
        )

    def test_returns_correct_breach_count_from_response(self):
        password = 'PwnedPass1!'
        suffix = hashlib.sha1(password.encode()).hexdigest().upper()[5:]

        with patch('urllib.request.urlopen') as mock_open:
            mock_open.return_value = _make_hibp_mock(suffix, 42)
            count = _check_hibp(password)

        assert count == 42

    def test_returns_zero_when_suffix_absent_from_response(self):
        """A password whose suffix does not appear in the response has 0 breaches."""
        password = 'UniquePass99!'

        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = (
            b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:1\n'
            b'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB:99'
        )

        with patch('urllib.request.urlopen', return_value=mock_resp):
            count = _check_hibp(password)

        assert count == 0

    def test_raises_runtime_error_on_non_200_status(self):
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 503

        with patch('urllib.request.urlopen', return_value=mock_resp):
            with pytest.raises(RuntimeError, match='HIBP returned HTTP 503'):
                _check_hibp('AnyPassword1!')

    def test_raises_runtime_error_when_api_unreachable(self):
        with patch(
            'urllib.request.urlopen',
            side_effect=urllib.error.URLError('connection refused'),
        ):
            with pytest.raises(RuntimeError, match='HIBP unreachable'):
                _check_hibp('AnyPassword1!')

    def test_sha1_prefix_is_uppercase(self):
        """HIBP API requires an uppercase hex prefix."""
        password = 'MixedCaseTest1!'
        expected_prefix = hashlib.sha1(password.encode()).hexdigest().upper()[:5]

        with patch('urllib.request.urlopen') as mock_open:
            suffix = hashlib.sha1(password.encode()).hexdigest().upper()[5:]
            mock_open.return_value = _make_hibp_mock(suffix, 0)
            _check_hibp(password)

        called_request = mock_open.call_args[0][0]
        # Extract the 5-char segment from the URL
        url_prefix = called_request.full_url.split('/range/')[-1]
        assert url_prefix == url_prefix.upper(), \
            f'Prefix must be uppercase; got "{url_prefix}"'
        assert url_prefix == expected_prefix




class TestUserRoleProperties:
    """
    The User class exposes two boolean properties derived from the stored role string: admin and is_manager.  
    These are computed properties with no database access.
    """

    def _user(self, role: str) -> User:
        return User(id=1, employee_id=10, username='testuser', password='hashed', role=role)

    # --- admin property ---

    def test_admin_role_returns_admin_true(self):
        assert self._user('admin').admin is True

    def test_employee_role_returns_admin_false(self):
        assert self._user('employee').admin is False

    def test_manager_role_returns_admin_false(self):
        assert self._user('manager').admin is False

    def test_unknown_role_returns_admin_false(self):
        assert self._user('superuser').admin is False

    # --- is_manager property ---

    def test_manager_role_returns_is_manager_true(self):
        assert self._user('manager').is_manager is True

    def test_employee_role_returns_is_manager_false(self):
        assert self._user('employee').is_manager is False

    def test_admin_role_returns_is_manager_false(self):
        """admin and manager are mutually exclusive roles."""
        user = self._user('admin')
        assert user.admin is True
        assert user.is_manager is False

    def test_unknown_role_returns_is_manager_false(self):
        assert self._user('superuser').is_manager is False

    # --- constructor ---

    def test_constructor_stores_all_attributes(self):
        user = User(id=42, employee_id=7, username='alice', password='ph', role='employee')
        assert user.id == 42
        assert user.employee_id == 7
        assert user.username == 'alice'
        assert user.password == 'ph'
        assert user.role == 'employee'





class TestBcryptHashing:
    """
    hashes are not stored as plaintext, verification is correct, and random
    salts mean the same password always produces a distinct hash.
    """

    def test_hash_does_not_equal_plaintext(self):
        pw = 'TestPassword1!'
        hashed = _bcrypt.generate_password_hash(pw).decode('utf-8')
        assert hashed != pw

    def test_correct_password_passes_verification(self):
        pw = 'TestPassword1!'
        hashed = _bcrypt.generate_password_hash(pw).decode('utf-8')
        assert _bcrypt.check_password_hash(hashed, pw) is True

    def test_wrong_password_fails_verification(self):
        pw = 'TestPassword1!'
        hashed = _bcrypt.generate_password_hash(pw).decode('utf-8')
        assert _bcrypt.check_password_hash(hashed, 'WrongPassword1!') is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses a random salt — identical inputs must yield distinct outputs."""
        pw = 'TestPassword1!'
        hash1 = _bcrypt.generate_password_hash(pw).decode('utf-8')
        hash2 = _bcrypt.generate_password_hash(pw).decode('utf-8')
        assert hash1 != hash2

    def test_each_hash_still_verifies_correctly(self):
        """Both independently generated hashes must still accept the original password."""
        pw = 'TestPassword1!'
        hash1 = _bcrypt.generate_password_hash(pw).decode('utf-8')
        hash2 = _bcrypt.generate_password_hash(pw).decode('utf-8')
        assert _bcrypt.check_password_hash(hash1, pw) is True
        assert _bcrypt.check_password_hash(hash2, pw) is True
