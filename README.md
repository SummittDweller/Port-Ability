# Port-Ability

Modified: Tuesday, August 16, 2018 10:40 AM

_Port-Ability_ is a Python 3 script, and associated files, designed to enable a simple, controlled, command-line DEV -> STAGE -> PROD development and deployment workflow for 'Dockerized' application stacks.

The goals of the project were to:

  - Leverage _Traefik_ and _Portainer_ to assist with stack creation, development, management and deployment.
  - Declare a home for application "stacks" containing a mix of application types such as Python, Flask, Drupal versions 6, 7 and 8, and more.  
  - Support easy local development (DEV), staging (STAGE), and deployment to production (PROD) environments.  
  - Provide easy engagement of IDEs, like PyCharm and PHPStorm, and XDebug in the local (DEV) environments.
  - Deployed PROD stacks should be easy to encrypt for secure SSL/TLS access and suitable for occupying a single Docker-ready VPS, or similar server, of reasonable scale.  
  - Configuration of this tool and the "stacks" it manages should be easy to define in a single file.

## Installation

_Port_Ability_ is currently dependent on Python 3 (version 3.6 in my case). In CentOS I recommend the process documented for CentOS at https://stackoverflow.com/questions/41328451/ssl-module-in-python-is-not-available-when-installing-package-with-pip3, or for Linux in general try https://www.tecmint.com/install-python-in-linux/ to ensure that Python 3 is installed.

_Port-Ability_ is built to run from its own Python 3 'virtual environment'.  I created my virtual environment following guidance in https://docs.python.org/3/tutorial/venv.html. My command sequence in OSX (or Linux) was...

```
cd ~
git clone https://github.com/SummittDweller/Port-Ability.git
cd ~/Port-Ability
mv -f app app-backup
python3 -m venv app     # assumes 'python3' runs a Python version 3 interpreter.  Mine is version 3.6
source app/bin/activate
rsync -aruvi app-backup/. app/ --exclude=bin --exclude=include --exclude=lib --exclude=pyvenv.cfg --progress
rm -fr app-backup
cd app
curl https://bootstrap.pypa.io/get-pip.py | python3
pip install -r requirements.txt
sudo ln -s ~/Port-Ability/app/port-ability.sh /usr/local/bin/port-ability
```

## Usage

Once installed you can open a terminal (command-line) window on your host and type `port-ability --help` to see the following:

```
usage: port-ability [-h] [-v] [--version] [-p] action target [target ...]

This is Port-Ability!

positional arguments:
  action           The action to be performed on the target(s)
  target           Target stacks (app and/or sites) to be processed

optional arguments:
  -h, --help       show this help message and exit
  -v, --verbosity  increase output verbosity (default: OFF)
  --version        show program's version number and exit
  -p               turns on Portainer inclusion
```

### Actions

Available actions are:

  - test -- This action returns information about...

    - Docker (the equivalent of `docker info`),
    - the _port-ability-proxy_ network,
    - the _traefik_ container,
    - and all containers that are part of the _target_ stack.


  - stop -- This action...

    - stops (as in `docker stop ...`) all _target_ containers,
    - removes the stopped containers along with non-persistent volumes (like `docker rm -v ...`), and
    - prunes unused Docker networks (like `docker prune`).


  - restart -- This action...

    - ensures that _traefik_ is running (restarting it if necessary),
    - stops all _target_ containers (just like the 'stop' action above), and
    - restarts the _target_ stack using the appropriate `docker-compose up -d` command.


  - backup -- @TODO Documentation to be provided.

  - fix-permissions -- @TODO Documentation to be provided.

  - pull-data -- @TODO Documentation to be provided.

#### test

It is recommended that the 'test' action be run with verbosity ov -vv.  For example, executing `port-ability -vv test wieting` in my DEV environment recently produced this output:

