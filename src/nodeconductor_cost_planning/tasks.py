import logging

from celery import shared_task

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
