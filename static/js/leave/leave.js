/**
 * Calculates the total bookable hours for a date range based on contracted hours.
 * Per-week hours are capped at contracted_weekly_hours, and per-day hours are
 * capped at contracted_daily_hours.
 *
 * @param {Date} start_date - Inclusive start date of the booking.
 * @param {Date} end_date   - Inclusive end date of the booking.
 * @param {number} daily_hours  - Contracted hours per day.
 * @param {number} weekly_hours - Contracted hours per week (cap).
 * @returns {number} Total hours for the booking.
 */
function calculateLeaveHours(start_date, end_date, daily_hours, weekly_hours) {
    let total_hours = 0;
    let current = new Date(start_date);

    while (current <= end_date) {
        // Find Monday of the week containing `current` (Mon=0 offset)
        const day_of_week = current.getDay();
        const days_since_monday = (day_of_week + 6) % 7;

        const week_end = new Date(current);
        week_end.setDate(current.getDate() + (6 - days_since_monday));

        // Intersection of this week with the booking range
        const effective_end = new Date(Math.min(week_end.getTime(), end_date.getTime()));

        const days_in_week = Math.round((effective_end - current) / (1000 * 60 * 60 * 24)) + 1;
        const week_hours = Math.min(days_in_week * daily_hours, weekly_hours);
        total_hours += week_hours;

        // Advance to the Monday of the next week
        current = new Date(week_end);
        current.setDate(week_end.getDate() + 1);
    }

    return total_hours;
}

