from nodeconductor.core import NodeConductorExtension


class CostPlanningExtension(NodeConductorExtension):

    @staticmethod
    def django_app():
        return 'nodeconductor_cost_planning'

    @staticmethod
    def rest_urls():
        from .urls import register_in
        return register_in
