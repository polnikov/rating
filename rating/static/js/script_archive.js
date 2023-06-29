var hasGroup = document.getElementById('has-group').textContent;

function fetchArchivedGroupSubjectsDataAndPopulate(hasGroup) {
    const url = window.location.origin + "/api/v1/groupsubjects/?is_archived=true";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#groupsubjects-table').DataTable();
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
                    `<div id="${gs.subjects.id}" name="subject">${gs.subjects.name}</div>`,
                    gs.subjects.form_control,
                    `<div id="${gs.groups.id}" name="group">${gs.groups.name}</div>`,
                    gs.semester,
                    (gs.teacher) ? gs.teacher : '---',
                    (gs.att_date) ? new Date(gs.att_date) : 'Нет',
                    (gs.cathedra) ? gs.cathedra : '---',
                    `<button id="trash-button" ${defFunc} class="circular ui red mini icon button"><i class="trash alternate outline icon"></i></button>`,
                    `<button id="edit-button" ${updFunc} class="circular ui blue mini icon button"><i class="edit icon"></i></button>`,
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

function fetchArchivedStudentsDataAndPopulate() {
    const url = window.location.origin + "/api/v1/archivedstudents/";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#students-table').DataTable();
            table.clear();

            data.forEach((student, index) => {
                let tag;
                if (student.tag) {
                    tag = `<div id="tag-label" class="ui small pink label">${student.tag}</div>`
                } else {
                    tag = ''
                };
                let rowData = [
                    index + 1,
                    `<div id="${student.student_id}" name="student" onclick="getAbsoluteURLforStudent(${student.student_id})"><a>${student.fullname}</a> ${tag}</div>`,
                    student.group,
                    student.semester,
                    student.level,
                    student.citizenship,
                    student.status,
                    student.comment,
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
                message: '<i class="exclamation circle large icon"></i> Упс! Список студентов не удалось загрузить....попробуйте попозже снова.'
            });
        });
};

function fetchArchivedSubjectsDataAndPopulate() {
    const url = window.location.origin + "/api/v1/archivedsubjects/";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#subjects-table').DataTable();
            table.clear();

            data.forEach((subject, index) => {
                let rowData = [
                    index + 1,
                    `<div id="${subject.id}" name="subject" onclick="getAbsoluteURLforSubject(${subject.id})"><a>${subject.name}</a></div>`,
                    subject.form_control,
                    subject.semester,
                    (subject.cathedra !== null) ? subject.cathedra :  '---',
                    subject.comment,
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

function fetchArchivedMarksDataAndPopulate(hasGroup) {
    const url = window.location.origin + "/api/v1/archivedresults/";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#marks-table').DataTable();
            table.clear();

            data.forEach((result, index) => {
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
                mark1 = `<div name="result" class="column collapsing">${result.mark[0]}</div>`;
                mark2 = (result.mark[1]) ? `<div name="result" class="column collapsing">${result.mark[1]}</div>` : '<div name="result" class="column collapsing"></div>';
                mark3 = (result.mark[2]) ? `<div name="result" class="column collapsing">${result.mark[2]}</div>` : '<div name="result" class="column collapsing"></div>';
                let rowData = [
                    index + 1,
                    `<div id="${result.students.student_id}" name="student" onclick="getAbsoluteURLforStudent(${result.students.student_id})"><a>${result.students.fullname}</a> ${tag}</div>`,
                    result.groupsubject.groups.name,
                    `<div id="${result.groupsubject.subjects.id}" name="subject" onclick="getAbsoluteURLforSubject(${result.groupsubject.subjects.id})"><a>${result.groupsubject.subjects.name}</a></div>`,
                    result.groupsubject.subjects.form_control,
                    result.groupsubject.subjects.semester,
                    (result.groupsubject.att_date) ? new Date(result.groupsubject.att_date) : 'Нет',
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
            fetchArchivedMarksDataAndPopulate(hasGroup);
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
            const table = $('#marks-table').DataTable();
            table.clear();
            fetchArchivedMarksDataAndPopulate(hasGroup);
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
