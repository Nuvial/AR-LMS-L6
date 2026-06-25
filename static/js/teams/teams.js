const teams = {
    teams: [],
    newTeam: null,
    initialTeam: null,
    _state: {
        container: '',
        editing: false
    },

    async init(container = $()) {
        this._state.container = container;
        const teams = await this.data.loadData();

        if (teams.length > 0) {
            for (let team of teams) {
                const teamObj = new Team(
                    team['pk_team_id'],
                    team['name'],
                    team['fk_manager_id'],
                    `${team['manager_first_name']} ${team['manager_last_name']}`,
                    team['employee_count'],
                    team['employees']
                );
            this.teams.push(teamObj);
            }
        }

        this.presentation.render();
    },

    softRefresh() {
        this.teams = [];
        teams.actions.cancelAction(true);
        this.init(this._state.container);
    },

    toggleEditingState(state, $unaffectedRow = '') {
        this._state.editing = state;
        $('#createTeam').prop('disabled', state);
        this._state.container.find('.team-actions').not($unaffectedRow).toggleClass('disabled', state);
    },

    presentation: {
        render() {
            // Reset state
            teams._state.container.empty();

            if (teams.teams.length == 0) {
                this.drawEmptyRow();
                return;
            }

            // TODO
            for (let team of teams.teams) {
                team.appendRow(teams._state.container);
            }
        },

        drawEmptyRow() {
            teams._state.container.append(`
                <tr>
                    <td colspan="999" class="no-teams">
                        <i class="fas fa-exclamation-triangle"></i>
                        There are currently no teams to display.
                    </td>
                </tr>
            `);
        },

        refreshSelect($select){
            // TODO: Remove and replace with .selectpicker('refresh') when Selectpicker beta3 fixes method as currently has bugs
            // https://github.com/snapappointments/bootstrap-select/issues/2738
            $select
                .selectpicker('destroy')
                .selectpicker( {countSelectedText: (n) => n + ' Employees'} )
                .addClass('selectpicker')
        },

        disableOptions($targetSelect, $target) {
            if ($targetSelect.length == 0 || $target.length == 0) return;

            const $currentDisabled = $target.prop('disabled');
            const $disabled = $targetSelect.find('[disabled]');

            $disabled.prop('disabled', false);
            $target.prop('disabled', true);

            this.refreshSelect($targetSelect);            
        },

        $buildSelectPicker(options, config, onChange) {
            return $(`
                <select id="${config.elementName}" name="${config.elementName}" class="selectpicker" 
                    data-live-search="${config.liveSearch}"
                    data-live-search-normalize="true"
                    data-live-search-style="contains"
                    data-live-search-placeholder="${config.placeholder}"
                    data-actions-box="${config.actionsBox}"
                    data-style="btn-sm btn-outline-custom"
                    data-show-tick="false"
                    data-selected-text-format="count"
                    data-container="body"
                    ${config.multiple ? 'multiple' : ''}
                    ${config.required ? 'required' : ''}
                    >
                    <option data-divider="true">
                    ${options}
                </select>
            `).on('change', onChange);
        },

        buildOptions(list) {
            list = list.sort((a, b) => a.pk_employee_id - b.pk_employee_id);
            var optionsList = '';
            var searchEnabled = true;

            if (list.length > 0) {
                for (let i of list) {
                    optionsList += `
                        <option 
                            value="${i.pk_employee_id}"
                            data-content='
                                <div class="option">
                                    <span class="option-employee-id">${i.pk_employee_id}</span>
                                    <span class="option-employee-name">${i.first_name} ${i.last_name}</span>
                                </div>
                                '
                        >
                        ${i.first_name} ${i.last_name}
                        </option>
                    `;
                }
            } else {
                optionsList += '<option class="option" disabled>There are no free employees to assign this position to.</option>'
                searchEnabled = false;
            }

            return [optionsList, searchEnabled]
        },

        drawNewTeamRow(employeesList = [], managersList = [], replaceRow = null) {
            const employeeOptionsBuild = this.buildOptions(employeesList);
            const managerOptionsBuild = this.buildOptions(managersList);

            const employeeOptions = employeeOptionsBuild[0];
            const managerOptions = managerOptionsBuild[0];
            const enableEmployeeSearch = employeeOptionsBuild[1];
            const enableManagerSearch = managerOptionsBuild[1];
            let newRowHtml;

            teams.toggleEditingState(true);

            // Build the dynamic new team row
            newRowHtml = $(`
                <tr>
                    <td class="placeholder-glow"><span class="placeholder col-4"></span></td>
                    <td>
                        <input id="team_name" name="team_name" class="form-control form-control-sm editable" placeholder="Team Name...">
                        <div class="invalid-feedback"></div>
                    </td>
                    <td class="placeholder-glow"><span class="placeholder col-4"></span></td>
                    <td class="manager-name"></td>
                    <td class="team-employees"></td>
                    <td style="min-width: 170px;">
                        <div class="editing-action-btns">
                            <button id="saveNew" type="button" class="btn btn-outline-primary btn-sm">Save</button>
                            <button id="cancelNew" type="button" class="btn btn-outline-secondary btn-sm">Cancel</button>
                        </div>
                    </td>
                </tr>`
            )

            // Attach custom selectpickers with event listeners to the relevant fields
            newRowHtml.find('.manager-name').append(
                this.$buildSelectPicker(
                    managerOptions,
                    {
                        elementName: 'manager_name',
                        liveSearch: enableManagerSearch,
                        placeholder: 'Search Employees...',
                        actionsBox: false,
                        multiple: false,
                        required: true,
                    },
                    (e) => {
                        const value = e.target.value;
                        const $employees = $('#team_employees');
                        const $target = $employees.find(`[value="${value}"]`);
                        this.disableOptions($employees, $target);
                    }
                ),
                '<div class="invalid-feedback"></div>'
            );
            newRowHtml.find('.team-employees').append(
                this.$buildSelectPicker(
                    employeeOptions,
                    {
                        elementName: 'team_employees',
                        liveSearch: enableEmployeeSearch,
                        placeholder: 'Search Employees...',
                        actionsBox: enableEmployeeSearch,
                        multiple: true,
                        required: false
                    },
                    (e) => {
                        const values = $(e.target.selectedOptions);
                        const $manager = $('#manager_name');
                        let targetElements = [];
                        values.each((_, el) => {
                            const managerId = $manager.find(`[value="${el.value}"]`)[0];
                            if (managerId) targetElements.push(managerId);
                        });

                        const $target = $(targetElements);
                        this.disableOptions($manager, $target);
                    }
                ),
                '<div class="invalid-feedback"></div>'
            );
            newRowHtml.find('#cancelNew').on('click', () => teams.actions.cancelAction());
            newRowHtml.find('#saveNew').on('click', () => {
                $('#confirmAction #confirmActionBtn').removeClass('edit-team').addClass('create-team');
                teams.data.createNewTeam();
            });

            const $noTeam = $('.no-teams');
            if ($noTeam.length > 0) {
                teams._state.container.empty().append(newRowHtml);
            } else if (replaceRow != null) {
                replaceRow.replaceWith(newRowHtml);
            } else { // Draw html as the first row
                teams._state.container.find('tr').first().before(newRowHtml)
            }

            // Initialise seletpicker element
            $(teams._state.container).find('.selectpicker').selectpicker({
                countSelectedText: (n) => {
                    return n + ' Employees';
                }
            });
        },

        editTeamRow(teamDetails, teamId) {
            const tableRow = teams._state.container.find(`.main-row[data-team-id="${teamId}"]`);
            const employees = teamDetails.freeEmployees;
            const managers = teamDetails.freeManagers;
            const currentDetails = teamDetails.currentTeam;

            this.drawNewTeamRow(employees, managers, tableRow);

            // Dynamically update the row with current team details
            const teamName = currentDetails.teamName;
            if (teamName) {
                $('#team_name').val(teamName);
            }

            const managerName = currentDetails.managerName;
            const managerId = currentDetails.managerId;
            const $managerSelect = $('#manager_name');
            if (managerName && managerId) {
                const optionHtml = `
                    <option selected value="${managerId}" data-content='
                        <div class="option">
                            <span class="option-employee-id">${managerId}</span>
                            <span class="option-employee-name">${managerName}</span>
                        </div>
                    '>${managerName}</option>
                `;

                var inserted = false;
                $managerSelect.find('option').each((_, option) => {
                    if (inserted) return;
                    if ($(option).data('divider')) return;
                    if (parseInt(managerId) > parseInt($(option).val())) return;
                    $(option).before(optionHtml);
                    inserted = true;
                });

                if (!inserted) $managerSelect.append(optionHtml);

                this.refreshSelect($managerSelect);
            }

            const currentEmployees = currentDetails.employees;
            const $employeeSelect = $('#team_employees')
            if (currentEmployees.length > 0) {
                const combinedEmployees = [...employees, ...currentEmployees];
                var employeeOptions = $(this.buildOptions(combinedEmployees)[0]);
                $employeeSelect.empty().append(employeeOptions);
                
                for (let employee of currentEmployees) {
                    $employeeSelect
                        .find(`option[value="${employee.pk_employee_id}"]`)
                        .prop('selected', true);
                        
                }

                this.refreshSelect($employeeSelect);
            }

            // Trigger change to disable relevant options
            $managerSelect.trigger('change');
            $employeeSelect.trigger('change');

            // Change the purpose of the save button to save rather than create
            teams._state.container.find('#saveNew').off('click').on('click', () => {
                $('#confirmAction #confirmActionBtn').removeClass('create-team').addClass('edit-team');
                teams.data.saveTeam();
            });
        }
    },

    actions: {
        async newTeam() {
            if (teams._state.editing) return;
            teams.toggleEditingState(true);

            const freeEmployees = await teams.data.getFreeEmployees();
            const freeManagers = await teams.data.getFreeManagers();

            teams.newTeam = new Team();
            teams.initialTeam = teams.newTeam.clone();
            teams.presentation.drawNewTeamRow(freeEmployees, freeManagers);
        },

        async editTeam(id) {
            if (teams._state.editing) return;
            teams.toggleEditingState(true);
            
            const teamObj = teams.teams.find((t) => t.teamId === id);
            teams.newTeam = teamObj.clone();
            teams.initialTeam = teamObj.clone();
            
            const teamDetails = {
                freeEmployees: await teams.data.getFreeEmployees(),
                freeManagers: await teams.data.getFreeManagers(),
                currentTeam: teamObj
            };

            teams.presentation.editTeamRow(teamDetails, id);
        },

        applyChangesForComparison() {
            teams._state.container.find('input, select').each(function(index, input){
                const value = $(input).val();
                const field = input.name;
                if (field === 'team_name') teams.newTeam.teamName = value;
                if (field === 'manager_name') teams.newTeam.managerId = parseInt(value);
                if (field === 'team_employees') {
                    teams.newTeam.employees = value.map(id => ({ pk_employee_id: parseInt(id) }));
                };
            });
        },

        async cancelAction(confirmed = false) {
            if (!teams._state.editing) return;

            // Check if any changes have been made
            if (!confirmed) {
                this.applyChangesForComparison();

                if (!teams.newTeam.equals(teams.initialTeam)) {
                    $('#revertModal').modal('show');
                    return
                }
            }

            if (teams.newTeam !== null) teams.newTeam = null;
            if (teams.initialTeam !== null) teams.initialTeam = null;

            teams.toggleEditingState(false);

            teams._state.container.find('.selectpicker').selectpicker('destroy');
            teams.presentation.render();
        },

        deleteTeam(team) {
            if (teams._state.editing) return;

            $('#deleteWarning #confirmDeleteBtn').data('team-id', team.teamId);
            $('#deleteWarning .modal-title').empty().html(`Delete Team: <strong>${team.teamName}</strong> ?`);
            $('#deleteWarning .modal-body').empty().html(`
                <h5 class="warning-header">Are you sure you want to delete this team? This action cannot be reversed once confirmed.</h5>
                <br>
                <div class="warning-callout">
                    <i class="fas fa-triangle-exclamation"></i>
                    <strong>Note:</strong>
                    This action will delete the <strong>selected team</strong>. The assigned employees and manager will
                    no longer be assigned to a team and <strong>will require re-assignment</strong> to have visibility over their leave requests.
                </div>
            `)
            $('#deleteWarning').modal('show');
        },
    },

    data: {
        validate() {
            if (!teams._state.editing) return;
            let valid = true;

            function invalidate(feedbackDiv, feedback, input) {
                valid = false;
                addFeedback(feedbackDiv, feedback, input);
            };

            // Custom field validation for each input.
            teams._state.container.find('input, select').each(function(index, input){
                const value = $(input).val();
                const feedback = $(input).siblings().closest('.invalid-feedback');
                const field = input.name;

                // Name: alphanumeric, length 2-50
                if (field === 'team_name') {
                    if (!isValidTeamName(value)) {
                        invalidate(feedback, 'Team name must be 3–50 characters, start and end with a letter or number, and may only contain letters, numbers, spaces, hyphens, and underscores.', input);
                    } else {
                        $(feedback).closest('is-invalid').toggleClass('is-invalid');
                        teams.newTeam.teamName = value;
                    }
                }

                // Manager Name: Required
                if (field === 'manager_name') {
                    if (!this.checkValidity()) {
                        invalidate(
                            $(this).closest('.bootstrap-select').siblings().closest('.invalid-feedback'), 
                            'A manager is required', 
                            $(this).closest('.bootstrap-select')
                        )
                    } else {
                        $(this).closest('.bootstrap-select.is-invalid').toggleClass('is-invalid');
                        teams.newTeam.managerId = value;
                    }
                }

                // Employees
                if (field === 'team_employees') {
                    if (!this.checkValidity()) {
                        invalidate(
                            $(this).closest('.bootstrap-select').siblings().closest('.invalid-feedback'), 
                            'Please enter valid options', 
                            $(this).closest('.bootstrap-select')
                        )
                    } else {
                        $(this).closest('.bootstrap-select.is-invalid').toggleClass('is-invalid');
                        teams.newTeam.employees = value;
                    }
                }

            });

            if (valid){
                $('.is-invalid').removeClass('is-invalid');
            }
            return valid;
        },

        async deleteTeam(id) {
            return $.ajax({
                url: `/teams/delete_team/${id}`,
                type: 'DELETE',
                beforeSend: showLoader,
                success: (resp) => {
                    if (resp.message == 'success') {
                        flashMessage('Team has been deleted successfully', 'success')
                        teams.softRefresh();
                    }

                    if (resp.message == 'error') {
                        flashMessage(resp.error, 'danger', 0)
                        console.error(resp.error);
                    }
                },
                complete: hideLoader,
                error: function(xhr, status, error) {
                    console.log("Error deleting team: " + error);
                    alert("Failed to delete team. Please try again later.");
                }
            });
        },

        async loadData() {
            var teams = await $.ajax({
                url: '/teams/get_teams',
                type: 'GET',
                beforeSend: showLoader,
                success: (resp) => {return resp},
                complete: hideLoader,
                error: function(xhr, status, error) {
                    console.log("Error loading teams: " + error);
                    alert("Failed to load teams. Please try again later.");
                }
            });

            if (!teams.length > 0) return teams;
            const teamIds = teams.map((team) => {return team.pk_team_id});

            var employees = await this.getEmployees(teamIds)

            for (let team of Object.values(teams)) {
                team.employees = employees[team.pk_team_id]['employees'];
            }
            return teams;
        },

        async getFreeEmployees() {
            return $.ajax({
                url: '/teams/get_employees/',
                type: 'GET',
                beforeSend: showLoader,
                success: (resp) => {return resp},
                complete: hideLoader,
                error: function(xhr, status, error) {
                    console.log("Error loading employees: " + error);
                    alert("Failed to load employees. Please try again later.");
                }
            });
        },

        async getEmployees(teamIds) {
            return $.ajax({
                url: '/teams/get_employees/',
                type: 'POST',
                data: JSON.stringify({'teamIds': teamIds}),
                contentType: 'application/json',
                processData: false,
                beforeSend: showLoader,
                success: (resp) => {return resp;},
                complete: hideLoader,
                error: function(xhr, status, error) {
                    console.log("Error loading teams: " + error);
                    alert("Failed to load teams. Please try again later.");
                }
            });
        },

        async getFreeManagers() {
            return $.ajax({
                url: '/teams/get_potential_managers/',
                type: 'GET',
                beforeSend: showLoader,
                success: (resp) => {return resp},
                complete: hideLoader,
                error: function(xhr, status, error) {
                    console.log("Error loading employees: " + error);
                    alert("Failed to load employees. Please try again later.");
                }
            });
        },

        async createNewTeam(confirmed=false) {
            if (!this.validate()) return;
            if (!confirmed) {
                const confirmModal = $('#confirmAction');
                confirmModal.find('.custom-action').empty().text('New Team');
                $('#confirmAction').modal('show');
                return;
            };

            $.ajax({
                url: '/teams/add_team',
                type: 'POST',
                data: JSON.stringify({
                    'teamName': teams.newTeam.teamName,
                    'managerId': teams.newTeam.managerId,
                    'employees': teams.newTeam.employees
                }),
                contentType: 'application/json',
                processData: false,
                beforeSend: showLoader,
                success: (resp) => {
                    if (resp.message == 'success') {
                        flashMessage('New team has been created successfully', 'success')
                        teams.softRefresh();
                    }

                    if (resp.message == 'error') {
                        flashMessage(resp.error, 'danger', 0)
                        console.error(resp.error);
                    }
                },
                complete: hideLoader,
                error: function(xhr, status, error) {
                    console.log("Error creating new team: " + error);
                    alert("Failed to create new team. Please try again later.");
                }
            });
        },

        async saveTeam(confirmed=false) {
            if (!this.validate()) return;

            teams.actions.applyChangesForComparison();
            if (teams.newTeam.equals(teams.initialTeam)) {
                teams.actions.cancelAction();
                return;
            }

            if (!confirmed) {
                const confirmModal = $('#confirmAction');
                confirmModal.find('.custom-action').empty().text('Changes to Team');
                $('#confirmAction').modal('show');
                return;
            };

            $.ajax({
                url: `/teams/update_team/${teams.newTeam.teamId}`,
                type: 'POST',
                data: JSON.stringify({
                    'teamName': teams.newTeam.teamName,
                    'managerId': teams.newTeam.managerId,
                    'employees': teams.newTeam.employees
                }),
                contentType: 'application/json',
                processData: false,
                beforeSend: showLoader,
                success: (resp) => {
                    if (resp.message == 'success') {
                        flashMessage('Team has been updated successfully', 'success')
                        teams.softRefresh();
                    }

                    if (resp.message == 'error') {
                        flashMessage(resp.error, 'danger', 0)
                        console.error(resp.error);
                    }
                },
                complete: hideLoader,
                error: function(xhr, status, error) {
                    console.log("Error updating team: " + error);
                    alert("Failed to update team. Please try again later.");
                }
            });
        },
    }
}

