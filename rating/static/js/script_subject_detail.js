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

function showUpdateSubject(subjectId) {
    var url = window.location.origin + `/api/v1/subjects/${subjectId}/`;
    var updateModal = document.getElementById('update-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        console.log(data);
        var form = document.querySelector('#update-form').elements;

        form.name.value = data.name;
        $('.ui.dropdown').dropdown('set selected', data.form_control);
        $('.ui.dropdown').dropdown('set selected', data.semester.semester);
        if (data.cathedra) {
            $('.ui.dropdown').dropdown('set selected', data.cathedra.id);
        };
        form.zet.value = data.zet;
        form.comment.value = data.comment;
        form.is_archived.checked = data.is_archived;

        var updateButton = document.getElementById('update-btn');
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
    var button = document.getElementById("update-btn");
    var subjectId = button.getAttribute("data-subject-id");
    var url = window.location.origin + `/api/v1/subjects/${subjectId}/update_subject/`;
    var updateModal = document.getElementById('update-modal');
    var form = document.querySelector('#update-form');
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
    var deleteModal = document.getElementById('delete-modal');
    
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

        var deleteButton = document.getElementById('delete-btn');
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
    var button = document.getElementById("delete-btn");
    var subjectId = button.getAttribute("data-subject-id");
    var url = window.location.origin + `/api/v1/subjects/${subjectId}/delete_subject/`;
    var deleteSubjectModal = document.getElementById('delete-modal');

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
