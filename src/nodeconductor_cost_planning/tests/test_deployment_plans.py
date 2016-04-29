from rest_framework import status, test

from nodeconductor.core.utils import hours_in_month
from nodeconductor.cost_tracking.tests.factories import DefaultPriceListItemFactory
from nodeconductor.openstack.tests.factories import OpenStackServiceFactory
from nodeconductor.structure.models import CustomerRole
from nodeconductor.structure.tests import factories as structure_factories

from . import factories
from .. import models


class BaseTest(test.APISimpleTestCase):
    def setUp(self):
        self.staff = structure_factories.UserFactory(is_staff=True)
        self.no_role_user = structure_factories.UserFactory()
        self.customer_owner = structure_factories.UserFactory()

        self.owned_customer = structure_factories.CustomerFactory()
        self.owned_customer.add_user(self.customer_owner, CustomerRole.OWNER)


class DeploymentPlanListTest(BaseTest):
    def setUp(self):
        super(DeploymentPlanListTest, self).setUp()
        service = OpenStackServiceFactory(customer=self.owned_customer)
        models.DeploymentPlan.objects.all().delete()
        factories.DeploymentPlanFactory.create(customer=self.owned_customer, service=service)

    def test_customer_owner_can_list_deployment_plans(self):
        response = self.get_deployment_plans(self.customer_owner)
        self.assertEqual(len(response.data), 1)

    def test_deployment_plans_are_not_visible_for_user_without_role(self):
        response = self.get_deployment_plans(self.no_role_user)
        self.assertEqual(len(response.data), 0)

    def test_staff_can_list_all_deployment_plans(self):
        response = self.get_deployment_plans(self.staff)
        self.assertEqual(len(response.data), 1)

    def test_deployment_plans_can_be_filtered_by_customer(self):
        self.client.force_authenticate(user=self.staff)
        customer = structure_factories.CustomerFactory()
        response = self.client.get(factories.DeploymentPlanFactory.get_list_url(), {
            'customer': customer.uuid.hex
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def get_deployment_plans(self, user):
        self.client.force_authenticate(user=user)
        response = self.client.get(factories.DeploymentPlanFactory.get_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response


class DeploymentPlanCreateTest(BaseTest):
    def test_customer_owner_can_create_deployment_plan(self):
        response = self.create_deployment_plan(self.customer_owner)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        plan = models.DeploymentPlan.objects.get(uuid=response.data['uuid'])
        self.assertEqual(1, plan.items.count())

    def test_customer_without_role_can_not_create_deployment_plan(self):
        response = self.create_deployment_plan(self.no_role_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def create_deployment_plan(self, user):
        self.client.force_authenticate(user=user)
        return self.client.post(factories.DeploymentPlanFactory.get_list_url(), {
            'customer': structure_factories.CustomerFactory.get_url(self.owned_customer),
            'name': 'Webapp for Monster Inc.',
            'items': [
                {
                    'preset': factories.PresetFactory.get_url(),
                    'quantity': 1
                }
            ]
        })


class DeploymentPlanUpdateTest(BaseTest):
    def setUp(self):
        super(DeploymentPlanUpdateTest, self).setUp()
        self.plan = factories.DeploymentPlanFactory(customer=self.owned_customer)

        self.preset1 = factories.PresetFactory()
        self.plan.items.create(preset=self.preset1, quantity=1)

        self.preset2 = factories.PresetFactory()
        self.plan.items.create(preset=self.preset2, quantity=2)

    def test_other_customer_can_not_update_plan(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.put(factories.DeploymentPlanFactory.get_url(self.plan), {
            'name': 'New name for plan'
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_owner_can_update_item_list(self):
        """
        Old item is removed, remaining item is updated.
        """
        self.client.force_authenticate(user=self.customer_owner)

        item = {
            'preset': factories.PresetFactory.get_url(self.preset1),
            'quantity': 2
        }
        response = self.client.put(factories.DeploymentPlanFactory.get_url(self.plan), {
            'items': [item]
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.plan.refresh_from_db()
        self.assertEqual(1, self.plan.items.count())
        self.assertEqual(2, self.plan.items.first().quantity)

    def test_customer_owner_can_update_name(self):
        self.client.force_authenticate(user=self.customer_owner)
        response = self.client.put(factories.DeploymentPlanFactory.get_url(self.plan), {
            'name': 'New name for plan'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.name, 'New name for plan')

    def test_customer_owner_can_update_service(self):
        self.client.force_authenticate(user=self.customer_owner)

        service = OpenStackServiceFactory(customer=self.owned_customer)
        response = self.client.put(factories.DeploymentPlanFactory.get_url(self.plan), {
            'service': OpenStackServiceFactory.get_url(service)
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        refreshed_plan = models.DeploymentPlan.objects.get(id=self.plan.id)
        self.assertEqual(refreshed_plan.service, service)


class DeploymentPlanPriceTest(test.APISimpleTestCase):
    def test_plan_price(self):
        customer = structure_factories.CustomerFactory()
        service = OpenStackServiceFactory(customer=customer)

        item_type = 'storage'
        key = '1 GB'

        storage_price = 10
        storage_per_instance = 200
        instance_count = 3

        default_item = DefaultPriceListItemFactory(item_type=item_type, key=key, value=storage_price)

        preset = factories.PresetFactory()
        factories.PresetItemFactory(preset=preset,
                                    default_price_list_item=default_item,
                                    quantity=storage_per_instance)

        plan = factories.DeploymentPlanFactory(customer=customer, service=service)
        models.DeploymentPlanItem.objects.create(plan=plan, preset=preset, quantity=instance_count)

        expected = hours_in_month() * storage_price * storage_per_instance * instance_count
        self.assertEqual(plan.total_price, expected)
