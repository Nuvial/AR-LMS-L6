const teams = {
    teams: [],
    newTeam: null,
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
        teams.actions.cancelAction();
        this.init(this._state.container);
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

        drawNewTeamRow(employeesList = [], managersList = []) {
            function disableOptions($targetSelect, $target) {
                if ($targetSelect.length == 0 || $target.length == 0) return;

                console.log($target[0])
                console.log($targetSelect[0])
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
                        ${config.required ? 'required' : ''}
                        >
                        <option data-divider="true">
                        ${options}
                    </select>
                `).on('change', onChange);
            }

            function buildOptions(list) {
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
            }

            const employeeOptionsBuild = buildOptions(employeesList);
            const managerOptionsBuild = buildOptions(managersList);

            const employeeOptions = employeeOptionsBuild[0];
            const managerOptions = managerOptionsBuild[0];
            const enableEmployeeSearch = employeeOptionsBuild[1];
            const enableManagerSearch = managerOptionsBuild[1];
            let newRowHtml;

            teams._state.editing = true;

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
                $buildSelectPicker(
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
                        disableOptions($employees, $target);
                    }
                ),
                '<div class="invalid-feedback"></div>'
            );
            newRowHtml.find('.team-employees').append(
                $buildSelectPicker(
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
                        disableOptions($manager, $target);
                    }
                ),
                '<div class="invalid-feedback"></div>'
            );
            newRowHtml.find('#cancelNew').on('click', () => teams.actions.cancelAction());
            newRowHtml.find('#saveNew').on('click', () => teams.data.createNewTeam());

            const $noTeam = $('.no-teams');
            if ($noTeam.length > 0) {
                teams._state.container.empty().append(newRowHtml);
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

        toggleCreateButton(state = teams._state.editing) {
            $('#createTeam').prop('disabled', state);
        }
    },

    actions: {
        async newTeam() {
            if (teams._state.editing) return;
            teams._state.editing = true;
            teams.presentation.toggleCreateButton();

            const freeEmployees = await teams.data.getFreeEmployees();
            const freeManagers = await teams.data.getFreeManagers();

            teams.newTeam = new Team();
            teams.presentation.drawNewTeamRow(freeEmployees, freeManagers);
        },

        cancelAction() {
            if (!teams._state.editing) return;
            if (teams.newTeam !== null) teams.newTeam = null;
            teams._state.editing = false;
            teams.presentation.toggleCreateButton();

            teams._state.container.find('.selectpicker').selectpicker('destroy');
            teams.presentation.render();
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

                // Name: alphanumeric, length 1-32
                if (field === 'team_name') {
                    if (!isAlphaNumeric(value)) {
                        invalidate(feedback, 'Name must be alphanumeric', input);
                    } else if (!isValidLength(value, 0, 33)) {
                        invalidate(feedback, 'Name must be 1-32 characters', input);
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

            var employees = await $.ajax({
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

            for (let team of Object.values(teams)) {
                team.employees = employees[team.pk_team_id];
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

        async createNewTeam() {
            if (!this.validate()) return;
            return $.ajax({
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
        }
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

    set teamName (name) {
        this.#teamName = name;
    }
    set managerId (id) {
        this.#managerId = id;
    }
    set employees (employees) {
        this.#employees = employees;
    }

    get teamName () {
        return this.#teamName
    }

    get managerId () {
        return this.#managerId
    }

    get employees () {
        return this.#employees
    }

    appendRow(target) {
        target.append(`
            <tr data-team-id="${this.#teamId}">
                <td>${this.#teamId}</td>
                <td>${this.#teamName}</td>
                <td>${this.#managerId}</td>
                <td>${this.#managerName}</td>
                <td>${this.#employeesCount}</td>
                <td>Test</td>
            </tr>
        `)
    }
}