const new_leave = {
    employee_id: current_user.employee_id,
    type: null,
    leave_available: null,
    sick_leave_available: null,
    default_leave: null,
    default_sick_leave: null,
    contracted_daily_hours: null,
    contracted_weekly_hours: null,
    hours: null,
    getLeaveAvailable: async function(){
        const data = await getRemainingLeave(this.employee_id, false);
        const default_data = await getDefaultLeave(this.employee_id, false);
        this.leave_available = data.leave_remaining;
        this.sick_leave_available = data.sick_leave_remaining;
        this.default_leave = default_data.default_leave_balance;
        this.default_sick_leave = default_data.default_sick_leave_balance;
        this.contracted_daily_hours = default_data.contracted_daily_hours;
        this.contracted_weekly_hours = default_data.contracted_weekly_hours;
    },
    stop: function(){
        $('.calendar-container').removeClass('active-calendar requesting-leave').addClass('idle-calendar hover-calendar');
        $('.selected-date').removeClass('selected-date');
        $('#employee-records-body.disabled').removeClass('disabled');
        this.type = null;
        this.hours = null;
        first_date = '';
        second_date = '';
        selecting_date = false;
        softRefresh();
    },
    handleDateClick: function(){
        function getDatesBetween(start_date, end_date){
            const dates = [];
            let current = new Date(start_date);
            while (current <= end_date){
                dates.push(new Date(current));
                current.setDate(current.getDate() + 1);
            }
            return dates;
        }
        function toYMD(date) {
            return date.getFullYear() + '-' +
                String(date.getMonth() + 1).padStart(2, '0') + '-' +
                String(date.getDate()).padStart(2, '0');
        }

        if (first_date && second_date){
            let start_date = new Date(first_date);
            let end_date = new Date(second_date);
            selecting_date = false;

            if (start_date > end_date){
                [start_date, end_date] = [end_date, start_date];
                [first_date, second_date] = [second_date, first_date];
            }

            const all_dates = getDatesBetween(start_date, end_date);

            // Calculate hours using contracted hours
            const daily = this.contracted_daily_hours || 8;
            const weekly = this.contracted_weekly_hours || 40;
            const calculated_hours = calculateLeaveHours(start_date, end_date, daily, weekly);

            // Check if requested hours exceeds available balance (TOIL has no balance cap)
            if (this.type !== 'Time off in Lieu') {
                const selected_leave_available = this.type === 'Annual Leave'
                    ? this.leave_available
                    : this.sick_leave_available;
                if (calculated_hours > selected_leave_available){
                    flashMessage('You do not have enough leave available for this booking. Please select fewer days.', 'danger', 10000);
                    first_date = '';
                    second_date = '';
                    selecting_date = true;
                    $('.selected-date').removeClass('selected-date');
                    return;
                }
            }

            // Mark selected dates on calendar
            all_dates.forEach(date => {
                $(`td[data-date="${toYMD(date)}"]`).not('.selected-date').addClass('selected-date');
            });

            this.hours = calculated_hours;
            this.populateRequestModal(start_date, end_date, calculated_hours);
        }
    },
    populateRequestModal: function(start, end, hours){
        const modal = $('#viewRequest');

        modal.find('#deleteRequest').hide();
        modal.find('.status-text').hide();

        modal.find('#requestTitleID').text('Confirm New Leave Request');
        modal.find('#requestTitleType').text('');

        modal.find('.date-requested').text(new Date().toLocaleString());
        modal.find('.date-from').text(start.toLocaleDateString());
        modal.find('.date-to').text(end.toLocaleDateString());
        modal.find('.days-difference').text(hours);

        modal.find('.default-leave').text(this.default_leave);
        modal.find('.default-sick-leave').text(this.default_sick_leave);

        modal.find('.leave-taken').text(this.default_leave - this.leave_available);
        modal.find('.sick-leave-taken').text(this.default_sick_leave - this.sick_leave_available);

        modal.find('#adminComments').attr('disabled', '').val('');
        modal.find('#employeeComments').removeAttr('disabled').val('');

        modal.find('.action-bar').hide();
        modal.find('.action-bar-request').show();

        modal.modal('show');
    },
    confirmRequest: function(){
        const firstDate = new Date(first_date);
        const secondDate = new Date(second_date);

        firstDate.setDate(firstDate.getDate() + 1);
        secondDate.setDate(secondDate.getDate() + 1);

        const start_date = firstDate.toISOString().slice(0, 10);
        const end_date = secondDate.toISOString().slice(0, 10);

        data = {
            'start_date': start_date,
            'end_date': end_date,
            'employee_comments': $('#employeeComments').val(),
            'leave_type': this.type,
            'hours_requested': this.hours
        }

        $.ajax({
            url: `/leave/request_leave`,
            type: 'POST',
            data: JSON.stringify(data),
            contentType: 'application/json',
            success: function(resp){
                if (resp.message === 'success'){
                    $('.modal.show').modal('hide');
                    $('#cancelAddRequestBtn').click();
                    flashMessage('Leave request has been successfully made.', 'success');
                } else {
                    flashMessage(resp.error || 'Could not submit leave request. Please try again.', 'danger', 6000);
                }
            },
            error: function(xhr, status, error) {
                console.log(`Error requesting leave.`);
            }
        });
    },
    deleteRequest: function(id){
        $.ajax({
            url: `/leave/update_leave/delete/${id}`,
            type: 'DELETE',
            success: function(resp){
                if (resp.message === 'success'){
                    $('.modal.show').modal('hide');
                    $('#cancelAddRequestBtn').click();
                    flashMessage('Leave request has been successfully deleted.', 'success');
                } else {
                    flashMessage(resp.error || 'Could not delete leave request. Please try again.', 'danger', 6000);
                }
            },
            error: function(xhr, status, error) {
                console.log(`Error requesting leave.`);
            }
        });
    }
}

let cached_pending_details = {};
let selected_leave_id = null;
let isRefreshing = false;

function softRefresh(){
    if (isRefreshing) return;
    isRefreshing = true;
    $('.refresh').addClass('refresh-disabled');

    selected_leave_id = null;
    cached_pending_details = {};
    $('#adminComments').val('');
    deSelectRecord($('.selected-record'));
    calendar.removeAllEvents();
    getRequestedLeave();

    setTimeout(() => {
        isRefreshing = false;
        $('.refresh').removeClass('refresh-disabled');
    }, 3000);
}

$('.refresh').on('click', softRefresh);

