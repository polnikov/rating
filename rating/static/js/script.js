/* <script type="text/javascript" src="{% static 'js\script.js' %}"></script> */

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

// убрать нижний отступ сегмента с заголовком и кнопками
function deletePaddingTopBottomForTitleBlock() {
   let segments = document.getElementById("segments");
   segments.style.paddingTop = '0';
   segments.style.paddingBottom = '0';
};

// убрать верхний отступ сегмента с таблицей
function deletePaddingTopForDatatableSegment() {
   let datatableSegment = document.getElementById("datatable-segment");
   datatableSegment.style.paddingTop = '0';
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
