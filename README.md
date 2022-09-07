## Рейтинг успеваемости студентов университета

Рейтинг сформирован на базе учебной траектории студентов [СПбГАСУ](https://spbgasu.ru).

### **Основной функционал:**
- создание факультетов, кафедр, учебных групп
- создание студента и его основных учебных реквизитов
- создание дисциплины с её характеристиками (форма контроля, преподаватель и прочие)
- назначение группам дисциплин в каждом из семестров в соответствии с учебным планом
- статистика по контингенту (численность, стипендия и прочие)
- формирование списка студентов для назначения стипендии по результатам учебного семестра
- формирование списков академических задолженностей (по студентам и дисциплинам)
- вычисление среднего балла студента по семестрам и общего
- импорт данных из CSV файла (кафедры, студенты, дисциплины, назначения дисциплин)

### **Предварительные настройки через панель администратора:**
- создание основ обучения (Бюджет, Контракт и прочие)
- создание семестров

### **Основной стек:**
- Python 3.10.6
- Django 2.2.12
- PostgreSQL

### **Django package's:**
- [django-better-admin-arrayfield](https://github.com/gradam/django-better-admin-arrayfield)
- [django-currentuser](https://github.com/PaesslerAG/django-currentuser)
- [django-dynamic-breadcrumbs](https://github.com/marcanuy/django-dynamic-breadcrumbs)
- [django-import-export](https://github.com/django-import-export/django-import-export)
- [django-semanticui-forms](https://github.com/michaelmob/django-semanticui-forms)
- [django-stronghold](https://github.com/mgrouchy/django-stronghold)

### **Project Model's Diagram**
![Project Diagram](/docs/img/Project_Diagram.jpg)
