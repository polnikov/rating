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
    const url = window.location.origin + "/students/json/rating";
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

        // определяем тело таблицы для вставки строк
        let tableBody =  document.querySelector("table[id='students-rating'] tbody");
        response.data.forEach(e => {

            // готовим массив строк
            let isIll = e.isIll, tag = e.tag;
            let result = [];
            if(isIll & tag != 0) {
                var line1 = `<td id="${e.studentId}"name="student" class="collapsing" onclick="getAbsoluteURL(${e.studentId})"><i class="heart broken red icon"></i> <a>${e.fullname}</a> <div id="tag-label" class="ui tiny pink label">${e.tag}</div></td>`
            } else if(isIll) {
                var line1 = `<td id="${e.studentId}"name="student" class="collapsing" onclick="getAbsoluteURL(${e.studentId})"><i class="heart broken red icon"></i> <a>${e.fullname}</a></td>`
            } else if(tag != 0) {
                var line1 = `<td id="${e.studentId}"name="student" class="collapsing" onclick="getAbsoluteURL(${e.studentId})"><a>${e.fullname}</a> <div id="tag-label" class="ui tiny pink label">${e.tag}</div></td>`
            } else {
                var line1 = `<td id="${e.studentId}"name="student" class="collapsing" onclick="getAbsoluteURL(${e.studentId})"><a>${e.fullname}</a></td>`
            };
            
            result.push(
                `<tr>
                    ${line1}
                    <td class="collapsing center aligned">${e.group}</td>
                    <td class="collapsing center aligned">${e.currentSemester}</td>
                    <td name="has-negative" class="collapsing center aligned">${e.basis}</td>
                    <td class="collapsing center aligned">${e.level}</td>
                    <td class="collapsing center aligned">${e.rating}</td>
                </tr>`
            );
            // вставляем массив в таблицу
            tableBody.insertAdjacentHTML('afterbegin', result.join(""));
        });
    })
    .fail(function() {
    alert("Данные недоступны!")
    });
};

//  функция формирования ссылки на студента
function getAbsoluteURL(id) {
    let baseURL = window.location.origin;
    let pathName = window.location.pathname.split("/")[1];
    let url = `${baseURL}/${pathName}/${id}`;
    let a = document.querySelector(`[id='${id}'] a`);
    a.href = url;
    return a.href
};

// функция удаления содержимого таблицы
function deleteTableData() {
    let tableData =  document.querySelectorAll("table[id='students-rating'] tbody > tr");
    tableData.forEach(e => {
        e.remove();
    })
};

// убрать нижний отступ сегмента с заголовком и кнопками
function deletePaddingTopBottomForMenuSegment() {
    let segments = document.getElementById("menu-segment");
    segments.style.paddingTop = '0';
    segments.style.paddingBottom = '0';
 };
 

