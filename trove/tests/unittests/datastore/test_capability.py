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
from trove.datastore.models import CapabilityOverride
from trove.datastore.models import Capability
from trove.common.exception import CapabilityNotFound
from trove.datastore.models import DBCapabilityOverrides


class TestCapabilities(TestDatastoreBase):
    def setUp(self):
        super(TestCapabilities, self).setUp()

        self.capability_name = "root_on_create" + self.rand_id
        self.capability_desc = "Enables root on create"
        self.capability_enabled = True

        self.cap1 = Capability.create(self.capability_name,
                                      self.capability_desc, True)
        self.cap2 = Capability.create("require_volume" + self.rand_id,
                                      "Require external volume", True)
        self.cap3 = Capability.create("test_capability" + self.rand_id,
                                      "Test capability", False)

    def tearDown(self):
        super(TestCapabilities, self).tearDown()

        capabilities_overridden = DBCapabilityOverrides.find_all(
            datastore_version_id=self.datastore_version.id).all()

        for ce in capabilities_overridden:
            ce.delete()

        self.cap1.delete()
        self.cap2.delete()
        self.cap3.delete()

    def test_capability(self):
        cap = Capability.load(self.capability_name)
        self.assertEqual(cap.name, self.capability_name)
        self.assertEqual(cap.description, self.capability_desc)
        self.assertEqual(cap.enabled, self.capability_enabled)

    def test_ds_capability_create_disabled(self):
        self.ds_cap = CapabilityOverride.create(
            self.cap1, self.datastore_version.id, enabled=False)
        self.assertFalse(self.ds_cap.enabled)
        
        self.ds_cap.delete()

    def test_capability_enabled(self):
        self.assertTrue(Capability.load(self.capability_name).enabled)

    def test_capability_disabled(self):
        capability = Capability.load(self.capability_name)
        capability.disable()
        self.assertFalse(capability.enabled)

        self.assertFalse(Capability.load(self.capability_name).enabled)

    def test_load_nonexistant_capability(self):
        self.assertRaises(CapabilityNotFound, Capability.load, "non-existant")

    def capability_name_filter(self, capabilities):
        new_capabilities = []
        for capability in capabilities:
            if self.rand_id in capability.name:
                new_capabilities.append(capability)
        return new_capabilities