function getRequestedLeave(){
    $.ajax({
        url: '/leave/get_leave/requested',
        type: 'GET',
        beforeSend: function(){
            showLoader();
        },
        success: function(resp){
            if (resp){
                if (resp.error){
                    noRequestedLeave();
                    resp = [];
                }

                resp.push({'fk_employee_id': Number(current_user.employee_id)});
                formatted = [...new Set(resp.map(record => record.fk_employee_id))];

                loadEmployees(formatted);
            }
        },
        complete: hideLoader,
        error: function(xhr, status, error) {
            console.log("Error loading requested leave: " + error);
            alert("Failed to load employees requested leave. Please try again later.");
        }
    });
}
function noRequestedLeave(){
    hideLoader();
    if (current_user.admin == 0 && current_user.is_manager == 0) {
        return
    };

    flashMessage('There are no active leave requests at the moment.<br> If you are expecting a leave request please double check it was submitted by the employee.', 'warning', 9000);
    $('.no-requests').show();
    $('#employee-records-body').hide();
}

function cachePendingDetails(data){
    data.forEach(id => {
        $.ajax({
            url: `/leave/get_leave/${id}`,
            type: 'GET',
            success: function(resp){
                if (resp.message == 'error'){
                    if (!cached_pending_details[id]) cached_pending_details[id] = {};
                    return;
                }

                resp.leave.forEach(request => {
                    if (!cached_pending_details[id]) cached_pending_details[id] = {};
                    if (!cached_pending_details[id][request.pk_leave_id]) cached_pending_details[id][request.pk_leave_id] = request;
                });
            },
            complete: function(){
                if (!cached_pending_details[id]) cached_pending_details[id] = {};
                getRemainingLeave(id);
                getDefaultLeave(id);
            },
            error: function(xhr, status, error) {
                console.log(`Error loading leave data for id ${id} : ${error}`);
            }
        });
    })
}

async function getRemainingLeave(id, cache=true){
    const resp = await $.ajax({
        url: `/leave/get_leave/remaining/${id}`,
        type: 'GET',
        error: function(xhr, status, error) {
            console.log(`Error loading leave data for id ${id} : ${error}`);
        }
    });
    if (!resp[0]){
        console.error(`No remaining leave data for id ${id}`)
        return
    }
    if (cache){
        const entries = Object.values(cached_pending_details[id] || {});
        if (entries.length){
            entries.forEach(value => {
                value['leave_remaining'] = resp[0].leave_remaining;
                value['sick_leave_remaining'] = resp[0].sick_leave_remaining;
            });
        } else {
            cached_pending_details[id]._meta = {
                leave_remaining: resp[0].leave_remaining,
                sick_leave_remaining: resp[0].sick_leave_remaining
            };
        }
    } else {
        return resp[0]
    }
}
async function getDefaultLeave(id, cache=true){
    const resp = await $.ajax({
        url: `/employees/get_employees/${id}`,
        type: 'GET',
        error: function(xhr, status, error) {
            console.log(`Error loading employee data for id ${id} : ${error}`);
        }
    });
    if (!resp[0]){
        console.error(`No default leave data for id ${id}`);
        return;
    }
    if (cache){
        const entries = Object.values(cached_pending_details[id] || {});
        if (entries.length){
            entries.forEach(value => {
                value['default_leave_balance'] = resp[0].default_leave_balance;
                value['default_sick_leave_balance'] = resp[0].default_sick_leave_balance;
                value['contracted_daily_hours'] = resp[0].contracted_daily_hours;
                value['contracted_weekly_hours'] = resp[0].contracted_weekly_hours;
            });
        } else {
            cached_pending_details[id]._meta = {
                ...(cached_pending_details[id]._meta || {}),
                default_leave_balance: resp[0].default_leave_balance,
                default_sick_leave_balance: resp[0].default_sick_leave_balance,
                contracted_daily_hours: resp[0].contracted_daily_hours,
                contracted_weekly_hours: resp[0].contracted_weekly_hours
            };
        }
    } else {
        return resp[0];
    }
}

