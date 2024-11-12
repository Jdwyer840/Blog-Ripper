from configparser import ConfigParser
from typing import Union

from django.db import models

from utilities.common import CoreUtilities
from utilities.model_helpers import ConfigDict


class Configuration(models.Model):
    class ValueTypeChoices(models.TextChoices):
        STR = 'string', 'String'
        INTEGER = 'integer', 'Integer'
        BOOLEAN = 'boolean', 'Boolean'
        JSON = 'json', 'JSON'
        DATE = 'date', 'Date'
        TEXT = 'text', 'Text'
        MAP = 'map', 'Map'

    namespace = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    value_type = models.CharField(max_length=20, choices=ValueTypeChoices.choices, default=ValueTypeChoices.STR)
    value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.namespace}.{self.name} ({self.value_type})"

    unique_constraint_fields = ['namespace', 'name']

    _config_pattern_json = r'^\s*(\{|\[)'
    _config_pattern_ini = r'^\s*[a-zA-Z0-9_]+\s*=\s*.*'

    @classmethod
    def get_config(cls, namespace: Union[str, list] = None, name: str = None) -> ConfigDict | str:
        is_namespace_list = isinstance(namespace, list)

        if name and not namespace:
            raise ValueError('namespace cannot be None if name is provided.')
        if name and is_namespace_list:
            raise ValueError('Cannot filter on name with multiple namespaces')

        filters = {}
        if namespace:
            filters['namespace__in' if is_namespace_list else 'namespace'] = namespace
        if name:
            filters['name'] = name

        namespace_configs = ConfigDict()

        for row in cls.objects.filter(**filters).values():
            # Initialize the namespace in the dictionary if it doesn’t exist
            if row['namespace'] not in namespace_configs:
                namespace_configs[row['namespace']] = ConfigDict()

            # Use only the primary 'value' field
            namespace_configs[row['namespace']][row['name']] = row['value']

        final_config = ConfigDict()

        # Process each namespace configuration and handle value parsing
        for namespace_config in namespace_configs:
            section_configs = ConfigDict()
            for key, value in namespace_configs[namespace_config].items():
                if CoreUtilities.regex_matches(Configuration._config_pattern_json, value):
                    section_configs[key] = CoreUtilities.json_loads_relaxed(value)
                elif CoreUtilities.regex_matches(Configuration._config_pattern_ini, value, re.MULTILINE):
                    configparser = ConfigParser()
                    configparser.read_string(f'[{key}]\n{value}')
                    section_configs.update(
                        ConfigDict({s: ConfigDict(configparser.items(s)) for s in configparser.sections()})
                    )
                else:
                    section_configs[key] = value
            final_config[namespace_config] = section_configs

        # Adjust final_config based on namespace presence and type
        final_config.namespace = namespace

        try:
            if namespace and not is_namespace_list:
                final_config = final_config[namespace]
                final_config.namespace = namespace
        except ConfigDict.MissingConfigurationField:
            raise ConfigDict.MissingConfigurationField(namespace, name)

        if name:
            final_config = final_config[name]
            if isinstance(final_config, ConfigDict):
                final_config.namespace = namespace

        return final_config

    @classmethod
    def get_namespace_settings(cls, namespace: str) -> ConfigDict:
        return cls.get_config(namespace=namespace)