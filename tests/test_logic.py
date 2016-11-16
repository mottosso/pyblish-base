import os
import contextlib

# Local library
from . import lib

from pyblish import api, logic, plugin, util

from nose.tools import (
    with_setup,
    assert_equals,
)


@contextlib.contextmanager
def no_guis():
    os.environ.pop("PYBLISHGUI", None)
    for gui in logic.registered_guis():
        logic.deregister_gui(gui)

    yield


@with_setup(lib.setup, lib.teardown)
def test_iterator():
    """Iterator skips inactive plug-ins and instances"""

    count = {"#": 0}

    class MyCollector(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            inactive = context.create_instance("Inactive")
            active = context.create_instance("Active")

            inactive.data["publish"] = False
            active.data["publish"] = True

            count["#"] += 1

    class MyValidatorA(api.InstancePlugin):
        order = api.ValidatorOrder
        active = False

        def process(self, instance):
            count["#"] += 10

    class MyValidatorB(api.InstancePlugin):
        order = api.ValidatorOrder

        def process(self, instance):
            count["#"] += 100

    context = api.Context()
    plugins = [MyCollector, MyValidatorA, MyValidatorB]

    assert count["#"] == 0, count

    for Plugin, instance in logic.Iterator(plugins, context):
        assert instance.name != "Inactive" if instance else True
        assert Plugin.__name__ != "MyValidatorA"

        plugin.process(Plugin, context, instance)

    # Collector runs once, one Validator runs once
    assert count["#"] == 101, count


def test_register_gui():
    """Registering at run-time takes precedence over those from environment"""
    
    with no_guis():
        os.environ["PYBLISHGUI"] = "second,third"
        logic.register_gui("first")

        print(logic.registered_guis())
        assert logic.registered_guis() == ["first", "second", "third"]


@with_setup(lib.setup_empty, lib.teardown)
def test_subset_match():
    """Plugin.match = api.Subset works as expected"""

    count = {"#": 0}

    class MyPlugin(api.InstancePlugin):
        families = ["a", "b"]
        match = api.Subset

        def process(self, instance):
            count["#"] += 1

    context = api.Context()

    context.create_instance("not_included_1", families=["a"])
    context.create_instance("not_included_1", families=["x"])
    context.create_instance("included_1", families=["a", "b"])
    context.create_instance("included_2", families=["a", "b", "c"])

    util.publish(context, plugins=[MyPlugin])

    assert_equals(count["#"], 2)

    instances = logic.instances_by_plugin(context, MyPlugin)
    assert_equals(list(i.name for i in instances), ["included_1", "included_2"])


def test_subset_exact():
    """Plugin.match = api.Exact works as expected

    Notice the 'default' family in the plug-in. Instances are automatically
    imbued with this family on creation, as value to their `data["family"]` key.

    When using multiple families, it is common not to bother modifying `family`,
    and in the future this member needn't be there at all and may/should be
    removed. But till then, for complete clarity, it might be worth removing this
    explicitly during the creation of instances if instead choosing to use the
    `families` key.

    """

    count = {"#": 0}

    class MyPlugin(api.InstancePlugin):
        families = ["default", "a", "b"]
        match = api.Exact

        def process(self, instance):
            count["#"] += 1

    context = api.Context()

    context.create_instance("not_included_1", families=["a"])
    context.create_instance("not_included_1", families=["x"])
    context.create_instance("not_included_3", families=["a", "b", "c"])
    context.create_instance("included_1", families=["a", "b"])

    util.publish(context, plugins=[MyPlugin])

    assert_equals(count["#"], 1)

    instances = logic.instances_by_plugin(context, MyPlugin)
    assert_equals(list(i.name for i in instances), ["included_1"])
