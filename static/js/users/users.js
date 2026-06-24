let editing = false;

function setEditing(state, $editRow = null) {
    editing = state;
    if (state) {
        $('#createAccount').addClass('disabled');
        const $allRows = $('#userTableBody tr');
        const $toDisable = $editRow ? $allRows.not($editRow) : $allRows;
        $toDisable.find('td.actions > div').addClass('disabled');
    } else {
        $('#createAccount').removeClass('disabled');
        $('#userTableBody tr').find('td.actions > div').removeClass('disabled');
    }
}

$(document).ready(function(){
    //Check localstorage for any stored flashmessages - This is stored if the user changes their own username.
    const flash = localStorage.getItem('flashMessage');
    if (flash){
        const { message, type } = JSON.parse(flash);
        flashMessage(message, type, 3000);;
        localStorage.removeItem('flashMessage');
    }

    loadUsers();
    loadPendingRegistrations();

    initSearch(
        '#employee-search',
        '#userTableBody tr',
        [
            {selector: '.first-name'},
            {selector: '.last-name'},
            {selector: '.employee-id-div'},
            {selector: '.username-div'}
        ]
    );
});

function softRefresh(){
    $('.modal.show').modal('hide');
    setEditing(false);
    loadUsers();
    loadPendingRegistrations();
}

function loadUsers(){
    $.ajax({
        url: '/users/get_users',
        type: 'GET',
        beforeSend: function(){
            showLoader();
        },
        success: function(resp){
            if (resp.length > 0){
                populateUserTable(resp);
            }
        },
        complete: function(){
            hideLoader();
        },
        error: function(xhr, status, error) {
            console.log("Error loading users: " + error);
            alert("Failed to load users. Please try again later.");
        }
    });
}

function loadPendingRegistrations(){
    if (current_user.admin != '1') return;
    $.ajax({
        url: '/users/pending_registrations',
        type: 'GET',
        success: function(resp){
            if (resp.length > 0){
                populatePendingTable(resp);
                $('#pendingCard').show();
            } else {
                $('#pendingCard').hide();
            }
        },
        error: function(){
            $('#pendingCard').hide();
        }
    });
}

function populatePendingTable(pending) {
    const tbody = $('#pendingTableBody');
    let html = '';
    pending.forEach(user => {
        html += `
            <tr data-user-id="${user.pk_user_id}">
                <td class="employee-id">${user.fk_employee_id}</td>
                <td class="first-name">${user.first_name}</td>
                <td class="last-name">${user.last_name}</td>
                <td class="username">${user.username}</td>
                <td class="actions align-middle">
                    <div class="pending-actions">
                        <button type="button" class="btn btn-success btn-sm pending-approve w-100" title="Approve registration.">Approve</button>
                        <button type="button" class="btn btn-danger btn-sm pending-deny w-100" title="Deny registration.">Deny</button>
                    </div>
                </td>
            </tr>
        `;
    });
    tbody.html(html);
}

function approvePendingRegistration(user_id){
    $.ajax({
        url: `/users/confirm_registration/${user_id}`,
        type: 'PUT',
        beforeSend: function(){ showLoader(); },
        success: function(resp){
            if (resp.message === 'success'){
                softRefresh();
                flashMessage('Registration approved. The user can now log in.', 'success', 3000);
            } else {
                softRefresh();
                flashMessage(resp.error || 'Error approving registration. Please try again.', 'danger', 6000);
            }
        },
        complete: function(){ hideLoader(); },
        error: function(){
            flashMessage('Failed to approve registration. Please try again.', 'danger', 6000);
        }
    });
}

function denyPendingRegistration(user_id){
    $.ajax({
        url: `/users/deny_registration/${user_id}`,
        type: 'DELETE',
        beforeSend: function(){ showLoader(); },
        success: function(resp){
            if (resp.message === 'success'){
                softRefresh();
                flashMessage('Registration denied and pending account removed.', 'success', 3000);
            } else {
                softRefresh();
                flashMessage(resp.error || 'Error denying registration. Please try again.', 'danger', 6000);
            }
        },
        complete: function(){ hideLoader(); },
        error: function(){
            flashMessage('Failed to deny registration. Please try again.', 'danger', 6000);
        }
    });
}

