// csrftoken
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};
var csrftoken = getCookie('csrftoken');

fetchStudentsAllDebtsDataAndPopulate();
function fetchStudentsAllDebtsDataAndPopulate() {
    const url = window.location.origin + "/api/v1/studentsalldebts/";
    $('#datatable-segment').dimmer({
        displayLoader: true,
        loaderVariation: 'slow orange medium elastic',
        loaderText: 'Загрузка данных...'
    }).dimmer('show');
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#students-debts').DataTable();
            table.clear();

            for(let i = 0; i < data.data.length; i++) {
                line = data.data[i];
                if(line.debts.att1 === 0) {
                    att1 = `<div id="att-label" class="ui red tiny label">${line.debts.att1}</div>`;
                } else {
                    att1 = `<div id="att-label" class="ui grey tiny label">${line.debts.att1}</div>`;
                };
                att2 = (line.debts.att2) ? `<div id="att-label" class="ui grey tiny label">${line.debts.att2}</div>` : ''
                att3 = (line.debts.att3) ? `<div id="att-label" class="ui red tiny label">${line.debts.att3}</div>` : ''

                let rowData = [
                    i + 1,
                    `<div id="${line.group_id}" name="group" onclick="getAbsoluteURLforGroup([${line.group_id}, '${line.group}', ${line.semester}])"><a>${line.group}</a></div>`,
                    line.semester,
                    `<div id="${line.student_id}" name="student" onclick="getAbsoluteURLforStudent(${line.student_id})"><a>${line.fullname}</a></div>`,
                    line.basis,
                    att1,
                    att2,
                    att3,
                ];
                table.row.add(rowData);
            };
            table.draw();
            $('#datatable-segment').dimmer('hide');
        })
        .catch(error => {
            $('#datatable-segment').dimmer('hide');
            console.error(error);
            $.toast({
                class: 'error center aligned',
                position: 'centered',
                message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
            });
    });
};
