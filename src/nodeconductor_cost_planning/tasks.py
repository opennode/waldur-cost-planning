import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from . import models
from . import report


logger = logging.getLogger(__name__)


@shared_task(name='nodeconductor.cost_planning.generate_pdf')
def generate_pdf(plan_id):
    try:
        plan = models.DeploymentPlan.objects.get(pk=plan_id)
    except models.DeploymentPlan.DoesNotExist:
        logger.warning('Missing deployment plan with id %s', plan_id)
        return

    report.PlanReportGenerator(plan).generate_pdf()


@shared_task(name='nodeconductor.cost_planning.send_report')
def send_report(plan_id):
    try:
        plan = models.DeploymentPlan.objects.get(pk=plan_id)
    except models.DeploymentPlan.DoesNotExist:
        logger.warning('Missing deployment plan with id %s', plan_id)
        return

    if not plan.email_to:
        logger.warning('Missing destination email for plan with id %s', plan_id)
        return

    subject = 'Deployment plan details for %s' % plan.name
    body = report.BaseReportGenerator(plan).render_html()
    send_mail(subject,
              message='Attachment contains deployment plan detail',
              html_message=body,
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=[plan.email_to])
