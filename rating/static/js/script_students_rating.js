/* Document *****************************************************************************************************/
$(document).ready(function() {
    var semStart = document.querySelector("input[name='semester-start']").value;
    var semStop = document.querySelector("input[name='semester-stop']").value;

    // ограничиваем возможность выбора конечного семестра без стартового
    let stopValueList = document.querySelectorAll("#semester-stop-menu div");
    // отключаем видимость семестров меньших стартового
    stopValueList.forEach(e => {
        if(semStart == "" & e.textContent != "-") {
            e.style.display = 'none';
        } else {
            e.style.removeProperty('display');
        };
    });
    
    const url = window.location.origin + "/students/json/rating";

    // запрос в БД на получение данных о среднем балле студентов за указанный семестр
    function getDataFromServer(semStart, semStop) {
        $.ajax({
        url: url,
        type: "GET",
        dataType: "JSON",
        contentType: "application/json",
        data: {
            semStart: semStart,
            semStop: semStop,
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
                    var line1 = `<td id="${e.studentId}"name="student" class="collapsing" onclick="getAbsoluteURL(${e.studentId})"><i class="heart broken red icon"></i> <a>${e.fullname}</a> <div class="ui tiny pink label">${e.tag}</div></td>`
                } else if(isIll) {
                    var line1 = `<td id="${e.studentId}"name="student" class="collapsing" onclick="getAbsoluteURL(${e.studentId})"><i class="heart broken red icon"></i> <a>${e.fullname}</a></td>`
                } else if(tag != 0) {
                    var line1 = `<td id="${e.studentId}"name="student" class="collapsing" onclick="getAbsoluteURL(${e.studentId})"><a>${e.fullname}</a> <div class="ui tiny pink label">${e.tag}</div></td>`
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
    getDataFromServer(semStart, semStop);

    // отслеживаем изменение стартового семестра
    $(document).on("change", "input[name='semester-start']", function() {
        // определяем стартовый семестр
        let startValue = document.querySelector("input[name='semester-start']").value;

        // ограничиваем выбор конечного семестра во втором списке в зависимости от стартового семестра
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
        let stopValue = document.querySelector("input[name='semester-stop']").value;
        // проверяем, что конечный семестр не выбран
        if(!stopValue | stopValue == "-") {
            deleteTableData();
            getDataFromServer(startValue);
        } else if(stopValue & stopValue) {
            deleteTableData();
            getDataFromServer(startValue, stopValue);
        };
    });

    // отслеживаем изменение конечного семестра
    $(document).on("change", "input[name='semester-stop']", function() {
        let startValue = document.querySelector("input[name='semester-start']").value;
        let stopValue = document.querySelector("input[name='semester-stop']").value;
        deleteTableData();
        getDataFromServer(startValue, stopValue);
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
