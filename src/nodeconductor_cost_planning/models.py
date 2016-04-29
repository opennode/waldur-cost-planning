from __future__ import unicode_literals

import logging
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.lru_cache import lru_cache
from model_utils.models import TimeStampedModel

from nodeconductor.core import models as core_models
from nodeconductor.cost_tracking.models import DefaultPriceListItem
from nodeconductor.structure import SupportedServices
from nodeconductor.structure.models import Customer


logger = logging.getLogger(__name__)


def get_content_types_query(items):
    content_types = ContentType.objects.get_for_models(*items).values()
    return {'id__in': [ct.id for ct in content_types]}


@lru_cache(maxsize=1)
def get_service_content_types():
    services = [service['service'] for service in SupportedServices.get_service_models().values()]
    return get_content_types_query(services)


@python_2_unicode_compatible
class DeploymentPlan(core_models.UuidMixin, core_models.NameMixin, TimeStampedModel):
    """
    Deployment plan contains list of plan items.
    """
    class Permissions(object):
        customer_path = 'customer'

    class Meta:
        ordering = ['-created']

    # Generic key to service
    content_type = models.ForeignKey(ContentType, null=True, blank=True, related_name='+',
                                     limit_choices_to=get_service_content_types)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    service = GenericForeignKey('content_type', 'object_id')

    customer = models.ForeignKey(Customer, related_name='+')
    email_to = models.EmailField(blank=True)
    pdf = models.FileField(upload_to='deployment_plans', blank=True, null=True)

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class DeploymentPlanItem(models.Model):
    """
    Plan item specifies quantity of presets.
    For example:
    {
        "preset": <Hadoop DataNode>,
        "quantity": 10
    }
    """
    class Meta:
        ordering = 'plan', 'preset'
        unique_together = 'plan', 'preset'

    plan = models.ForeignKey(DeploymentPlan, related_name='items')
    preset = models.ForeignKey('Preset')
    quantity = models.PositiveSmallIntegerField(default=1)

    @property
    def price_list_items(self):
        # Terminate if plan does not have service
        if self.plan.service is None:
            return 0

        # Get resource content types for plan's service
        resources = SupportedServices.get_related_models(self.plan.service)['resources']
        resource_types = ContentType.objects.get_for_models(*resources).values()

        # Terminate if service does not have resources
        if not resource_types:
            return 0

        items = self.preset.items.filter(
            default_price_list_item__resource_content_type__in=resource_types
        ).exclude(quantity=0)
        return items

    @property
    def total_price(self):
        subtotal = sum(Decimal(item.default_price_list_item.monthly_rate) * item.quantity
                       for item in self.price_list_items)
        return subtotal * self.quantity

    def __str__(self):
        return '%s %s' % (self.quantity, self.preset)


@python_2_unicode_compatible
class Category(core_models.NameMixin):
    class Meta(object):
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Preset(core_models.UuidMixin, core_models.NameMixin):
    """
    Preset contains list of items.
    Example rendering of preset:
    {
        "category": "Big Data",
        "name": "Hadoop DataNode",
        "variant": "Large",
        "items": [<Large Flavor>, <Large Storage>, <Large Image>]
    }
    """
    class Meta:
        ordering = 'category', 'name', 'variant'
        unique_together = 'category', 'name', 'variant'

    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'

    VARIANTS = (
        (SMALL, 'Small'),
        (MEDIUM, 'Medium'),
        (LARGE, 'Large'),
    )

    category = models.ForeignKey(Category, related_name='presets')
    variant = models.CharField(max_length=150, choices=VARIANTS)

    def __str__(self):
        return '%s %s %s' % (self.get_variant_display(), self.name, self.category)


class PresetItem(models.Model):
    """
    Preset item specifies quantity of default price list items.
    For example:
    {
        "default_price_list_item": <Medium OpenStack Flavor>,
        "quantity": 1
    }
    """
    preset = models.ForeignKey(Preset, related_name='items')
    default_price_list_item = models.ForeignKey(DefaultPriceListItem, related_name='+')
    quantity = models.PositiveSmallIntegerField(default=1)
