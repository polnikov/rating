var segments = document.getElementById("segments");
if (segments) {
   segments.style.marginTop = '14px'
};

// изменить шрифт в поле <input> в формах
function changeFormsInputFont() {
   let formElements = document.forms.form.elements;
   for (let i = 0; i < formElements.length; i++) {
      if (formElements[i].localName == "input" && formElements[i].type == "text") {
         formElements[i].style.fontFamily = "Hack"
      }
   };
};

// изменить шрифт в полях <input> datatable's
function changeDatatableInputFont() {
   let dataInputs = document.querySelectorAll(".ui.segment input");
   for (let i = 0; i < dataInputs.length; i++) {
      dataInputs[i].style.fontFamily = "Hack";
   };
};

// изменить шрифт в полях <input> на вкладках (tabs)
function changeDatatableTabsInputFont() {
   let dataInputs = document.querySelectorAll(".ui.input");
   for (let i = 0; i < dataInputs.length; i++) {
      dataInputs[i].style.fontFamily = "Hack";
   };
};

// изменить шрифт в <input> загрузки CSV
function changeFileInputFont() {
   let fileInput = document.querySelectorAll(".ui.segment input")[1];
   fileInput.style.fontFamily = "Hack";
};

// убрать боковой отступ ячейки таблицы
function deleteSidePadding(attr, name) {
   if(attr == "name") {
      let elements = document.getElementsByName(name);
      elements.forEach(element => {
         element.style.paddingLeft = '0';
         element.style.paddingRight = '0';
      });
   } else if(attr == "id") {
      let element = document.getElementById(name);
      element.style.paddingLeft = '0';
      element.style.paddingRight = '0';
   };
};

// убрать верхний отступ сегмента с таблицей
function deletePaddingTopForDatatableSegment() {
   let datatableSegments = document.querySelectorAll("[id='datatable-segment']");
   datatableSegments.forEach(e => {
      e.style.paddingTop = '0';
   });
};

// подсветка текущего раздела меню
function shineLinks(id) {
   let el = document.getElementById(id).getElementsByTagName("a");
   let url = document.location.href;
   for(let i = 0; i < el.length; i++) {
      if (url = el[i].href) {
         el[i].classList.add("red")
      } else {
         el[i].classList.remove("active")
      };
   };
};

// убрать нижний отступ сегмента с заголовком и кнопками
function deleteTitleBlockPaddingBottom() {
   let titleSegment = document.getElementById("segments");
   titleSegment.style.paddingBottom = '0';
};

// убрать верхний отступ сегмента с вкладками
function deleteTabsBlockPaddingBottom() {
   let tabsSegment = document.getElementById("tabs-segment");
   tabsSegment.style.paddingTop = '0';
};

// отобразить инфо по текущим занятиям
function jobTimeInfo() {

   const noLessons = '<i class="glass cheers red icon"></i> <div class="ui brown small label">Занятий нет</div>';
   const months = {
      0: "January",
      1: "February",
      2: "March",
      3: "April",
      4: "May",
      5: "June",
      6: "July",
      7: "August",
      8: "September",
      9: "October",
      10: "November",
      11: "December",
   };
   workMonths = new Array(1, 2, 3, 4, 5, 6, 8, 9, 10, 11);
   workDays = new Array(1, 2, 3, 4, 5, 6);

   // // узел вставки инфо
   var el = document.getElementById("job-time");

   // текущие дата и время
   let date = new Date();
   let currentYear = date.getFullYear();
   let currentMonth = date.getMonth();
   let currentMonthDay = date.getDate();
   let currentWeekDay = date.getDay();
	let currentHour = date.getHours();
   let currentMin = date.getMinutes();

   // 1 пара
   let lesson1Stop = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 10:30:00`);
   
   // 2 пара
   let lesson2Start = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 10:45:00`);
   let lesson2Stop = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 12:15:00`);
   
   // 3 пара
   let lesson3Start = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 12:30:00`);
   let lesson3Stop = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 14:00:00`);
   
   // 4 пара
   let lesson4Start = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 15:00:00`);
   let lesson4Stop = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 16:30:00`);
   
   // 5 пара
   let lesson5Start = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 16:45:00`);
   let lesson5Stop = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 18:15:00`);
   
   // 6 пара
   let lesson6Start = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 18:30:00`);
   let lesson6Stop = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 20:00:00`);

   // 7 пара
   let lesson7Start = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 20:15:00`);
   let lesson7Stop = new Date(`${months[currentMonth]} ${currentMonthDay}, ${currentYear}, 21:45:00`);

   // учебные месяц и день недели
   if(workMonths.includes(currentMonth) & workDays.includes(currentWeekDay)) {

      // не учебное время: с 20 до 8 часов
      if(currentHour < 8 | currentHour >= 20 ) {

         el.innerHTML = noLessons;

      } else if(currentHour == 8) { // час до начала занятий

         let waitMinutes = 60 - currentMin;
         el.innerHTML = `<div class="ui violet small label">До начала занятий осталось <div class="ui black circular small label">${waitMinutes}</div> мин.</div>`;

      } else { // учебное время

         // идёт 1 пара
         if(date < lesson1Stop) {
            getJobInfo(date, lesson1Stop, "1");

         // перерыв после 1 пары
         } else if(lesson1Stop <= date & date < lesson2Start) {
            getJobInfo(date, lesson2Start, "1 и 2");

         // идёт 2 пара
         } else if(lesson2Start <= date & date < lesson2Stop) {
            getJobInfo(date, lesson2Stop, "2");

         // перерыв после 2 пары
         } else if(lesson2Stop <= date & date < lesson3Start) {
            getJobInfo(date, lesson3Start, "2 и 3");

         // идёт 3 пара
         } else if(lesson3Start <= date & date < lesson3Stop) {
            getJobInfo(date, lesson3Stop, "3");

         // большой перерыв между 3 и 4 парами
         } else if(lesson3Stop <= date & date < lesson4Start) {
            getJobInfo(date, lesson4Start, "большой перерыв");

         // идёт 4 пара
         } else if(lesson4Start <= date & date < lesson4Stop) {
            getJobInfo(date, lesson4Stop, "4");

         // перерыв после 4 пары
         } else if(lesson4Stop <= date & date < lesson5Start) {
            getJobInfo(date, lesson5Start, "4 и 5");

         // идёт 5 пара
         } else if(lesson5Start <= date & date < lesson5Stop) {
            getJobInfo(date, lesson5Stop, "4");

         // перерыв после 5 пары
         } else if(lesson5Stop <= date & date < lesson6Start) {
            getJobInfo(date, lesson6Start, "5 и 6");

         // идёт 6 пара
         } else if(lesson6Start <= date & date < lesson6Stop) {
            getJobInfo(date, lesson6Stop, "6");
            
         // перерыв после 6 пары
         } else if(lesson6Stop <= date & date < lesson7Start) {
            getJobInfo(date, lesson7Start, "6 и 7");
            
         // идёт 7 пара
         } else if(lesson7Start <= date & date < lesson7Stop) {
            getJobInfo(date, lesson7Stop, "7");
         };
      };
   } else {el.innerHTML = noLessons;};
};

