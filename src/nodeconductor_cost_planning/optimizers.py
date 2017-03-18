""" This module contains optimizers - objects, that calculates the cheapest price for deployment plans """

from nodeconductor.structure import models as structure_models


class SingleServiceOptimizer(object):
    """ Optimize deployment plan for each service separately """
    def __init__(self, deployment_plan):
        self.plan = deployment_plan

    def _get_valid_service_settings(self):
        """ Return all services that are valid for deployment plan """
        # TODO: too many queries to DB. Should be optimized.
        service_models = structure_models.Service.get_all_models()
        service_settings = set()
        for model in service_models:
            for service in model.objects.filter(customer=self.plan.customer):
                service_settings.add(service.settings)
        return [settings for settings in service_settings
                if set(settings.certifications.all()).issuperset(self.plan.certifications.all())]

    def get_optimized_service_settings(self):
        optimized_service_settings = []
        service_settings = self._get_valid_service_settings()

        for settings in service_settings:
            if settings.type != 'OpenStack':
                continue
            optimized_service_settings.append(OptimizedOpenStackSettings(settings, self.plan))
        return optimized_service_settings


class OptimizedOpenStackSettings(object):

    def __init__(self, service_settings, deployment_plan):
        self.settings = service_settings
        self.plan = deployment_plan
        self.package_templates = self.get_best_package_templates()

    def get_best_package_templates(self):
        from nodeconductor_assembly_waldur.packages.models import PackageTemplate
        return [{
            'template': PackageTemplate.objects.filter(service_settings=self.settings).first(),
            'quantity': 2,
        }]
