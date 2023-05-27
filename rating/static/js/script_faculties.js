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
                    <tr class="center aligned">
                        <td class="collapsing">${index + 1}</td>
                        <td class="collapsing">${faculty.short_name}</td>
                        <td class="left aligned">${faculty.name}</td>
                        <td><button id="trash-button" ${defFunc} class="circular ui red mini icon button"><i class="trash alternate outline icon"></i></button></td>
                        <td><button id="edit-button" ${updFunc} class="circular ui blue mini icon button"><i class="edit icon"></i></button></td>
                    </tr>
                `;
                tbody.insertAdjacentHTML('beforeend', rowData);
            });
        })
        .catch(error => {
            console.error(error);
            alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
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

        var updateButton = document.getElementById('update-button');
        updateButton.dataset.facultyId = facultyId;

        $(updateModal).modal({blurring: true}).modal('show');
    })
    .catch(error => {
        console.error(error);
        alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
    });
};

function updateFaculty() {
    var button = document.getElementById("update-button");
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
            $('#success').nag({displayTime: 1500}).show();
        };
    })
    .catch(error => {
        console.error(error);
        alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
        $(updateModal).modal({blurring: true}).modal('hide');
    });
};

function showDeleteFaculty(facultyId) {
    const url = window.location.origin + `/api/v1/faculties/${facultyId}/`;
    var deleteModal = document.getElementById('delete-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        document.querySelector('#del-info').textContent = `Вы уверены, что хотите удалить факультет: ${data.name} (${data.short_name})`;
        var deleteButton = document.getElementById('delete-button');
        deleteButton.dataset.facultyId = facultyId;

        $(deleteModal).modal({blurring: true}).modal('show');
    })
    .catch(error => {
        console.error(error);
        alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
    });
};

function deleteFaculty() {
    var button = document.getElementById("delete-button");
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
            $('#success').nag({displayTime: 1500}).show();
        };
    })
    .catch(error => {
        console.error(error);
        alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
        $(deleteModal).modal({blurring: true}).modal('hide');
    });
};
