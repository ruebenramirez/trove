# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
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

import gettext
import inspect
import sys


gettext.install('trove', unicode=1)


from trove.common import cfg
from trove.common import exception
from trove.common import utils
from trove.db import get_db_api
from trove.openstack.common import log as logging
from trove.datastore import models as datastore_models


CONF = cfg.CONF


class Commands(object):

    def __init__(self):
        self.db_api = get_db_api()

    def db_sync(self, repo_path=None):
        self.db_api.db_sync(CONF, repo_path=repo_path)

    def db_upgrade(self, version=None, repo_path=None):
        self.db_api.db_upgrade(CONF, version, repo_path=None)

    def db_downgrade(self, version, repo_path=None):
        self.db_api.db_downgrade(CONF, version, repo_path=None)

    def execute(self):
        exec_method = getattr(self, CONF.action.name)
        args = inspect.getargspec(exec_method)
        args.args.remove('self')
        kwargs = {}
        for arg in args.args:
            kwargs[arg] = getattr(CONF.action, arg)
        exec_method(**kwargs)

    def datastore_update(self, datastore_name, default_version):
        try:
            datastore_models.update_datastore(datastore_name,
                                              default_version)
            print("Datastore '%s' updated." % datastore_name)
        except exception.DatastoreVersionNotFound as e:
            print(e)

    def datastore_version_update(self, datastore_id_or_name, version_name,
                                 manager, image_id, packages, active):
        try:
            datastore_models.update_datastore_version(datastore_id_or_name,
                                                      version_name,
                                                      manager,
                                                      image_id,
                                                      packages, active)
            print("Datastore version '%s' updated." % version_name)
        except exception.DatastoreNotFound as e:
            print(e)

    def db_recreate(self, repo_path):
        """Drops the database and recreates it."""
        self.db_api.drop_db(CONF)
        self.db_sync(repo_path)

    def params_of(self, command_name):
        if Commands.has(command_name):
            return utils.MethodInspector(getattr(self, command_name))

    def add_capability(self, name, description, enabled):
        """Add capability."""
        try:
            datastore_models.Capability.create(name, description, enabled)
        except Exception as e:
            print('unable to create the capability: %s' % e)

    def remove_capability(self, capability_id_or_name):
        """Remove capability and all children capability overrides."""
        try:
            capability = datastore_models.Capability.load(
                capability_id_or_name)
            capability.delete()
        except Exception as e:
            print('unable to remove capability: %s' % e)

    def add_capability_override(self, capability_id, datastore_version_id,
                                enabled):
        """Adds capabilty override to a datastore."""
        try:
            datastore_models.CapabilityOverride.create(capability_id,
                                                       datastore_version_id,
                                                       enabled)
        except Exception as e:
            print('Unable to add capability override: %s' % e)

    def remove_capability_override(self, capability_id, datastore_version_id):
        """Removes capability override on a datastore version."""
        try:
            capability_override = datastore_models.CapabilityOverride.load(
                capability_id, datastore_version_id)
            # TODO: (rramirez) ?????????? is there anything wrong with calling
            # CapabilityOverride.delete(), which is really just a call to
            # BaseCapability.delete()?
            capability_override.delete()
        except Exception as e:
            print('Unable to remove capability override: %s' % e)

    def remove_capability_overrides(self, capability_id, enabled='everything'):
        """Remove overrides for a capability."""
        try:
            datastore_models.CapabilityOverrides.delete_capability_overrides(
                capability_id, enabled)
        except Exception as e:
            print('Unable to remove capability overrides: %s' % e)


def main():

    def actions(subparser):
        parser = subparser.add_parser('db_sync')
        parser.add_argument('--repo_path')

        parser = subparser.add_parser('db_upgrade')
        parser.add_argument('--version')
        parser.add_argument('--repo_path')

        parser = subparser.add_parser('db_downgrade')
        parser.add_argument('version')
        parser.add_argument('--repo_path')

        parser = subparser.add_parser('datastore_update')
        parser.add_argument('datastore_name')
        parser.add_argument('default_version')

        parser = subparser.add_parser('datastore_version_update')
        parser.add_argument('datastore_id_or_name')
        parser.add_argument('version_name')
        parser.add_argument('manager')
        parser.add_argument('image_id')
        parser.add_argument('packages')
        parser.add_argument('active')

        parser = subparser.add_parser(
            'db_recreate', description='Drop the database and recreate it.')
        parser.add_argument(
            '--repo_path', help='SQLAlchemy Migrate repository path.')

        parser = subparser.add_parser('db_recreate')
        parser.add_argument('repo_path')

        parser = subparser.add_parser('add_capability')
        parser.add_argument('name')
        parser.add_argument('description')
        parser.add_argument('enabled')

        parser = subparser.add_parser('remove_capability')
        parser.add_argument('capability_id_or_name')

        parser = subparser.add_parser('add_capability_override')
        parser.add_argument('capability_id')
        parser.add_argument('datastore_version_id')
        parser.add_argument('enabled')

        parser = subparser.add_parser('remove_capability_override')
        parser.add_argument('capability_id')
        parser.add_argument('datastore_version_id')

        parser = subparser.add_parser('remove_capability_overrides')
        parser.add_argument('capability_id')
        parser.add_argument('enabled')

    cfg.custom_parser('action', actions)
    cfg.parse_args(sys.argv)

    try:
        logging.setup(None)

        Commands().execute()
        sys.exit(0)
    except TypeError as e:
        print(_("Possible wrong number of arguments supplied %s") % e)
        sys.exit(2)
    except Exception:
        print(_("Command failed, please check log for more info."))
        raise
