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

function showUpdateStudent(studentId) {
    var url = window.location.origin + `/api/v1/students/${studentId}/`;
    var updateModal = document.getElementById('student-update-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        var form = document.querySelector('#student-update-form').elements;

        form.last_name.value = data.last_name;
        form.first_name.value = data.first_name;
        form.second_name.value = data.second_name;
        form.student_id.value = data.student_id;
        $('.ui.dropdown').dropdown('set selected', data.group.id);
        $('.ui.dropdown').dropdown('set selected', data.semester.semester);
        $('.ui.dropdown').dropdown('set selected', data.citizenship);
        $('.ui.dropdown').dropdown('set selected', data.basis.id);
        $('.ui.dropdown').dropdown('set selected', data.level);
        form.start_date.value = formatDate(data.start_date);
        form.status.value = data.status;
        form.tag.value = data.tag;
        form.money.value = data.money;
        form.comment.value = data.comment;
        form.is_archived.checked = data.is_archived;

        var updateButton = document.getElementById('update-btn');
        updateButton.dataset.studentId = studentId;

        $(updateModal).modal({blurring: true}).modal('show');
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

function updateStudent() {
    var button = document.getElementById("update-btn");
    var studentId = button.getAttribute("data-student-id");
    var url = window.location.origin + `/api/v1/students/${studentId}/update_student/`;
    var updateModal = document.getElementById('student-update-modal');
    var form = document.querySelector('#student-update-form');
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
            $(updateModal).modal({blurring: true}).modal('hide');
            $.toast({
                class: 'success center aligned',
                position: 'centered',
                message: '<i class="checkmark icon"></i> Обновлено!'
            });
            setTimeout(function() {document.location.reload()}, 1500);
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

function showDeleteStudent(studentId) {
    var url = window.location.origin + `/api/v1/students/${studentId}/`;
    var deleteModal = document.getElementById('student-delete-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        document.querySelector('#del-id').textContent = data.student_id;
        document.querySelector('#del-citizenship').textContent = data.citizenship;
        document.querySelector('#del-basis').textContent = data.basis.name;
        document.querySelector('#del-level').textContent = data.level;
        document.querySelector('#del-group').textContent = data.group.name;
        document.querySelector('#del-semester').textContent = data.semester;
        document.querySelector('#del-date').textContent = formatDate(data.start_date);
        document.querySelector('#del-money').textContent = data.money;
        document.querySelector('#del-status').textContent = data.status;
        document.querySelector('#del-comment').textContent = data.comment;

        var deleteButton = document.getElementById('delete-btn');
        deleteButton.dataset.studentId = studentId;

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

function deleteStudent() {
    var button = document.getElementById("delete-btn");
    var studentId = button.getAttribute("data-student-id");
    var url = window.location.origin + `/api/v1/students/${studentId}/delete_student/`;
    var deleteStudentModal = document.getElementById('student-delete-modal');

    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
    .then(response => {
        if (response.ok) {
            $(deleteStudentModal).modal({blurring: true}).modal('hide');
            url = window.location.origin + "/students/";
            window.location.href = url;
        };
    })
    .catch(error => {
        console.error(error);
        $(deleteStudentModal).modal({blurring: true}).modal('hide');
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
        });
    });
};

function formatDate(dateString) {
    var dateParts = dateString.split("-");
    var year = dateParts[0];
    var month = dateParts[1];
    var day = dateParts[2];
    return day + "." + month + "." + year;
};

var hasGroup = document.getElementById('has-group').textContent;
var studentId = document.getElementById('student-id').textContent;
fetchStudentMarksDataAndPopulate(hasGroup);
function fetchStudentMarksDataAndPopulate(hasGroup) {
    const queryParams = new URLSearchParams({ student_id: studentId });
    const url = window.location.origin + `/api/v1/studentresults/?${queryParams}`;
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#student-marks').DataTable();
            table.clear();

            data.forEach((result) => {
                let tag;
                if (result.tag) {
                    tag = `<div id="tag-label" class="ui tiny pink label">${result.tag}</div>`
                } else {
                    tag = ''
                };
                let delFunc, updFunc;
                if (hasGroup === 'True') {
                    delFunc = `onclick="showDeleteResult(${result.id})"`;
                    updFunc = `onclick="showUpdateResult(${result.id})"`;
                } else {
                    delFunc = '';
                    updFunc = '';
                };
                lastMark = result.mark[result.mark.length - 1];
                if ('2нянз'.includes(lastMark)) {
                    negative = 'red'
                } else {negative = ''};
                mark1 = `<div name="result" class="column ${negative} collapsing">${result.mark[0]}</div>`;
                mark2 = (result.mark[1]) ? `<div name="result" class="column ${negative} collapsing">${result.mark[1]}</div>` : `<div name="result" class="column ${negative} collapsing"></div>`;
                mark3 = (result.mark[2]) ? `<div name="result" class="column ${negative} collapsing">${result.mark[2]}</div>` : `<div name="result" class="column ${negative} collapsing"></div>`;
                let rowData = [
                    result.groupsubject.subjects.semester,
                    `<div id="${result.groupsubject.groups.id}" name="group" onclick="getAbsoluteURLforGroup([${result.groupsubject.groups.id}, '${result.groupsubject.groups.name}', ${result.groupsubject.subjects.semester}])"><a>${result.groupsubject.groups.name}</a></div>`,
                    `<div id="${result.groupsubject.subjects.id}" name="subject" onclick="getAbsoluteURLforSubject(${result.groupsubject.subjects.id})"><a>${result.groupsubject.subjects.name}</a> ${tag}</div>`,
                    result.groupsubject.subjects.form_control,
                    (result.groupsubject.teacher) ? result.groupsubject.teacher : '<td class="negative"><i class="icon close"></i> Нет</td>',
                    (result.groupsubject.att_date) ? formatDate(result.groupsubject.att_date) : '<td class="negative"><i class="icon close"></i> Нет</td>',
                    `<a id="${result.id}" ${updFunc}>
                        <div class="ui equal width stackable grid center aligned">
                            ${mark1}${mark2}${mark3}
                        </div>
                    </a>`,
                    `<button id="trash-button" ${delFunc} class="circular ui red mini icon button"><i class="trash alternate outline icon"></i></button>`,
                ];
                table.row.add(rowData);
            });
            table.draw();
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

function saveResultForm() {
    var url = window.location.origin + `/api/v1/results/create_result/`;
    var addModal = document.getElementById('add-result-modal');
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
            $(addModal).modal({blurring: true}).modal('hide');
            resetAddForm();
            const table = $('#student-marks').DataTable();
            table.clear();
            fetchStudentMarksDataAndPopulate(hasGroup);
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

function showUpdateResult(resultId) {
    var url = window.location.origin + `/api/v1/results/${resultId}/`;
    var updateModal = document.getElementById('result-update-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        var form = document.querySelector('#result-update-form').elements;

        $('.ui.dropdown').dropdown('set selected', data.students.student_id);
        $('.ui.dropdown').dropdown('set selected', data.groupsubject.id);
        form.id_mark_0.value = data.mark[0];
        form.id_mark_1.value = (data.mark[1]) ? data.mark[1] : '';
        form.id_mark_2.value = (data.mark[2]) ? data.mark[2] : '';
        form.tag.value = data.tag;
        form.is_archived.checked = data.is_archived;

        var updateButton = document.getElementById('update-btn');
        updateButton.dataset.resultId = resultId;

        $(updateModal).modal({blurring: true}).modal('show');
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

function updateResult() {
    var button = document.getElementById("update-btn");
    var resultId = button.getAttribute("data-result-id");
    var url = window.location.origin + `/api/v1/results/${resultId}/update_result/`;
    var updateModal = document.getElementById('result-update-modal');
    var form = document.querySelector('#result-update-form');
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
            $(updateModal).modal({blurring: true}).modal('hide');
            $.toast({
                class: 'success center aligned',
                position: 'centered',
                message: '<i class="checkmark icon"></i> Обновлено!'
            });
            const table = $('#marks-table').DataTable();
            table.clear();
            fetchStudentMarksDataAndPopulate(hasGroup);
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

function showDeleteResult(resultId) {
    var url = window.location.origin + `/api/v1/results/${resultId}/`;
    var deleteModal = document.getElementById('result-delete-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        let modal = '#result-delete-modal';
        document.querySelector(`${modal} #del-name`).textContent = data.students.fullname;
        document.querySelector(`${modal} #del-group`).textContent = data.groupsubject.groups.name;
        document.querySelector(`${modal} #del-semester`).textContent = data.groupsubject.subjects.semester;
        document.querySelector(`${modal} #del-subject`).textContent = data.groupsubject.subjects.name;
        document.querySelector(`${modal} #del-formcontrol`).textContent = data.groupsubject.subjects.form_control;
        document.querySelector(`${modal} #del-date`).textContent = (data.groupsubject.att_date) ? formatDate(data.groupsubject.att_date) : 'Нет';
        document.querySelector(`${modal} #del-marks`).textContent = data.mark.join(' ');

        var deleteButton = document.getElementById('delete-btn');
        deleteButton.dataset.resultId = resultId;

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

function deleteResult() {
    var button = document.getElementById("delete-btn");
    var resultId = button.getAttribute("data-result-id");
    var url = window.location.origin + `/api/v1/results/${resultId}/delete_result/`;
    var deletetModal = document.getElementById('result-delete-modal');

    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
    .then(response => {
        if (response.ok) {
            $(deletetModal).modal({blurring: true}).modal('hide');
            const table = $('#student-marks').DataTable();
            table.clear();
            fetchStudentMarksDataAndPopulate(hasGroup);
        };
    })
    .catch(error => {
        console.error(error);
        $(deletetModal).modal({blurring: true}).modal('hide');
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
        });
    });
};

function formatDate(dateString) {
    var dateParts = dateString.split("-");
    var year = dateParts[0];
    var month = dateParts[1];
    var day = dateParts[2];
    return day + "." + month + "." + year;
};

function showResultModal(id) {
    var element = document.getElementById('add-result-modal');
    $(element).modal({blurring: true}).modal('show');
    $('div.ui.selection.dropdown').dropdown('set selected', id);
 };
 