import unittest
from unittest import mock
from unittest.mock import call

import riptide.config.document.app as module
from configcrunch import ConfigcrunchError
from tests.helpers import side_effect_for_load_subdocument
from configcrunch.test_utils import YamlConfigDocumentStub


class AppTestCase(unittest.TestCase):

    def test_header(self):
        app = module.App({})
        self.assertEqual(module.HEADER, app.header())

    def test_schema(self):
        """TODO"""

    @mock.patch("riptide.config.document.app.YamlConfigDocument.resolve_and_merge_references")
    def test_resolve_and_merge_references_no_subdocs(self, super_mock):
        doc = {
            'name': 'test'
        }
        app = module.App(doc)
        app.resolve_and_merge_references(['./path1', './path2'])
        super_mock.assert_called_once_with(['./path1', './path2'])

    @mock.patch('riptide.config.document.app.YamlConfigDocument.resolve_and_merge_references')
    def test_resolve_and_merge_references_with_services(self, super_mock):
        paths = ['path1', 'path2']

        service1 = {'key1': 'value1'}
        service2 = {'key2': 'value2'}
        doc = {
            'name': 'test',
            'services': {
                'service1': service1,
                'service2': service2
            }
        }

        with mock.patch(
                "riptide.config.document.app.load_subdocument",
                side_effect=side_effect_for_load_subdocument()
        ) as load_subdoc_mock:
            app = module.App(doc)
            app.resolve_and_merge_references(paths)

            self.assertIsInstance(app['services']['service1'], YamlConfigDocumentStub)
            self.assertIsInstance(app['services']['service2'], YamlConfigDocumentStub)
            self.assertEqual({'$name': 'service1', 'key1': 'value1'}, app['services']['service1'].doc)
            self.assertEqual({'$name': 'service2', 'key2': 'value2'}, app['services']['service2'].doc)

            super_mock.assert_called_once_with(paths)
            load_subdoc_mock.assert_has_calls([
                call(service1, app, module.Service, paths),
                call(service2, app, module.Service, paths)
            ], any_order=True)

    def test_resolve_and_merge_references_with_services_no_dict(self):

        paths = ['path1', 'path2']

        service1 = 'nodict'
        doc = {
            'name': 'test',
            'services': {
                'service1': service1,
            }
        }

        with mock.patch(
                "riptide.config.document.app.load_subdocument",
                side_effect=side_effect_for_load_subdocument()
        ):
            app = module.App(doc)
            with self.assertRaises(ConfigcrunchError):
                app.resolve_and_merge_references(paths)

    @mock.patch('riptide.config.document.app.YamlConfigDocument.resolve_and_merge_references')
    def test_resolve_and_merge_references_with_commands(self, super_mock):
        paths = ['path1', 'path2']

        cmd1 = {'key1': 'value1'}
        cmd2 = {'key2': 'value2'}
        doc = {
            'name': 'test',
            'commands': {
                'cmd1': cmd1,
                'cmd2': cmd2
            }
        }

        with mock.patch(
                "riptide.config.document.app.load_subdocument",
                side_effect=side_effect_for_load_subdocument()
        ) as load_subdoc_mock:
            app = module.App(doc)
            app.resolve_and_merge_references(paths)

            self.assertIsInstance(app['commands']['cmd1'], YamlConfigDocumentStub)
            self.assertIsInstance(app['commands']['cmd2'], YamlConfigDocumentStub)
            self.assertEqual({'$name': 'cmd1', 'key1': 'value1'}, app['commands']['cmd1'].doc)
            self.assertEqual({'$name': 'cmd2', 'key2': 'value2'}, app['commands']['cmd2'].doc)

            super_mock.assert_called_once_with(paths)
            load_subdoc_mock.assert_has_calls([
                call(cmd1, app, module.Command, paths),
                call(cmd2, app, module.Command, paths)
            ], any_order=True)

    def test_resolve_and_merge_references_with_commands_no_dict(self):

        paths = ['path1', 'path2']

        cmd1 = 'nodict'
        doc = {
            'name': 'test',
            'commands': {
                'cmd1': cmd1,
            }
        }

        with mock.patch(
                "riptide.config.document.app.load_subdocument",
                side_effect=side_effect_for_load_subdocument()
        ):
            app = module.App(doc)
            with self.assertRaises(ConfigcrunchError):
                app.resolve_and_merge_references(paths)

    def test_get_service_by_role(self):

        SEARCHED_ROLE = 'needle'

        service_no_roles = {
            '$name': 'service1'
        }

        service_not_searched_role = {
            '$name': 'service1',
            'roles': [
                'role1', 'role2', 'role3'
            ]
        }

        service_searched_role = {
            '$name': 'service1',
            'roles': [
                'role1', SEARCHED_ROLE, 'role2', 'role3'
            ]
        }

        doc = {
            'name': 'test',
            'services': {
                'service_no_roles': service_no_roles,
                'service_not_searched_role': service_not_searched_role,
                'service_searched_role': service_searched_role
            }
        }

        app = module.App(doc)

        self.assertEqual(service_searched_role,    app.get_service_by_role(SEARCHED_ROLE))