class Team {
    #teamId
    #teamName;
    #managerId;
    #managerName;
    #employeesCount;
    #employees;

    constructor(teamId, teamName, managerId, managerName, employeesCount, employees) {
        this.#teamId = teamId;
        this.#teamName = teamName;
        this.#managerId = managerId;
        this.#managerName = managerName;
        this.#employeesCount = employeesCount;
        this.#employees = employees;
    }

    clone() {
        var clonedEmployees;
        if (this.#employees) {
            clonedEmployees = this.#employees.map(emp => ({ ...emp }));
        }

        return new Team(
            this.#teamId,
            this.#teamName,
            this.#managerId,
            this.#managerName,
            this.#employeesCount,
            clonedEmployees
        )
    }

    equals(other) {
        if (!(other instanceof Team)) return false;
        return (
            this.#teamId === other.#teamId &&
            this.#teamName === other.#teamName &&
            this.#managerId === other.#managerId &&
            this.#managerName === other.#managerName &&
            this.#employeesCount === other.#employeesCount &&
            this.#employeesArrayEquals(other.#employees)
        );
    }

    #employeesArrayEquals(otherEmployees) {
        if (!this.#employees && !otherEmployees) return true; // If both are undefined
        if (this.#employees.length === 0 && otherEmployees.length === 0) return true; 
        if ((this.#employees && !otherEmployees) || (!this.employees && otherEmployees)) return false; // If one or the other is undefined
        if (this.#employees.length !== otherEmployees.length) return false;

        return this.#employees.every((emp, i) =>
            parseInt(emp.pk_employee_id) === parseInt(otherEmployees[i].pk_employee_id)
        )
    }  

    set teamName (name) {
        this.#teamName = name;
    }
    set managerId (id) {
        this.#managerId = id;
    }
    set employees (employees) {
        this.#employees = employees;
    }

    get teamId () {
        return this.#teamId;
    }

    get teamName () {
        return this.#teamName;
    }

    get managerId () {
        return this.#managerId;
    }

    get managerName () {
        return this.#managerName;
    }

    get employees () {
        return this.#employees;
    }

    appendRow(target) {
        const createEmployeesHtml = () => {
            var html = '';
            for (let employee of this.#employees) {
                html += `
                    <tr>
                        <td class="employee-id">${employee.pk_employee_id}</td>
                        <td class="employee-first-name">${employee.first_name}</td>
                        <td class="employee-last-name">${employee.last_name}</td>
                        <td class="employee-position">${formatRole(employee.role)}</td>
                    </tr>
                `;
            }
            return html;
        }

        const toggleEmployees = (teamId) => {
            const employeeRow = $(`[data-team-id="${teamId}"].employee-row`);
            const employeeCountRow = $(`[data-team-id=${teamId}].main-row .employee-count`);
            
            employeeRow.toggleClass('shown', 'search-hidden');
            employeeCountRow.toggleClass('expanded');
        }

        const $rowHtml = $(`
            <tr class="main-row" data-team-id="${this.#teamId}">
                <td class="team-id">${this.#teamId}</td>
                <td class="team-name">${this.#teamName}</td>
                <td class="manager-id">${this.#managerId}</td>
                <td class="manager-name">${this.#managerName}</td>
                <td class="employee-count">
                    <div>
                        <span>${this.#employeesCount}</span> 
                        <i class="fas fa-chevron-down fa-sm"></i>
                    </div>
                </td>
                <td class="team-actions">
                    <div class="actions-wrapper">
                        <i class="fas fa-square-pen fa-xl edit-team" title="Edit Team."></i>
                        <i class="fas fa-trash fa-xl delete-team" title="Delete Team."></i>
                    </div>
                </td>
            </tr>
            <tr class="employee-row" data-team-id="${this.#teamId}">
                <td colspan="999">
                    <table class="employee-sub-table table table-hover">
                        <thead>
                            <tr class="sub-table-header">
                                <th>Employee ID</th>
                                <th>First Name</th>
                                <th>Last Name</th>
                                <th>Position</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${createEmployeesHtml()}
                        </tbody>
                    </table>
                </td>
            </tr>
        `);
        
        $rowHtml.find('.employee-count div').on('click', () => toggleEmployees(this.#teamId));
        $rowHtml.find('.edit-team').on('click', (e) => {
            if ($(e.target).closest('tr').find('.employee-count').hasClass('expanded')) {
                toggleEmployees(this.#teamId);
            }
            teams.actions.editTeam(this.#teamId)
        });
        $rowHtml.find('.delete-team').on('click', () => teams.actions.deleteTeam(this));

        target.append($rowHtml);
    }
}