function approveLeave(id, comment){
    $.ajax({
        url: `/leave/update_leave/approve/${id}`,
        type: 'PUT',
        data: JSON.stringify({comment: comment}),
        contentType: 'application/json',
        success: function(resp){
            if (resp && resp.message === 'success'){
                softRefresh();
                $('.modal.show').modal('hide');
                flashMessage('Leave Approval Successful.', 'success', 3000);
            } else {
                flashMessage(resp.error || 'Could not approve leave. Please try again.', 'danger', 6000);
            }
        },
        error: function(xhr, status, error) {
            console.log(`Error approving leave for id ${id} : ${error}`);
        }
    });
}
function rejectLeave(id, comment){
    $.ajax({
        url: `/leave/update_leave/deny/${id}`,
        type: 'PUT',
        data: JSON.stringify({comment: comment}),
        contentType: 'application/json',
        success: function(resp){
            if (resp && resp.message === 'success'){
                softRefresh();
                $('.modal.show').modal('hide');
                flashMessage('Leave Rejection Successful.', 'success', 3000);
            } else {
                flashMessage(resp.error || 'Could not reject leave. Please try again.', 'danger', 6000);
            }
        },
        error: function(xhr, status, error) {
            console.log(`Error rejecting leave for id ${id} : ${error}`);
        }
    });
}

// Handles click of calendar event by populating leave modal
function handleEditClick(data, page){
    const status = data.extendedProps.status;
    const leave_id = data.extendedProps.pk_leave_id;
    const leave_data = cached_pending_details[selected_employee_id][leave_id];

    selected_leave_id = leave_id;

    const date_requested = new Date(leave_data.date_requested).toLocaleString();
    const date_from = data.start;
    const date_to = new Date(leave_data.end_date);

    const modal = $('#viewRequest');

    modal.find('#requestTitleID').text(`Leave ID: ${leave_data.pk_leave_id}`);
    modal.find('#requestTitleType').text(`Leave Type: ${leave_data.leave_type}`);

    modal.find('.date-info .date-requested').text(date_requested);
    modal.find('.date-info .date-from').text(date_from.toLocaleDateString());
    modal.find('.date-info .date-to').text(date_to.toLocaleDateString());

    modal.find('.date-info .days-difference').text(leave_data.hours_requested);
    modal.find('.date-info .default-leave').text(leave_data.default_leave_balance);
    modal.find('.date-info .default-sick-leave').text(leave_data.default_sick_leave_balance);
    modal.find('.date-info .leave-taken').text(leave_data.default_leave_balance - leave_data.leave_remaining);
    modal.find('.date-info .sick-leave-taken').text(leave_data.default_sick_leave_balance - leave_data.sick_leave_remaining);

    modal.find('.action-bar-request').hide();

    const employee_comments = modal.find('#employeeComments');
    const admin_comments = modal.find('#adminComments');

    employee_comments.val(leave_data.comment_employee);
    admin_comments.val(leave_data.comment_admin);

    $('#deleteRequest').hide();
    if (status == 'Approved' || status == 'Rejected' || page == 'view_records' || page == 'modify_records'){
        employee_comments.attr('disabled', '');
        admin_comments.attr('disabled', '');
        $('.action-bar').hide();
        $('.status-text').text(status);
        if (date_from > new Date() && current_user.employee_id == selected_employee_id && status == 'Approved'){
            if (!(page == 'view_records') && !(page == 'modify_records')){
                $('#deleteRequest').show();
            }
        }
    } else {
        $('.action-bar').show();
        $('.status-text').text('');

        if ((current_user.admin == 1 || current_user.is_manager == 1) && !(current_user.employee_id == selected_employee_id)){
            employee_comments.attr('disabled', '');
            admin_comments.removeAttr('disabled');
        } else {
            employee_comments.attr('disabled', '');
            admin_comments.attr('disabled', '');
            $('.action-bar').hide();
            $('.status-text').text(status);
            $('#deleteRequest').show();
        }
    }

    modal.modal('toggle');
}
$('.card-body #tableView').on('click', 'tr td:last-child()', function(){
    const leave_id = $(this).closest('tbody').data('leave-id');
    const event = calendar.getEvents().find(ev =>
        ev.extendedProps.pk_leave_id === leave_id
    );
    calendar.gotoDate(event.start);
    const eventEl = $(`[data-pk-leave-id="${leave_id}"]`).first();
    if (eventEl.length) {
        eventEl[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));
    }
})


