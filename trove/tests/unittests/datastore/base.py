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

import testtools
from trove.datastore import models as datastore_models
from trove.datastore.models import Datastore
from trove.datastore.models import DatastoreVersion
from trove.tests.unittests.util import util
from trove.datastore.models import Capability
from trove.datastore.models import CapabilityOverride
import uuid


class TestDatastoreBase(testtools.TestCase):

    def setUp(self):
        # Basic setup and mock/fake structures for testing only
        super(TestDatastoreBase, self).setUp()
        util.init_db()
        self.rand_id = str(uuid.uuid4())
        self.ds_name = "my-test-datastore" + self.rand_id
        self.ds_version = "my-test-version" + self.rand_id

        datastore_models.update_datastore(self.ds_name, False)
        self.datastore = Datastore.load(self.ds_name)

        datastore_models.update_datastore_version(
            self.ds_name, self.ds_version, "mysql", "", "", True)

        self.datastore_version = DatastoreVersion.load(self.datastore,
                                                       self.ds_version)
        self.test_id = self.datastore_version.id

        self.create_base_capabilities()
        self.create_datastores()
        self.create_capability_overrides()

    def tearDown(self):
        super(TestDatastoreBase, self).tearDown()
        Datastore.load(self.ds_name).delete()
        try:
            """
            remove the base capabilities
            (also removes any capability override children)
            """
            self.cap1.delete()
            self.cap2.delete()
            self.cap3.delete()
        except Exception:
            """skip exceptions for capabilities already removed"""
            pass

    def create_base_capabilities(self):
        self.capability_name = "root_on_create" + self.rand_id
        self.capability_desc = "Enables root on create"
        self.capability_enabled = True
        self.cap1 = Capability.create(self.capability_name,
                                      self.capability_desc, True)
        self.cap2 = Capability.create("require_volume" + self.rand_id,
                                      "Require external volume", True)
        self.cap3 = Capability.create(
            "test_default_enabled_capability" + self.rand_id,
            "test default enabled capability",
            True)
        self.cap4 = Capability.create(
            "test_default_disabled_capability" + self.rand_id,
            "Test default disabled capability",
            False)

    def create_datastores(self):
        self.ds2_name = 'test-datastore2'
        datastore_models.update_datastore(self.ds2_name, default_version=False)
        self.ds2 = Datastore.load(self.ds2_name)
        self.ds3_name = 'test-datastore3'
        datastore_models.update_datastore(self.ds3_name, default_version=False)
        self.ds3 = Datastore.load(self.ds3_name)

    def create_capability_overrides(self):
        self.disabled_override1 = CapabilityOverride.create(
            capability_id=self.cap3.id,
            datastore_version_id=self.ds2.id,
            enabled=False)
        self.disabled_override2 = CapabilityOverride.create(
            capability_id=self.cap3.id,
            datastore_version_id=self.ds3.id,
            enabled=False)
        self.enabled_override1 = CapabilityOverride.create(
            capability_id=self.cap4.id,
            datastore_version_id=self.ds2.id,
            enabled=True)
        self.enabled_override2 = CapabilityOverride.create(
            capability_id=self.cap4.id,
            datastore_version_id=self.ds3.id,
            enabled=True)

    def capability_name_filter(self, capabilities):
        new_capabilities = []
        for capability in capabilities:
            if self.rand_id in capability.name:
                new_capabilities.append(capability)
        return new_capabilities
