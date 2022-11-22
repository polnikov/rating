## University Student Achievement Ranking

[![CodeQL](https://github.com/polnikov/rating/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/polnikov/rating/actions/workflows/codeql-analysis.yml)
[![Deploying changes](https://github.com/polnikov/rating/actions/workflows/Deploying%20changes.yml/badge.svg?event=push)](https://github.com/polnikov/rating/actions/workflows/Deploying%20changes.yml)

The rating is based on the educational trajectory of students [SPSUACE](https://spbgasu.ru).

### **Main functions:**
- creation of faculties, cathedras, study groups
- creation of the student and his basic training props
- creation of a discipline with its characteristics (form of control, teacher, etc.)
- assignment of disciplines to groups in each of the semesters in accordance with the curriculum
- statistics on the contingent (number, stipend, etc.)
- transfer of students in courses
- formation of a list of students for the appointment of scholarships based on the results of the academic semester
- formation of lists of academic debts (by students and disciplines)
- calculation of the student's average score by semester and general
- import of data from a CSV file (cathedras, students, disciplines, assignments of disciplines, statements from 1c with grades)


### **Presets via admin site:**
- creation of training foundations (budget, contract, etc.)
- creation of semesters

### **Main stack:**
- Python 3.10.6
- Django 3.2.16
- Django Rest Framework 3.2.14
- PostgreSQL

### **Django package's:**
- [django-better-admin-arrayfield](https://github.com/gradam/django-better-admin-arrayfield)
- [django-currentuser](https://github.com/PaesslerAG/django-currentuser)
- [django-import-export](https://github.com/django-import-export/django-import-export)
- [django-semanticui-forms](https://github.com/michaelmob/django-semanticui-forms)
- [django-stronghold](https://github.com/mgrouchy/django-stronghold)

### **Project Model's Diagram**
![Project Diagram](/docs/img/Project_Diagram.jpg)
