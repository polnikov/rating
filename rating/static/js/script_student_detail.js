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

function showUpdateStudent(studentId) {
    var url = window.location.origin + `/api/v1/students/${studentId}/`;
    var updateModal = document.getElementById('update-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        var form = document.querySelector('#update-form').elements;

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

function showDeleteStudent(studentId) {
    var url = window.location.origin + `/api/v1/students/${studentId}/`;
    var deleteModal = document.getElementById('delete-modal');
    
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
    var deleteStudentModal = document.getElementById('delete-modal');

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
