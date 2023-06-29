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
fetchGroupsDataAndPopulate(hasGroup);

function fetchGroupsDataAndPopulate(hasGroup) {
    let url;
    if (location.href.includes('archive')) {
        url = window.location.origin + "/api/v1/groups/?is_archived=true";
    } else {
        url = window.location.origin + "/api/v1/groups/";
    };
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const table = $('#groups-table').DataTable();
            table.clear();

            data.forEach((group, index) => {
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
            $.toast({
                class: 'error center aligned',
                position: 'centered',
                message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
            });
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

function showUpdateGroup(groupId) {
    let url;
    if (location.href.includes('archive')) {
        url = window.location.origin + `/api/v1/groups/${groupId}/?is_archived=true`;
    } else {
        url = window.location.origin + `/api/v1/groups/${groupId}/`;
    }
    var updateGroupModal = document.getElementById('group-update-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        var form = document.querySelector('#group-update-form').elements;
        form.name.value = data.name;
        form.direction.value = data.direction;
        form.profile.value = data.profile;
        form.level.value = data.level;
        form.code.value = data.code;
        form.is_archived.checked = data.is_archived;

        var updateButton = document.getElementById('edit-button');
        updateButton.dataset.groupId = groupId;

        $(updateGroupModal).modal({blurring: true}).modal('show');
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

function updateGroup() {
    var button = document.getElementById("edit-button");
    var groupId = button.getAttribute("data-group-id");
    var url = window.location.origin + `/api/v1/groups/${groupId}/update_group/`;
    var updateModal = document.getElementById('group-update-modal');
    var form = document.querySelector('#group-update-form');
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

function showDeleteGroup(groupId) {
    let url;
    if (location.href.includes('archive')) {
        url = window.location.origin + `/api/v1/groups/${groupId}/?is_archived=true`;
    } else {
        url = window.location.origin + `/api/v1/groups/${groupId}/`;
    }
    var deleteModal = document.getElementById('group-delete-modal');
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        document.querySelector('#del-name').textContent = data.name;
        document.querySelector('#del-direction').textContent = data.direction;
        document.querySelector('#del-profile').textContent = data.profile;
        document.querySelector('#del-level').textContent = data.level;
        document.querySelector('#del-code').textContent = data.code;

        var deleteButton = document.getElementById('trash-button');
        deleteButton.dataset.groupId = groupId;

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

function deleteGroup() {
    var button = document.getElementById("trash-button");
    var groupId = button.getAttribute("data-group-id");
    var url = window.location.origin + `/api/v1/groups/${groupId}/delete_group/`;
    var deleteGroupModal = document.getElementById('group-delete-modal');

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
            $.toast({
                class: 'success center aligned',
                position: 'centered',
                message: '<i class="checkmark icon"></i> Удалено!'
            });
        };
    })
    .catch(error => {
        console.error(error);
        $(updateGroupModal).modal({blurring: true}).modal('hide');
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Упс! Похоже что-то пошло не так....попробуйте попозже снова.'
        });
    });
};