```
Port-Ability v1.0.0 (app/port_ability.py) called on Mark-iMac with arguments: -vv test wieting
OK, you are targeting 'traefik' in a 'dev' environment on host 'Mark-iMac'.
The 'port-ability-proxy' network already exists.  Moving on.
The 'Traefik' container already exists and is running.  Moving on.
OK, you are targeting 'wieting' in a 'dev' environment on host 'Mark-iMac'.
Launching a 'test' action for target 'wieting'.
Docker info:
   ID: 4RT4:NH4H:FV6B:4HHH:QVT2:AHWC:AGQ3:HR3K:L6MO:Q4HJ:QOGN:DDMU
   Containers: 21
   ContainersRunning: 21
   ContainersPaused: 0
   ContainersStopped: 0
   Images: 25
   Driver: overlay2
   DriverStatus: [['Backing Filesystem', 'extfs'], ['Supports d_type', 'true'], ['Native Overlay Diff', 'true']]
   SystemStatus: None
   Plugins: {'Volume': ['local'], 'Network': ['bridge', 'host', 'ipvlan', 'macvlan', 'null', 'overlay'], 'Authorization': None, 'Log': ['awslogs', 'fluentd', 'gcplogs', 'gelf', 'journald', 'json-file', 'logentries', 'splunk', 'syslog']}
   MemoryLimit: True
   SwapLimit: True
   KernelMemory: True
   CpuCfsPeriod: True
   CpuCfsQuota: True
   CPUShares: True
   CPUSet: True
   IPv4Forwarding: True
   BridgeNfIptables: True
   BridgeNfIp6tables: True
   Debug: True
   NFd: 367
   OomKillDisable: True
   NGoroutines: 363
   SystemTime: 2018-08-13T16:51:57.277249118Z
   LoggingDriver: json-file
   CgroupDriver: cgroupfs
   NEventsListener: 3
   KernelVersion: 4.9.93-linuxkit-aufs
   OperatingSystem: Docker for Mac
   OSType: linux
   Architecture: x86_64
   IndexServerAddress: https://index.docker.io/v1/
   RegistryConfig: {'AllowNondistributableArtifactsCIDRs': [], 'AllowNondistributableArtifactsHostnames': [], 'InsecureRegistryCIDRs': ['127.0.0.0/8'], 'IndexConfigs': {'docker.io': {'Name': 'docker.io', 'Mirrors': [], 'Secure': True, 'Official': True}}, 'Mirrors': []}
   NCPU: 2
   MemTotal: 2096058368
   GenericResources: None
   DockerRootDir: /var/lib/docker
   HttpProxy: gateway.docker.internal:3128
   HttpsProxy: gateway.docker.internal:3129
   NoProxy:
   Name: linuxkit-025000000001
   Labels: []
   ExperimentalBuild: True
   ServerVersion: 18.06.0-ce
   ClusterStore:
   ClusterAdvertise:
   Runtimes: {'runc': {'path': 'docker-runc'}}
   DefaultRuntime: runc
   Swarm: {'NodeID': '', 'NodeAddr': '', 'LocalNodeState': 'inactive', 'ControlAvailable': False, 'Error': '', 'RemoteManagers': None}
   LiveRestoreEnabled: False
   Isolation:
   InitBinary: docker-init
   ContainerdCommit: {'ID': 'd64c661f1d51c48782c9cec8fda7604785f93587', 'Expected': 'd64c661f1d51c48782c9cec8fda7604785f93587'}
   RuncCommit: {'ID': '69663f0bd4b60df09991c08812a60108003fa340', 'Expected': '69663f0bd4b60df09991c08812a60108003fa340'}
   InitCommit: {'ID': 'fec3683', 'Expected': 'fec3683'}
   SecurityOptions: ['name=seccomp,profile=default']
Container 'wieting_mariadb' exists with a status of: running.
Container 'wieting_nginx' exists with a status of: running.
Container 'wieting_php' exists with a status of: running.
That's all folks!
```

#### stop
@TODO Documentation to be provided.

#### restart
@TODO Documentation to be provided.

#### backup
@TODO Documentation to be provided.

#### fix-permissions
@TODO Documentation to be provided.

#### pull-data
@TODO Documentation to be provided.

## History

This project is a re-write of my earlier SummittServices.com (SS) project work.  It began as a stripped-down version of _SS_ with only _Traefik_ and _Portainer_ left in the original.  Much of the _Traefix_ and cert handling here was informed by https://www.digitalocean.com/community/tutorials/how-to-use-traefik-as-a-reverse-proxy-for-docker-containers-on-ubuntu-16-04.  

## Project Structure

```
Port-Ability  
|--app
  |--port-ability.sh
  |--port_ability.py         <-- The guts of Port-Ability
  |--requirements.txt  
|--docs
|--portainer
  |--docker-compose.yml
|--traefik  
  |--acme.json               <-- This file created for you.  DO NOT share it!
  |--traefik.toml.dev
  |--traefik.toml.stage
  |--traefik.toml.prod
|--_master                   <-- Your '.master.env' file goes here.  But DO NOT share it!
  | master.env.sample
|--README.md
```

