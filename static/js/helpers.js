/**
 * Show spinner loader with whole screen backdrop.
 */
function showLoader(){
    $('#spinnerLoader').addClass('active');
}
/**
 * Hide spinner loader with whole screen backdrop.
 */
function hideLoader(){
    $('#spinnerLoader').removeClass('active');
}

/**
 * Dynamically displays a Bootstrap alert message at the top right of the page.
 * @param {string} message - The message to display.
 * @param {string} [type='success'] - Bootstrap alert type: 'success', 'danger', 'warning', 'info'.
 * @param {number} [timeout=4500] - How long to show the message (ms).
 */
function flashMessage(message, type='success', timeout=3000) {
    const alert = $(`
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    $('#flash-container').append(alert);

    if (timeout !== 0){
        setTimeout(() => {
            alert.alert('close');
        }, timeout);
    }
}


let first_date = '';
let second_date = '';
let selecting_date = false;
/**
 * Initialises a FullCalendar instance. Events have to be dynamically added (Not accepted in the function). 
 * 
 * @param {string} id ID of the container div for the FullCalendar.
 * @param {boolean} edit Whether or not to enable editing of events.
 * @returns {Object} The FullCalendar instance object.
 */
function initCalendar(id, height='100%', edit=false) {
    const calendar_div = $(id);
    const calendar = new FullCalendar.Calendar(calendar_div[0], {
        initialView: 'dayGridMonth',
        themeSystem: 'bootstrap5',
        height: height,
        firstDay: 1,
        aspectRatio: 1.25,
        dayCellClassNames: 'calendar-day',
        buttonText: {
            today: 'Today'
        },
        headerToolbar: {
            left: 'title',
            center: '',
            right: 'prev today next'
        },
        events: [],
        eventDidMount: function(info) {
            info.el.title = `${info.event.extendedProps.status}`;
            if (info.event.extendedProps.pk_leave_id) {
                $(info.el).attr('data-pk-leave-id', info.event.extendedProps.pk_leave_id);
            }
        },
        eventClick: function(info){
            if (edit) {
                handleEditClick(info.event, active_page);
            }
        },
        dateClick: function(info){
            if (selecting_date){
                if (!first_date) {
                    first_date = String(info.date.toDateString());
                    $(info.dayEl).addClass('selected-date');
                    $('.alert').alert('close');
                    flashMessage('Please select the leave request end date', 'info', 0);
                    second_date = null;
                } else {
                    second_date = String(info.date.toDateString());
                    $(info.dayEl).addClass('selected-date');
                    $('.alert').alert('close');
                    new_leave.handleDateClick();
                }
            }
        },
        datesSet: function(){
            $('.calendar-day').each(function() {
                const cell = this;
                const cellDate = cell.getAttribute('data-date');
                if (!cellDate) return;
                $(cell).removeClass('selected-date');
                if (first_date && (new Date(cellDate).toDateString() == first_date)) {
                    $(cell).addClass('selected-date');
                }
                if (second_date && (new Date(cellDate).toDateString() == second_date)) {
                    $(cell).addClass('selected-date');
                }
            });
        }
    });
    calendar.render();
    return calendar;
}

/**
 * Initialises a form control to be a search bar for specified attributes in a search container.
 * 
 * @param {string} form Selector for the search input element.
 * @param {string} search_container  Selector for the body containing the records to search.
 * @param {Object[]} attributes Array of objects specifying the selectors for the attributes to search within.
 * @param {string} attributes[].selector Selector for the attribute to include in the search. 
 */
function initSearch(form, search_container, attributes){
    $(form).on('input', function(){
        const search = $(this).val().toLowerCase().split(' ');
        const records = $(search_container);
        records.each(function(index, record){
            let record_text = '';
            attributes.forEach(attr => {
                const value = $(record).find(attr.selector).text().toLowerCase();
                record_text += ` ${value}`;
            });
            
            const matches = search.every(term => record_text.includes(term));
            $(record).toggleClass('search-hidden', !matches);
        });
    });
}

/**
 * Compares two objects deeply to check if they are equal.
 * 
 * @param {Object} obj1 
 * @param {Object} obj2 
 * @returns {Boolean}
 */
function deepEqual(obj1, obj2) {
    if (obj1 === obj2) return true;
    if (typeof obj1 !== 'object' || obj1 === null || typeof obj2 !== 'object' || obj2 === null) {
        return false;
    }

    const keys1 = Object.keys(obj1);
    const keys2 = Object.keys(obj2);

    if (keys1.length !== keys2.length) {
        return false;
    }
    for (let key of keys1) {
        if (!keys2.includes(key) || !deepEqual(obj1[key], obj2[key])) {
            return false;
        }
    }

    return true;
}

/**
 * Adds dynamic feedback to an `<input>` element during form validation.
 * 
 * @param {HTMLElement} element - The feedback element to show the feedback text on. This is typically an empty div with the class `invalid-feedback`.
 * @param {String} feedback -  The feedback text to display.
 * @param {HTMLElement} input -  The HTML input element to add the `is-invalid` class to.
 */
function addFeedback(element, feedback, input){
    $(element).text(feedback);
    $(input).addClass('is-invalid');
}

/**
 * Turns regular element text fields into input fields preserving the current class list and any
 * units.
 * 
 * @param {String} selector A jquery selector string for the text to convert.
 */
function createInputFields(selector, size='sm', copy_classes=false, required=false){
    const fields = $(selector).find('.editable');
    fields.each(function(index, field){
        const first_class = $(field).attr('class').split(' ')[0];

        const classes = copy_classes 
                        ? $(field).attr('class')
                        : '';
        const [value, unit] = !(classes.includes('name'))
                        ? $(field).text().trim().split(' ')
                        : [$(field).text().trim(), ''];
        const isRequired = required === true 
                        ? 'required'
                        : '';

        let input = `
            <div class="input-group input-group-${size} mb-1 has-validation">
                <input name="${first_class}" class="bs form-control ${classes}" value="${value}" ${isRequired}>
        `
        if (unit && isAlphaNumeric(unit) && !(classes.includes('name'))){
            input += `<span class="bs input-group-text">${unit}</span>`
        }
        input += `
                <div class="invalid-feedback"></div>
            </div>
        `

        $(field).replaceWith(input);
    });
}
/**
 * Turns regular input fields into text fields preserving the current class list and any
 * units.
 * 
 * @param {String} selector A jquery selector string for the input field to convert.
 */
function revertInputFields(selector, copy_classes=false, wrapper='span'){
    const fields = $(selector);
    fields.each(function(index, field){
        const input = $(field).find('input');
        if (!input.length) return;
        const input_group_text = $(field).find('.input-group-text');
        const classes = copy_classes ? $(input).attr('class').replace('bs ', '').replace('form-control ', ''): '';
        const [value, unit] = [input.val(), input_group_text.text()];

        let text = `
            <${wrapper} class="${classes}">${value} ${unit}</${wrapper}}>
        `

        $(field).replaceWith(text);
    });
}


/**
 * Simple check to test length of a string
 * @param {String} str 
 * @param {int} min 
 * @param {int} max 
 * @returns {Boolean}
 */
function isValidLength(str, min, max){
    return (str.length > min) && (str.length < max)
}
/**
 * Regex check to see if a string is a valid team name.
 * @param {String} str 
 * @returns {Boolean}
 */
function isValidTeamName(str){
    return /^[a-zA-Z0-9][a-zA-Z0-9 _-]{1,48}[a-zA-Z0-9]$/.test(str);
}
/**
 * Simple check to test if a string is alpha numeric
 * @param {String} str 
 * @returns {Boolean}
 */
function isAlphaNumeric(str) {
    return /^[a-z0-9]+$/i.test(str);
}
/**
 * Simple check if a string contains only numbers (0-9)
 * @param {String} str 
 * @returns {Boolean}
 */
function isNumeric(str) {
    if (str === '') return false
    return !Number.isNaN(Number(str));
}
/**
 * Simple check if a string contains only letters (a-z, A-Z)
 * @param {String} str 
 * @returns {Boolean}
 */
function isAlphabetic(str) {
    return /^[a-zA-Z\s]+$/.test(str);
}
/**
 * Simple check if an int is a valid number based on min max
 * @param {int} number
 * @param {int} min
 * @param {int} max
 * @returns {Boolean}
 */
function isValidNumber(number, min, max){
    if (number === '') return false;
    const num = Number(number);
    return (num > min) && (num < max)
}

/**
 * Initialises the toggle functionality between table and calendar views for leave records.
 * 
 * Attaches an event listener to the element with ID 'toggleTableView'. When toggled,
 * it shows or hides the elements with IDs 'calendar' and 'tableView' accordingly,
 * and re-renders the calendar to ensure correct display.
 */
function initTableToggle() {
    // Add event listener to toggle between table and calendar view for leave records
    $('#toggleTableView').on('change', function() {
        $('#calendar').toggle();
        $('#tableView').toggle();

        calendar.render();
    });
}
/**
 * Change the location of the current browser to a new target location.
 * The target location must be stored in the element as a data attribute under the name "href".
 * 
 * @param {HTMLElement} element
 */
function redirect(element) {
        const href = $(element).data('href');
        window.location.href = href;
    }

/**
 * Initialises BootStrap tooltips using a jQuery selector.
 * 
 * @param {object} $selector jQuery object e.g., `$('.info-icon')`.
 * @param {int} hideDelay The delay between the hide trigger, and the hide event beginning. Measured in ms.
 * @param {int} fadeTime The length of time the fading of the popup should go on for when the hide event begins. Measured in ms.
 */
function initToolTips(
    $selector,
    hideDelay = 400, //ms
    fadeTime = 200 // ms
) {
    // Manually activate the bootstrap info popover for interactivity
    $selector.each(function() {
        const $trigger = $(this);
        const tooltip = new bootstrap.Tooltip(this, { trigger: 'manual', animation: false});
        let hideTimer = null;
        let fadeTimer = null;
        let $tip = null;
        let isShown = false;

        const cancelHide = () => {
            clearTimeout(hideTimer);
            clearTimeout(fadeTimer);
            if ($tip) $tip.css('opacity', 1);
        };
        const scheduleHide = () => {
            clearTimeout(hideTimer);
            hideTimer = setTimeout(fadeOut, hideDelay);
        };
        const fadeOut = () => {
            if (!$tip) return tooltip.hide();
            $tip.css('opacity', 0);
            fadeTimer = setTimeout(() => tooltip.hide(), fadeTime);
        }

        $trigger
            .on('mouseenter', () => {
                cancelHide();
                if (!isShown) tooltip.show();
            })
            .on('mouseleave', scheduleHide);
        
        $trigger
            .on('inserted.bs.tooltip', function() {
                $tip = $(`#${$(this).attr('aria-describedby')}`);
                $tip.css({ transition: `opacity ${fadeTime}ms ease`, opacity: 0});
            })
            .on('shown.bs.tooltip', function() {
                isShown = true;
                if (!$tip) return;
                $tip[0].offsetHeight;
                $tip.css('opacity', 1);
                $tip.on('mouseenter', cancelHide).on('mouseleave', scheduleHide);
            })
            .on('hidden.bs.tooltip', () => { isShown = false; $tip = null; });
    });
}