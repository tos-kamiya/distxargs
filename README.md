# distxargs, Parallel execution with a pool of worker processes on cluster via ssh.

`distxargs` is a esay-to-use parallel execution of cli commands, basicaly a distributed version of `xargs -P`.

`distxargs` runs cli commands in a parallel way on host computers via ssh.
You can specify count of max processes for each of the host computers.

## Installation

To install disxargs script:

```
python3 -m pip install git+https://github.com/tos-kamiya/distxargs
```

A cli script `distxargs` will be installed.

To uninstall:

```
python3 -m pip uninstall distxargs
```

## Configuration

`distxargs` requires a configuration file `conf.distxargs.yaml`, which contains a list of host name and count of max processes for each host.

To prepare the configuration file, run the following command:

```
distxargs --generate-sample-config-file
```

And then edit the configuration like:

```
default:
  user_name: "toshihiro"

hosts:
- host_name: "localhost"
  max_processes: 2
- host_name: "node01"
  max_processes: 2
```

`distxargs` requires that each host can be connected using `ssh` command **without passwword** . If you do not sure about that, set up the hosts with following steps.

### SSH configuration for localhost

As for `localhost`, you can make it so with the following steps:

(1) If you do not have a public key for ssh (that is, a file `~/.ssh/id_rsa.pub`), generate it:

```
ssh-keygen -t rsa
(...Press enter for each line...)
```

(2) Add it to the authorized-key list:

```
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod og-wx ~/.ssh/authorized_keys
```

(refer https://stackoverflow.com/questions/7439563/how-to-ssh-to-localhost-without-password )

### SSH configuration for other hosts

As for the other hosts,

(1) Ensure you can login to the host with `ssh`:

```
ssh username@hostname
```

If the host do not ask password, you already have established a password-less connection to the host, so skip the following steps:

(2) Ensure you have a public key for ssh. If you do not have, make the key with the step (1) for localhost.

(3) Add the public key to a authorized-key list of the host.

```
ssh-copy-id username@hostname
```

If successfully done, you can now login to the host without password with `ssh`.

## CLI usage

`distxargs` has a limited subset of CLI options/arguments of command `xargs`

```
Usage:
  distxargs [options] (-n MAX_ARGS|-L MAX_ARGS) <command>...

Options:
  -a FILE           Read arguments from file.
  -I REPLACE_STR    Replace the string in command with arguments.
  -n MAX_ARGS       Max count of arguments passed to a process.
  -L MAX_ARGS       Same as `-n`, but arguments are separated by new line.
  -t                Show command line on command execution.
  -c_FILE           Configuration file. [default: ./conf.distxargs.yaml]
  --localhost-only  Run commands only on localhost.
  --generate-sample-config-file
```

## Example

```
echo alice bob charlie dave | distxargs -n 1 -t echo
ssh toshihiro@localhost echo alice
ssh toshihiro@localhost echo bob
ssh toshihiro@node01 echo charlie
ssh toshihiro@node01 echo dave
dave
charlie
bob
alice
```

## License

MIT License.
