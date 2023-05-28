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
fetchGroupsDataAndPopulate(hasGroup);

function fetchGroupsDataAndPopulate(hasGroup) {
    let url;
    if (location.href.includes('archive')) {
        url = window.location.origin + "/api/v1/groups/?is_archived=true";
    } else {
        url = window.location.origin + "/api/v1/groups/";
    }

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#groups-table').DataTable();
            table.clear();

            data.forEach((group, index) => {
                console.log(hasGroup);
                let defFunc, updFunc;
                if (hasGroup === 'True') {
                    defFunc = `onclick="showDeleteGroup(${group.id})"`;
                    updFunc = `onclick="showUpdateGroup(${group.id})"`;
                } else {
                    defFunc = '';
                    updFunc = '';
                };
                let rowData = [
                    index + 1,
                    group.name,
                    group.level,
                    group.direction,
                    group.profile,
                    group.code,
                    `<button id="trash-button" ${defFunc} class="circular ui red mini icon button"><i class="trash alternate outline icon"></i></button>`,
                    `<button id="edit-button" ${updFunc} class="circular ui blue mini icon button"><i class="edit icon"></i></button>`,
                ];
                table.row.add(rowData);
            });
            table.draw();
        })
        .catch(error => {
            console.error(error);
            alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
        });
};

function saveGroupForm() {
    var url = window.location.origin + `/api/v1/groups/create_group/`;
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
            fetchGroupsDataAndPopulate(hasGroup);
            $(addModal).modal({blurring: true}).modal('hide');
            resetAddForm();
            $('#success')
                .transition({
                    animation: 'slide',
                    duration: 1000,
                })
            ;
            setTimeout(function() {
                $('#success')
                    .transition({
                        animation: 'slide',
                        duration: 1000,
                    })
                ;
            }, 1500);
        };
    })
    .catch(error => {
        console.error(error);
        alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
        $(addModal).modal({blurring: true}).modal('hide');
    });
};

function showUpdateGroup(groupId) {
    let url;
    if (location.href.includes('archive')) {
        url = window.location.origin + `/api/v1/groups/${groupId}/?is_archived=true`;
    } else {
        url = window.location.origin + `/api/v1/groups/${groupId}/`;
    }
    var updateGroupModal = document.getElementById('update-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        var form = document.querySelector('#update-form');
        form.elements.name.value = data.name;
        form.elements.direction.value = data.direction;
        form.elements.profile.value = data.profile;
        form.elements.level.value = data.level;
        form.elements.code.value = data.code;
        form.elements.is_archived.checked = data.is_archived;

        var updateButton = document.getElementById('update-btn');
        updateButton.dataset.groupId = groupId;

        $(updateGroupModal).modal({blurring: true}).modal('show');
    })
    .catch(error => {
        console.error(error);
        alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
    });
};

function updateGroup() {
    var button = document.getElementById("update-btn");
    var groupId = button.getAttribute("data-group-id");
    var url = window.location.origin + `/api/v1/groups/${groupId}/update_group/`;
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
            fetchGroupsDataAndPopulate(hasGroup);
            $(updateModal).modal({blurring: true}).modal('hide');
            $('#success')
                .transition({
                    animation: 'slide',
                    duration: 1000,
                })
            ;
            setTimeout(function() {
                $('#success')
                    .transition({
                        animation: 'slide',
                        duration: 1000,
                    })
                ;
            }, 1500);
        };
    })
    .catch(error => {
        console.error(error);
        alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
        $(updateModal).modal({blurring: true}).modal('hide');
    });
};

function showDeleteGroup(groupId) {
    let url;
    if (location.href.includes('archive')) {
        url = window.location.origin + `/api/v1/groups/${groupId}/?is_archived=true`;
    } else {
        url = window.location.origin + `/api/v1/groups/${groupId}/`;
    }
    var deleteModal = document.getElementById('delete-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        document.querySelector('#del-name').textContent = data.name;
        document.querySelector('#del-direction').textContent = data.direction;
        document.querySelector('#del-profile').textContent = data.profile;
        document.querySelector('#del-level').textContent = data.level;
        document.querySelector('#del-code').textContent = data.code;

        var deleteButton = document.getElementById('delete-btn');
        deleteButton.dataset.groupId = groupId;

        $(deleteModal).modal({blurring: true}).modal('show');
    })
    .catch(error => {
        console.error(error);
        alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
    });
};

function deleteGroup() {
    var button = document.getElementById("delete-btn");
    var groupId = button.getAttribute("data-group-id");
    var url = window.location.origin + `/api/v1/groups/${groupId}/delete_group/`;
    var deleteGroupModal = document.getElementById('delete-modal');

    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
    .then(response => {
        if (response.ok) {
            fetchGroupsDataAndPopulate(hasGroup);
            $(deleteGroupModal).modal({blurring: true}).modal('hide');
            $('#success')
                .transition({
                    animation: 'slide',
                    duration: 1000,
                })
            ;
            setTimeout(function() {
                $('#success')
                    .transition({
                        animation: 'slide',
                        duration: 1000,
                    })
                ;
            }, 1500);
        };
    })
    .catch(error => {
        console.error(error);
        alert('Упс! Похоже что-то пошло не так....попробуйте попозже снова.');
        $(updateGroupModal).modal({blurring: true}).modal('hide');
    });
};