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
        return $(`div[data-employee-id=${selected_employee_id}]`).find(selector).val();
    },
    updateData: function() {
        this.new_data.employees = {
            first_name: this.getDataCell('.employee-first-name'),
            last_name: this.getDataCell('.employee-last-name'),
            default_leave_balance: this.getDataCell('.employee-default-leave-bal'),
            default_sick_leave_balance: this.getDataCell('.employee-default-sick-bal'),
            contracted_daily_hours: this.getDataCell('.employee-contracted-daily'),
            contracted_weekly_hours: this.getDataCell('.employee-contracted-weekly')
        };
    },
    setOriginalData: function(){
        this.updateData();
        this.original_data = JSON.parse(JSON.stringify(this.new_data));
    },
    saveChanges: function() {
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
        }
        function createRecord(){
            $.ajax({
                url: `/employees/add_employee`,
                data: JSON.stringify(modify.new_data.employees),
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
                        flashMessage(resp.error || 'Failed to add employee. Please try again.', 'danger', 6000);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Could not add to Employees table: " + error);
                    flashMessage('Failed to add employee. Please try again later.', 'danger', 6000);
                }
            });
        }

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
    $('#toggleTableView')[0].checked = false;

    await loadEmployees();

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
    if (!modify.modified() && !modify.new) {
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
    new_stats.find('.id').hide();

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

        // Default Leave Balance: numeric, 0-5000 hours
        if (field === 'employee-default-leave-bal') {
            if (!isNumeric(value)) {
                invalidate(feedback, 'Leave balance must be numeric', input);
            } else if (!isValidNumber(Number(value), -1, 5001)) {
                invalidate(feedback, 'Leave balance must be 0-5000 hours', input);
            }
        }

        // Default Sick Leave Balance: numeric, 0-5000 hours
        if (field === 'employee-default-sick-bal') {
            if (!isNumeric(value)) {
                invalidate(feedback, 'Sick leave balance must be numeric', input);
            } else if (!isValidNumber(Number(value), -1, 5001)) {
                invalidate(feedback, 'Sick leave balance must be 0-5000 hours', input);
            }
        }

        // Contracted Daily Hours: numeric, 0-24 (exclusive)
        if (field === 'employee-contracted-daily') {
            if (!isNumeric(value)) {
                invalidate(feedback, 'Contracted daily hours must be numeric', input);
            } else if (!isValidNumber(Number(value), 0, 25)) {
                invalidate(feedback, 'Contracted daily hours must be between 0 and 24', input);
            }
        }

        // Contracted Weekly Hours: numeric, 0-168 (exclusive)
        if (field === 'employee-contracted-weekly') {
            if (!isNumeric(value)) {
                invalidate(feedback, 'Contracted weekly hours must be numeric', input);
            } else if (!isValidNumber(Number(value), 0, 169)) {
                invalidate(feedback, 'Contracted weekly hours must be between 0 and 168', input);
            }
        }
    });

    if (valid){
        $('.is-invalid').removeClass('is-invalid');
    }
    return valid;
}

$('#employee-records-body').on('click', 'tr', function() {
    if (!$('#stats-editing-controls').length) return;

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
