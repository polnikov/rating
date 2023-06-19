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
const csrftoken = getCookie('csrftoken');
fetchSubjectsDataAndPopulate();
 
function fetchSubjectsDataAndPopulate() {
    const url = window.location.origin + "/api/v1/activesubjects/";
    $('#datatable-segment').dimmer({
        displayLoader: true,
        loaderVariation: 'slow orange medium elastic',
        loaderText: 'Загрузка данных...'
    }).dimmer('show');

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#subjects-table').DataTable();
            table.clear();

            data.forEach((subject, index) => {
                let rowData = [
                    index + 1,
                    `<div id="${subject.id}" name="subject" onclick="getAbsoluteURL(${subject.id})"><a>${subject.name}</a></div>`,
                    subject.form_control,
                    subject.semester,
                    (subject.cathedra !== null) ? subject.cathedra :  '<td class="negative"><i class="icon close"></i> Нет</td>',
                    subject.comment,
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
                message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
            });
        });
};

function saveSubjectForm() {
    var url = window.location.origin + `/api/v1/subjects/create_subject/`;
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
            fetchSubjectsDataAndPopulate();
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

function importSubjects() {
    const url = window.location.origin + "/api/v1/import/subjects/";
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
            $('#import-subjects').modal('hide');
            
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
            $('#import-subjects').modal('hide');
            fetchSubjectsDataAndPopulate();
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
