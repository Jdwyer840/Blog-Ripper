from django.db import models


class Configuration(models.Model):
    VALUE_TYPE_CHOICES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('date', 'Date'),
        ('text', 'Text'),
        ('map', 'Map'),
    ]

    namespace = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    value_type = models.CharField(max_length=20, choices=VALUE_TYPE_CHOICES)
    value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.namespace}.{self.name} ({self.value_type})"

    unique_constraint_fields = ['namespace', 'name']

    _config_pattern_json = r'^\s*(\{|\[)'
    _config_pattern_ini = r'^\s*[a-zA-Z0-9_]+\s*=\s*.*'

        # @classmethod
        # def get_config(cls: typing.Any, namespace: str | list = None, name: str = None) -> ConfigDict | str:
        #
        #     is_namespace_list = type(namespace) is list
        #
        #     if name and not namespace:
        #         raise ValueError('namespace cannot be None if name is provided.')
        #     if name and is_namespace_list:
        #         raise ValueError('Cannot filter on name with multiple namespaces')
        #
        #     filters = {}
        #     if namespace:
        #         filters['namespace__in' if is_namespace_list else 'namespace'] = namespace
        #     if name:
        #         filters['name'] = name
        #
        #     namespace_configs = ConfigDict()
        #     is_production = CoreUtilities.truthy(os.getenv("PRODUCTION"))
        #     is_staging = CoreUtilities.truthy(os.getenv("STAGING"))
        #     is_development = not is_production and not is_staging
        #
        #     for row in list(cls.objects.filter(**filters).values()):
        #         if row['namespace'] not in namespace_configs:
        #             namespace_configs[row['namespace']] = ConfigDict()
        #         value = row['value']
        #         if (is_staging or is_development) and row['staging_value']:
        #             value = row['staging_value']
        #         if is_development and row['development_value']:
        #             value = row['development_value']
        #         namespace_configs[row['namespace']][row['name']] = value
        #     final_config = ConfigDict()
        #
        #     for namespace_config in namespace_configs:
        #         section_configs = ConfigDict()
        #         for key, value in namespace_configs[namespace_config].items():
        #             if CoreUtilities.regex_matches(ConfigurationDDL._config_pattern_json, value):
        #                 section_configs[key] = CoreUtilities.json_loads_relaxed(value)
        #             elif CoreUtilities.regex_matches(ConfigurationDDL._config_pattern_ini, value, re.MULTILINE):
        #                 configparser = ConfigParser()
        #                 configparser.read_string(f'[{key}]\n{value}')
        #                 section_configs.update(ConfigDict({s: ConfigDict(configparser.items(s)) for s in configparser.sections()}))
        #             else:
        #                 section_configs[key] = value
        #         final_config[namespace_config] = section_configs
        #
        #     final_config.namespace = namespace
        #
        #     try:
        #         if namespace and not is_namespace_list:
        #             final_config = final_config[namespace]
        #             final_config.namespace = namespace
        #     except ConfigDict.MissingConfigurationField:
        #         # This exception will show the namespace twice unless we catch and correct it.
        #         raise ConfigDict.MissingConfigurationField(namespace, name)
        #
        #     if name:
        #         final_config = final_config[name]
        #         if isinstance(final_config, ConfigDict):
        #             final_config.namespace = namespace
        #
        #     return final_config
        #
        # @classmethod
        # def get_namespace_settings(cls: Any, namespace: str) -> ConfigDict:
        #     return cls.get_config(namespace=namespace)