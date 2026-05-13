import unittest
from enum import StrEnum
from typing import Optional

from cqp_tree.configuration import *
from cqp_tree.configuration.configuration import (
    CONFIGURATION_ENTRIES,
    CONFIGURATION_VALUES,
    set_config_value,
)


def declaration(
    key: str = 'key',
    readable_name: str = 'name',
    readable_description: str = 'description',
    default_value: Optional = None,
    validation_type: type = None,
    validation_options: list[str] = None,
):
    return DeclaredConfig(
        key=key,
        readable_name=readable_name,
        readable_description=readable_description,
        default_value=default_value,
        validation_type=validation_type,
        validation_options=validation_options,
    )


class TestEnum(StrEnum):
    A = 'a'
    B = 'b'


class ConfigurationTests(unittest.TestCase):

    def setUp(self):
        CONFIGURATION_ENTRIES.clear()
        CONFIGURATION_VALUES.clear()

    def test_global_declaration_conflicts(self):
        d1 = declaration(key='key')
        d2 = declaration(key='key')

        declare_configuration(d1)
        with self.assertRaises(ValueError):
            declare_configuration(d2)

    def test_local_declaration_conflicts(self):
        d1 = declaration(key='key')
        d2 = declaration(key='key')

        declare_configuration(d1, 'frontend')
        with self.assertRaises(ValueError):
            declare_configuration(d2, 'frontend')

    def test_global_declaration_defaults(self):
        d = declaration(key='key', default_value='value')
        declare_configuration(d)

        cfg = get_global_config()
        self.assertEqual(cfg.key, 'value')

    def test_local_declaration_defaults(self):
        d = declaration(key='key', default_value='value')
        declare_configuration(d, 'frontend')

        cfg = get_frontend_configuration('frontend')
        self.assertEqual(cfg.key, 'value')

    def test_local_declaration_shadows(self):
        d1 = declaration(key='key', default_value='global')
        d2 = declaration(key='key', default_value='shadowed')

        declare_configuration(d1)
        declare_configuration(d2, 'frontend')

        cfg = get_frontend_configuration('frontend')
        self.assertEqual(cfg.key, 'shadowed')

    def test_declaration_with_empty_validation_fails(self):
        with self.assertRaises(ValueError):
            d = declaration(validation_options=[])
            declare_configuration(d)

    def test_declaration_with_invalid_type_fails(self):
        with self.assertRaises(ValueError):
            d = declaration(validation_type=type(None))
            declare_configuration(d)

    def test_bool_validation(self):
        d = declaration('key', validation_type=bool)
        declare_configuration(d)
        set_config_value('key', 'true')

        cfg = get_global_config()
        self.assertEqual(cfg.key, True)

    def test_int_validation(self):
        d = declaration('key', validation_type=int)
        declare_configuration(d)
        set_config_value('key', '123')

        cfg = get_global_config()
        self.assertEqual(cfg.key, 123)

    def test_float_validation(self):
        d = declaration('key', validation_type=float)
        declare_configuration(d)
        set_config_value('key', '1.2')

        cfg = get_global_config()
        self.assertEqual(cfg.key, 1.2)

    def test_str_validation(self):
        d = declaration('key', validation_type=str)
        declare_configuration(d)
        set_config_value('key', 'abc')

        cfg = get_global_config()
        self.assertEqual(cfg.key, 'abc')

    def test_list_validation(self):
        d = declaration('key', validation_options=['a', 'b', 'c'])
        declare_configuration(d)

        with self.assertRaises(ValueError):
            set_config_value('key', 'abc')

        set_config_value('key', 'a')
        cfg = get_global_config()
        self.assertEqual(cfg.key, 'a')

    def test_enum_validation(self):
        d = declaration('key', validation_type=TestEnum)
        declare_configuration(d)

        with self.assertRaises(ValueError):
            set_config_value('key', 'INVALID')
        set_config_value('key', 'b')

        cfg = get_global_config()
        self.assertEqual(cfg.key, TestEnum.B)
