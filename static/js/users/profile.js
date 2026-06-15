const profile = {
    profile: {
        firstName: "",
        lastName: "",
        position: "",
        lineManager: null,
        team: null,
    },
    originalData: {
        firstName: "",
        lastName: "",
        username: "",
    },
    newData: {},
    modified: function() {
        return !deepEqual(this.originalData, this.newData)
    }
};

async function loadProfile() {
    return $.ajax({
        url: '/employees/get_employees/self',
        type: 'GET',
        beforeSend: showLoader,
        success: function(resp){
            if (resp.length > 0) {
                const employee = resp[0];
                
                // Update profile object
                profile.profile.firstName = employee.first_name;
                profile.profile.lastName = employee.last_name;
                profile.profile.position = employee.employee_position;

                if (employee.fk_team_id !== null) {
                    profile.profile.lineManager = `${employee.manager_first_name} ${employee.manager_last_name}`;
                    profile.profile.team = employee.team_name;
                }

                // Update profile object state management
                profile.originalData.firstName = profile.profile.firstName;
                profile.originalData.lastName = profile.profile.lastName;
                profile.newData = JSON.parse(JSON.stringify(profile.originalData));
            }
        },
        complete: hideLoader,
        error: function(xhr, status, error) {
            console.log("Error loading users: " + error);
            alert("Failed to load users. Please try again later.");
        }
    });
}

function updateForm() {
    const $form = $('#profileForm');
    const keys = Object.keys(profile.profile);
    $form.find('input').each((_, input) => {
        const id = input.id;
        if (keys.includes(id)) {
            $(input).val(profile.profile[id]);
        }
    });
}

async function validateFields() {
    let valid = true;
    const promises = [];

    function invalidate(feedbackDiv, feedback, input){
        valid = false;
        addFeedback(feedbackDiv, feedback, input);
    };

    // Custom field validation for each input.
    $('form#profileForm input.editable').each(function(index, input){
        const value = $(input).val();
        const feedback = $(input).parent().find('.invalid-feedback');
        const field = input.name;

        if (profile.originalData[field] === value) return;

        // First Name or Last Name: alphabetic, length 1-32
        if (field === 'firstName' || field === 'lastName') {
            if (!isAlphabetic(value)) {
                invalidate(feedback, 'Name contains invalid characters', input);
            } else if (!isValidLength(value, 0, 33)) {
                invalidate(feedback, 'Name must be 1-32 characters', input);
            }
        }

        if (field === 'username') {
            promises.push((async () => {
                if (!isAlphaNumeric(value)) {
                    invalidate(feedback, 'Username must be alphanumeric.', input);
                    return false;
                } else if (!isValidLength(value, 3, 25)) {
                    invalidate(feedback, 'Username must be between 3 - 25 characters.', input);
                    return false;
                } else if (!(await isUsernameUnique(value))) {
                    invalidate(feedback, 'Username must be unique', input);
                    return false;
                }
                return true;
            })());
        }
    });

    const results = await Promise.all(promises);
    
    valid = results.every(Boolean) && valid;
    if (valid){
        $('.is-invalid').removeClass('is-invalid');
    }
    return valid;
}

async function isUsernameUnique(username) {
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

async function updateData() {
    showLoader();

    const originalData = profile.originalData;
    const newData = profile.newData;

    if (originalData.firstName !== newData.firstName ||
        originalData.lastName !== newData.lastName) {
        $.ajax({
            url: `/employees/update_employee/self`,
            type: 'PUT',
            data: JSON.stringify({
                'first_name': newData.firstName,
                'last_name': newData.lastName
            }),
            contentType: 'application/json',
            success: function(resp){
                if (resp.message = 'success'){
                    flashMessage('Name was changed successfully.', 'success', 3000)
                } else {
                    flashMessage('Error changing name. Please try again', 'danger', 3000)
                }
            },
            error: function(xhr, status, error) {
                console.log("Error changing name: " + error);
                alert("Failed to change name. Please try again later.");
            }
        });
    }

    if (originalData.username !== newData.username) {
        $.ajax({
            url: `/users/change_username/self`,
            type: 'PUT',
            data: JSON.stringify({'username': newData.username}),
            contentType: 'application/json',
            success: function(resp){
                if (resp.message = 'success'){
                    flashMessage('Username was changed successfully.', 'success', 3000)
                } else {
                    flashMessage('Error changing username for user account. Please try again', 'danger', 3000)
                }
            },
            error: function(xhr, status, error) {
                console.log("Error changing username: " + error);
                alert("Failed to change username. Please try again later.");
            }
        });
    }

    hideLoader();
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
            if (resp.message = 'success'){
                flashMessage('User password changed successfully.', 'success', 3000)
            } else {
                flashMessage('Error changing password on user account. Please try again', 'danger', 3000)
            }
            $('.modal.show').modal('hide');
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

function deleteProfile(){
    $.ajax({
        url: `/users/delete_user/self`,
        type: 'DELETE',
        beforeSend: function(){
            showLoader();
        },
        success: function(resp){
            if (resp.message = 'success'){
                localStorage.setItem('flashMessage', JSON.stringify({
                    message: 'Account deleted successfully.',
                    type: 'success',
                    length: 3000,
                }));
            } else {
                flashMessage('Error deleting account. Please try again', 'danger', 3000)
            }
            window.location.href = '/';
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