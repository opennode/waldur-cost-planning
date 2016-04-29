from __future__ import unicode_literals

import factory
from django.core.urlresolvers import reverse

from nodeconductor.cost_tracking.tests.factories import DefaultPriceListItemFactory
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


class PresetFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.Preset

    name = factory.Sequence(lambda n: 'preset%s' % n)
    category = factory.SubFactory(CategoryFactory)

    @classmethod
    def get_url(cls, obj=None):
        if obj is None:
            obj = PresetFactory()
        return 'http://testserver' + reverse('deployment-preset-detail', kwargs={'uuid': obj.uuid.hex})


class PresetItemFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.PresetItem

    default_price_list_item = factory.SubFactory(DefaultPriceListItemFactory)
