const PASSWORD_MIN = 15;
const PASSWORD_MAX = 128;

/**
 * Returns a validation error message, or null if the value is acceptable.
 * @param {string} value
 * @returns {string|null}
 */
function getPasswordError(value) {
    if (!value) return 'Password is required.';
    if (value.length < PASSWORD_MIN) return `Password must be at least ${PASSWORD_MIN} characters.`;
    if (value.length > PASSWORD_MAX) return `Password must not exceed ${PASSWORD_MAX} characters.`;
    return null;
}

/**
 * Validates a password <input>, toggles is-invalid, and updates the
 * sibling .invalid-feedback text.
 * @param {jQuery} $input
 * @returns {boolean}
 */
function validatePasswordInput($input) {
    const error = getPasswordError($input.val());
    const $feedback = $input.siblings('.invalid-feedback').first();
    if (error) {
        $input.addClass('is-invalid');
        if ($feedback.length) $feedback.text(error);
        return false;
    }
    $input.removeClass('is-invalid');
    return true;
}

/**
 * Validates a confirm-password <input> against its paired password <input>.
 * @param {jQuery} $password  The primary password field.
 * @param {jQuery} $confirm   The confirm password field.
 * @returns {boolean}
 */
function validateConfirmInput($password, $confirm) {
    const val = $confirm.val();
    const matches = val.length > 0 && $password.val() === val;
    if (!matches) {
        $confirm.addClass('is-invalid');
        return false;
    }
    $confirm.removeClass('is-invalid');
    return true;
}
