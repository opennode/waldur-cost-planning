from __future__ import unicode_literals

from nodeconductor.core.permissions import StaffPermissionLogic


PERMISSION_LOGICS = (
    ('nodeconductor_cost_planning.DeploymentPlan', StaffPermissionLogic(any_permission=True)),
    ('nodeconductor_cost_planning.Category', StaffPermissionLogic(any_permission=True)),
    ('nodeconductor_cost_planning.Preset', StaffPermissionLogic(any_permission=True)),
)
