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
 
const hasGroup = document.getElementById('has-group').textContent;
fetchFacultiesDataAndPopulate(hasGroup);

function fetchFacultiesDataAndPopulate(hasGroup) {
    const url = window.location.origin + "/api/v1/faculties/";

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = document.getElementById('faculties-table');
            const tbody = table.getElementsByTagName('tbody')[0];
            tbody.innerHTML = '';

            data.forEach((faculty, index) => {
                let defFunc, updFunc;
                if (hasGroup === 'True') {
                    defFunc = `onclick="showDeleteFaculty(${faculty.id})"`;
                    updFunc = `onclick="showUpdateFaculty(${faculty.id})"`;
                } else {
                    defFunc = '';
                    updFunc = '';
                };
                let rowData = `
                    <tr>
                        <td class="center aligned collapsing">${index + 1}</td>
                        <td class="center aligned collapsing">${faculty.short_name}</td>
                        <td>${faculty.name}</td>
                        <td class="center aligned collapsing"><button id="trash-button" ${defFunc} class="circular ui red mini icon button"><i class="trash alternate outline icon"></i></button></td>
                        <td class="center aligned collapsing"><button id="edit-button" ${updFunc} class="circular ui blue mini icon button"><i class="edit icon"></i></button></td>
                    </tr>
                `;
                tbody.insertAdjacentHTML('beforeend', rowData);
            });
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

function saveFacultyForm() {
    var url = window.location.origin + `/api/v1/faculties/create_faculty/`;
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
            fetchFacultiesDataAndPopulate(hasGroup);
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

function showUpdateFaculty(facultyId) {
    const url = window.location.origin + `/api/v1/faculties/${facultyId}/`;
    var updateModal = document.getElementById('update-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        var form = document.querySelector('#update-form');
        form.elements.name.value = data.name;
        form.elements.short_name.value = data.short_name;

        var updateButton = document.getElementById('update-btn');
        updateButton.dataset.facultyId = facultyId;

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

function updateFaculty() {
    var button = document.getElementById("update-btn");
    var facultyId = button.getAttribute("data-faculty-id");
    var url = window.location.origin + `/api/v1/faculties/${facultyId}/update_faculty/`;
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
            fetchFacultiesDataAndPopulate(hasGroup);
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

function showDeleteFaculty(facultyId) {
    const url = window.location.origin + `/api/v1/faculties/${facultyId}/`;
    var deleteModal = document.getElementById('delete-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        document.querySelector('#del-info').textContent = `Вы уверены, что хотите удалить факультет: ${data.name} (${data.short_name})`;
        var deleteButton = document.getElementById('delete-btn');
        deleteButton.dataset.facultyId = facultyId;

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

function deleteFaculty() {
    var button = document.getElementById("delete-btn");
    var facultyId = button.getAttribute("data-faculty-id");
    var url = window.location.origin + `/api/v1/faculties/${facultyId}/delete_faculty/`;
    var deleteModal = document.getElementById('delete-modal');

    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
    .then(response => {
        if (response.ok) {
            fetchFacultiesDataAndPopulate(hasGroup);
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
