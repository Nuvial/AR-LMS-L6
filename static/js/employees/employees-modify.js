const modify = {
    original_data: {},
    new_data: {},
    new: false,
    modified: function(){
        this.updateData();
        return !deepEqual(this.original_data, this.new_data);
    },
    stopEditing: function(){
        this.original_data = {};
        this.new_data = {};
        this.new = false;
        $('#addRecordBtn').removeClass('disabled');
        deSelectRecord($(`tr[data-employee-id=${selected_employee_id}]`));
        revertInputFields(`form#employee-form .input-group`, true);
        editing = false;
    },
    getDataCell: function(selector){
        //Helper function to get the data from a table cell
        return $(`div[data-employee-id=${selected_employee_id}]`).find(selector).val();
    },
    updateData: function() {
        // Iterates through the table rows and updates the new_data object with the current values
        this.new_data.employees = {
            first_name: this.getDataCell('.employee-first-name'),
            last_name: this.getDataCell('.employee-last-name'),
            employee_position: this.getDataCell('.employee-position'),
            default_leave_balance: this.getDataCell('.employee-default-leave-bal'),
            default_sick_leave_balance: this.getDataCell('.employee-default-sick-bal')
        };
        this.new_data.stats = {
            attendance: this.getDataCell('.employee-attendance'),
            productivity: this.getDataCell('.employee-productivity'),
            performance: this.getDataCell('.employee-performance')
        };
    },
    setOriginalData: function(){
        this.updateData();
        this.original_data = JSON.parse(JSON.stringify(this.new_data));
    },
    saveChanges: function() {
        // Helper function to ajax UPDATE changes / editing EXISTING record
        function updateChanges(){
            if (!deepEqual(modify.new_data.employees, modify.original_data.employees)){
                $.ajax({
                    url: `/employees/update_employee/${selected_employee_id}`,
                    data: JSON.stringify(modify.new_data.employees),
                    type: 'PUT',
                    contentType: 'application/json',
                    success: function(resp){
                        if (resp.message === 'success'){
                            $('.modal.show').modal('hide');
                            modify.stopEditing();
                            softRefresh();
                            flashMessage('Employee record updated successfully.', 'success');
                        } else {
                            $('.modal.show').modal('hide');
                            flashMessage(resp.error || 'Failed to update employee. Please try again.', 'danger', 6000);
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error("Could not update Employees table: " + error);
                        flashMessage('Failed to update employee. Please try again later.', 'danger', 6000);
                    }
                });
            }
            if (!deepEqual(modify.new_data.stats, modify.original_data.stats)){
                $.ajax({
                    url: `/stats/update/${selected_employee_id}`,
                    data: JSON.stringify(modify.new_data.stats),
                    type: 'PUT',
                    contentType: 'application/json',
                    success: function(resp){
                        if (resp.message === 'success'){
                            $('.modal.show').modal('hide');
                            modify.stopEditing();
                            softRefresh();
                            flashMessage('Employee stats updated successfully.', 'success');
                        } else {
                            $('.modal.show').modal('hide');
                            flashMessage(resp.error || 'Failed to update stats. Please try again.', 'danger', 6000);
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error("Could not update EmployeeStats table: " + error);
                        flashMessage('Failed to update stats. Please try again later.', 'danger', 6000);
                    }
                });
            }
        }
        function createRecord(){
            $.ajax({
                url: `/employees/add_employee`,
                data: JSON.stringify(modify.new_data.employees),
                type: 'POST',
                contentType: 'application/json',
                success: function(resp){
                    if (resp.message === 'success' && resp.employee_id){
                        createStats(resp.employee_id);
                    } else {
                        $('.modal.show').modal('hide');
                        flashMessage(resp.error || 'Failed to add employee. Please try again.', 'danger', 6000);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Could not add to Employees table: " + error);
                    flashMessage('Failed to add employee. Please try again later.', 'danger', 6000);
                }
            });
        }
        function createStats(id){
            $.ajax({
                url: `/stats/create/${id}`,
                data: JSON.stringify(modify.new_data.stats),
                type: 'POST',
                contentType: 'application/json',
                success: function(resp){
                    if (resp.message === 'success'){
                        $('.modal.show').modal('hide');
                        modify.stopEditing();
                        softRefresh();
                        flashMessage('Employee added successfully.', 'success');
                    } else {
                        $('.modal.show').modal('hide');
                        flashMessage(resp.error || 'Failed to add employee stats. Please try again.', 'danger', 6000);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Could not add to EmployeeStats table: " + error);
                    flashMessage('Failed to add stats. Please try again later.', 'danger', 6000);
                }
            });
        }

        // If fields not valid, dont continue to ajax
        if (!validateFields()){
            $('.modal.show').modal('hide');
            return
        };

        if (!modify.new){
            updateChanges();
        } else {
            createRecord();
        }
    },
    revertChanges: function() {
        softRefresh();
        this.stopEditing();
        $('.modal.show').modal('hide');
    },
    deleteRecord: function() {
        const selfDelete = Number(selected_employee_id) === Number(current_user.employee_id);
        $.ajax({
            url: `/employees/delete_employee/${selected_employee_id}`,
            type: 'DELETE',
            success: function(resp){
                if (resp.message === 'success'){
                    $('.modal.show').modal('hide');
                    if (selfDelete) {
                        localStorage.setItem('flashMessage', JSON.stringify({
                            message: 'Your employee record and associated account have been deleted.',
                            type: 'success',
                            length: 3000,
                        }));
                        window.location.href = '/';
                    } else {
                        modify.stopEditing();
                        softRefresh();
                        flashMessage('Employee deleted successfully.', 'success');
                    }
                } else {
                    $('.modal.show').modal('hide');
                    flashMessage(resp.error || 'Failed to delete employee. Please try again.', 'danger', 6000);
                }
            },
            error: function(xhr, status, error) {
                console.error("Could not delete from Employees table: " + error);
                flashMessage('Failed to delete employee. Please try again later.', 'danger', 6000);
            }
        });
    },

};

$(document).ready(async function(){
    // Ensure calendar view is default
    $('#toggleTableView')[0].checked = false;
    $('#viewSelector').val('View All');

    // Begin loading employees data
    await loadEmployees();

    // Initialise elements
    calendar = initCalendar('#calendar', '100%', true);
    initSearch(
        '#employee-search',
        '#employee-records-body tr',
        [
            {selector: '.employee-name'},
            {selector: '.employee-id'}
        ]
    );
    initTableToggle();
});

async function softRefresh(){
    await loadEmployees();
}

function initSaveButtons(){
    // Editing controls live in the Statistics card header; ensure hidden on init
    $('#stats-editing-controls').fadeOut(300);
}

function saveRecordModal(e) {
    if (e) e.stopPropagation();
    if (!modify.modified() && !modify.new) {
        modify.stopEditing();
        return;
    }
    $('#saveModal').modal('toggle');
}
function revertRecordModal(e) {
    if (e) e.stopPropagation();
    if (!modify.modified() && !modify.new) { //Don't ask to unsave changes if no changes made or if not creating a new record.
        modify.stopEditing();
        return;
    }
    $('#revertModal').modal('toggle');
}
async function deleteRecordModal(e) {
    if (e) e.stopPropagation();
    if (modify.new) return $('#revertModal').modal('toggle');

    const isSelfDelete = Number(selected_employee_id) === Number(current_user.employee_id);

    if (isSelfDelete) {
        try {
            const users = await $.ajax({ url: '/users/get_users', type: 'GET' });
            const adminCount = users.filter(u => u.admin === 1).length;
            if (adminCount <= 1) {
                flashMessage('Cannot delete your account as you are the only admin. Please assign another admin first.', 'danger', 0);
                return;
            }
        } catch (err) {
            console.error('Failed to check admin count:', err);
            flashMessage('Failed to verify admin status. Please try again.', 'danger', 6000);
            return;
        }
        $('#deleteWarning .modal-title').html('Delete Your Employee Record?');
        $('#deleteWarning .modal-body').html(`
            <div class="warning-callout danger mb-3">
                <i class="fa-solid fa-circle-exclamation"></i><strong>Warning:</strong> You are about to delete your own employee record.
            </div>
            <p>Deleting your employee record will also remove your associated login account. <strong>You will immediately lose access to the application.</strong></p>
            <p>To regain access, another admin will need to create a new employee profile and login account for you.</p>
            <p class="mb-0"><strong>This action is irreversible.</strong></p>
        `);
        $('#deleteWarning').modal('show');
    } else {
        const employee_name = $(`tr[data-employee-id=${selected_employee_id}]`).find('.employee-name').text().trim();
        $('#deleteModal #deleteModalEmployee').text(employee_name);
        $('#deleteModal').modal('toggle');
    }
}
$('#saveChangesConfirm').on('click', function(){modify.saveChanges()});
$('#revertChangesConfirm').on('click', function(){modify.revertChanges()});
$('#deleteRecordConfirm').on('click', function(){modify.deleteRecord()});
$('#confirmDeleteBtn').on('click', function(){modify.deleteRecord()});

$('#addRecordBtn').on('click', function() {
    $(this).addClass('disabled');
    // Find the last employee record row and stats block
    const last_row = $('#employee-records-body tr').last();
    const last_stats = $('#employee-stats-body > .row').last();

    const new_record = last_row.clone();
    new_record.attr('data-employee-id', 'new');
    new_record.find('.employee-id').text('ID');
    new_record.find('.employee-name').text('Name')
    new_record.addClass('new-record')

    const new_stats = last_stats.clone();
    new_stats.attr('data-employee-id', 'new');
    new_stats.find('.editable').text('');
    new_stats.find('.employee-id').text('');
    new_stats.find('.employee-leave-remaining').text('');
    new_stats.find('.employee-sick-remaining').text('');
    new_stats.find('.employee-stats-recorded').text('');
    new_stats.find('.id').hide(); // Employee ID is auto-generated; hide for new records

    last_row.after(new_record);
    last_stats.after(new_stats);

    modify.new = true;
    new_record.click();

});

function validateFields(){
    let valid = true;

    function invalidate(feedbackDiv, feedback, input) {
        valid = false;
        addFeedback(feedbackDiv, feedback, input);
    };

    // Custom field validation for each input.
    $('form#employee-form input').each(function(index, input){
        const value = $(input).val();
        const feedback = $(input).closest('.input-group').find('.invalid-feedback');
        const field = input.name;

        // First Name: alphabetic, length 1-32
        if (field === 'employee-first-name') {
            if (!isAlphabetic(value)) {
                invalidate(feedback, 'Name contains invalid characters', input);
            } else if (!isValidLength(value, 0, 33)) {
                invalidate(feedback, 'Name must be 1-32 characters', input);
            }
        }

        // Last Name: alphabetic, length 1-32
        if (field === 'employee-last-name') {
            if (!isAlphabetic(value)) {
                invalidate(feedback, 'Name contains invalid characters', input);
            } else if (!isValidLength(value, 0, 33)) {
                invalidate(feedback, 'Name must be 1-32 characters', input);
            }
        }

        // Position: letters, numbers, and spaces; length 1-32
        if (field === 'employee-position') {
            if (!isValidPosition(value)) {
                invalidate(feedback, 'Position must contain only letters, numbers and spaces', input);
            } else if (!isValidLength(value.trim(), 0, 33)) {
                invalidate(feedback, 'Position must be 1-32 characters', input);
            }
        }

        // Default Leave Balance: numeric, 0-365
        if (field === 'employee-default-leave-bal') {
            if (!isNumeric(value)) {
                invalidate(feedback, 'Leave balance must be numeric', input);
            } else if (!isValidNumber(Number(value), -1, 366)) {
                invalidate(feedback, 'Leave balance must be 0-365', input);
            }
        }

        // Default Sick Leave Balance: numeric, 0-365
        if (field === 'employee-default-sick-bal') {
            if (!isNumeric(value)) {
                invalidate(feedback, 'Sick leave balance must be numeric', input);
            } else if (!isValidNumber(Number(value), -1, 366)) {
                invalidate(feedback, 'Sick leave balance must be 0-365', input);
            }
        }

        // Attendance, Productivity: numeric, 0-100
        if (field === 'employee-attendance' || field === 'employee-productivity') {
            if (!isNumeric(value)) {
                invalidate(feedback, 'Value must be numeric', input);
            } else if (!isValidNumber(Number(value), -1, 101)) {
                invalidate(feedback, 'Value must be 0-100', input);
            }
        }

        // Performance: numeric: 0-10
        if (field === 'employee-performance'){
            if (!isNumeric(value)) {
                invalidate(feedback, 'Value must be numeric', input);
            } else if (!isValidNumber(Number(value), -1, 11)) {
                invalidate(feedback, 'Value must be 0-10', input);
            }
        }
    });

    if (valid){
        $('.is-invalid').removeClass('is-invalid');
    }
    return valid;
}

$('#employee-records-body').on('click', 'tr', function() {
    // Admin-only: editing controls must be present
    if (!$('#stats-editing-controls').length) return;

    // Handle selecting employee record
    if (editing){
        if (modify.modified() || modify.new) revertRecordModal();
        else saveRecordModal();
        return;
    };

    const selected = $(this).data('employee-id') == selected_employee_id;
    $('#addRecordBtn').addClass('disabled');

    if (selected) {
        $('#stats-editing-controls').fadeIn(300);
        editing = true;

        createInputFields(`#employee-stats-body div[data-employee-id=${selected_employee_id}]`, 'sm', true);
        modify.setOriginalData();
    }
});

// View selector (admin only)
function call(url, area, text, averages=false){
    $.ajax({
        url: `/stats/${area}/${url}`,
        type: 'GET',
        beforeSend: function(){
            $('.averages-text .label').text('');
            $('.averages-text .value').text('');
        },
        success: function(resp){
            if (resp.length > 1){
                const id_list = resp.map(id => id.fk_employee_id);
                loadEmployees(id_list);

                if (averages){
                    let percentage = area === 'attendance' ? '%' : '';
                    $('.averages-text .label').text(`${text} ${area}:`);
                    $('.averages-text .value').text(`${resp[0][`${text}_${area}`].toFixed(2)} ${percentage}`);
                }
            }
        },
        complete: function(){
            hideLoader()
        },
        error: function(xhr, status, error) {
            console.error(`Could not get ${text} attendance: ${error}`);
            alert(`Failed to get ${text} attendance. Please try again later.`);
        }
    });
}

$('#viewSelector').on('change', function(){
    const option = $(this).val();
    showLoader();
    if (selected_employee_id){
        deSelectRecord($('.selected-record'));
    }

    if (option === 'View All'){
        $('.averages-text .label').text('');
        $('.averages-text .value').text('');
        loadEmployees();
    } else if (option === 'attendance-top5'){
        call('top5', 'attendance', 'top 5');
    } else if (option === 'attendance-bottom5'){
        call('bottom5', 'attendance', 'bottom 5');
    } else if (option === 'attendance-mean'){
        call('mean', 'attendance', 'mean', true);
    } else if (option === 'attendance-median'){
        call('median', 'attendance', 'median', true);
    } else if (option === 'attendance-range'){
        call('range', 'attendance', 'range', true);
    } else if (option === 'attendance-modal'){
        call('modal', 'attendance', 'modal', true);
    } else if (option === 'performance-top5'){
        call('top5', 'performance', 'top5');
    } else if (option === 'performance-bottom5'){
        call('bottom5', 'performance', 'bottom 5');
    } else if (option === 'performance-mean'){
        call('mean', 'performance', 'mean', true);
    } else if (option === 'performance-median'){
        call('median', 'performance', 'median', true);
    } else if (option === 'performance-range'){
        call('range', 'performance', 'range', true);
    } else if (option === 'performance-modal'){
        call('modal', 'performance', 'modal', true);
    }
});
