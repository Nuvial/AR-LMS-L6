$(document).ready(function(){
    $('#toggleTableView')[0].checked = false;

    loadEmployees();

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
