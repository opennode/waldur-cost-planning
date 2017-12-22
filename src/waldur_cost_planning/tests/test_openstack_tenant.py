from ddt import ddt, data
from rest_framework import status, test

from waldur_openstack.openstack_tenant.tests import factories as ot_factories

from . import factories, fixtures


@ddt
class OpenStackTenantOptimizerTest(test.APITransactionTestCase):
    def setUp(self):
        self.fixture = fixtures.CostPlanningOpenStackPluginFixture()
        self.plan = self.fixture.deployment_plan
        self.url = factories.DeploymentPlanFactory.get_url(self.plan, action='evaluate')
        self.settings = self.fixture.spl.service.settings
        self.flavor_params = [
            {'cores': 1, 'ram': 1 * 1024, 'name': 'flavor-1'},
            {'cores': 2, 'ram': 2 * 1024, 'name': 'flavor-2'},
            {'cores': 2, 'ram': 3 * 1024, 'name': 'flavor-3'},
            {'cores': 4, 'ram': 4 * 1024, 'name': 'flavor-4'},
        ]

        for p in self.flavor_params:
            ot_factories.FlavorFactory(settings=self.settings, **p)

    @data(
        {'variant': 'small', 'cores': 2, 'ram': 1 * 1024},
        {'variant': 'small', 'cores': 1, 'ram': 4 * 1024},
    )
    def test_filter_flavors_if_exist_any_meet_plan_requirements(self, preset_param):
        response = self._get_response(preset_param)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        optimal_flavor = filter(lambda x: x['cores'] >= preset_param['cores'] and x['ram'] >= preset_param['ram'],
                                self.flavor_params)[0]['name']
        self.assertTrue(optimal_flavor in data[0]['error_message'])

    @data(
        {'variant': 'small', 'cores': 8, 'ram': 4 * 1024},
    )
    def test_filter_flavors_if_not_exist_any_meet_plan_requirements(self, preset_param):
        response = self._get_response(preset_param)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue('It is too big' in data[0]['error_message'])

    def _get_response(self, preset_param):
        self.preset = factories.PresetFactory(category=self.fixture.category, **preset_param)
        factories.DeploymentPlanItemFactory(plan=self.plan, preset=self.preset)

        self.client.force_authenticate(self.fixture.staff)
        response = self.client.get(self.url)
        return response
