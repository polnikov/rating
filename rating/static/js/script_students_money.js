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

fetchStudentsMoneyDataAndPopulate();
function fetchStudentsMoneyDataAndPopulate() {
    const url = window.location.origin + "/api/v1/money/";
    $('#datatable-segment').dimmer({
        displayLoader: true,
        loaderVariation: 'slow orange medium elastic',
        loaderText: 'Загрузка данных...'
    }).dimmer('show');

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#students-money-table').DataTable();
            table.clear();

            data.forEach((student, index) => {
                let isIll;
                if (student.is_ill === true) {
                    isIll = '<i class="heart broken red icon"></i>'
                } else {
                    isIll = ''
                };
                let tag;
                if (student.tag) {
                    tag = `<div id="tag-label" class="ui small pink label">${student.tag}</div>`
                } else {
                    tag = ''
                };
                let rowData = [
                    index + 1,
                    `<div id="${student.group.id}" name="group" onclick="getAbsoluteURLforGroup([${student.group.id}, '${student.group.name}', ${student.semester}])"><a>${student.group.name}</a></div>`,
                    student.semester,
                    `<div id="${student.student_id}" name="student" onclick="getAbsoluteURLforStudent(${student.student_id})">${isIll}<a>${student.fullname}</a> ${tag}</div>`,
                    student.money,
                    student.basis,
                ];
                table.row.add(rowData);
            });
            table.draw();
            $('#datatable-segment').dimmer('hide');
        })
        .catch(error => {
            $('#datatable-segment').dimmer('hide');
            console.error(error);
            $.toast({
                class: 'error center aligned',
                position: 'centered',
                message: '<i class="exclamation circle large icon"></i> Упс! Список студентов не удалось загрузить....попробуйте попозже снова.'
            });
        });
};
