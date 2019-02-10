import os

from schema import Schema, Optional, Or

from configcrunch import YamlConfigDocument
from configcrunch.abstract import variable_helper
from riptide.config.files import get_project_meta_folder, CONTAINER_SRC_PATH, CONTAINER_HOME_PATH
from riptide.config.service.config_files import get_config_file_path
from riptide.lib.cross_platform import cppath


class Command(YamlConfigDocument):

    @classmethod
    def header(cls) -> str:
        return "command"

    def schema(self) -> Schema:
        return Schema(
            Or({
                Optional('$ref'): str,  # reference to other Service documents
                Optional('$name'): str,  # Added by system during processing parent app.

                Optional('image'): str,
                Optional('command'): str,
                Optional('additional_volumes'): [
                    {
                        'host': str,
                        'container': str,
                        Optional('mode'): str  # default: rw - can be rw/ro.
                    }
                ]
            }, {
                Optional('$ref'): str,  # reference to other Service documents
                Optional('$name'): str,  # Added by system during processing parent app.

                Optional('aliases'): str
            })
        )

    def process_vars(self) -> 'YamlConfigDocument':
        # todo needs to happen after variables have been processed, but we need a cleaner callback for this
        super().process_vars()

        # Normalize all host-paths to only use the system-type directory separator
        if "additional_volumes" in self:
            for obj in self.doc["additional_volumes"]:
                obj["host"] = cppath.normalize(obj["host"])

        return self

    def get_project(self):
        try:
            return self.parent_doc.parent_doc
        except Exception as ex:
            raise IndexError("Expected command to have a project assigned") from ex

    def collect_volumes(self):
        """
        Collect volume mappings that this command should be getting when running.
        Volumes are built from following sources:
        - Source code is mounted as volume if role "src" is set
        - additional_volumes are added.
        """
        project = self.get_project()
        volumes = {}

        # source code
        volumes[project.src_folder()] = {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'}

        # additional_volumes
        # todo: merge with services logic
        if "additional_volumes" in self:
            for vol in self["additional_volumes"]:
                # ~ paths
                if vol["host"][0] == "~":
                    vol["host"] = os.path.expanduser("~") + vol["host"][1:]
                # Relative paths
                if not os.path.isabs(vol["host"]):
                    vol["host"] = os.path.join(project.folder(), vol["host"])

                mode = vol["mode"] if "mode" in vol else "rw"
                volumes[vol["host"]] = {'bind': vol["container"], 'mode': mode}

        return volumes

    def resolve_alias(self):
        """ If this is not an alias, returns self. Otherwise returns command that is aliased by this (recursively). """
        if "aliases" in self:
            return self.parent()["commands"][self["aliases"]].resolve_alias()
        return self

    def collect_environment(self):
        """
        Collect environment variables from the "environment" entry in the service
        configuration.
        # TODO: This propably is really not the best idea
        The passed environment is simple all of the riptide's process environment,
        minus some important meta-variables such as USERNAME and PATH.
        Adds HOME to be /home_cmd.
        :return:
        """
        env = os.environ.copy()
        keys_to_remove = {"PATH", "PS1", "USERNAME", "PWD", "SHELL", "HOME"}.intersection(set(env.keys()))
        for key in keys_to_remove:
            del env[key]
        return env

    @variable_helper
    def volume_path(self):
        path = os.path.join(get_project_meta_folder(self.get_project().folder()), 'cmd_data', self["$name"])
        os.makedirs(path, exist_ok=True)
        return path

    @variable_helper
    def home_path(self):
        return CONTAINER_HOME_PATH
