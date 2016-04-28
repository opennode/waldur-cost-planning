import logging
import StringIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils.encoding import force_text
import xhtml2pdf.pisa as pisa

logger = logging.getLogger(__name__)


class PlanReportGenerator(object):
    TEMPLATE = 'nodeconductor_cost_planning/report.html'

    def __init__(self, plan):
        self.plan = plan

    def generate_pdf(self):
        # cleanup if pdf already existed
        if self.plan.pdf is not None:
            self.plan.pdf.delete()

        context = {'plan': self.get_plan_dict(self.plan)}
        result = StringIO.StringIO()
        pdf = pisa.pisaDocument(
            StringIO.StringIO(render_to_string(self.TEMPLATE, context)), result)

        # generate a new file
        if not pdf.err:
            self.plan.pdf.save(self.generate_file_name(), ContentFile(result.getvalue()))
            self.plan.save(update_fields=['pdf'])
        else:
            logger.error(pdf.err)

    def generate_file_name(self):
        return 'deployment-plan-{}-{}.pdf'.format(self.plan.created.strftime('%Y-%m-%d'), self.plan.pk)

    def get_plan_dict(self, plan):
        items = map(self.get_item_dict, self.plan.items.exclude(price_list_item__isnull=True))
        return {
            'name': self.plan.name,
            'customer': self.plan.customer.name,
            'provider': self.plan.service.name,
            'items': items,
            'total': self.plan.total_price,
            'currency': settings.NODECONDUCTOR_COST_PLANNING.get('currency', '')
        }

    def get_item_dict(self, item):
        return {
            'description': force_text(item.configuration),
            'configuration': self.format_dict(item.configuration.metadata.items()),
            'flavor': item.price_list_item.key,
            'quantity': item.quantity,
            'price': item.price_list_item.monthly_rate
        }

    def format_dict(self, items):
        return ", ".join("{}: {}".format(key, val) for (key, val) in items)
