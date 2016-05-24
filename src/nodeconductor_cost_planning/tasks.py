import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from . import models
from . import report


logger = logging.getLogger(__name__)


@shared_task(name='nodeconductor.cost_planning.generate_pdf')
def generate_pdf(plan_uuid):
    try:
        plan = models.DeploymentPlan.objects.get(uuid=plan_uuid)
    except models.DeploymentPlan.DoesNotExist:
        logger.warning('Missing deployment plan with uuid %s', plan_uuid)
        return

    report.PdfReportGenerator(plan).generate_pdf()


@shared_task(name='nodeconductor.cost_planning.send_report')
def send_report(plan_uuid):
    try:
        plan = models.DeploymentPlan.objects.get(uuid=plan_uuid)
    except models.DeploymentPlan.DoesNotExist:
        logger.warning('Missing deployment plan with uuid %s', plan_uuid)
        return

    if not plan.email_to:
        logger.warning('Missing destination email for plan with uuid %s', plan_uuid)
        return

    subject = 'Deployment plan details for %s' % plan.name
    body = report.HtmlReportGenerator(plan).render_html()
    send_mail(subject,
              message='Attachment contains deployment plan detail',
              html_message=body,
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=[plan.email_to])
