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
                        if (resp.message){
                            $('.modal.show').modal('hide');
                            modify.stopEditing();
                            softRefresh();
                            flashMessage(resp.message, 'success');
                            return
                        } else if (resp.error){
                            console.error(resp.error)
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error("Could not update Employees table: " + error);
                        alert("Failed to update employees. Please try again later.");
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
                        if (resp.message){
                            $('.modal.show').modal('hide');
                            modify.stopEditing();
                            softRefresh();
                            flashMessage(resp.message, 'success');
                            return
                        } else if (resp.error){
                            console.error(resp.error)
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error("Could not update EmployeeStats table: " + error);
                        alert("Failed to update employees. Please try again later.");
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
                    if (resp.employee_id){
                        createStats(resp.employee_id)
                    } else if (resp.error){
                        console.error(resp.error)
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Could not add to Employees table: " + error);
                    alert("Failed to add to employees. Please try again later.");
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
                    if (resp.message){
                        $('.modal.show').modal('hide');
                        modify.stopEditing();
                        softRefresh();
                        flashMessage(resp.message, 'success');
                        return
                    } else if (resp.error){
                        console.error(resp.error)
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Could not add to EmployeeStats table: " + error);
                    alert("Failed to add to stats. Please try again later.");
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
        $.ajax({
            url: `/employees/delete_employee/${selected_employee_id}`,
            type: 'DELETE',
            success: function(resp){
                if (resp.message){
                    $('.modal.show').modal('hide');
                    modify.stopEditing();
                    softRefresh();
                    flashMessage(resp.message, 'success');
                    return
                } else if (resp.error){
                    console.error(resp.error)
                }
            },
            error: function(xhr, status, error) {
                console.error("Could not update Employees table: " + error);
                alert("Failed to delete employees. Please try again later.");
            }
        });
    },

};

$(document).ready(async function(){
    // Ensure calendar view is default
    $('#toggleTableView')[0].checked = false;

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

    // Add editing UI dynamically to stats
    initSaveButtons();
});

async function softRefresh(){
    await loadEmployees();
    initSaveButtons();
}

function initSaveButtons(){
    const records = $('#employee-records-body tr');
    records.find('.editing-controls-container').remove();
    records.each(function(index, record){
        $(record).find('.employee-name').append(`
            <div class="editing-controls-container" style="display: none;">
                <div class="icon-square" onclick="saveRecordModal(event)"><i class="fas fa-floppy-disk"></i></div>
                <div class="icon-square" onclick="revertRecordModal(event)"><i class="fas fa-rotate-left"></i></div>
                <div class="icon-square" onclick="deleteRecordModal(event)"><i class="fas fa-trash"></i></div>
            </div>
        `)
    });
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
function deleteRecordModal(e) {
    if (e) e.stopPropagation();
    // Handle deleting if done when creating new record
    if (modify.new) return $('#revertModal').modal('toggle');

    const employee_name = $(`tr[data-employee-id=${selected_employee_id}]`).find('.employee-name').text().trim();
    $('#deleteModal #deleteModalEmployee').text(employee_name);
    $('#deleteModal').modal('toggle');
}
$('#saveChangesConfirm').on('click', function(){modify.saveChanges()});
$('#revertChangesConfirm').on('click', function(){modify.revertChanges()});
$('#deleteRecordConfirm').on('click', function(){modify.deleteRecord()});

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

    last_row.after(new_record);
    last_stats.after(new_stats);

    modify.new = true;
    initSaveButtons();
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

        // Position: alphanumeric, length 1-32
        if (field === 'employee-position') {
            if (!isAlphaNumeric(value)) {
                invalidate(feedback, 'Position must be alphanumeric', input);
            } else if (!isValidLength(value, 0, 33)) {
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
    // Handle selecting employee record
    if (editing){
        if (modify.modified() || modify.new) revertRecordModal();
        else saveRecordModal();
        return;
    };

    const editing_containers = $('.editing-controls-container');
    const this_editing_container = $(this).find('.editing-controls-container');
    const selected = $(this).data('employee-id') == selected_employee_id;
    $('#addRecordBtn').addClass('disabled');

    editing_containers.hide(300);
    if (selected) {
        this_editing_container.fadeIn(300);
        editing = true;

        createInputFields(`#employee-stats-body div[data-employee-id=${selected_employee_id}]`, 'sm', true);
        modify.setOriginalData();
    }
});