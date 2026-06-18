class Teams {
    constructor() {
        this.teams = [];
        this.init();
    }

    async init() {
        const teams = await this.loadData()
        if (teams.length == 0) {
            return;
        }
        for (let team of teams) {
            const teamObj = new Team(
                team['pk_team_id'],
                team['name'],
                team['fk_manager_id'],
                `${team['manager_first_name']} ${team['manager_last_name']}`,
                team['employee_count'],
            );
            this.teams.push(teamObj);
        }
    }

    async loadData() {
        return $.ajax({
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
    }

    drawEmptyRow() {
        return `
            <tr>
                <td colspan="999" class="no-teams">
                    <i class="fas fa-exclamation-triangle"></i>
                    There are currently no teams to display.
                </td>
            </tr>
        `
    }

    drawNewRow() {
        return `
            <tr>

        `
    }

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
    }
}

class Team {
    constructor(teamId, teamName, managerId, managerName, employeesCount) {
        this.teamId = teamId;
        this.teamName = teamName;
        this.managerId = managerId;
        this.managerName = managerName;
        this.employeesCount = employeesCount;
    }

    drawNewTeamRow(employeesList = []) {
        function disableOptions($targetSelect, $target) {
            const $currentDisabled = $target.prop('disabled');
            const $disabled = $targetSelect.find('[disabled]');
            
            $disabled.prop('disabled', false);
            $target.prop('disabled', true);

            // TODO: Remove and replace with .selectpicker('refresh') when Selectpicker beta3 fixes method as currently has bugs
            // https://github.com/snapappointments/bootstrap-select/issues/2738
            $targetSelect
                .selectpicker('destroy')
                .selectpicker( {countSelectedText: (n) => n + ' Employees'} )
        }

        function $buildSelectPicker(options, config, onChange) {
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
                    >
                    <option data-divider="true">
                    ${options}
                </select>
            `).on('change', onChange);
        }

        let employeeOptions = '';
        let enableSearch = true;
        let newRowHtml;

        if (employeesList.length > 0) {
            for (let employee of employeesList) {
                employeeOptions += `
                    <option 
                        value="${employee.pk_employee_id}"
                        data-content='
                            <div class="option">
                                <span class="option-employee-id">${employee.pk_employee_id}</span>
                                <span class="option-employee-name">${employee.first_name} ${employee.last_name}</span>
                            </div>
                            '
                    >
                    ${employee.first_name} ${employee.last_name}
                    </option>
                `;
            }
        } else {
            // In the case of there being no employees to assign relevant roles to a team within, limit the selectpicker functionality.
            employeeOptions = `
                <option class="option" disabled>There are no free employees to assign this position to.</option>
            `
            enableSearch = false;
        }

        // Build the dynamic new team row
        newRowHtml = $(`
            <tr>
                <td class="placeholder-glow"><span class="placeholder col-4"></span></td>
                <td><input class="form-control form-control-sm editable" placeholder="Team Name..."></td>
                <td class="placeholder-glow"><span class="placeholder col-4"></span></td>
                <td class="manager-name"></td>
                <td class="team-employees"></td>
                <td style="min-width: 170px;">
                    <div class="editing-action-btns">
                        <button type="button" class="btn btn-outline-primary btn-sm">Save</button>
                        <button type="button" class="btn btn-outline-secondary btn-sm">Cancel</button>
                    </div>
                </td>
            </tr>`
        )

        // Attach custom selectpickers with event listeners to the relevant fields
        newRowHtml.find('.manager-name').append(
            $buildSelectPicker(
                employeeOptions,
                {
                    elementName: 'manager_name',
                    liveSearch: true,
                    placeholder: 'Search Employees...',
                    actionsBox: false,
                    multiple: false,
                },
                (e) => {
                    const value = e.target.value;
                    const $employees = $('#team_employees');
                    const $target = $employees.find(`[value="${value}"]`);
                    disableOptions($employees, $target);
                }
            )
        )
        newRowHtml.find('.team-employees').append(
            $buildSelectPicker(
                employeeOptions,
                {
                    elementName: 'team_employees',
                    liveSearch: true,
                    placeholder: 'Search Employees...',
                    actionsBox: true,
                    multiple: true,
                },
                (e) => {
                    const values = $(e.target.selectedOptions);
                    const $manager = $('#manager_name');
                    let targetElements = [];
                    values.each((_, el) => {
                        targetElements.push($manager.find(`[value="${el.value}"]`)[0])
                    });
                    const $target = $(targetElements);
                    disableOptions($manager, $target);
                }
            )
        )

        return newRowHtml;
    }

    drawRow() {
        const html = `
            <tr data-team-id="${this.teamId}">
                <td>${this.teamId}</td>
                <td>${this.teamName}</td>
                <td>${this.managerId}</td>
                <td>${this.managerName}</td>
                <td>${this.employeesCount}</td>
                <td>Test</td>
            </tr>
        `
    }
}