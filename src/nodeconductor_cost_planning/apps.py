from django.apps import AppConfig
from django.db.models import signals

from . import handlers


class CostPlanningConfig(AppConfig):
    name = 'nodeconductor_cost_planning'
    verbose_name = 'Cost planning'

    def ready(self):
        DeploymentPlan = self.get_model('DeploymentPlan')
        DeploymentPlanItem = self.get_model('DeploymentPlanItem')

        signals.post_save.connect(
            handlers.update_items_if_resource_type_changed,
            sender=DeploymentPlan,
            dispatch_uid='nodeconductor_cost_planning.handlers.update_items_if_resource_type_changed'
        )

        signals.post_save.connect(
            handlers.update_price_list_item_for_plan_item,
            sender=DeploymentPlanItem,
            dispatch_uid='nodeconductor_cost_planning.handlers.update_price_list_item_for_plan_item'
        )