function enableLeaveRequest(){
    $('#employee-records-body').addClass('disabled');

    if (new_leave.type === 'Annual Leave'){
        $('#selectedLeave').text('Annual Leave Available:');
        $('#selectedLeaveAvailable').text(`${new_leave.leave_available} Hours`);
    } else if (new_leave.type === 'Sick Leave') {
        $('#selectedLeave').text('Sick Leave Available:');
        $('#selectedLeaveAvailable').text(`${new_leave.sick_leave_available} Hours`);
    } else {
        // TOIL has no balance to show
        $('#selectedLeave').text('Time off in Lieu');
        $('#selectedLeaveAvailable').text('');
    }

    $('.calendar-container').removeClass('idle-calendar hover-calendar').addClass('active-calendar requesting-leave');
    selecting_date = true;
    flashMessage('Please select the leave request start date.', 'info', 0);
}

function closeModal(e){
    const modal = $(e.target).closest('.modal')
    selected_leave_id = null;
    $(modal).modal('toggle');
}
$('#viewRequest .btn-close').on('click', closeModal);
$('#viewRequest .close-modal').on('click', closeModal);
$('#deleteRequestModal .close-modal').on('click', closeModal);

$('#approveRequestConfirm').on('click', function(){
    const comment = $('#adminComments').val();
    approveLeave(selected_leave_id, comment);
});
$('#denyRequestConfirm').on('click', function(){
    const comment = $('#adminComments').val();
    rejectLeave(selected_leave_id, comment);
});

$(document).on('click', '#employee-records-body tr', function(){
    if (!employee_leave[selected_employee_id]){
        if ($('.calendar-container').hasClass('idle-calendar') && selected_employee_id){
            $('.idle-calendar').removeClass('idle-calendar').addClass('active-calendar');
        } else {
            $('.active-calendar').removeClass('active-calendar').addClass('idle-calendar');
        }
    }

    if (selected_employee_id == current_user.employee_id){
        $('#addRequestBtn').removeClass('disabled');
    } else {
        $('#addRequestBtn').addClass('disabled');
    }
});
$('#addRequestBtn').on('click', function(){
    if ($('#toggleTableView')[0].checked){
        $('#toggleTableView').trigger('click');
    }
    $('#selectLeaveTypeModal').modal('show');
});
$('#annualLeaveType').on('click', async function(){
    new_leave.type = 'Annual Leave';
    await new_leave.getLeaveAvailable();
    $('#addRequestBtn').hide();
    $('#cancelAddRequestBtn').show();
    $('#toggleTableView').attr('disabled', '');
    enableLeaveRequest();
});
$('#sickLeaveType').on('click', async function(){
    new_leave.type = 'Sick Leave';
    await new_leave.getLeaveAvailable();
    $('#addRequestBtn').hide();
    $('#cancelAddRequestBtn').show();
    $('#toggleTableView').attr('disabled', '');
    enableLeaveRequest();
});
$('#toilLeaveType').on('click', async function(){
    new_leave.type = 'Time off in Lieu';
    await new_leave.getLeaveAvailable();
    $('#addRequestBtn').hide();
    $('#cancelAddRequestBtn').show();
    $('#toggleTableView').attr('disabled', '');
    enableLeaveRequest();
});
$('#cancelAddRequestBtn').on('click', function(){
    $(this).hide();
    $('#toggleTableView').removeAttr('disabled');
    $('#selectedLeave').text('');
    $('#selectedLeaveAvailable').text('');
    $('#addRequestBtn').show().addClass('disabled');
    $('.alert').alert('close');
    new_leave.stop();
});
$('#modifyLeaveRequest').on('click', function(){
    $('.modal.show').modal('hide');
    $('.selected-date').removeClass('selected-date');
    first_date = '';
    second_date = '';

    $('#selectLeaveTypeModal').modal('show');
});
$('#confirmLeaveRequest').on('click', function(){new_leave.confirmRequest()});
$('#deleteRequestConfirm').on('click', function(){
    new_leave.deleteRequest(selected_leave_id);
});
