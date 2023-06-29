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

fetchStudentsDataAndPopulate();
function fetchStudentsDataAndPopulate() {
    const url = window.location.origin + "/api/v1/activestudents/";
    const tab1 = $("div.ui.tab.active[data-tab='first']");
    tab1.dimmer({
        displayLoader: true,
        loaderVariation: 'slow orange medium elastic',
        loaderText: 'Загрузка данных...'
    }).dimmer('show');

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#students-table').DataTable();
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
                    `<div id="${student.student_id}" name="student" onclick="getAbsoluteURLforStudent(${student.student_id})">${isIll}<a>${student.fullname}</a> ${tag}</div>`,
                    student.group,
                    student.semester,
                    student.level,
                    student.citizenship,
                    student.comment,
                ];
                table.row.add(rowData);
            });
            table.draw();
            tab1.dimmer('hide');
        })
        .catch(error => {
            tab1.dimmer('hide');
            console.error(error);
            $.toast({
                class: 'error center aligned',
                position: 'centered',
                message: '<i class="exclamation circle large icon"></i> Упс! Список студентов не удалось загрузить....попробуйте попозже снова.'
            });
        });
};

fetchStudentsHistoryDataAndPopulate();
function fetchStudentsHistoryDataAndPopulate() {
    const url = window.location.origin + "/api/v1/history/students/";
    const tab2 = $("div.ui.tab[data-tab='second']");
    tab2.dimmer({
        displayLoader: true,
        loaderVariation: 'slow orange medium elastic',
        loaderText: 'Загрузка данных...'
    }).dimmer('show');

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#history-table').DataTable();
            table.clear();
            
            data.forEach((record) => {
                let name;
                if (record.fullname === false) {
                    name = `Удалён [${record.record_id}]`;
                } else {
                    name = `<div id="${record.record_id}" name="student" onclick="getAbsoluteURL(${record.record_id})"><a>${record.fullname}</a></div>`;
                };
                var oldValue, newValue;
                if (record.field === 'Архив') {
                    switch (record.old_value) {
                        case 'True':
                            oldValue = 'Да';
                            break
                        case 'False':
                            oldValue = 'Нет';
                            break
                    };
                    switch (record.new_value) {
                        case 'True':
                            newValue = 'Да';
                            break
                        case 'False':
                            newValue = 'Нет';
                            break
                    };
                } else {
                    switch (record.old_value) {
                        case '':
                            oldValue = '---';
                            break
                        default:
                            oldValue = record.old_value;
                            break
                    };
                    switch (record.new_value) {
                        case '':
                            newValue = '---';
                            break
                        default:
                            newValue = record.new_value;
                            break
                    };
                };

                let rowData = [
                    new Date(record.timestamp),
                    record.user,
                    name,
                    record.field,
                    oldValue,
                    newValue,
                ];
                table.row.add(rowData);
            });
            table.draw();
            tab2.dimmer('hide');
        })
        .catch(error => {
            tab2.dimmer('hide');
            console.error(error);
            $.toast({
                class: 'error center aligned',
                position: 'centered',
                message: '<i class="exclamation circle large icon"></i> Упс! Список изменений не удалось загрузить....попробуйте попозже снова.'
            });
        });
};

function saveStudentForm() {
    var url = window.location.origin + `/api/v1/students/create_student/`;
    var addModal = document.getElementById('add-modal');
    var form = document.querySelector('#add-form');
    var formData = new FormData(form);
 
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        },
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (!data.errors) {
            fetchStudentsDataAndPopulate();
            $(addModal).modal({blurring: true}).modal('hide');
            resetAddForm();
            $.toast({
                class: 'success center aligned',
                position: 'centered',
                message: '<i class="checkmark icon"></i> Добавлено!'
            });
        };
    })
    .catch(error => {
        console.error(error);
        $(addModal).modal({blurring: true}).modal('hide');
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
        });
    });
};

function importStudents() {
    const url = window.location.origin + "/api/v1/import/students/";
    var fileInput = document.querySelector('input[type="file"]');
    var formData = new FormData();
    var file = fileInput.files[0];
    formData.append('import_files', file);
    document.getElementById("errors-list").textContent = '';

    fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken,
        },
        body: formData,
    })
    .then(function(response) {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Network response was not ok.');
        };
    })
    .then(function(data) {
        var success = data.data[0].success;
        if (!success) {
            $('#import-students').modal('hide');
            
            var error = data.data[0].error;
            if (error) {
                $.toast({
                    class: 'error center aligned',
                    closeIcon: true,
                    displayTime: 0,
                    position: 'centered',
                    message: '<i class="exclamation circle large icon"></i> Ничего не выбрано для импорта или неверный формат файла!'
                });
            };
    
            var errors = data.data[0].errors;
            if (errors) {
                console.log('ERRORS', errors)
                $('#errors').modal({blurring: true}).modal('show');
                
                var errorsList = document.getElementById("errors-list");
                for (var i = 0; i < errors.length; i++) {
                    console.log(errors[i])
                    var errorString = `
                    <div class="item">
                        <i class="bug red icon"></i>
                        <div class="content">
                            <div class="description">${errors[i]}</div>
                        </div>
                    </div>
                    `;
                    errorsList.insertAdjacentHTML('beforeend', errorString);
                };
            };
        } else {
            $('#import-students').modal('hide');
            fetchStudentsDataAndPopulate();
            $.toast({
                class: 'success center aligned',
                position: 'centered',
                message: '<i class="checkmark icon"></i> Импортировано!'
            });
        };
    })
    .catch(function(error) {
        console.log(error);
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
        });
    });
    fileInput.value = '';
};

function formatDateString(dateString) {
    const date = new Date(dateString);
  
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const year = date.getFullYear().toString().slice(-2);
  
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
  
    const formattedDate = `${day}.${month}.${year}`;
    const formattedTime = `${hours}:${minutes}`;
  
    return `${formattedDate} | ${formattedTime}`;
};