# Everything below this point needs significant work!

## Basics
Some "as-built" resources and documents...

- The project environments are:

    - DEV = OSX host, my MacBook Air
    - STAGE = CentOS 7 host, my home Docker server
    - PROD = Grinnell College's DGDockerX CentOS 7 host

- Development and deployment are designed around the practice of "Code Up, Data Down".  Essentially, code is pushed up from DEV to PROD only, while data (databases and data files) are pulled only from PROD down to DEV.

- Network management leverages Traefik (https://docs.traefik.io/).  It makes obtaining and maintaining SSL/TLS certs a breeze.  

- Portainer (https://portainer.io/) is used to assist with management of the entire environment.  

- Lumogon (https://lumogon.com/) is used to inventory the environment as needed.  

- Atom is used for much of the editing and its _remote-sync_ package (defined in a _.remote-sync.json_ file) is employed to sync modifications between my DEV and PROD.


## Portainer

I have really become dependent on _Portainer_ to assist with all my Docker management activities, so much so that I decided to make it a 'site' of its own running in parallel to my other sites.  Note that _Portainer_ is launched with a `docker-compose.yml` file which includes _command_ and _volumes_ specs like this:

```
command: ${PORTAINER_AUTH} -H unix:///var/run/docker.sock
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

This means that a single instance of it running on your Docker host can detect EVERY container on the host.  So you only need ONE _Portainer_ per host, not one for every container as some bloggers apparently believe.

My PROD instance of _Portainer_ can be found at https://portainer.grinnell.edu, but it's password protected (as is https://traefik.grinnell.edu) so you can't necessarily see it.


## Scripts and Environment - Tieing It All Together

Very early on I created the *_scripts* directory to hold some of the _bash_ that I'd use to keep things tidy.  I also started with the notion of keeping all my secrets (passwords mostly) in _.env_ files, but this became cumbersome so I have consolidated all secrets here into a single _.master.env_ file and _restart.sh_ takes care of distribution.

### .env File

Clauses like `${PORTAINER_AUTH}` that you see in the code snippet above are references to these environment variables.  The `docker-compose` command automatically reads any `.env` file it finds in the same directory as the `docker-compose.yml` it is reading, so I followed suit by putting a `.env` file in every such directory.

`.env` files are also environment-specific.  There's a .master.env for DEV and a **different** copy for PROD, with some different values in each environment.  For example, in DEV `${PORTAINER_AUTH}` has a value of '--no-auth' specifying that no login/authorization is required; but in PROD that variable is set to '--admin-password $2abcdefg2tt2kMJhijklmnopxxxOkwvPqrstuvqmZOUiwxyzrJjibberish' which specifies that the _admin_ username requires a password for authentication.

A technique documented in https://docs.docker.com/compose/environment-variables/ is employed here to manage environment variables.

### restart.sh

I created the _restart.sh_ script in the *_scripts/* folder to assist with starting, or re-starting, a single site and it's containers. Specifically it...

  - Ensures that the external _port-ability-proxy_ network is up and running.

  - Is home to the `docker run -d...` command used to launch Traefik, and it ensures that the _traefik_ service is up and running.

  - In a loop, working on each target site...

      - Stops, then removes, all containers and unused not-persistent volumes associated with the site.

      - Temporarily copies _.master.env_ into the target *_sites* directory as _.env_ to provide environment settings to the container.

      - Invokes a `docker-compose up -d` command to bring the site's containers back up.

Suggested use of _restart.sh_ is to create a symbolic link on your host to launch it.  Ensure that the script is executable (`chmod u+x restart.sh`) and try something like this...

```
sudo ln -s /path/to/Port-Ability/_scripts/restart.sh /usr/local/bin/port-ability-restart
```
Launch the script by typing something like `port-ability-restart --portainer` in a host terminal.

See *_scripts/restart.sh* for complete details.

## Notes

Used https://docs.python.org/3/tutorial/venv.html to build the 'app' virtual environment on each node.

Requires Python 3 (with a python3 alias) which I installed on DGDockerX with help https://medium.com/@gkmr.aus/python-3-6-x-installation-centos-7-4-55ada041a03
