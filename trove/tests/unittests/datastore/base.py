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


    def tearDown(self):
        super(TestDatastoreBase, self).tearDown()
        Datastore.load(self.ds_name).delete()

