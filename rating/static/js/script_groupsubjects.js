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

var hasGroup = document.getElementById('has-group').textContent;
fetchGroupSubjectsDataAndPopulate(hasGroup);

function fetchGroupSubjectsDataAndPopulate(hasGroup) {
    const url = window.location.origin + "/api/v1/activegroupsubjects/";
    $('#datatable-segment').dimmer({
        displayLoader: true,
        loaderVariation: 'slow orange medium elastic',
        loaderText: 'Загрузка данных...'
    }).dimmer('show');

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#group-subjects-table').DataTable();
            table.clear();

            data.forEach((gs, index) => {
                let defFunc, updFunc;
                if (hasGroup === 'True') {
                    defFunc = `onclick="showDeleteGroupSubject(${gs.id})"`;
                    updFunc = `onclick="showUpdateGroupSubject(${gs.id})"`;
                } else {
                    defFunc = '';
                    updFunc = '';
                };
                let rowData = [
                    index + 1,
                    `<div id="${gs.subjects.id}" name="subject" onclick="getAbsoluteURL(${gs.subjects.id})"><a>${gs.subjects.name}</a></div>`,
                    gs.subjects.form_control,
                    `<div id="${gs.groups.id}" name="group" onclick="getAbsoluteURLforGroup([${gs.groups.id}, '${gs.groups.name}', ${gs.semester}])"><a>${gs.groups.name}</a></div>`,
                    gs.semester,
                    (gs.teacher) ? gs.teacher : '<td class="negative"><i class="icon close"></i> Нет</td>',
                    (gs.att_date) ? new Date(gs.att_date) : '<td class="negative"><i class="icon close"></i> Нет</td>',
                    (gs.cathedra) ? gs.cathedra : '<td class="negative"><i class="icon close"></i> Нет</td>',
                    `<button id="trash-button" ${defFunc} class="circular ui red mini icon button"><i class="trash alternate outline icon"></i></button>`,
                    `<button id="edit-button" ${updFunc} class="circular ui blue mini icon button"><i class="edit icon"></i></button>`,
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

function saveGroupSubjectForm() {
    var url = window.location.origin + `/api/v1/groupsubjects/create_groupsubject/`;
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
            fetchGroupSubjectsDataAndPopulate(hasGroup);
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

function showUpdateGroupSubject(groupSubjectId) {
    var url = window.location.origin + `/api/v1/groupsubjects/${groupSubjectId}/`;
    var updateGroupSubjectsModal = document.getElementById('group-subject-update-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        console.log(data);
        var form = document.querySelector('#group-subject-update-form').elements;
        $('div.ui.selection.dropdown').dropdown('set selected', data.subjects.id);
        $('div.ui.selection.dropdown').dropdown('set selected', data.groups.id);
        form.teacher.value = data.teacher;
        form.att_date.value = (data.att_date) ? formatDate(data.att_date) : '';
        form.comment.value = (data.comment) ? data.comment : '';
        form.is_archived.checked = data.is_archived;

        var updateButton = document.getElementById('edit-button');
        updateButton.dataset.groupSubjectId = groupSubjectId;

        $(updateGroupSubjectsModal).modal({blurring: true}).modal('show');
    })
    .catch(error => {
        console.error(error);
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
        });
    });
};

function updateGroupSubject() {
    var button = document.getElementById("edit-button");
    var groupSubjectId = button.getAttribute("data-group-subject-id");
    var url = window.location.origin + `/api/v1/groupsubjects/${groupSubjectId}/update_groupsubject/`;
    var updateModal = document.getElementById('group-subject-update-modal');
    var form = document.querySelector('#group-subject-update-form');
    var formData = new FormData(form);

    fetch(url, {
        method: 'PATCH',
        headers: {
            'X-CSRFToken': csrftoken,
        },
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (!data.errors) {
            if (location.href.includes('archive')) {
                fetchArchivedGroupSubjectsDataAndPopulate(hasGroup);
            } else {
                fetchGroupSubjectsDataAndPopulate(hasGroup);
            };
            $(updateModal).modal({blurring: true}).modal('hide');
            $.toast({
                class: 'success center aligned',
                position: 'centered',
                message: '<i class="checkmark icon"></i> Обновлено!'
            });
        };
    })
    .catch(error => {
        console.error(error);
        $(updateModal).modal({blurring: true}).modal('hide');
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
        });
    });
};