// определяет шаблон строки
function getJobInfo(date, lessonTime, num) {
   // узел вставки инфо
   var el = document.getElementById("job-time");
   // остаток времени
   let waitMinutes = Math.round((lessonTime - date) / 60000);

   if(num.length == 1) {
      el.innerHTML = `<div class="ui violet small label">Идёт <div class="ui black circular small label">${num}</div> пара. 
                     Осталось <div class="ui black circular small label">${waitMinutes}</div> мин.</div>`;
   } else if(num.length == 5){
      el.innerHTML = `<div class="ui violet small label">Перерыв между <div class="ui black circular small label">${num}</div> парами. 
                     Осталось <div class="ui black circular small label">${waitMinutes}</div> мин.</div>`;
   } else {
      el.innerHTML = `<i class="utensils green icon"></i><div class="ui violet small label">Перерыв между <div class="ui black circular small label">3 и 4</div> парами. 
                     Осталось <div class="ui black circular small label">${waitMinutes}</div> мин.</div>`;
   };
};

function resetAddForm() {
   var form = document.querySelector('#add-form');
   form.reset();
};

function showModal(modal) {
   var element = document.getElementById(modal);
   $(element).modal({blurring: true}).modal('show');
};

//  функция формирования ссылки на объект
function getAbsoluteURL(id) {
   let baseURL = window.location.origin;
   let pathName = window.location.pathname.split("/")[1];
   let url = `${baseURL}/${pathName}/${id}`;
   let hrefs = document.querySelectorAll(`[id='${id}'] a`);
   hrefs.forEach(a => {
      a.href = url;
   });
};

//  функция формирования ссылки на студента
function getAbsoluteURLforStudent(id) {
   let baseURL = window.location.origin;
   let pathName = 'students';
   let url = `${baseURL}/${pathName}/${id}`;
   let hrefs = document.querySelectorAll(`[id='${id}'] a`);
   hrefs.forEach(a => {
      a.href = url;
   });
};

//  функция формирования ссылки на студента
function getAbsoluteURLforSubject(id) {
   let baseURL = window.location.origin;
   let pathName = 'subjects';
   let url = `${baseURL}/${pathName}/${id}`;
   let hrefs = document.querySelectorAll(`[id='${id}'] a`);
   hrefs.forEach(a => {
      a.href = url;
   });
};

//  функция формирования ссылки на карточку группы
function getAbsoluteURLforGroup([id, name, semester]) {
   let baseURL = window.location.origin;
   let pathName = 'groups/cards';
   let url = `${baseURL}/${pathName}/${name}-${semester}`;
   let hrefs = document.querySelector(`[id='${id}'] a`);
   hrefs.href = url;
};

//  функция удаления лейбла сортировки в строке фильтрации
function removeSortingLabel(table) {
   var cells = document.querySelectorAll(`#${table} thead tr`)[1].children;
   for(let i = 0; i < cells.length; i++) {
      cells[i].classList.remove('sorting', 'sorting_asc')
   };
};
