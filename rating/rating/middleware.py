import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.contrib import messages

from students.models import Student


class ShowMessageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # список болеющих студентов
        sick_students = []
        students = Student.active_objects.select_related('group', 'semester').filter(comment__icontains='болеет')
        for st in students:
            pattern_sick = r'Болеет:([0-9]{2})\.([0-9]{2})\.([0-9]{4})'  # Болеет:DD.MM.YYYY
            try:
                comment = st.comment
                sick_date_string = re.search(pattern_sick, comment).group(0).split(':')[-1]
                st.sick_date = datetime.strptime(sick_date_string, '%d.%m.%Y').date()
                sick_students.append(st)
            except AttributeError:
                if 'болеет' in st.comment.lower():
                    sick_students.append(st)

        # список студентов для выхода из АО
        students_for_return = []
        delay_students = Student.archived_objects.select_related('group', 'semester').filter(status='Академический отпуск')
        for st in delay_students:
            pattern_delay = r'АО:([0-9]{2})\.([0-9]{2})\.([0-9]{4})'  # АО:DD.MM.YYYY
            try:
                comment = st.comment
                delay_start_date_string = re.search(pattern_delay, comment).group(0).split(':')[-1]
                delay_start_date = datetime.strptime(delay_start_date_string, '%d.%m.%Y').date()
                delay_end_date = delay_start_date + relativedelta(months=12)
                delta_days = (delay_end_date - datetime.now().date()).days
                if delta_days <= 30:
                    st.delta_days = delta_days
                    students_for_return.append(st)
            except AttributeError:
                delta_days = 0
                st.delta_days = delta_days
                students_for_return.append(st)

        if not request.session.get('message_shown', False):
            if sick_students:
                message_text = '<div class="ui large label"><i class="heart broken red icon"></i> Следующие студенты всё еще болеют</div>\n'
                messages.info(request, message_text)
                message_text = '<div class="ui fitted divider"></div>'
                messages.info(request, message_text)
                for st in sick_students:
                    message_text = f'{st.fullname} | {st.group.name}-{st.semester}\n'
                    messages.info(request, message_text)

            if students_for_return:
                students_for_return = sorted(students_for_return, key=lambda o: (o.delta_days))
                message_text = '<div class="ui large label"><i class="hourglass blue icon"></i> Следующие студенты скоро выходят из АО</div>\n'
                messages.warning(request, message_text)
                message_text = '<div class="ui fitted divider"></div>'
                messages.info(request, message_text)
                for st in students_for_return:
                    delta_days = f'<a class="ui circular red label">{st.delta_days}</a>' if st.delta_days > 0 else '<i class="times red large icon"></i>'
                    message_text = f'{st.fullname} | {st.group.name}-{st.semester} | До выхода: {delta_days}\n'
                    messages.warning(request, message_text)

            request.session['message_shown'] = True

        response = self.get_response(request)
        return response
