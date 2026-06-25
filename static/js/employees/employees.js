let calendar;
let selected_employee_id = null;
let editing = false
let employee_leave = {}; // Cache for employee leave records
let employee_leave_calendar_cache = {}; // Cache for calendar events

async function softRefresh(){
    await loadEmployees();
}

/**
 * @param {Array} specific - Array of employee ID's to load specifically. (Optional)
 */
async function loadEmployees(specific=null, leave=true) {
    try {
        const resp = await $.ajax({
            url: '/employees/get_employees',
            type: 'GET'
        });

        if (resp.length > 0){
            populateEmployeesRecords(resp, specific);
            if (leave) {
                loadEmployeeLeave();
                let formatted = specific
                if (!specific){
                    formatted = [...new Set(resp.map(record => record.pk_employee_id))];
                }
                cachePendingDetails(formatted);
            };
        }
    } catch (error){
        console.error("Error loading employees: " + error);
        alert("Failed to load employees data. Please try again later.");
    }
}

function loadEmployeeLeave() {
    $.ajax({
        url: '/leave/get_leave',
        type: 'GET',
        beforeSend: function(){
            showLoader();
        },
        success: function(resp){
            if (resp.message == 'success') {
                const leave = resp.leave;
                employee_leave = {};
                employee_leave_calendar_cache = {};

                leave.forEach(leave_rercord => {
                    if (!employee_leave[leave_rercord.fk_employee_id]) {
                        employee_leave[leave_rercord.fk_employee_id] = [];
                    }
                    employee_leave[leave_rercord.fk_employee_id].push({
                        leave_type: leave_rercord.leave_type,
                        start_date: leave_rercord.start_date,
                        end_date: leave_rercord.end_date,
                        status: leave_rercord.status,
                        leave_id: leave_rercord.pk_leave_id
                    });
                });

                Object.keys(employee_leave).forEach(employee_id => {
                    if (!employee_leave_calendar_cache[employee_id]) {
                        employee_leave_calendar_cache[employee_id] = employee_leave[employee_id].map(record => {
                            const start_date = new Date(record.start_date);
                            const end_date = new Date(record.end_date);
                            end_date.setDate(end_date.getDate() + 1);
                            return {
                                title: record.leave_type,
                                start: start_date,
                                end: end_date,
                                allDay: true,
                                className: [record.status, 'calendar-event'],
                                textColor: 'black',
                                extendedProps: {
                                    status: record.status,
                                    pk_leave_id: record.leave_id
                                }
                            };
                        });
                    }
                })
            } else if (resp.message == 'error') {
                flashMessage(resp['error'], 'danger', 0);
            } else {
                flashMessage('Error loading employee leave. Please try again', 'danger', 0);
            }
        },
        complete: function() {
            populateLeaveTable();
            hideLoader();
        },
        error: function(xhr, status, error) {
            console.log("Error loading employees: " + error);
            alert("Failed to load employees leave. Please try again later.");
        }
    });

    $.ajax({
        url: '/leave/get_leave/remaining',
        type: 'GET',
        success: function(resp){
            populateEmployeesRecordsStats(resp, 'leave');
        },
        error: function(xhr, status, error) {
            console.log("Error loading employees: " + error);
            alert("Failed to load employees leave remaining. Please try again later.");
        }
    })
}

function populateEmployeesRecords(data, specific) {
    const table_body = $('#employee-records-body');
    const stats_body = $('#employee-stats-body');

    table_body.empty();
    stats_body.empty();

    if (Array.isArray(specific) && specific.length > 0) {
        const data_map = new Map(data.map(record => [record.pk_employee_id, record]));
        data = specific
                .map(id => data_map.get(id))
                .filter(record => record !== undefined);
    }
    table_html = '';
    stats_html = '';
    data.forEach(function(employee_record) {
        table_html += `
        <tr data-employee-id="${employee_record.pk_employee_id}">
            <td class="employee-id">${employee_record.pk_employee_id}</td>
            <td class="employee-name">${employee_record.first_name} ${employee_record.last_name}</td>
        </tr>
        `

        stats_html += `
        <div class="row h-100" style="display: none;" data-employee-id="${employee_record.pk_employee_id}">
            <div class="col-4 left">
                <div class="first-name">
                    <span class="label">First Name:</span>
                    <span class="employee-first-name editable">${employee_record.first_name}</span>
                </div>
                <div class="last-name">
                    <span class="label">Last Name:</span>
                    <span class="employee-last-name editable">${employee_record.last_name}</span>
                </div>
                <hr>
                <div class="position">
                    <span class="label">Position:</span>
                    <span class="employee-position">${formatRole(employee_record.role)}</span>
                </div>
                <div class="id">
                    <span class="label">Employee ID:</span>
                    <span class="employee-id">${employee_record.pk_employee_id}</span>
                </div>
            </div>
            <div class="col-4 center">
                <div class="leave-balance">
                    <span class="label">Default Leave Balance:</span>
                    <span class="employee-default-leave-bal editable">${employee_record.default_leave_balance} hours</span>
                </div>
                <div class="leave-remaining placeholder-glow">
                    <span class="label">Leave Remaining:</span>
                    <span class="employee-leave-remaining placeholder"></span>
                </div>
                <div class="sick-leave">
                    <span class="label">Default Sick Leave:</span>
                    <span class="employee-default-sick-bal editable">${employee_record.default_sick_leave_balance} hours</span>
                </div>
                <div class="sick-leave-remaining placeholder-glow">
                    <span class="label">Sick Leave Remaining:</span>
                    <span class="employee-sick-remaining placeholder"></span>
                </div>
            </div>
            <div class="col-4 right">
                <div class="contracted-daily">
                    <span class="label">Contracted Daily Hours:</span>
                    <span class="employee-contracted-daily editable">${employee_record.contracted_daily_hours} hours</span>
                </div>
                <div class="contracted-weekly">
                    <span class="label">Contracted Weekly Hours:</span>
                    <span class="employee-contracted-weekly editable">${employee_record.contracted_weekly_hours} hours</span>
                </div>
            </div>
        </div>
        `
    });
    table_body.html(table_html);
    stats_body.html(stats_html);
}