function showDeleteGroupSubject(groupSubjectId) {
    var url = window.location.origin + `/api/v1/groupsubjects/${groupSubjectId}/`;
    var deleteModal = document.getElementById('group-subject-delete-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        document.querySelector('#del-subject').textContent = data.subjects.name;
        document.querySelector('#del-formcontrol').textContent = data.subjects.form_control;
        document.querySelector('#del-group').innerHTML = `<div class="ui label">${data.groups.name}-${data.semester}</div>`;
        if (data.teacher) {
            document.querySelector('#del-teacher').innerHTML = `<i class="icon checkmark"></i> ${data.teacher}`;
            document.querySelector('#del-teacher').classList.remove("negative");
            document.querySelector('#del-teacher').classList.add("positive");
        } else {
            document.querySelector('#del-teacher').innerHTML = '<i class="icon close"></i> Нет';
            document.querySelector('#del-teacher').classList.add("negative");
        };
        if (data.att_date !== null) {
            document.querySelector('#del-date').innerHTML = `<i class="icon checkmark"></i> ${formatDate(data.att_date)}`;
            document.querySelector('#del-date').classList.remove("negative");
            document.querySelector('#del-date').classList.add("positive");
        } else {
            document.querySelector('#del-date').innerHTML = '<i class="icon close"></i> Нет';
            document.querySelector('#del-date').classList.add("negative");
        };
        document.querySelector('#del-comment').textContent = (data.comment) ? data.comment : '';
        if (data.cathedra !== false) {
            document.querySelector('#del-cathedra').textContent = data.cathedra;
            document.querySelector('#del-cathedra').classList.remove("negative");
        } else {
            document.querySelector('#del-cathedra').innerHTML = '<i class="icon close"></i> Нет';
            document.querySelector('#del-cathedra').classList.add("negative");
        };

        var deleteButton = document.getElementById('delete-btn');
        deleteButton.dataset.groupSubjectId = groupSubjectId;

        $(deleteModal).modal({blurring: true}).modal('show');
    })
    .catch(error => {
        console.error(error);
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
        });
    });
};

function deleteGroupSubject() {
    var button = document.getElementById("delete-btn");
    var groupSubjectId = button.getAttribute("data-group-subject-id");
    var url = window.location.origin + `/api/v1/groupsubjects/${groupSubjectId}/delete_groupsubject/`;
    var deleteModal = document.getElementById('group-subject-delete-modal');

    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
    .then(response => {
        if (response.ok) {
            if (location.href.includes('archive')) {
                fetchArchivedGroupSubjectsDataAndPopulate(hasGroup);
            } else {
                fetchGroupSubjectsDataAndPopulate(hasGroup);
            };
            $(deleteModal).modal({blurring: true}).modal('hide');
            $.toast({
                class: 'success center aligned',
                position: 'centered',
                message: '<i class="checkmark icon"></i> Удалено!'
            });
        };
    })
    .catch(error => {
        console.error(error);
        $(deleteModal).modal({blurring: true}).modal('hide');
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
        });
    });
};

function importGroupSubjects() {
    const url = window.location.origin + "/api/v1/import/groupsubjects/";
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
            $('#import-groupsubjects').modal('hide');
            
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
            $('#import-groupsubjects').modal('hide');
            fetchGroupSubjectsDataAndPopulate(hasGroup);
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

function formatDate(dateString) {
    var dateParts = dateString.split("-");
    var year = dateParts[0];
    var month = dateParts[1];
    var day = dateParts[2];
    return day + "." + month + "." + year;
};
