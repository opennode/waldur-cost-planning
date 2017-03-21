""" This module calculates the cheapest price for deployment plans. """

from nodeconductor.structure import models as structure_models
from nodeconductor_openstack.openstack import apps as openstack_apps


def get_filtered_services(deployment_plan):
    """ Get services that fits deployment plan requirements """
    service_models = structure_models.Service.get_all_models()
    deployment_plan_certifications = deployment_plan.get_required_certifications()
    for model in service_models:
        services = (
            model.objects
            .filter(projects=deployment_plan.project)
            .select_related('settings')
            .prefetch_related('settings__certifications')
        )
        for service in services:
            if set(service.settings.certifications.all()).issuperset(deployment_plan_certifications):
                yield service


class OptimizedService(object):
    """ Abstract object that represents the best choice for a particular service.

        Each descendant should define how to reach the best choice.
        Optimized objects should not contain any logic, just define data
        structures.
    """
    def __init__(self, service, price):
        self.service = service
        self.price = price


class OptimizedOpenStack(OptimizedService):
    """ Defines package template with the best price for OpenStack service """

    def __init__(self, service, price, package_template):
        super(OptimizedOpenStack, self).__init__(service, price)
        self.package_template = package_template


class Strategy(object):
    """ Abstract. Defines how get the cheapest services setups for deployment plan. """

    def __init__(self, deployment_plan):
        self.deployment_plan = deployment_plan

    def get_optimized(self):
        """ Return list of OptimizedService objects """
        raise NotImplementedError()


class SingleServiceStrategy(Strategy):
    """ Optimize deployment plan for each service separately and return list
        of all available variants.
    """
    _registry = {}

    @classmethod
    def register(cls, service_type, optimizer):
        """ Register service optimizer """
        cls._registry[service_type] = optimizer

    def _get_optimized_service(self, service):
        optimizer_class = self._registry.get(service.settings.type)
        if optimizer_class:
            optimizer = optimizer_class(self.deployment_plan, service)
            return optimizer.optimize()

    def get_optimized(self):
        optimized = []
        for service in get_filtered_services(self.deployment_plan):
            optimized_service = self._get_optimized_service(service)
            if optimized_service:
                optimized.append(optimized_service)
        return optimized


class Optimizer(object):
    """ Abstract. Descendant should define how to get the cheapest setup for a
        particular service.
    """
    def __init__(self, deployment_plan, service):
        self.service = service
        self.deployment_plan = deployment_plan

    def optimize(self):
        """ Return the cheapest setup as Optimized object """
        raise NotImplementedError()


class OpenStackOptimizer(Optimizer):
    """ Find the cheapest package template for OpenStack service """

    def optimize(self):
        # XXX: This import creates cyclic dependency with assembly module
        from nodeconductor_assembly_waldur.packages.models import PackageTemplate, PackageComponent
        requirements = self.deployment_plan.get_requirements()
        # Step 1. Find suitable templates.
        templates = PackageTemplate.objects.filter(
            service_settings=self.service.settings).prefetch_related('components')
        suitable_templates = []
        for template in templates:
            components = {c.type: c.amount for c in template.components.all()}
            is_suitable = (
                components[PackageComponent.Types.RAM] >= requirements['ram'] and
                components[PackageComponent.Types.STORAGE] >= requirements['storage'] and
                components[PackageComponent.Types.CORES] >= requirements['cores']
            )
            if is_suitable:
                suitable_templates.append(template)
        # Step 2. Find the cheapest template.
        if not suitable_templates:
            # return empty optimized service if there is no suitable templates
            return OptimizedOpenStack(self.service, price=None, package_template=None)
        cheapest_template = min(suitable_templates, key=lambda t: t.price)
        return OptimizedOpenStack(self.service, cheapest_template.price, cheapest_template)


SingleServiceStrategy.register(openstack_apps.OpenStackConfig.service_name, OpenStackOptimizer)
