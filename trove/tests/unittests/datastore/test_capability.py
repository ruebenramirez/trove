#    Copyright (c) 2014 Rackspace Hosting
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from trove.tests.unittests.datastore.base import TestDatastoreBase
from trove.datastore.models import CapabilityOverrides
from trove.datastore.models import CapabilityOverride
from trove.datastore.models import Capability
from trove.common import exception
from sqlalchemy import exc as SQLAlchemyException


class TestCapabilities(TestDatastoreBase):
    def setUp(self):
        super(TestCapabilities, self).setUp()

    def tearDown(self):
        super(TestCapabilities, self).tearDown()

    def test_capability(self):
        cap = Capability.load(self.capability_name)
        self.assertEqual(cap.name, self.capability_name)
        self.assertEqual(cap.description, self.capability_desc)
        self.assertEqual(cap.enabled, self.capability_enabled)

    def test_ds_capability_create_disabled(self):
        self.ds_cap = CapabilityOverride.create(
            self.cap1.id, self.datastore_version.id, enabled=False)
        self.assertFalse(self.ds_cap.enabled)
        self.ds_cap.delete()

    def test_capability_overrides_were_created_successfully(self):
        self.assertIn(self.disabled_override1, self.cap3.overrides)
        self.assertIn(self.disabled_override2, self.cap3.overrides)

    def test_overrides_load_properly(self):
        self.cap3 = Capability.load(self.cap3.id)
        self.assertIn(self.disabled_override1, self.cap3.overrides)
        self.assertIn(self.disabled_override2, self.cap3.overrides)

    def test_remove_single_capability_override(self):
        self.disabled_override1.delete()

        # check override1 removed
        self.cap3 = Capability.load(self.cap3.id)
        self.assertFalse(self.disabled_override1 in self.cap3.overrides)

        # check only override1 was removed
        self.assertTrue(self.disabled_override2 in self.cap3.overrides)

    def test_override_update_requires_reloading_capability_object(self):
        self.assertTrue(self.disabled_override2 in self.cap3.overrides)
        self.disabled_override2.delete()

        # requires another load to update list
        self.assertTrue(self.disabled_override2 in self.cap3.overrides)
        self.cap3 = Capability.load(self.cap3.id)
        self.assertTrue(self.disabled_override2 not in self.cap3.overrides)

    def test_remove_enabled_capability_overrides(self):
        disabled_base_capability = Capability.load(self.cap4.id)
        self.assertTrue(self.enabled_override1 in
                        disabled_base_capability.overrides)
        self.assertTrue(self.enabled_override2 in
                        disabled_base_capability.overrides)

        CapabilityOverrides.delete_enabled_overrides(self.cap4.id)

        # check capabilties were removed
        disabled_base_capability = Capability.load(self.cap4.id)
        self.assertFalse(self.enabled_override1 in
                         disabled_base_capability.overrides)
        self.assertFalse(self.enabled_override2 in
                         disabled_base_capability.overrides)

    def test_remove_disabled_capability_overrides(self):
        enabled_base_capability = Capability.load(self.cap3.id)
        self.assertTrue(self.disabled_override1 in
                        enabled_base_capability.overrides)
        self.assertTrue(self.disabled_override2 in
                         enabled_base_capability.overrides)

        CapabilityOverrides.delete_disabled_overrides(self.cap3.id)

        # check capabilties were removed
        enabled_base_capability = Capability.load(self.cap4.id)
        self.assertFalse(self.disabled_override1 in
                         enabled_base_capability.overrides)
        self.assertFalse(self.disabled_override2 in
                         enabled_base_capability.overrides)

    def test_remove_all_capability_overrides(self):
        original_capability_id = self.cap3.id
        original_name = self.cap3.name
        original_description = self.cap3.description

        # remove overrides
        CapabilityOverrides.delete_all_overrides(self.cap3.id)
        CapabilityOverrides.delete_all_overrides(self.cap4.id)

        # check capabilties were removed
        enabled_base_capability = Capability.load(self.cap3.id)
        disabled_base_capability = Capability.load(self.cap4.id)
        self.assertFalse(self.disabled_override1 in
                         enabled_base_capability.overrides)
        self.assertFalse(self.disabled_override2 in
                         enabled_base_capability.overrides)
        self.assertFalse(self.enabled_override1 in
                         disabled_base_capability.overrides)
        self.assertFalse(self.enabled_override2 in
                         disabled_base_capability.overrides)

        # check base capability still exists
        self.assertEqual(original_capability_id, self.cap3.id)
        self.assertEqual(original_name, self.cap3.name)
        self.assertEqual(original_description, self.cap3.description)

    def test_base_capability_exists_after_delete_overrides(self):
        original_capability_id = self.cap3.id
        original_name = self.cap3.name
        original_description = self.cap3.description

        CapabilityOverrides.delete_all_overrides(self.cap3.id)

        # check base capability still exists
        base_capability = Capability.load(self.cap3.id)
        self.assertEqual(original_capability_id, self.cap3.id)
        self.assertEqual(original_name, self.cap3.name)
        self.assertEqual(original_description, self.cap3.description)

    def test_remove_capability_along_with_all_overrides(self):
        self.cap3.delete()

        # check capabilty overrides were removed
        self.assertRaises(exception.CapabilityOverrideNotFound,
                          CapabilityOverride.load,
                          self.disabled_override1.capability_id,
                          self.disabled_override1.datastore_version_id)
        self.assertRaises(exception.CapabilityOverrideNotFound,
                          CapabilityOverride.load,
                          self.disabled_override2.capability_id,
                          self.disabled_override2.datastore_version_id)

        # check base capability was removed
        self.assertRaises(exception.CapabilityNotFound,
                          Capability.load, self.cap3.id)

    def test_load_enabled_capability_overrides(self):
        enabled_overrides = CapabilityOverrides.load_enabled_overrides(
            self.cap4.id)
        self.assertTrue(self.enabled_override1 in enabled_overrides)
        self.assertTrue(self.enabled_override2 in enabled_overrides)

    def test_load_disabled_capability_overrides(self):
        disabled_overrides = CapabilityOverrides.load_disabled_overrides(
            self.cap3.id)
        self.assertTrue(self.disabled_override1 in disabled_overrides)
        self.assertTrue(self.disabled_override2 in disabled_overrides)

    def test_load_all_capability_overrides(self):
        loaded_overrides = CapabilityOverrides.load_overrides(self.cap3.id)
        self.assertTrue(self.disabled_override1 in loaded_overrides)
        self.assertTrue(self.disabled_override2 in loaded_overrides)

        loaded_overrides = CapabilityOverrides.load_enabled_overrides(
            self.cap4.id)
        self.assertTrue(self.enabled_override1 in loaded_overrides)
        self.assertTrue(self.enabled_override2 in loaded_overrides)

    def test_capability_enabled(self):
        self.assertTrue(Capability.load(self.capability_name).enabled)

    def test_capability_disabled(self):
        capability = Capability.load(self.capability_name)
        capability.disable()
        self.assertFalse(capability.enabled)

        self.assertFalse(Capability.load(self.capability_name).enabled)

    def test_load_nonexistant_capability(self):
        self.assertRaises(exception.CapabilityNotFound, Capability.load,
                          "non-existent")

    def test_remove_a_nonexistant_capability(self):
        """
        if capability already removed, SQLAlchemy exception is thrown
        """
        self.cap3.delete()
        self.assertRaises(SQLAlchemyException.InvalidRequestError,
                          self.cap3.delete)
