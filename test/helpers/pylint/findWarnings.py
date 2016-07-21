from .helpers            import get_pylint_output, write_output
from ..automation_tools import read_yaml

def find_warnings():
    print('Generating warnings in all of pygsti. This takes around 30 seconds')
    config    = read_yaml('pylint_config.yml')
    blacklist = config['blacklisted-warnings']
    commands  = [config['pylint-version'],
                 '--disable=R,C,E,%s' % ','.join(blacklist),
                 '--rcfile=%s' % config['config-file'],
                 '--reports=n'] + config['packages']
    output = get_pylint_output(commands, 'warnings')
