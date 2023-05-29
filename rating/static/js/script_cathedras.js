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
fetchCathedrasDataAndPopulate(hasGroup);

function fetchCathedrasDataAndPopulate(hasGroup) {
    const url = window.location.origin + "/api/v1/cathedras/";

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#cathedras-table').DataTable();
            table.clear();

            data.forEach((cathedra, index) => {
                let defFunc, updFunc;
                if (hasGroup === 'True') {
                    defFunc = `onclick="showDeleteCathedra(${cathedra.id})"`;
                    updFunc = `onclick="showUpdateCathedra(${cathedra.id})"`;
                } else {
                    defFunc = '';
                    updFunc = '';
                };
                let rowData = [
                    index + 1,
                    (cathedra.faculty !== null) ? cathedra.faculty.short_name : "-",
                    (cathedra.short_name) ? cathedra.short_name : "-",
                    cathedra.name,
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

function saveCathedraForm() {
    var url = window.location.origin + `/api/v1/cathedras/create_cathedra/`;
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
            fetchCathedrasDataAndPopulate(hasGroup);
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
 
function showUpdateCathedra(cathedraId) {
    const url = window.location.origin + `/api/v1/cathedras/${cathedraId}/`;
    var updateModal = document.getElementById('update-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        var form = document.querySelector('#update-form');
        form.elements.name.value = data.name;
        form.elements.short_name.value = data.short_name;
        if (data.faculty) {
            $('.ui.dropdown').dropdown('set selected', data.faculty.id);
        };

        var updateButton = document.getElementById('update-btn');
        updateButton.dataset.cathedraId = cathedraId;

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

function updateCathedra() {
    var button = document.getElementById("update-btn");
    var cathedraId = button.getAttribute("data-cathedra-id");
    var url = window.location.origin + `/api/v1/cathedras/${cathedraId}/update_cathedra/`;
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
            fetchCathedrasDataAndPopulate(hasGroup);
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

function showDeleteCathedra(cathedraId) {
    const url = window.location.origin + `/api/v1/cathedras/${cathedraId}/`;
    var deleteModal = document.getElementById('delete-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        document.querySelector('#del-name').textContent = data.name;
        if (data.faculty) {
            document.querySelector('#del-fac').textContent = data.faculty.name;
        } else {
            document.querySelector('#del-fac').textContent = "-";
        };

        var deleteButton = document.getElementById('delete-btn');
        deleteButton.dataset.cathedraId = cathedraId;

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

function deleteCathedra() {
    var button = document.getElementById("delete-btn");
    var cathedraId = button.getAttribute("data-cathedra-id");
    var url = window.location.origin + `/api/v1/cathedras/${cathedraId}/delete_cathedra/`;
    var deleteModal = document.getElementById('delete-modal');

    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
    .then(response => {
        if (response.ok) {
            fetchCathedrasDataAndPopulate(hasGroup);
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

// функция импорта кафедр
function importCathedras() {
    const url = window.location.origin + "/api/v1/import/cathedras/";
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
        console.log(response);
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Network response was not ok.');
        };
    })
    .then(function(data) {
        var success = data.data[0].success;
        if (!success) {
            $('#import-cathedras').modal('hide');
            
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
            $('#import-cathedras').modal('hide');
            fetchCathedrasDataAndPopulate(hasGroup);
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
 