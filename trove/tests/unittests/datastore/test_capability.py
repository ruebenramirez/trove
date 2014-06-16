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
from trove.datastore import models as datastore_models
from trove.datastore.models import CapabilityOverrides
from trove.datastore.models import CapabilityOverride
from trove.datastore.models import Capability
from trove.common import exception
from trove.datastore.models import Datastore
from sqlalchemy import exc as SQLAlchemyException


class TestCapabilities(TestDatastoreBase):
    def setUp(self):
        super(TestCapabilities, self).setUp()
        self.create_base_capabilities()
        self.create_datastores()
        self.create_capability_overrides()

    def tearDown(self):
        super(TestCapabilities, self).tearDown()
        try:
            """
            remove the base capabilities
            (also removes any capability override children)
            """
            self.cap1.delete()
            self.cap2.delete()
            self.cap3.delete()
        except Exception:
            """don't choke on capabilities that we're already removed"""
            pass

    def create_base_capabilities(self):
        self.capability_name = "root_on_create" + self.rand_id
        self.capability_desc = "Enables root on create"
        self.capability_enabled = True
        self.cap1 = Capability.create(self.capability_name,
                                      self.capability_desc, True)
        self.cap2 = Capability.create("require_volume" + self.rand_id,
                                      "Require external volume", True)
        self.cap3 = Capability.create("test_capability" + self.rand_id,
                                      "Test capability", False)
    def create_datastores(self):
        self.ds2_name = 'test-datastore2'
        datastore_models.update_datastore(self.ds2_name, default_version=False)
        self.ds2 = Datastore.load(self.ds2_name)
        self.ds3_name = 'test-datastore3'
        datastore_models.update_datastore(self.ds3_name, default_version=False)
        self.ds3 = Datastore.load(self.ds3_name)

    def create_capability_overrides(self):
        self.override1 = CapabilityOverride.create(
            capability_id=self.cap3.id,
            datastore_version_id=self.ds2.id,
            enabled=True)
        self.override2 = CapabilityOverride.create(
            capability_id=self.cap3.id,
            datastore_version_id=self.ds3.id,
            enabled=True)

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
        self.assertIn(self.override1, self.cap3.overrides)
        self.assertIn(self.override2, self.cap3.overrides)

    def test_remove_single_capability_override(self):
        self.override1.delete()
        self.cap3 = Capability.load(self.cap3.id)
        self.assertFalse(self.override1 in self.cap3.overrides)

    def test_capability_overrides_update_requires_reloading_capability_object(self):
        self.assertTrue(self.override2 in self.cap3.overrides)
        self.override2.delete()

        # fails without this line -- requires another load to update list
        self.cap3 = Capability.load(self.cap3.id)
        self.assertTrue(self.override2 not in self.cap3.overrides)


    def test_remove_all_capability_overrides(self):
        original_capability_id = self.cap3.id
        original_name = self.cap3.name
        original_description = self.cap3.description

        # remove overrides
        CapabilityOverrides.delete(self.cap3.id)

        # check capabilties were removed
        base_capability = Capability.load(self.cap3.id)
        self.assertFalse(self.override1 in base_capability.overrides)
        self.assertFalse(self.override2 in base_capability.overrides)

        # check base capability still exists
        self.assertEqual(original_capability_id, self.cap3.id)
        self.assertEqual(original_name, self.cap3.name)
        self.assertEqual(original_description, self.cap3.description)

    def test_remove_capability_along_with_all_overrides(self):
        self.cap3.delete()

        # check capabilty overrides were removed
        self.assertRaises(exception.CapabilityOverrideNotFound,
                          CapabilityOverride.load, self.override1.capability_id,
                                                  self.override1.datastore_version_id)
        self.assertRaises(exception.CapabilityOverrideNotFound,
                          CapabilityOverride.load, self.override2.capability_id,
                                                  self.override2.datastore_version_id)
        # check base capability was removed
        self.assertRaises(exception.CapabilityNotFound,
                          Capability.load, self.cap3.id)

    def test_capability_enabled(self):
        self.assertTrue(Capability.load(self.capability_name).enabled)

    def test_capability_disabled(self):
        capability = Capability.load(self.capability_name)
        capability.disable()
        self.assertFalse(capability.enabled)

        self.assertFalse(Capability.load(self.capability_name).enabled)

    def test_load_nonexistant_capability(self):
        self.assertRaises(exception.CapabilityNotFound, Capability.load, "non-existant")

    def capability_name_filter(self, capabilities):
        new_capabilities = []
        for capability in capabilities:
            if self.rand_id in capability.name:
                new_capabilities.append(capability)
        return new_capabilities

    def test_remove_a_nonexistant_capability(self):
        """
        if capability already removed, SQLAlchemy exception is thrown
        """
        self.cap3.delete()
        self.assertRaises(SQLAlchemyException.InvalidRequestError,
                          self.cap3.delete)
