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

function showUpdateSubject(subjectId) {
    var url = window.location.origin + `/api/v1/subjects/${subjectId}/`;
    var updateModal = document.getElementById('subject-update-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        var form = document.querySelector('#subject-update-form').elements;

        form.name.value = data.name;
        $('.ui.dropdown').dropdown('set selected', data.form_control);
        $('.ui.dropdown').dropdown('set selected', data.semester.semester);
        if (data.cathedra) {
            $('.ui.dropdown').dropdown('set selected', data.cathedra.id);
        };
        form.zet.value = data.zet;
        form.comment.value = data.comment;
        form.is_archived.checked = data.is_archived;

        var updateButton = document.getElementById('update-subject-btn');
        updateButton.dataset.subjectId = subjectId;

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

function updateSubject() {
    var button = document.getElementById("update-subject-btn");
    var subjectId = button.getAttribute("data-subject-id");
    var url = window.location.origin + `/api/v1/subjects/${subjectId}/update_subject/`;
    var updateModal = document.getElementById('subject-update-modal');
    var form = document.querySelector('#subject-update-form');
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

function showDeleteSubject(subjectId) {
    var url = window.location.origin + `/api/v1/subjects/${subjectId}/`;
    var deleteModal = document.getElementById('subject-delete-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        let semester = `<div class="ui circular label">${data.semester.semester}</div>`;
        if (data.groups.length !== 0) {
            var groups = data.groups.map(element => `<div class="ui circular label">${element}</div>`).join('');
            document.querySelector('#del-groups').innerHTML = groups;
        } else {
            var groups = '<i class="icon close"></i> Не назначено';
            document.querySelector('#del-groups').innerHTML = groups;
            document.querySelector('#del-groups').classList.add("negative");
        };
        if (data.cathedra && data.cathedra.faculty !== null) {
            document.querySelector('#del-faculty').textContent = data.cathedra.faculty.name;
        } else {
            document.querySelector('#del-faculty').innerHTML = '<i class="icon close"></i> Нет';
            document.querySelector('#del-faculty').classList.add("negative");
        };
        if (data.cathedra !== null) {
            document.querySelector('#del-cathedra').textContent = data.cathedra.name;
        } else {
            document.querySelector('#del-cathedra').innerHTML = '<i class="icon close"></i> Нет';
            document.querySelector('#del-cathedra').classList.add("negative");
        };
        document.querySelector('#del-name').textContent = data.name;
        document.querySelector('#del-semester').innerHTML = semester;
        document.querySelector('#del-formcontrol').textContent = data.form_control;
        document.querySelector('#del-zet').textContent = data.zet;
        document.querySelector('#del-comment').textContent = data.comment;

        var deleteButton = document.getElementById('delete-subject-btn');
        deleteButton.dataset.subjectId = subjectId;

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

function deleteSubject() {
    var button = document.getElementById("delete-subject-btn");
    var subjectId = button.getAttribute("data-subject-id");
    var url = window.location.origin + `/api/v1/subjects/${subjectId}/delete_subject/`;
    var deleteSubjectModal = document.getElementById('subject-delete-modal');

    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
    .then(response => {
        if (response.ok) {
            $(deleteSubjectModal).modal({blurring: true}).modal('hide');
            url = window.location.origin + "/subjects/";
            window.location.href = url;
        };
    })
    .catch(error => {
        console.error(error);
        $(deleteSubjectModal).modal({blurring: true}).modal('hide');
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
        });
    });
};

var hasGroup = document.getElementById('has-group').textContent;
var subjectId = document.getElementById('subject-id').textContent;
fetchSubjectMarksDataAndPopulate(hasGroup);
function fetchSubjectMarksDataAndPopulate(hasGroup) {
    const queryParams = new URLSearchParams({ subject_id: subjectId });
    const url = window.location.origin + `/api/v1/subjectresults/?${queryParams}`;
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#subject-marks').DataTable();
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
                    `<div id="${result.students.student_id}" name="student" onclick="getAbsoluteURLforStudent(${result.students.student_id})"><a>${result.students.fullname}</a> ${tag}</div>`,
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
            const table = $('#subject-marks').DataTable();
            table.clear();
            fetchSubjectMarksDataAndPopulate(hasGroup);
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

        var updateButton = document.getElementById('update-result-btn');
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
    var button = document.getElementById("update-result-btn");
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
            const table = $('#subject-marks').DataTable();
            table.clear();
            fetchSubjectMarksDataAndPopulate(hasGroup);
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
};
 