function createAccount(data){
    $.ajax({
        url: '/users/add_user',
        type: 'POST',
        data: JSON.stringify(data),
        contentType: 'application/json',
        beforeSend: function(){
            showLoader();
        },
        success: function(resp){
            if (resp.message === 'success'){
                softRefresh()
                flashMessage('User account created successfully.', 'success', 3000)
            } else {
                softRefresh()
                flashMessage(resp.error || 'Error creating user account. Please try again', 'danger', 6000)
            }
        },
        complete: function(){
            hideLoader();
        },
        error: function(xhr, status, error) {
            console.log("Error creating user: " + error);
            alert("Failed to create user. Please try again later.");
        }
    });
}
function deleteUser(user_id){
    $.ajax({
        url: `/users/delete_user/${user_id}`,
        type: 'DELETE',
        beforeSend: function(){
            showLoader();
        },
        success: function(resp){
            if (resp.message === 'success'){
                softRefresh()
                flashMessage('User account deleted successfully.', 'success', 3000)
            } else {
                softRefresh()
                flashMessage(resp.error || 'Error deleting user account. Please try again', 'danger', 6000)
            }
        },
        complete: function(){
            hideLoader();
        },
        error: function(xhr, status, error) {
            console.log("Error deleting user: " + error);
            alert("Failed to delete user. Please try again later.");
        }
    });
}
function promoteUser(user_id){
    $.ajax({
        url: `/users/promote_user/${user_id}`,
        type: 'PUT',
        beforeSend: function(){
            showLoader();
        },
        success: function(resp){
            if (resp.message == 'success'){
                softRefresh()
                flashMessage('User account promoted successfully.', 'success', 3000)
            } else if (resp.message == 'error') {
                softRefresh()
                flashMessage(resp['error'], 'danger', 6000)
            } else {
                softRefresh()
                flashMessage('Error promoting user account. Please try again', 'danger', 3000)
            }
        },
        complete: function(){
            hideLoader();
        },
        error: function(xhr, status, error) {
            console.log("Error promoting user: " + error);
            alert("Failed to promote user. Please try again later.");
        }
    });
}
function demoteUser(user_id){
    $.ajax({
        url: `/users/demote_user/${user_id}`,
        type: 'PUT',
        beforeSend: function(){
            showLoader();
        },
        success: function(resp){
            if (resp.message === 'success'){
                softRefresh()
                flashMessage('User account demoted successfully.', 'success', 3000)
            } else {
                softRefresh()
                flashMessage(resp.error || 'Error demoting user account. Please try again', 'danger', 6000)
            }
        },
        complete: function(){
            hideLoader();
        },
        error: function(xhr, status, error) {
            console.log("Error demoting user: " + error);
            alert("Failed to demote user. Please try again later.");
        }
    });
}
function changePassword(id, password){
    $.ajax({
        url: `/users/change_password/${id}`,
        type: 'PUT',
        data: JSON.stringify({'password': password}),
        contentType: 'application/json',
        beforeSend: function(){
            showLoader();
        },
        success: function(resp){
            if (resp.message === 'success'){
                softRefresh()
                flashMessage('User password changed successfully.', 'success', 3000)
            } else {
                softRefresh()
                flashMessage(resp.error || 'Error changing password on user account. Please try again', 'danger', 6000)
            }
        },
        complete: function(){
            hideLoader();
        },
        error: function(xhr, status, error) {
            console.log("Error changing user password: " + error);
            alert("Failed to change user password. Please try again later.");
        }
    });
}
function changeUsername(id, username){
    $.ajax({
        url: `/users/change_username/${id}`,
        type: 'PUT',
        data: JSON.stringify({'username': username}),
        contentType: 'application/json',
        beforeSend: function(){
            showLoader();
        },
        success: function(resp){
            if (resp.message === 'success'){
                if (id === current_user.id){
                    localStorage.setItem('flashMessage', JSON.stringify({
                        message: 'Username was changed successfully',
                        type: 'success'
                    }));
                    location.reload();
                    return;
                }
                softRefresh()
                flashMessage('Username was changed successfully.', 'success', 3000)
            } else {
                softRefresh()
                flashMessage(resp.error || 'Error changing username for user account. Please try again', 'danger', 6000)
            }
        },
        complete: function(){
            hideLoader();
        },
        error: function(xhr, status, error) {
            console.log("Error changing username: " + error);
            alert("Failed to change username. Please try again later.");
        }
    });
}

