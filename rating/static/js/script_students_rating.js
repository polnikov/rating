/* Document *****************************************************************************************************/
$(document).ready(function() {
    var semStart = document.querySelector("input[name='semester-start']").value;
    var semStop = document.querySelector("input[name='semester-stop']").value;
    var groups = $("#groups :selected").map((_, e) => e.textContent).get();

    // ограничиваем возможность выбора конечного семестра без стартового
    var stopSemesterDropdown = document.getElementById("semester-stop");
    if(semStart != "") {
        stopSemesterDropdown.classList.remove("disabled");
    } else {
        stopSemesterDropdown.classList.add("disabled");
    };
    // получаем первоначальные дефолтные данные
    getDataFromServer(semStart, semStop, groups);

    // отслеживаем изменение стартового семестра
    $(document).on("change", "input[name='semester-start']", function() {
        // определяем стартовый семестр
        var startValue = document.querySelector("input[name='semester-start']").value;

        // ограничиваем выбор конечного семестра в зависимости от стартового семестра
        if(startValue != "") {stopSemesterDropdown.classList.remove("disabled");};
        let stopValueList = document.querySelectorAll("#semester-stop-menu div");
        // отключаем видимость семестров меньше стартового
        stopValueList.forEach(e => {
            if(e.textContent <= startValue & e.textContent != "-") {
                e.style.display = 'none';
            } else {
                e.style.removeProperty('display');
            };
        });

        // определяем конечный семестр
        var stopValue = document.querySelector("input[name='semester-stop']").value;
        // определяем выбранные группы
        var groups = $("#groups :selected").map((_, e) => e.textContent).get();
        deleteTableData();
        getDataFromServer(startValue, stopValue, groups);
    });

    // отслеживаем изменение конечного семестра
    $(document).on("change", "input[name='semester-stop']", function() {
        // определяем стартовый и конечный семестры
        var startValue = document.querySelector("input[name='semester-start']").value;
        var stopValue = document.querySelector("input[name='semester-stop']").value;
        // определяем выбранные группы
        var groups = $("#groups :selected").map((_, e) => e.textContent).get();
        deleteTableData();
        getDataFromServer(startValue, stopValue, groups);
    });

    // отслеживаем изменение выбранных групп
    $(document).on("change", ".ui.fluid.clearable.multiple.selection.dropdown", function() {
        // определяем стартовый и конечный семестры
        var startValue = document.querySelector("input[name='semester-start']").value;
        var stopValue = document.querySelector("input[name='semester-stop']").value;
        // определяем группы
        var groups = $("#groups :selected").map((_, e) => e.textContent).get();
        deleteTableData();
        getDataFromServer(startValue, stopValue, groups);
    });
});

/* Functions **********************************************************************************************************/

// csrftoken
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
       var cookies = document.cookie.split(';');
       for (var i = 0; i < cookies.length; i++) {
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

// запрос в БД на получение данных о среднем балле студентов за указанный семестр
function getDataFromServer(semStart, semStop, groups) {
    $('#datatable-segment').dimmer({
        displayLoader: true,
        loaderVariation: 'slow orange medium elastic',
        loaderText: 'Загрузка данных...'
    }).dimmer('show');

    const url = window.location.origin + "/students/json/rating/";
    $.ajax({
        url: url,
        type: "GET",
        dataType: "JSON",
        contentType: "application/json",
        data: {
            semStart: semStart,
            semStop: semStop,
            groups: groups,
            csrfmiddlewaretoken: csrftoken,
        },
    })
    .done(function(response) {
        console.log('Запрос данных выполнен успешно');
        const table = $('#students-rating').DataTable();
        table.clear();

        response.data.forEach(e => {
            let isIll = e.isIll, tag = e.tag;
            if(isIll & tag != 0) {
                var line1 = `<div id="${e.studentId}"name="student" onclick="getAbsoluteURL(${e.studentId})"><i class="heart broken red icon"></i> <a>${e.fullname}</a> <div id="tag-label" class="ui tiny pink label">${e.tag}</div></div>`
            } else if(isIll) {
                var line1 = `<div id="${e.studentId}"name="student" onclick="getAbsoluteURL(${e.studentId})"><i class="heart broken red icon"></i> <a>${e.fullname}</a></div>`
            } else if(tag != 0) {
                var line1 = `<div id="${e.studentId}"name="student" onclick="getAbsoluteURL(${e.studentId})"><a>${e.fullname}</a> <div id="tag-label" class="ui tiny pink label">${e.tag}</div></div>`
            } else {
                var line1 = `<div id="${e.studentId}"name="student" onclick="getAbsoluteURL(${e.studentId})"><a>${e.fullname}</a></div>`
            };
            let rowData = [
                line1,
                e.group,
                e.currentSemester,
                e.basis,
                e.level,
                e.rating,
            ];
            table.row.add(rowData);
        });
        table.draw();
        $('#datatable-segment').dimmer('hide');
    })
    .fail(function() {
        $('#datatable-segment').dimmer('hide');
        $.toast({
            class: 'error center aligned',
            position: 'centered',
            message: '<i class="exclamation circle large icon"></i> Данные недоступны!'
        });
    });
};

// функция удаления содержимого таблицы
function deleteTableData() {
    let tableData =  document.querySelectorAll("table[id='students-rating'] tbody > tr");
    tableData.forEach(e => {
        e.remove();
    })
};

// убрать верхний и нижний отступы сегмента с фильтрами
function deletePaddingTopBottomForFilterSegment() {
    let segment = document.getElementById("filter-segment");
    segment.style.paddingTop = '0';
    segment.style.paddingBottom = '0';
 };
 
 // убрать нижний отступ сегмента с заголовком
 function deletePaddingTopBottomForTitleSegment() {
    let segment = document.getElementById("title-segment");
    segment.style.paddingBottom = '0';
};