function populateLeaveTable() {
    const leave_table_body = $('#tableView-tables');

    let html = '';
    Object.keys(employee_leave).forEach(employee_id => {
        const leave_records = employee_leave[employee_id];
        html += `
            <table class="table table-striped table-bordered" data-employee-id="${employee_id}" style="display: none;">
                <thead>
                    <tr>
                        <th>Leave Type</th>
                        <th>Start Date</th>
                        <th>End Date</th>
                        <th>Status</th>
                    </tr>
                </thead>
        `
        leave_records.forEach(record => {
            html += `
                <tbody data-leave-id="${record.leave_id}">
                    <tr>
                        <td>${record.leave_type}</td>
                        <td>${new Date(record.start_date).toLocaleDateString()}</td>
                        <td>${new Date(record.end_date).toLocaleDateString()}</td>
                        <td class="${record.status}">${record.status}</td>
                    </tr>
                </tbody>
            `
        });
        html += '</table>';
    });

    leave_table_body.html(html);
}


function populateEmployeesRecordsStats(data, field) {
    const stats_body = $('#employee-stats-body');

    stats_body.children().each(function(index, record) {
        const employee_id = $(record).data('employee-id');
        const target_data = data.find(target => target.fk_employee_id === employee_id);
        if (field === 'leave'){
            if (target_data) {
                try {
                    $(record).find('.employee-leave-remaining').text(`${target_data.leave_remaining} hours`).removeClass('placeholder');
                    $(record).find('.employee-sick-remaining').text(`${target_data.sick_leave_remaining} hours`).removeClass('placeholder');
                } catch (e) {
                    if (e instanceof TypeError){
                        console.log(`Employee ID ${employee_id} does not have a valid sick leave.`);
                    } else {
                        console.error(e);
                    }
                }
            }
        }
    });
}

function handleStatsPeek(element) {
    const employeeId = $(element).data('employee-id');
    const statsDiv = $(`#employee-stats-body div[data-employee-id="${employeeId}"]`);

    $('#employee-stats-body div.row').hide();
    statsDiv.removeClass('active-stats')
            .addClass('hover-stats')
            .show();
}

function handleLeavePeek(element, calendar) {
    calendar.removeAllEvents();
    const employeeId = $(element).data('employee-id');
    const calendarContainerDiv = $('.card-body.calendar-container');
    const events = employee_leave_calendar_cache[employeeId] || [];

    if (events.length === 0) {
        calendarContainerDiv.removeClass('hover-calendar active-calendar')
                            .addClass('idle-calendar');
        $('#tableView-tables table').hide();
        $('#tableView-empty').show();
        return;
    }

    calendar.addEventSource(events);
    calendarContainerDiv.removeClass('idle-calendar active-calendar')
                        .addClass('hover-calendar');

    $('#tableView-tables table').hide();
    $('#tableView-empty').hide();
    $(`#tableView-tables table[data-employee-id="${employeeId}"]`).show();
}

function focusEmployeeRecord(element, calendar) {
    handleStatsPeek(element);
    $('#employee-stats-body div.hover-stats').removeClass('hover-stats')
                                             .addClass('active-stats');

    handleLeavePeek(element, calendar);
    if ($('.card-body.calendar-container').hasClass('hover-calendar')) {
        $('.card-body.calendar-container').removeClass('hover-calendar')
                                          .addClass('active-calendar');
    }
}

function deSelectRecord(record) {
    $(record).removeClass('selected-record');
    selected_employee_id = null;
    editing = false;
    $('#stats-editing-controls').fadeOut(300);
    $('#tableView-empty').hide();
    handleStatsPeek(record);
    handleLeavePeek(record, calendar);
}

$('#employee-records-body').on('mouseover', 'tr', function() {
    if (selected_employee_id) return;
    handleStatsPeek(this);
    handleLeavePeek(this, calendar);
});

$('#employee-records-body').on('mouseleave', 'tr', function() {
    if (selected_employee_id) return;
    $('#employee-stats-body div.hover-stats').removeClass('hover-stats').hide();
    $('.card-body.calendar-container').removeClass('hover-calendar')
                                      .addClass('idle-calendar');
    $('#tableView-tables table').hide();
    $('#tableView-empty').hide();
    calendar.removeAllEvents();
});

$('#employee-records-body').on('click', 'tr', function() {
    if (editing) return;

    const employeeId = $(this).data('employee-id');

    if (selected_employee_id === employeeId) {
        deSelectRecord(this)
        return;
    }

    selected_employee_id = employeeId;
    $(this).siblings().removeClass('selected-record');
    $(this).addClass('selected-record');

    focusEmployeeRecord(this, calendar);
});
