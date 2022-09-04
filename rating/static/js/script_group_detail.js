/* Document *****************************************************************************************************/
$(document).ready(function() {

   const groupName = document.getElementById('groupname').textContent;
   const semester = document.getElementById('semester').textContent;
   const url = "http://127.0.0.1:8000/groups/json/groupmarks"

   // запрос в БД на получение данных о студентах: оценки, задолженности, стипендия
   function getFromServer(groupName, semester) {
      $.ajax({
         url: url,
         type: "GET",
         dataType: "JSON",
         contentType: "application/json",
         data: {
            groupname: groupName,
            semester: semester,
            csrfmiddlewaretoken: csrftoken,
         },
      })
      .done(function(response) {
         console.log('Запрос данных выполнен успешно');

         let startNodes = document.getElementsByName('student');  // узлы, после которых вставляем массив оценок
         let ind = 0;  // индекс, для перемещения по стартовым узлам
         response.data.forEach(e => {

            // готовим массив оценок
            let result = [];
            result.push(
               `<td id="money" data-student-id="${e.studentId}" class="collapsing center aligned" style="width: 30px">${e.money}</td>
               <td id="att1" data-student-id="${e.studentId}" class="collapsing center aligned">${e.att1}</div></td>
               <td id="att2" data-student-id="${e.studentId}" class="collapsing center aligned">${e.att2}</div></td>
               <td id="att3" data-student-id="${e.studentId}" class="collapsing center aligned">${e.att3}</div></td>`
            );
            for (let value of Object.values(e.marks)) {
               for (let [k, v] of Object.entries(value)) {
                  let marksValue = v[3];

                  // проверяем тип оценки, если оценок по предмету еще нет, то это строка, если массив = распаковываем его
                  if(typeof marksValue !== "string") {
                     marksValue = marksValue.join(" ");
                  };

                  result.push(
                     `<td name="marks" class="collapsing center aligned editable"
                     data-result-id="${v[2]}"
                     data-student-id="${e.studentId}"
                     data-group-subject-id="${k}"
                     data-subject-form-control="${v[1]}"
                     data-type="mark">${marksValue}</td>`
                  );
               };
            };
            // вставляем массив оценок на страницу
            startNodes[ind].insertAdjacentHTML('afterend', result.join(""));
            ind++;  // смещаем индекс
         });
         // подсветка ячеек со стипендией
         let moneyCells = document.querySelectorAll("#money");
         moneyCells.forEach(e => {
            if(e.textContent === "нет") {
               e.classList.add("negative");
            } else {e.classList.remove("negative")};
         });
         // подсветка задолженностей
         const greyLabel = [];
         greyLabel.push.apply(greyLabel, document.querySelectorAll("#att1"));
         greyLabel.push.apply(greyLabel, document.querySelectorAll("#att2"));
         for (let i = 0; i < greyLabel.length; i++) {
            let value = greyLabel[i].textContent;
            if (value > 0) {
               greyLabel[i].textContent = "";
               let elem = (`<div id="att-label" class="ui grey mini label">${value}</div>`);
               greyLabel[i].insertAdjacentHTML("afterBegin", elem);
            };
         };
         let redLabel = document.querySelectorAll("#att3");
         redLabel.forEach(e => {
            let value = e.textContent;
            if (value > 0) {
               e.textContent = "";
               let elem = (`<div id="att-label" class="ui red mini label">${value}</div>`);
               e.insertAdjacentHTML("afterBegin", elem);
            };
         });
      })
      .fail(function() {
         console.log("Ошибка данных!");
         alert("Данные недоступны!")
      });
   };
   getFromServer(groupName, semester);

   // убрать верхний и нижний отступ ячеек с формой контроля
   let formElements = document.querySelectorAll("thead > tr + tr > th");
   formElements.forEach(element => {
      element.style.paddingTop = '0';
      element.style.paddingBottom = '0';
   });

   // отслеживание двойного клика по ячейке
   $(document).on("dblclick",  ".editable", function() {
      // извлечение текущего значения в глобальную переменную
      window.oldValue = $(this).text();
      // добавление в текущую ячейку поля <input> и вставка текущего значения в него
      let input = '<input type="text" class="input-data" value="'+ window.oldValue +'" class="form-control" style="width: 100px; text-align: center">';
      $(this).html(input);
      // удаление возможности редактирования пока ячейка активна
      $(this).removeClass("editable");
      // устанавливаем курсор в активный <input>
      $(this).children().focus();
   });

   // отслеживание клика вне поля <input>
   $(document).on("blur", ".input-data", function() {
      // определяем ячейку в которой активный <input>
      let td = $(this).parent("td");
      // удаляем <input>
      $(this).remove();
      // возвращаем старое значение в ячейку
      td.html(window.oldValue);
      // возвращаем ячейке класс редактирования
      td.addClass("editable");
   });

   // отслеживание нажатия клавиши <enter>
   $(document).on("keypress", ".input-data", function(e) {
      let key = e.which;
      if(key == 13) {
         window.newValue = $(this).val().trim();
         let td = $(this).parent("td");
         $(this).remove();
         td.html(window.newValue);
         td.addClass("editable");

         // извлечение данных из редактируемой ячейки
         let resId = td[0].dataset.resultId,
         studentId = td.data("student-id"),
         groupSubId = td.data("group-subject-id"),
         form = td.data("subject-form-control");

         if(!(resId == "-")) {
            // валидация вводимых оценок
            let validate = validateMark(window.newValue, form);
            // если валидация прошла успешно - отправляем данные в БД на сохранение/обновление
            if(validate) {
               sendToServer(resId, studentId, groupSubId, form, window.newValue, td);
            } else {
               td.html(window.oldValue.trim());
               // отправляется сообщение о неверном формате оценки и перезагружается страница для сброса введенного значения
               alert("Неверный формат оценки!");
            };
         } else {
            // валидация вводимых оценок
            let validate = validateMark(window.newValue, form);
            // если валидация прошла успешно - отправляем данные в БД на сохранение/обновление
            if(validate) {
               sendToServer(resId, studentId, groupSubId, form, window.newValue, td);
            } else {
               td.html(window.oldValue.trim());
               // отправляется сообщение о неверном формате оценки и перезагружается страница для сброса введенного значения
               alert("Неверный формат оценки!");
            };
         };
      };
   });

   // функция отправки данных об оценках в БД
   function sendToServer(resId, studentId, groupSubId, form, value, obj) {
      $.ajax({
         url: url,
         type: "POST",
         data: {
            resId: resId,
            studentId: studentId,
            groupSubId: groupSubId,
            form: form,
            value: value,
            groupName: groupName,
            semester: semester,
            csrfmiddlewaretoken: csrftoken,
         },
      })
      .done(function(response) {
         console.log('Успешное сохранение/обновление');
         obj[0].dataset.resultId = response.newResId;
         const dataForUpdate = [response.money, response.att1, response.att2, response.att3,];
         document.querySelector(`#money[data-student-id="${studentId}"]`).textContent = dataForUpdate[0];
         document.querySelector(`#att1[data-student-id="${studentId}"]`).textContent = dataForUpdate[1];
         document.querySelector(`#att2[data-student-id="${studentId}"]`).textContent = dataForUpdate[2];
         document.querySelector(`#att3[data-student-id="${studentId}"]`).textContent = dataForUpdate[3];
         // смена подсветки ячейки со стипендией в зависимости от новой оценки
         let moneyCell = document.querySelector(`#money[data-student-id='${studentId}']`)
         if(moneyCell.textContent === "нет") {
            moneyCell.classList.add("negative")
         } else {moneyCell.classList.remove("negative")};
         // добавление лейбла к задолженности в зависимости от новой оценки
         const attCells = [];
         attCells.push(document.querySelectorAll(`#att1[data-student-id='${studentId}']`)[0]);
         attCells.push(document.querySelectorAll(`#att2[data-student-id='${studentId}']`)[0]);
         attCells.push(document.querySelectorAll(`#att3[data-student-id='${studentId}']`)[0]);
         for (let i = 0; i < attCells.length; i++) {
            if(['att1', 'att2'].includes(attCells[i].id)) {
               let value = attCells[i].textContent;
               if (value > 0) {
                  attCells[i].textContent = "";
                  let elem = (`<div id="att-label" class="ui grey mini label">${value}</div>`);
                  attCells[i].insertAdjacentHTML("afterBegin", elem);
               };
            } else {
               let value = attCells[i].textContent;
               if (value > 0) {
                  attCells[i].textContent = "";
                  let elem = (`<div id="att-label" class="ui red mini label">${value}</div>`);
                  attCells[i].insertAdjacentHTML("afterBegin", elem);
               };
            };
         };
      })
      .fail(function() {
         console.log("Ошибка сохранения | обновления!");
         obj.html(window.oldValue);
         alert("Ошибка сохранения | обновления!");
         //document.location.reload();
      });
   };

   // обработка checkbox для выбора всех сразу
   $(document).on('change', 'input[type=checkbox]', function () {
      let $this = $(this), $chks = $(document.getElementsByName("chk")), $all = $chks.filter(".chk-all");

      if ($this.hasClass('chk-all')) {
         $chks.prop('checked', $this.prop('checked'));
      } else switch ($chks.filter(":checked").length) {
         case +$all.prop('checked'):
            $all.prop('checked', false).prop('indeterminate', false);
            break;
         case $chks.length - !!$this.prop('checked'):
            $all.prop('checked', true).prop('indeterminate', false);
            break;
         default:
            $all.prop('indeterminate', true);
      };
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

// функция подсветки отрицательных оценок
function addHighlightMarks() {
   const negative = ['ня', 'нз', '2'];
   let markCells = document.querySelectorAll("tbody .editable");

   markCells.forEach(element => {
      let marks = element.textContent;

      if(marks != "-") {
         marks = marks.split(" ");

         let mark = marks.pop();

         if(negative.includes(mark)) {
            element.classList.add("negative");
         } else {
            if(element.classList.contains("negative")) {
               element.classList.remove("negative");
            };
         };
      };
   });
};

// функция валидации вводимых оценок
function validateMark(value, form) {
   const formControlNumeric = ['Экзамен', 'Диффзачет', 'Курсовой проект', 'Курсовая работа'];
   const setNumeric = ['ня', '2', '3', '4', '5'];
   const setLiteral = ['ня', 'нз', 'зач'];
   const negative = ['ня', 'нз', '2'];
   // устанавливаем набор допустимых оценок в зависимости от формы контроля дисциплины
   let markTypes = formControlNumeric.includes(form) ? setNumeric : setLiteral;
   // преобразуем введенные оценки в список с ограничением длины не более 3х
   let marks = value.trim().split(" ", 3);

   if(marks.length == 1 && !markTypes.includes(marks[0])) {
      return false;
   // при наличии второй оценки - первая оценка должна быть отрицательной
   } else if(marks.length == 2) {
      marks.forEach(element => {
         if(!markTypes.includes(element)) {
            return false;
         };
      });
      if(!negative.includes(marks[0])) {
         return false;
      };
   // при наличии третьей оценки - первые две оценки должны быть отрицательными
   } else if(marks.length == 3) {
      marks.forEach(element => {
         if(!markTypes.includes(element)) {
            return false;
         };
      });
      // проверяем, что первые две оценки отрицательные
      for (let i = 0; i < 2; i++) {
         if (!negative.includes(marks[i])) {
            return false;
         };
      };
   };
   return true;
};


// функция добавления checkbox для выбора студентов для перевода на следующий семестр
function openCheckboxColumn() {
   if(document.getElementById("group-detail-table")) {
      willTransferButton = document.getElementById("transfer-button");
      transferButton = document.getElementById("transfer");
      cancelButton = document.getElementById("cancel-button");

      willTransferButton.style.display = "none";
      transferButton.style.display = "inline-block";
      cancelButton.style.display = "inline-block";

      thHash = document.getElementById("hash");
      thHash.innerHTML = '<input type="checkbox" class="chk-all" name="chk">';
      // выбор всех ячеек с нумерацией студентов
      tdNums = document.getElementsByName("number");
      // замена нумарации студентов на checkbox
      tdNums.forEach(element => {
         element.style.paddingLeft = '0';
         element.style.paddingRight = '0';
         let studentId = element.dataset.studentId;
         element.innerHTML = '<input type="checkbox" class="hidden" name="chk" data-student-id="'+ studentId +'">';
      });
   };
};

// функция удаления checkbox для выбора студентов для перевода на следующий семестр
function closeCheckboxColumn() {
   willTransferButton = document.getElementById("transfer-button");
   transferButton = document.getElementById("transfer");
   cancelButton = document.getElementById("cancel-button");

   willTransferButton.style.display = "inline-block";
   transferButton.style.display = "none";
   cancelButton.style.display = "none";

   tdNChecks = document.querySelectorAll("tbody input.hidden");
   // удаление всех checkbox
   tdNChecks.forEach(element => {
      element.remove();
   });

   thHash = document.getElementById("hash");
   thHash.innerHTML = "#";
   // выбор всех ячеек с нумерацией студентов
   tdNums = document.getElementsByName("number");
   for (let i = 0; i < tdNums.length; i++) {
      tdNums[i].innerHTML = i + 1;
   };
};

// функция отправки данных о переводе в БД
function transferStudents() {
   let checkedStudents = [];
   tdNChecks = document.querySelectorAll("tbody input.hidden");
   tdNChecks.forEach(element => {
      if(element.checked) {
         checkedStudents.push(element.dataset.studentId);
      };
   });
   console.log(checkedStudents.length);

   if(checkedStudents != 0) {
      $.ajax({
         url: "http://127.0.0.1:8000/students/transfer",
         type: "POST",
         data: {
            checkedStudents: checkedStudents,
            csrfmiddlewaretoken: csrftoken
         },
      })
      .done(function(response) {
         console.log('Перевод студентов прошел успешно', response);
         alert("Перевод студентов прошел успешно");
         document.location.reload();
      })
      .fail(function() {
         console.log("Ошибка перевода студентов!");
         alert("Ошибка перевода студентов!");
         //document.location.reload();
      });
   } else {closeCheckboxColumn()};
};

// добавить класс красной подсветки ячеек с основой обучения
function addHightlightBasis() {
   let negativeElements  = document.getElementsByName("has-negative");
   for (let i = 0; i < negativeElements.length; i++) {
      if (negativeElements[i].textContent == "К") {
         negativeElements[i].classList.add("negative")
      };
   };
};

// добавить цвет для ячеек Сессия/Пересдача/Комиссия
function addColorForAttCells() {
   let att = document.getElementsByName("att");
   att.forEach(element => {
      if (element.children[0].textContent == "Сессия") {
         element.style.background = '#fcfff5';
      } else if (element.children[0].textContent == "Пересдача") {
         element.style.background = '#fffaf3';
      } else {
         element.style.background = '#fff6f6';
      };
   });
};

/* Observer ***********************************************************************************************************/

// отслеживание изменения оценок для стилизации
if(document.getElementById("group-detail-table")) {
   let target = document.querySelector("#groupmarks");
   const mutationListener = (mutations) => {
      for (let mutation of mutations) {
         if (mutation.type === "childList"){
            addHighlightMarks();
         };
      };
   };
   let observer = new MutationObserver(mutationListener);
   observer.observe(target, {childList: true, characterData: true, subtree: true});
};
