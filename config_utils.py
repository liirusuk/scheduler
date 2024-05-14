from argparse import ArgumentParser, RawDescriptionHelpFormatter
import os
from configparser import ConfigParser


def read_list(str_element):
    if str_element is None:
        return []
    else:
        return str_element.split('|')


def get_config(name, dname):
    config = ConfigParser()
    config.read(dname + '/config/' + name)
    return config


def update_defaults(defaults, config, remaining_argv):
    defaults.update(dict(config.items('DEFAULT', raw=True)))
    parser = ArgumentParser()
    parser.set_defaults(**defaults)
    for key in defaults:
        parser.add_argument(f'-{key}')
    args = parser.parse_args(remaining_argv)
    return args


def parse_config(argv, defaults=None):
    if defaults is None:
        defaults = {}
    conf_parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter, add_help=False)
    conf_parser.add_argument('-config', help='config path', dest='config', required=True)
    args, remaining_argv = conf_parser.parse_known_args(argv[1:])
    dname = os.path.dirname(argv[0])
    config = get_config(args.config, dname)
    args = update_defaults(defaults, config, remaining_argv)
    config['DEFAULT'].update(vars(args))
    return config
