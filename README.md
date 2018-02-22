# distxargs, A parallel distributed version of xargs -P.

`distxargs` is a easy-to-use parallel execution of cli commands, basically a **distributed version of `xargs -P` **.

* Runs cli commands in a parallel way on host computers via ssh.
* Selects a host to run a cli command, depending on the number of running process on it at that time (a dynamic scheduling).
* Can put a distinct limitation of max processes to each host.

## Installation

To install `disxargs`:

```
python3 -m pip install git+https://github.com/tos-kamiya/distxargs
```

A cli script `distxargs` will be installed.

To uninstall:

```
python3 -m pip uninstall distxargs
```

## Configuration of hosts

`distxargs` requires that each host can be connected using `ssh` command **without password** . If you are not sure about that, set up the hosts with the following instruction.

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

If the host does not ask password, you already have established a password-less connection to the host, so skip the following steps:

(2) Ensure you have a public key for ssh. If you do not have, make the key with the step (1) for localhost.

(3) Add the public key to an authorized-key list of the host.

```
ssh-copy-id username@hostname
```

If successfully done, you can now login to the host without password with `ssh`.

## CLI usage

`distxargs` has a limited (and slightly modified) subset of CLI options/arguments of command `xargs`

```
Usage:
  distxargs [options] (-n MAX_ARGS|-L MAX_ARGS) (-P PROCESSES,USER@HOST...|-c FILE) <command>...

Options:
  -a FILE           Read arguments from file.
  -P PROCESSES,USER@HOST...     Specify max count of processes of a host.
  -I REPLACE_STR    Replace the string in command with arguments.
  -n MAX_ARGS       Max count of arguments passed to a process.
  -L MAX_ARGS       Same as `-n`, but arguments are separated by new line.
  -t                Show command line on command execution.
  -c FILE           Configuration file. [default: ./conf.distxargs.yaml]
  --localhost-only  Run commands only on localhost.
  --generate-sample-config-file
```

### Example

Runs `echo` commands total 5 times on 2 computers (hosts).
The `localhost` runs up to one process at a time.
A host `node1` runs up to two processes at a time.

```
echo alice bob charlie dave eve | distxargs \
-P 1,toshihiro@localhost -P 2,toshihiro@node1 -n1 -t -I '{}' \
echo hello, '{}'!
ssh toshihiro@localhost echo hello, alice!
ssh toshihiro@node1 echo hello, bob!
ssh toshihiro@node1 echo hello, charlie!
hello, charlie!
hello, bob!
ssh toshihiro@node1 echo hello, dave!
ssh toshihiro@node1 echo hello, eve!
hello, alice!
hello, dave!
hello, eve!
```

### Configuration file

If you feel annoying to specify option `-P`s every time you run `distxargs`,
consider to use a configuration file `./conf.distxargs.yaml`, containing a list of host name and count of max processes for each host.

To prepare the configuration file, run the following command:

```
distxargs --generate-sample-config-file
```

And then edit the configuration and save to a file `./conf.distxargs.yaml`:

```
default:
  user_name: "toshihiro"

hosts:
- host_name: "localhost"
  max_processes: 1
- host_name: "node01"
  max_processes: 2
```

Then the command line of the above example will become:

```
echo alice bob charlie dave eve | distxargs -c. -n1 -t -I '{}' echo hello, '{}'!
```

You can make a default configuration file by saving a configuration file to a path `~/.confg/distxargs/conf.distxargs.conf` .

In case of use the default configuration file, add option `-c~` to the command line:

```
echo alice bob charlie dave eve | distxargs -c~ -n1 -t -I '{}' echo hello, '{}'!
```

## License

MIT License.
