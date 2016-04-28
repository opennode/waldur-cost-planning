def update_items_if_resource_type_changed(sender, instance=None, created=False, **kwargs):
    plan = instance

    if created or plan.service is None or not plan.service_has_changed:
        return

    for plan_item in plan.items.all():
        plan_item.update_price()


def update_price_list_item_for_plan_item(sender, instance=None, created=False, **kwargs):
    if created or instance.tracker.has_changed('configuration_id'):
        instance.update_price()