async function isEmployeeIdUnique(id){
    try {
        const resp = await $.ajax({
            url: `/users/get_users/is_registered/${id}`,
            type: 'GET'
        });
        // if registered then not unique
        return !resp.registered;
    } catch (error){
        return false;
    }
}
async function isUsernameUnique(username){
    try {
        const resp = await $.ajax({
            url: `/users/get_users/username_taken`,
            type: 'GET',
            data: {username: username},
            contentType: 'application/json'
        });
        // If registered then not unique
        return !resp.registered;
    } catch (error){
        console.log('Error checking employee username' + error)
        alert("Failed to check employee username. Please try again later");
        return false;
    }
}
function populateUserTable(users) {
    const tbody = $('#userTableBody');
    let html = '';

    users.forEach(user => {
        const isAdmin = user.admin === 1;
        const isCurrentUser = Number(user.pk_user_id) === Number(current_user.id);
        const hasForgotPassword = user.forgot_password === 1;

        const adminMark = isAdmin
            ? '<i class="fas fa-square-check fa-xl"></i>'
            : '<i class="fas fa-square-xmark fa-xl"></i>';

        const forgotPasswordIcon = hasForgotPassword
            ? '<i class="fas fa-triangle-exclamation fa-lg" title="User has requested a password reset."></i>'
            : '';

        const forgotPasswordClass = hasForgotPassword ? 'forgot-pass' : '';

        const actionIcons = getActionIcons(isAdmin, isCurrentUser, forgotPasswordClass);

        html += `
            <tr data-user-id="${user.pk_user_id}">
                <td class="user-id">
                    <div class="position-relative">
                        ${forgotPasswordIcon}
                        ${user.pk_user_id}
                    </div>
                </td>
                <td class="employee-id">
                    <div class="employee-id-div editable">${user.fk_employee_id}</div>
                </td>
                <td class="first-name">${user.first_name}</td>
                <td class="last-name">${user.last_name}</td>
                <td class="username">
                    <div class="username-div editable">${user.username}</div>
                </td>
                <td class="admin">${adminMark}</td>
                <td class="actions align-middle">
                    <div class="d-flex justify-content-around align-items-center ${forgotPasswordClass}">
                        ${actionIcons}
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.html(html);
}

function getActionIcons(isAdmin, isCurrentUser, forgotPasswordClass) {
    if (isCurrentUser) {
        return '';
    }

    const canAdminister = current_user.admin == 1;
    const canDelete = canAdminister || current_user.is_manager == 1;

    if (isAdmin) {
        return `
            <i class="fas fa-square-pen fa-xl" title="Change username."></i>
            <i class="fas fa-key fa-xl ${forgotPasswordClass}" title="Change password."></i>
            ${canDelete ? `<i class="fas fa-trash fa-xl" title="Delete account."></i>` : ''}
            ${canAdminister ? `<i class="fas fa-arrow-trend-down fa-xl" title="Demote account."></i>` : ''}
        `;
    }

    return `
        <i class="fas fa-square-pen fa-xl" title="Change username."></i>
        <i class="fas fa-key fa-xl ${forgotPasswordClass}" title="Change password."></i>
        ${canDelete ? `<i class="fas fa-trash fa-xl" title="Delete account."></i>` : ''}
        ${canAdminister ? `<i class="fas fa-crown fa-xl" title="Promote account."></i>` : ''}
    `;
}

previous_actions_html = '';
function convertActions(row){
    //Helper function to convert row actions into save/cancel buttons
    previous_actions_html = $(row).find('.actions').clone();

    $(row).find('.actions').html(`
        <div class="actions-btns">
            <button type="button" class="btn btn-primary btn-sm w-100" id="saveAccount">Save</button>
            <button type="button" class="btn btn-outline-secondary btn-sm w-100" id="cancelAccount">Cancel</button>
        </div>
    `);
}
function revertActions(row){
    $(row).find('.actions').replaceWith(previous_actions_html);
    previous_actions_html = '';
}

function buildEmployeeSelectOptions(employees) {
    if (!employees || employees.length === 0) {
        return '<option disabled>No unregistered employees available.</option>';
    }
    return employees.map(e => `
        <option value="${e.pk_employee_id}"
            data-tokens="${e.first_name} ${e.last_name}"
            data-content='
                <div class="option">
                    <span class="option-employee-id">${e.pk_employee_id}</span>
                    <span class="option-employee-name">${e.first_name} ${e.last_name}</span>
                </div>'
        >${e.pk_employee_id}</option>
    `).join('');
}

async function placeholderRow(){
    const tbody = $('#userTableBody');
    const last_row = $(tbody).find('tr').last();
    const $row = last_row.clone();

    //Change data user-id to "new" for identification
    $row.attr('data-user-id', 'new');

    //Turn fixed fields to placeholders
    $row.find('.user-id').html('<span class="placeholder col-4"></span>');
    $row.find('.first-name').html('<span class="placeholder col-6"></span>');
    $row.find('.last-name').html('<span class="placeholder col-6"></span>');

    //Empty values
    $row.find('.employee-id .editable').text('');
    $row.find('.username .editable').text('');

    //Turn admin into checkbox
    $row.find('.admin').html('<div class="form-check"><input class="form-check-input" type="checkbox" value="" id="adminCheckBox" name="adminCheckBox"></div>');

    //Turn actions into save/cancel
    convertActions($row);

    //Add event handler to save/cancel buttons
    $row.find('#saveAccount').on('click', async function(){
        const valid = await validateFields();
        if (!valid) return;

        $('#confirmPassword').attr('data-bs-target', '#confirmAccount').attr('data-bs-toggle', 'modal');
        $('#passwordModal').modal('toggle');
    });
    $row.find('#cancelAccount').on('click', function(){
        revertChanges('tr[data-user-id="new"]', true);
    });

    // Skip employee-id in createInputFields — we replace it with a selectpicker below
    $row.find('.employee-id-div').removeClass('editable');
    createInputFields($row, 'sm', true, true);

    // Fetch unregistered employees for the dropdown
    let employees = [];
    try {
        showLoader();
        employees = await $.ajax({ url: '/users/get_unregistered_employees', type: 'GET' });
    } catch(e) {
        console.error('Failed to load unregistered employees', e);
    } finally {
        hideLoader();
    }

    const selectOptions = buildEmployeeSelectOptions(employees);
    const $selectWrapper = $(`
        <div class="employee-id-select-wrapper">
            <select name="employee-id-div" class="selectpicker"
                data-live-search="${employees.length > 5 ? 'true' : 'false'}"
                data-live-search-normalize="true"
                data-live-search-style="contains"
                data-live-search-placeholder="Search..."
                data-style="btn-sm btn-outline-custom"
                data-container="body"
                required>
                <option value="">Select employee...</option>
                <option data-divider="true"></option>
                ${selectOptions}
            </select>
            <div class="invalid-feedback">Please select an employee.</div>
        </div>
    `);

    $row.find('.employee-id .employee-id-div').replaceWith($selectWrapper);

    last_row.after($row);

    // Initialise the selectpicker
    const $select = $row.find('select[name="employee-id-div"]');
    $select.selectpicker();

    // When an employee is selected update the name placeholder cells
    $select.on('change', function(){
        const selectedId = Number($(this).val());
        const emp = employees.find(e => e.pk_employee_id === selectedId);
        if (emp) {
            $row.find('.first-name').text(emp.first_name);
            $row.find('.last-name').text(emp.last_name);
        } else {
            $row.find('.first-name').html('<span class="placeholder col-6"></span>');
            $row.find('.last-name').html('<span class="placeholder col-6"></span>');
        }
    });
}

//Validates initial employee ID and Username fields
async function validateFields() {
    const promises = [];

    // Validate employee select (create account mode)
    const $employeeSelect = $('#newUserForm select[name="employee-id-div"]');
    if ($employeeSelect.length) {
        promises.push((async () => {
            if (!$employeeSelect.val()) {
                $employeeSelect.closest('.bootstrap-select').addClass('is-invalid');
                return false;
            }
            return true;
        })());
    }

    $('#newUserForm input').each(function(index, input) {
        const name = input.name;
        const value = $(input).val();
        const feedback_div = $(input).siblings().closest('.invalid-feedback');

        if (name === 'adminCheckBox') return;
        if (name === 'employee-id-div') return; // handled by select above

        if (name === 'username-div') {
            promises.push((async () => {
                if (!isAlphaNumeric(value)) {
                    addFeedback(feedback_div, 'Username must be alphanumeric.', input);
                    return false;
                } else if (!isValidLength(value, 3, 25)) {
                    addFeedback(feedback_div, 'Username must be between 3 - 25 characters.', input);
                    return false;
                } else if (!(await isUsernameUnique(value))) {
                    addFeedback(feedback_div, 'Username must be unique', input);
                    return false;
                }
                return true;
            })());
        }
    });

    const results = await Promise.all(promises);
    const valid = results.every(Boolean);

    if (valid) {
        $('.is-invalid').removeClass('is-invalid');
    }
    return valid;
}


function revertChanges(selector, remove=false, wrapper){
    const row = $(selector);
    if (row.length > 0){
        if (remove){
            row.remove();
        } else {
            revertInputFields($(row), true, wrapper)
        }
        setEditing(false);
    }
}




// ----------------------- Event Handlers -------------------------------

$('#passwordModal').on('hidden.bs.modal', function(){
    $('#confirmPassword').attr('data-bs-target', '').attr('data-bs-toggle', '');
});
$('#closeConfirmBtn').on('click', function(){
    $('#confirmPassword').attr('data-bs-target', '#confirmAccount').attr('data-bs-toggle', 'modal');
});

$('#createAccount').on('click', async function(){
    if (editing) return;
    setEditing(true);
    await placeholderRow();
});

//Event handler for form submission
$('#confirmAccountBtn').on('click', function(){
    const form = $('#newUserForm');
    const data = {
        'employee_id': form.find('[name="employee-id-div"]').val(),
        'username': form.find('input[name="username-div"]').val(),
        'admin': form.find('input[name="adminCheckBox"]')[0].checked,
        'password': $('#tempPassword').val()
    }

    createAccount(data);
});

//Delete action event handler
$('#userTableBody').on('click', '.actions .fas.fa-trash', function(){
    const row = $(this).closest('tr');
    const modal = $('#deleteWarning');
    const employee_id = row.find('.employee-id-div').text();
    const user_id = row.data('user-id');
    const username = row.find('.username-div').text();

    modal.data('user-id', user_id);
    modal.find('.modal-title').text('Delete Account?')
    modal.find('.modal-body').empty().append(
        `
        User ID: <span class="user-id">${user_id}</span>
        <br>
        Employee ID: <span class="employee-id">${employee_id}</span>
        <br>
        Username: <span class="username">${username}</span>
        `
    );

    modal.modal('toggle');
});
$('#confirmDeleteBtn').on('click', function(){
    const user_id = $('#deleteWarning').data('user-id');
    deleteUser(user_id);
});
//Promote action event handler
$('#userTableBody').on('click', '.actions .fas.fa-crown', function(){
    const row = $(this).closest('tr');
    const modal = $('#confirmPromote');
    const employee_id = row.find('.employee-id-div').text();
    const user_id = row.data('user-id');
    const username = row.find('.username-div').text();

    modal.find('.user-id').text(user_id);
    modal.find('.employee-id').text(employee_id);
    modal.find('.username').text(username);
    modal.modal('toggle');
});
$('#confirmPromoteBtn').on('click', function(){
    const user_id = $('#confirmPromote').find('.user-id').text();
    promoteUser(user_id);
});
//Demote action event handler
$('#userTableBody').on('click', '.actions .fas.fa-arrow-trend-down', function(){
    const row = $(this).closest('tr');
    const modal = $('#confirmDemote');
    const employee_id = row.find('.employee-id-div').text();
    const user_id = row.find('.user-id').text().trim();
    const username = row.find('.username-div').text();

    modal.find('.user-id').text(user_id);
    modal.find('.employee-id').text(employee_id);
    modal.find('.username').text(username);
    modal.modal('toggle');
});
$('#confirmDemoteBtn').on('click', function(){
    const user_id = $('#confirmDemote').find('.user-id').text();
    demoteUser(user_id);
});
//Change password action event handler
$('#userTableBody').on('click', '.actions .fas.fa-key', function(){
    $('#confirmPassword').attr('data-bs-target', '#confirmPasswordChange').attr('data-bs-toggle', 'modal');
    $('#hidden-user-id').val($(this).closest('tr').data('user-id'));
    $('#tempPassword').val('');
    $('#passwordModal').modal('toggle');
});
$('#confirmPasswordChangeBtn').on('click', function(){
    const password = $('#tempPassword').val();
    const user_id = $('#hidden-user-id').val();
    changePassword(user_id, password);
});
//Edit username action event handler
$('#userTableBody').on('click', '.actions .fas.fa-square-pen', function(){
    if (editing) return;

    const row = $(this).closest('tr');
    const td = $(row).find('.username');
    const old_username = $(td).text();

    setEditing(true, row);

    createInputFields($(td), 'sm', true, true);
    convertActions(row);

    $('#saveAccount').on('click', async function(){
        valid = await validateFields();
        if (!valid) return;

        const modal = $('#confirmUsernameChange');
        const row = $(this).closest('tr');
        const user_id = $(row).find('.user-id').text().trim();
        const employee_id = $(row).find('.employee-id').text().trim();
        const new_username = $(row).find('.username-div.editable').val();

        modal.find('.user-id').text(user_id);
        modal.find('.employee-id').text(employee_id);
        modal.find('.username-old').text(old_username);
        modal.find('.username-new').text(new_username)

        modal.modal('toggle');
    });
    $('#cancelAccount').on('click', function(){
        revertChanges($(td).find('div'), false, 'div');
        revertActions(row);
    });
});
$('#confirmUsernameBtn').on('click', function(){
    const username = $('#confirmUsernameChange').find('.username-new').text();
    const user_id = $('#confirmUsernameChange').find('.user-id').text();
    changeUsername(user_id, username);
});

// Pending registrations - approve
$('#pendingTableBody').on('click', '.pending-approve', function(){
    const row = $(this).closest('tr');
    const user_id = row.data('user-id');
    const employee_id = row.find('.employee-id').text();
    const username = row.find('.username').text();
    const modal = $('#confirmApproveRegistration');
    modal.data('user-id', user_id);
    modal.find('.employee-id').text(employee_id);
    modal.find('.username').text(username);
    modal.modal('toggle');
});
$('#confirmApproveBtn').on('click', function(){
    const user_id = $('#confirmApproveRegistration').data('user-id');
    approvePendingRegistration(user_id);
});

// Pending registrations - deny
$('#pendingTableBody').on('click', '.pending-deny', function(){
    const row = $(this).closest('tr');
    const user_id = row.data('user-id');
    const employee_id = row.find('.employee-id').text();
    const username = row.find('.username').text();
    const modal = $('#confirmDenyRegistration');
    modal.data('user-id', user_id);
    modal.find('.employee-id').text(employee_id);
    modal.find('.username').text(username);
    modal.modal('toggle');
});
$('#confirmDenyBtn').on('click', function(){
    const user_id = $('#confirmDenyRegistration').data('user-id');
    denyPendingRegistration(user_id);
});
