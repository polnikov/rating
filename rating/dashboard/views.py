from dateutil.relativedelta import relativedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView

from students.models import Student, StudentLog


class DashboardView(LoginRequiredMixin, TemplateView):
    """Статистика."""
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # текущие студенты
        current_students = Student.objects.select_related('group', 'semester').filter(
            Q(is_archived=False) & Q(status='Является студентом') | Q(status='Академический отпуск'))
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
        no_money_students = active_students.filter(money='нет').count()
        num_money_students = num_active_students - no_money_students

        # общее
        num_min_money = active_students.filter(money='1.0').count()
        num_middle_money = active_students.filter(money='1.25').count()
        num_max_money = active_students.filter(money='1.5').count()

        try:
            per_min_money = round(num_min_money / num_money_students * 100, 1)
        except ZeroDivisionError:
            per_min_money = 0
        try:
            per_middle_money = round(num_middle_money / num_money_students * 100, 1)
        except ZeroDivisionError:
            per_middle_money = 0
        try:
            per_max_money = round(num_max_money / num_money_students * 100, 1)
        except ZeroDivisionError:
            per_max_money = 0
        try:
            per_no_money = round(no_money_students / num_active_students * 100, 1)
        except ZeroDivisionError:
            per_no_money = 0

        # бакалавриат
        num_bac_active_students = active_students.filter(level='Бакалавриат').count()
        num_bac_min_money = active_students.filter(money='1.0', level='Бакалавриат').count()
        num_bac_middle_money = active_students.filter(money='1.25', level='Бакалавриат').count()
        num_bac_max_money = active_students.filter(money='1.5', level='Бакалавриат').count()
        num_bac_no_money = num_bac_active_students - num_bac_min_money - num_bac_middle_money - num_bac_max_money

        try:
            per_bac_min_money = round(num_bac_min_money / num_bac_active_students * 100, 1)
        except ZeroDivisionError:
            per_bac_min_money = 0
        try:
            per_bac_middle_money = round(num_bac_middle_money / num_bac_active_students * 100, 1)
        except ZeroDivisionError:
            per_bac_middle_money = 0
        try:
            per_bac_max_money = round(num_bac_max_money / num_bac_active_students * 100, 1)
        except ZeroDivisionError:
            per_bac_max_money = 0
        try:
            per_bac_no_money = round(100 - per_bac_min_money - per_bac_middle_money - per_bac_max_money, 2)
        except ZeroDivisionError:
            per_bac_no_money = 0

        # магистратура
        num_mag_active_students = active_students.filter(level='Магистратура').count()
        num_mag_min_money = active_students.filter(money='1.0', level='Магистратура').count()
        num_mag_middle_money = active_students.filter(money='1.25', level='Магистратура').count()
        num_mag_max_money = active_students.filter(money='1.5', level='Магистратура').count()
        num_mag_no_money = num_mag_active_students - num_mag_max_money - num_mag_middle_money - num_mag_min_money

        try:
            per_mag_min_money = round(num_mag_min_money / num_money_students * 100, 1)
        except ZeroDivisionError:
            per_mag_min_money = 0
        try:
            per_mag_middle_money = round(num_mag_middle_money / num_money_students * 100, 1)
        except ZeroDivisionError:
            per_mag_middle_money = 0
        try:
            per_mag_max_money = round(num_mag_max_money / num_money_students * 100, 1)
        except ZeroDivisionError:
            per_mag_max_money = 0
        try:
            per_mag_no_money = round(100 - per_mag_min_money - per_mag_middle_money - per_mag_max_money, 2)
        except ZeroDivisionError:
            per_mag_no_money = 0

        # список болеющих студентов
        sick_students = []
        for st in active_students:
            if st.comment and 'болеет' in st.comment.lower():
                sick_date = StudentLog.objects.get(record_id=st.student_id, field='Примечание').timestamp
                st.sick_date = sick_date
                sick_students.append(st)

        # добавляем дату выхода в АО в академическом отпуске
        for st in delay_students:
            delay_start_date = StudentLog.objects.get(record_id=st.student_id, field='Текущий статус').timestamp
            st.delay_start_date = delay_start_date
            st.delay_end_date = delay_start_date + relativedelta(months=12)

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
        context['num_money_students'] = num_money_students
        context['no_money_students'] = no_money_students
        context['per_no_money'] = per_no_money
        context['num_min_money'] = num_min_money
        context['num_middle_money'] = num_middle_money
        context['num_max_money'] = num_max_money
        context['per_min_money'] = per_min_money
        context['per_middle_money'] = per_middle_money
        context['per_max_money'] = per_max_money

        # бакалавриат
        context['num_bac_min_money'] = num_bac_min_money
        context['num_bac_middle_money'] = num_bac_middle_money
        context['num_bac_max_money'] = num_bac_max_money
        context['num_bac_no_money'] = num_bac_no_money
        context['per_bac_min_money'] = per_bac_min_money
        context['per_bac_middle_money'] = per_bac_middle_money
        context['per_bac_max_money'] = per_bac_max_money
        context['per_bac_no_money'] = per_bac_no_money

        # магистратура
        context['num_mag_min_money'] = num_mag_min_money
        context['num_mag_middle_money'] = num_mag_middle_money
        context['num_mag_max_money'] = num_mag_max_money
        context['num_mag_no_money'] = num_mag_no_money
        context['per_mag_min_money'] = per_mag_min_money
        context['per_mag_middle_money'] = per_mag_middle_money
        context['per_mag_max_money'] = per_mag_max_money
        context['per_mag_no_money'] = per_mag_no_money

        context['sick_students'] = sick_students
        context['delay_students'] = delay_students

        return context
