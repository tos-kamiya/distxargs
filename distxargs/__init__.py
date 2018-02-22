#!/usr/bin/env python3

from collections import namedtuple, deque
import os
import os.path as path
import re
import sys
import time
import subprocess

import yaml


CONF_FILE = path.join(os.curdir, 'conf.distxargs.yaml')

HOST_NAME = 'host_name'
USER_NAME = 'user_name'
MAX_PROCESSES = 'max_processes'


HostConfig = namedtuple('HostConfig', ['host_name', 'user_name', 'max_processes'])
ProcessID = namedtuple('ProcessID', ['host_name', 'number'])


def is_localhost(addr):
    return addr in ('localhost', '127.0.0.1', '::1', '0000:0000:0000:0000:0000:0000:0000:0001', '0:0:0:0:0:0:0:1')


class ConfigKeyError(ValueError):
    pass


def read_config(config_file):
    host_config_table = dict()
    with open(config_file, 'r') as inp:
        yaml_data = yaml.load(inp)
        default_config = yaml_data.get('default')
        if default_config:
            k = set(default_config.keys()).difference_update([USER_NAME, MAX_PROCESSES])
            if k:
                raise ConfigKeyError('unknown config argument: %s' % repr(k[0]))
            default_user_name = default_config.get(USER_NAME)
            default_max_processes = default_config.get(MAX_PROCESSES)

        host_configs = yaml_data.get('hosts')
        for hc in host_configs:
            host_name = hc.get(HOST_NAME)
            assert host_name and isinstance(host_name, str)
            k = set(default_config.keys()).difference_update([USER_NAME, MAX_PROCESSES])
            if k:
                raise ConfigKeyError('unknown config argument: %s' % repr(k[0]))
            user_name = hc.get(USER_NAME)
            if user_name is None:
                user_name = default_user_name
                assert user_name and isinstance(user_name, str)
            max_processes = hc.get(MAX_PROCESSES)
            if max_processes is None:
                max_processes = default_max_processes
                assert max_processes >= 1
            host_config_table[host_name] = HostConfig(host_name, user_name, max_processes)
    return host_config_table



class WorkerPool:
    def __init__(self, host_config_table, cmd_template, replace_str, option_verbose=False):
        self.host_config_table = dict(host_config_table)
        self.cmd_template = cmd_template
        self.replace_str = replace_str
        self.option_verbose = option_verbose

        process_id_que = deque()
        for h, hc in sorted(host_config_table.items()):
            for i in range(hc.max_processes):
                process_id_que.append(ProcessID(h, i + 1))
        self.process_id_que = process_id_que
        self.running_procsses = []

    def has_running_processes(self):
        return len(self.running_procsses) >= 1

    def wait_until_one_process_ends(self):
        assert self.running_procsses
        while True:
            for i, (pi, p) in enumerate(self.running_procsses):
                r = p.poll()
                if r is not None:
                    del self.running_procsses[i]
                    return
            time.sleep(0.1)

    def alloc_process_id(self):
        if len(self.running_procsses) == len(self.process_id_que):
            self.wait_until_one_process_ends()
        for _ in range(len(self.process_id_que)):
            pi = self.process_id_que[0]
            if not any(pi == pi_p[0] for pi_p in self.running_procsses):
                return pi
            self.process_id_que.rotate(-1)
        assert False

    def run_process(self, chunk):
        chunk = [c.decode('utf-8') for c in chunk]
        idling_pi = self.alloc_process_id()
        hc = self.host_config_table[idling_pi.host_name]
        ssh_cmd = ['ssh', '%s@%s' % (hc.user_name, hc.host_name)]
        if self.replace_str:
            cmd = []
            replacement_occur = False
            for c in self.cmd_template:
                if self.replace_str in c:
                    c = c.replace(self.replace_str, ' '.join(chunk))
                    replacement_occur = True
                cmd.append(c)
            if not replacement_occur:
                sys.exit('no replacment string appear in command')
        else:
            cmd = self.cmd_template + chunk
        if self.option_verbose:
            print(' '.join(ssh_cmd + cmd))
        p = subprocess.Popen(ssh_cmd + cmd)
        self.running_procsses.append((idling_pi, p))


