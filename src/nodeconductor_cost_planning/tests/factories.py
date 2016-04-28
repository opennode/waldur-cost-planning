from __future__ import unicode_literals

import factory
from django.core.urlresolvers import reverse

from nodeconductor.structure.tests import factories as structure_factories

from .. import models


class DeploymentPlanFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.DeploymentPlan

    name = factory.Sequence(lambda n: 'plan%s' % n)
    customer = factory.SubFactory(structure_factories.CustomerFactory)

    @classmethod
    def get_list_url(cls):
        return 'http://testserver' + reverse('deployment-plan-list')

    @classmethod
    def get_url(cls, obj):
        return 'http://testserver' + reverse('deployment-plan-detail', kwargs={'uuid': obj.uuid.hex})


class CategoryFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.Category

    name = factory.Sequence(lambda n: 'category%s' % n)


class ConfigurationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.Configuration

    name = factory.Sequence(lambda n: 'configuration%s' % n)
    category = factory.SubFactory(CategoryFactory)
    metadata = {'ram': 1024, 'cores': 1, 'disk': 10240}

    @classmethod
    def get_url(cls, obj=None):
        if obj is None:
            obj = ConfigurationFactory()
        return 'http://testserver' + reverse('deployment-configuration-detail', kwargs={'uuid': obj.uuid.hex})
