import re
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView
from django.forms.models import model_to_dict

from dateutil.relativedelta import relativedelta
from students.models import Student


class DashboardView(LoginRequiredMixin, TemplateView):
    """Статистика."""
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # текущие студенты
        current_students = Student.objects.select_related('group', 'semester').filter(
            Q(status='Является студентом') | Q(status='Академический отпуск'))
        # активные студенты
        active_students = current_students.exclude(status='Академический отпуск')
        # в академическом отпуске
        delay_students = current_students.exclude(status='Является студентом')

        # количественный блок
        num_students = current_students.count()
        num_active_students = active_students.count()
        num_delay_students = num_students - num_active_students

        num_rus_students = current_students.filter(citizenship='Россия').count()
        num_for_students = num_students - num_rus_students

        num_bac_students = current_students.filter(level='Бакалавриат').count()
        num_bac_rus_students = current_students.filter(level='Бакалавриат', citizenship='Россия').count()
        num_bac_for_students = num_bac_students - num_bac_rus_students

        num_mag_students = num_students - num_bac_students
        num_mag_rus_students = current_students.filter(level='Магистратура', citizenship='Россия').count()
        num_mag_for_students = num_mag_students - num_mag_rus_students

        # блок стипендии
        no_money = active_students.filter(money='нет').count()
        num_money = num_active_students - no_money

        # общее
        num_min_money = active_students.filter(money='1.0').count()
        num_med_money = active_students.filter(money='1.25').count()
        num_max_money = active_students.filter(money='1.5').count()

        try:
            per_no_money = round(no_money / num_active_students * 100, 1)
        except ZeroDivisionError:
            per_no_money = 0

        # бакалавриат
        num_bac_active_students = active_students.filter(level='Бакалавриат').count()
        num_bac_min_money = active_students.filter(money='1.0', level='Бакалавриат').count()
        num_bac_med_money = active_students.filter(money='1.25', level='Бакалавриат').count()
        num_bac_max_money = active_students.filter(money='1.5', level='Бакалавриат').count()
        num_bac_no_money = num_bac_active_students - num_bac_min_money - num_bac_med_money - num_bac_max_money
        num_bac_money = num_bac_active_students - num_bac_no_money

        try:
            per_bac_min_money = round(num_bac_min_money / num_bac_active_students * 100, 1)
        except ZeroDivisionError:
            per_bac_min_money = 0
        try:
            per_bac_med_money = round(num_bac_med_money / num_bac_active_students * 100, 1)
        except ZeroDivisionError:
            per_bac_med_money = 0
        try:
            per_bac_max_money = round(num_bac_max_money / num_bac_active_students * 100, 1)
        except ZeroDivisionError:
            per_bac_max_money = 0
        try:
            per_bac_no_money = round(100 - per_bac_min_money - per_bac_med_money - per_bac_max_money, 2)
        except ZeroDivisionError:
            per_bac_no_money = 0

        # магистратура
        num_mag_active_students = active_students.filter(level='Магистратура').count()
        num_mag_min_money = active_students.filter(money='1.0', level='Магистратура').count()
        num_mag_med_money = active_students.filter(money='1.25', level='Магистратура').count()
        num_mag_max_money = active_students.filter(money='1.5', level='Магистратура').count()
        num_mag_no_money = num_mag_active_students - num_mag_max_money - num_mag_med_money - num_mag_min_money
        num_mag_money = num_mag_active_students - num_mag_no_money

        try:
            per_mag_min_money = round(num_mag_min_money / num_money * 100, 1)
        except ZeroDivisionError:
            per_mag_min_money = 0
        try:
            per_mag_med_money = round(num_mag_med_money / num_money * 100, 1)
        except ZeroDivisionError:
            per_mag_med_money = 0
        try:
            per_mag_max_money = round(num_mag_max_money / num_money * 100, 1)
        except ZeroDivisionError:
            per_mag_max_money = 0
        try:
            per_mag_no_money = round(100 - per_mag_min_money - per_mag_med_money - per_mag_max_money, 2)
        except ZeroDivisionError:
            per_mag_no_money = 0

        # список болеющих студентов
        sick_students = []
        for st in active_students.order_by('last_name'):
            # извлекаем дату начала болезни из комментария
            pattern_sick = r'Болеет:([0-9]{2})\.([0-9]{2})\.([0-9]{4})'  # Болеет:DD.MM.YYYY
            if 'болеет' in st.comment.lower():
                try:
                    comment = st.comment
                    sick_date_string = re.search(pattern_sick, comment).group(0).split(':')[-1]
                    st.sick_date = datetime.strptime(sick_date_string, '%d.%m.%Y').date()
                    sick_students.append(st)
                except AttributeError:
                    st.msg = 'no'
                    if 'болеет' in st.comment.lower():
                        sick_students.append(st)

        # добавляем дату выхода из АО
        for st in delay_students:
            # извлекаем дату ухода в АО из комментария
            pattern_delay = r'АО:([0-9]{2})\.([0-9]{2})\.([0-9]{4})'  # АО:DD.MM.YYYY
            try:
                comment = st.comment
                delay_start_date_string = re.search(pattern_delay, comment).group(0).split(':')[-1]
                st.delay_start_date = datetime.strptime(delay_start_date_string, '%d.%m.%Y').date()
                st.delay_end_date = st.delay_start_date + relativedelta(months=12)
                st.delta_days = (st.delay_end_date - datetime.now().date()).days
            except AttributeError:
                st.msg = 'no'
                st.delta_days = 0
        delay_students = sorted(delay_students, key=lambda o: (o.delta_days))

        # количественный блок
        context['num_students'] = num_students

        context['num_active_students'] = num_active_students
        context['num_delay_students'] = num_delay_students

        context['num_rus_students'] = num_rus_students
        context['num_for_students'] = num_for_students

        context['num_bac_students'] = num_bac_students
        context['num_bac_rus_students'] = num_bac_rus_students
        context['num_bac_for_students'] = num_bac_for_students

        context['num_mag_students'] = num_mag_students
        context['num_mag_rus_students'] = num_mag_rus_students
        context['num_mag_for_students'] = num_mag_for_students

        # блок стипендии
        context['num_money'] = num_money
        context['no_money'] = no_money
        context['per_no_money'] = per_no_money
        context['num_min_money'] = num_min_money
        context['num_med_money'] = num_med_money
        context['num_max_money'] = num_max_money
        context['per_bac_no_money'] = per_bac_no_money
        context['per_mag_no_money'] = per_mag_no_money

        # бакалавриат
        context['num_bac_min_money'] = num_bac_min_money
        context['num_bac_med_money'] = num_bac_med_money
        context['num_bac_max_money'] = num_bac_max_money
        context['num_bac_no_money'] = num_bac_no_money
        context['num_bac_money'] = num_bac_money

        # магистратура
        context['num_mag_min_money'] = num_mag_min_money
        context['num_mag_med_money'] = num_mag_med_money
        context['num_mag_max_money'] = num_mag_max_money
        context['num_mag_no_money'] = num_mag_no_money
        context['num_mag_money'] = num_mag_money

        context['sick_students'] = sick_students
        context['delay_students'] = delay_students
        context['num_sick_students'] = len(sick_students)
        context['num_delay_students'] = len(delay_students)

        return context
