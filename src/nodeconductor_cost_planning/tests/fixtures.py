from django.utils.functional import cached_property

from nodeconductor.structure.tests import fixtures as structure_fixtures

from . import factories


class CostPlanningFixture(structure_fixtures.ProjectFixture):

    @cached_property
    def category(self):
        return factories.CategoryFactory()

    @cached_property
    def preset(self):
        return factories.PresetFactory(category=self.category)

    @cached_property
    def deployment_plan(self):
        return factories.DeploymentPlanFactory(project=self.project)
