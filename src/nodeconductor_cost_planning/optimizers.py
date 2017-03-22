""" This module calculates the cheapest price for deployment plans. """

from nodeconductor.structure import models as structure_models

from . import register


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
    def _get_optimized_service(self, service):
        optimizer_class = register.Register.get_optimizer(service.settings.type)
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
        """ Return the cheapest setup as OptimizedService object """
        raise NotImplementedError()