SAMPLE_CONFIG_FILE = '''
default:
  user_name: "alibaba"

hosts:
- host_name: "localhost"
  max_processes: 4
- host_name: "flyingcarpet"
  max_processes: 4
'''[1:]


__doc__ = '''Parallel execution with a pool of worker processes on cluster via ssh.

Usage:
  distxargs [options] (-n MAX_ARGS|-L MAX_ARGS) <command>...

Options:
  -a FILE           Read arguments from file.
  -I REPLACE_STR    Replace the string in command with arguments.
  -n MAX_ARGS       Max count of arguments passed to a process.
  -L MAX_ARGS       Same as `-n`, but arguments are separated by new line.
  -t                Show command line on command execution.
  -c_FILE           Configuration file. [default: {config_file}]
  --localhost-only  Run commands only on localhost.
  --generate-sample-config-file
'''.format(config_file=CONF_FILE)


def main():
    args = dict()
    commands = []
    argv = sys.argv[1:]
    def parse_option_with_param(option, a):
        assert a.startswith(option)
        if a == option:
            args[option] = argv.pop(0)
        else:
            args[option] = a[len(option):]

    while argv:
        a = argv.pop(0)
        if a.startswith('-a'):
            parse_option_with_param('-a', a)
        elif a.startswith('-c'):
            parse_option_with_param('-c', a)
        elif a.startswith('-I'):
            parse_option_with_param('-I', a)
        elif a.startswith('-n'):
            parse_option_with_param('-n', a)
        elif a.startswith('-L'):
            parse_option_with_param('-L', a)
        elif a == '-t':
            args['-t'] = True
        elif a == '--localhost-only':
            args['--localhost-only'] = True
        elif a in ('-h', '--help'):
            print(__doc__)
            return
        elif a == '--generate-sample-config-file':
            with open('conf.distxargs.yaml.sample', 'w') as outp:
                outp.write(SAMPLE_CONFIG_FILE)
            return
        else:
            commands.append(a)
            break  # while argv
    commands.extend(argv)

    option_verbose = args.get('-t')
    option_localhost_only = args.get('--localhost-only')

    if args.get('-c'):
        config_file = args.get('-c')
        if path.isdir(config_file):
            candidate_files = [
                path.join(config_file, CONF_FILE),
                path.join(config_file, '.config', 'distxargs', CONF_FILE),
            ]
            for f in candidate_files:
                if path.isfile(f):
                    config_file = f
                    break  # for f
    else:
        config_file = CONF_FILE
    if not path.isfile(config_file):
        sys.exit("no configuration file found")

    host_config_table = read_config(config_file)
    replace_str = args.get('-I')
    cmd_template = commands[:]

    if option_localhost_only:
        host_config_table = dict((h, hc) for h, hc in host_config_table.items() if is_localhost(hc.host_name))

    worker_pool = WorkerPool(host_config_table, cmd_template, replace_str, option_verbose=option_verbose)

    chunk_size = int(args.get('-n') or args.get('-L') or -1)
    if chunk_size <= 0:
        sys.exit('specify a positive integer to `-n` or `-L`')
    if args.get('-a'):
        inp = open(args['-a'], 'rb')
    else:
        inp = sys.stdin.buffer
    try:
        if args.get('-n'):
            for L in inp:
                L = L.rstrip()
                params = re.split(b'\\s+', L)
                while params:
                    chunk = params[:chunk_size]
                    params = params[chunk_size:]
                    worker_pool.run_process(chunk)
        elif args.get('-L'):
            params = []
            for L in inp:
                L = L.rstrip()
                params.append(L)
                if len(params) >= chunk_size:
                    worker_pool.run_process(params)
                    params = []
            else:
                if params:
                    worker_pool.run_process(params)
        else:
            assert False

        while worker_pool.has_running_processes():
            worker_pool.wait_until_one_process_ends()
    finally:
        if inp is not sys.stdin.buffer:
            inp.close()


if __name__ == '__main__':
    main()