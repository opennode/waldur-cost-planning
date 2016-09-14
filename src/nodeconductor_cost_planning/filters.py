import django_filters

from nodeconductor.core.filters import UUIDFilter
from . import models


class DeploymentPlanFilter(django_filters.FilterSet):
    customer = UUIDFilter(
        name='customer__uuid',
        distinct=True,
    )

    class Meta(object):
        model = models.DeploymentPlan
        fields = ['customer']

        order_by = [
            'name',
            '-name',
            'created',
            '-created'
        ]
