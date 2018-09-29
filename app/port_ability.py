#!/usr/bin/env python3

#--------------------------------------------------------------------------------------
# port_ability.py      Modified: Saturday, September 29, 2018 7:56 AM
#
#
# If Pythonized...
#
#   This Python3 application has its own 'virtual environment'.
#   Follow https://docs.python.org/3/tutorial/venv.html for guidance to create,
#   activate and use it.
#
#   My command sequence was...
#
#     cd ~/Port-Ability; mv -f app app-backup; python3 -m venv app; source app/bin/activate
#     rsync -aruvi app-backup/. app/ --exclude=bin --exclude=include --exclude=lib --exclude=pyvenv.cfg --progress
#     rm -fr app-backup; cd app; curl https://bootstrap.pypa.io/get-pip.py | python3; pip install -r requirements.txt
#
#   Packaging and distribution of this utility should follow the guidance provided at
#     https://packaging.python.org/tutorials/packaging-projects/
#
# If Dockerized...
#
#   CAUTION!!!  I was never able to get a "Dockerized" version of Port-Ability to work properly
#   in all environements.  Enter at your own risk!
#
#   This Python3 application should be launched via Docker using the provided
#   port-ability.sh Bash script, and Dockerfile.
#
# In either case, for convenience you should define a symbolic link in your path like so:
#
#     sudo ln -s ~/Port-Ability/app/port-ability.sh /usr/local/bin/port-ability
#
#--------------------------------------------------------------------------------------

#--- Config data here ----------------
VERSION = "1.7.1"
identify = "Port-Ability v{0}".format(VERSION)

with open('./app/port_ability.py', 'r') as inF:
  for line in inF:
    if 'Modified: ' in line:
      trash, mod = line.split('Modified:', 2)
      extra_info = "Modified: " + mod.strip()
      break

with open('./_master/.master.env', 'r') as inF:
  for line in inF:
    if 'Modified: ' in line:
      trash, mod = line.split('Modified:', 2)
      master_info = ".master.env Modified: " + mod.strip()
      break

available_actions = ['test', 'stop', 'restart', 'backup', 'fix-permissions', 'pull-data', 'push-code']


import sys
import argparse
import socket
import docker
import configparser
import os
import datetime
import glob
import pwd
import grp
import shutil

from colorama import init, Fore, Back, Style

#--------------------------------
#
# Note: The following is based largely on the guidance and
# script found at https://www.drupal.org/node/244924

def do_fix_permissions(target, target_env):
  global base_dir

  try:
    target_env['DRUPAL_VERSION']
  except KeyError:
    yellow("{0} is not a Drupal stack and will be ignored.".format(target))
    return
  except:
    unexpected()
    raise

  drupal_path = target_env['STACKS'] + '/' + target_env['PROJECT_PATH'] + '/html/web'
  core = drupal_path + '/core/modules/system/system.module'
  modules = drupal_path + '/modules/system/system.module'
  sites = drupal_path + '/sites'
  private = target_env['STACKS'] + '/' + target_env['PROJECT_PATH'] + '/html/private'

  if not os.path.isdir(drupal_path) and not os.path.isfile(core) and not os.path.isfile(modules):
    red("ERROR: Please provide a valid Drupal path.")
    return

  try:
    user = target_env['DRUPAL_USER']
    group = target_env['HTTPD_GROUP']
  except KeyError:
    red("ERROR: DRUPAL_USER and HTTPD_GROUP must be defined in your .master.env file!")
    return
  except:
    unexpected()
    raise

  # os.chdir(drupal_path)
  uid = pwd.getpwnam(user).pw_uid
  gid = grp.getgrnam(group).gr_gid

  # for dirpath, dirs, files in os.walk("."):
  #   path = dirpath.split('/')
  #   print('|', (len(path)) * '---', '[', os.path.basename(dirpath), ']')
  #   for f in files:
  #     print('|', len(path) * '---', f)

  normal("Changing ownership of '{0}' to '{1}:{2}'.".format(drupal_path, user, group))
  for root, dirs, files in os.walk(drupal_path):
    for name in dirs:
      p = os.path.join(root, name)
      # debug("Changing ownership of directory '{0}'.".format(p))
      try:
        os.chown(p, uid, gid)
      except PermissionError:
        yellow("Could not change ownership of directory '{0}'.".format(p))
      except:
        unexpected( )
        raise

    for name in files:
      p = os.path.join(root, name)
      # debug("Changing ownership of file '{0}.".format(p))
      try:
        os.chown(p, uid, gid)
      except PermissionError:
        yellow("Could not change ownership of file '{0}'.".format(p))
      except:
        unexpected( )
        raise

  normal("Changing permissions of all directories inside '{0}' to 'rwxr-xr-x'.".format(drupal_path))   # was rwxr-xr-x
  for root, dirs, files in os.walk(drupal_path):
    for name in dirs:
      p = os.path.join(root, name)
      # debug("Changing permissions of directory '{0}' to 'rwxr-xr-x'.".format(p))
      try:
        os.chmod(p, 0o755)
      except PermissionError:
        yellow("Could not change permissions of directory '{0}'.".format(p))
      except:
        unexpected( )
        raise

  normal("Changing permissions of all files inside '{0}' to 'rw-r--r--'.".format(drupal_path))   # was rw-r-----
  for root, dirs, files in os.walk(drupal_path):
    for name in files:
      p = os.path.join(root, name)
      # debug("Changing permissions of file '{0}' to 'rw-r--r--'.".format(p))
      try:
        os.chmod(p, 0o644)
      except PermissionError:
        yellow("Could not change permissions of file '{0}'.".format(p))
      except:
        unexpected( )
        raise

  # Find all sites/*/files directories...
  filesDirs = []
  path = sites + "/*/files"
  normal("Changing permissions of all 'files' directories in '{0}' to 'rwxrwxrwx'.".format(path))   # was rwxrwx---

  for root, dirs, files in os.walk(sites):
    for name in dirs:
      if name == 'files':
        p = os.path.join(root, name)
        filesDirs.append(p)
        # debug("Changing permissions of directory '{0}' to 'rwxrwxrwx'.".format(p))
        try:
          os.chmod(p, 0o777)
        except PermissionError:
          yellow("Could not change permissions of directory '{0}'.".format(p))
        except:
          unexpected( )
          raise

  # Loop on each */files directory under sites...
  for d in filesDirs:
    normal("Changing permissions of all files inside '{0}' to 'rw-rw-r--'.".format(d))  # was rw-rw----
    for root, dirs, files in os.walk(d):
      for name in files:
        p = os.path.join(root, name)
        # debug("Changing permissions of file '{0}' to 'rw-rw-r--'.".format(p))
        try:
          os.chmod(p, 0o664)
        except PermissionError:
          yellow("Could not change permissions of file '{0}'.".format(p))
        except:
          unexpected( )
          raise

    # Specials... not from https://www.drupal.org/node/244924

      for name in dirs:
        if name in ['js', 'ctools', 'css'] :
          p = os.path.join(root, name)
          # debug("Changing permissions of directory '{0}' to 'rwxrwxrwx'.".format(p))
          try:
            os.chmod(p, 0o777)
          except PermissionError:
            yellow("Could not change permissions of file '{0}'.".format(p))
          except:
            unexpected( )
            raise

    # normal("Changing permissions of all directories inside '{0}' to 'rwxrwx---'.".format(d))  # was rwxrwxrwx
    # for root, dirs, files in os.walk(d):
    #   for name in dirs:
    #     p = os.path.join(root, name)
    #     debug("Changing permissions of directory '{0}' to 'rwxrwx---'.".format(p))
    #     os.chmod(p, 0o770)

  # Set 'private' directory permissions too
  debug("Changing permissions of directory '{0}' to 'rwxrwxrwx'.".format(private))
  try:
    os.chmod(private, 0o777)
  except PermissionError:
    yellow("Could not change permissions of directory '{0}'.".format(private))
  except:
    unexpected( )
    raise


#--------------------------------
def do_test(target, target_env):
  global client, do_not_repeat

  containers = target_env['CONTAINERS'].strip("'").split(' ')

  if not do_not_repeat:
    info = client.info( )
    yellow("Docker info: ")
    for key, val in info.items( ):
      yellow("   {0}: {1}".format(key, val))
    do_not_repeat = True

  for container in containers:
    cont_name = "{0}_{1}".format(target, container)

    try:
      cont = client.containers.get(cont_name)
      green("Container '{0}' exists with a status of: {1}.".format(cont_name, cont.status))
    except docker.errors.NotFound:
      magenta("Container '{0}' does not exist.".format(cont_name))
    except:
      unexpected()
      raise

#--------------------------------
def do_stop(target, target_env):
  global client, do_not_repeat

  # If portainer specified, stop Traefik too
  if target == 'portainer':
    try:
      cont = client.containers.get('traefik')
      if cont.status == 'running':
        cont.stop( )
        normal("Traefik container has been stopped.")
      cont.remove(v=True)
      normal("The Traefik container and associated non-persistent volumes have been removed.")
    except docker.errors.NotFound:
      yellow("Traefik container does not exist.  Nothing to stop or remove.")
    except:
      unexpected( )
      raise

  # Now, stop the target
  remove_containers(target, target_env)

  # And prune the networks
  client.networks.prune( )
  green("Unused Docker networks have been pruned.")

#--------------------------------
def do_restart(target, target_env):

  remove_containers(target, target_env)

  restart_containers(target, target_env)

  # If target_env['POST_RESTART_SCRIPT'] is defined, do an os.system( ) call with it.  Added in v1.2.0
  try:
    script = target_env['POST_RESTART_SCRIPT']
    green("Attempting to run POST_RESTART_SCRIPT '{0}'.".format(script))
    os.system(script)
  except KeyError:
    debug("There is no POST_RESTART_SCRIPT environment key defined for this target.  Moving on.")
  except:
    unexpected( )
    raise

#--------------------------------
def do_push_code(target, target_env):
  global client, base_dir

  # Determine the target's Drupal version.  If None, there's no backup to be done.
  try:
    v = target_env['DRUPAL_VERSION']
  except:
    yellow("Target '{0}' has no DRUPAL_VERSION parameter so no Drupal code-push is possible".format(target))
    return

  # This only works for a DEV server!
  e = target_env['ENVIRONMENT']
  if not e == 'dev':
    yellow("This action can only be run from a DEV server!")
    return

  # Build an rsync command to push the code from the target directory to PROD...
  cmd = "rsync -aruvi {4}/{3}/. {0}@{1}:{2}/{3}/ --progress --exclude=mariadb-init/ --exclude=sites/{3}/files/".format(target_env['PROD_SERVER_USER'], target_env['PROD_SERVER_ADDRESS'], target_env['PROD_SERVER_STACKS'], target, target_env['STACKS'])
  green("Pushing code via: '{0}'".format(cmd))
  try:
    # debug("Command '{0}' is disabled.".format(cmd))
    os.system(cmd)
  except:
    unexpected( )
    raise

#--------------------------------
def do_pull_data(target, target_env):
  global client, base_dir

  # Determine the target's Drupal version.  If None, there's no backup to be done.
  try:
    v = target_env['DRUPAL_VERSION']
  except:
    yellow("Target '{0}' has no DRUPAL_VERSION parameter so no Drupal data-pull is necessary".format(target))
    return

  # This only works for a DEV server!
  e = target_env['ENVIRONMENT']
  if not e == 'dev':
    yellow("This action can only be run from a DEV server!")
    return

  # Build and execute a remote 'port-ability backup' command. @TODO Not working.
  # do_drupal_backup(target, target_env)

  # Move all local *.sql files from mariadb-init to .inactive
  cmd = "rsync -aruvi {1}/{0}/mariadb-init/*.sql {1}/{0}/mariadb-init/.inactive/ --progress --remove-source-files".format(target, target_env['STACKS'])
  green("Moving all *.sql files from mariadb-init to .inactive: '{0}'".format(cmd))
  try:
    # debug("Command '{0}' is disabled.".format(cmd))
    os.system(cmd)
  except:
    unexpected( )
    raise

  # Build an rsync command to pull the SQL...
  cmd = "rsync -aruvi {0}@{1}:{2}/{3}/mariadb-init/. {4}/{3}/mariadb-init/ --exclude=.inactive --progress".format(target_env['PROD_SERVER_USER'], target_env['PROD_SERVER_ADDRESS'], target_env['PROD_SERVER_STACKS'], target, target_env['STACKS'])
  green("Fetching SQL data via: '{0}'".format(cmd))
  try:
    # debug("Command '{0}' is disabled.".format(cmd))
    os.system(cmd)
  except:
    unexpected( )
    raise

  #...and 'files' contents back to this DEV server.
  cmd = "rsync -aruvi {0}@{1}:{2}/{3}/html/web/sites/{3}/files/. {4}/{3}/html/web/sites/{3}/files/ --progress".format(target_env['PROD_SERVER_USER'], target_env['PROD_SERVER_ADDRESS'], target_env['PROD_SERVER_STACKS'], target, target_env['STACKS'])
  green("Fetching 'files' via: '{0}'".format(cmd))
  try:
    # debug("Command '{0}' is disabled.".format(cmd))
    os.system(cmd)
  except:
    unexpected( )
    raise

#--------------------------------
def do_drupal_backup(target, target_env):
  global client, base_dir

  # Determine the target's Drupal version.  If None, there's no backup to be done.
  try:
    v = target_env['DRUPAL_VERSION']
  except:
    yellow("Target '{0}' has no DRUPAL_VERSION parameter so no Drupal backup is necessary".format(target))
    return

  # Clear all Drupal caches
  container = "{0}_php".format(target)
  if v == 8:
    clear = "cr"
  else:
    clear = "cc all"

  # Launch Drush in the PHP container to clear the cache
  cmd = "drush @{0}.dev {1}".format(target, clear)
  try:
    cont = client.containers.get(container)
    normal("Attempting to clear Drupal caches in {0}.  Be patient, this could take a minute.".format(container))
    cont.exec_run(cmd)
    green("Drupal caches were successfully cleared in '{0}'.".format(container))
  except docker.errors.NotFound:
    yellow("There is no '{0}' container to backup.".format(container))
    return
  except:
    unexpected( )
    raise

  stack = "{0}/{1}".format(target_env['STACKS'], target)

  # Drush again to dump the SQL
  now = datetime.datetime.now( )
  stamp = now.strftime('%Y-%m-%d-%H-%M')
  dest = "{0}/mariadb-init/sql-dump_{1}.tmp".format(stack, stamp)
  cmd = "drush @{0}.dev sql-dump".format(target)

  try:
    normal("Attempting to dump SQL in '{0}'.  Be patient, this could take a minute.".format(container))
    (exit_code, output) = cont.exec_run(cmd)
    if exit_code == 0:
      with open(dest, 'wb') as sql:
        sql.write(output)
      green("SQL successfully dumped to '{0}'.".format(dest))
    else:
      red("ERROR: SQL dump ended with an exit code of {0}".format(exit_code))
      return
  except:
    unexpected( )
    raise

  # Move all previous dump(s) to .inactive
  inactive = "{0}/mariadb-init/.inactive".format(stack)

  if not os.path.isdir(inactive):
    os.mkdir(inactive)

  wild = "{0}/mariadb-init/*.sql".format(stack)
  for sql_file in glob.iglob(wild):
    moved = sql_file.replace('mariadb-init', 'mariadb-init/.inactive')
    normal("Moving old SQL '{0}' to '{1}'.".format(sql_file, moved))
    os.rename(sql_file, moved)

  # Concatenate sql.header to the new SQL dump
  header = "{0}/mariadb-init/sql.header".format(stack)
  files = [header, dest]
  final = "{0}/mariadb-init/sql-dump_{1}.sql".format(stack, stamp)
  normal("Concatenating '{0}' and '{1}' to make '{2}'.".format(header, dest, final))

  with open(final, 'w') as outfile:
    for fname in files:
      with open(fname) as infile:
        for line in infile:
          outfile.write(line)

  # Remove any remaining *.tmp files
  wild = "{0}/mariadb-init/*.tmp".format(stack)
  normal("Removing all temporary '{0}' files.".format(wild))
  for tmp_file in glob.iglob(wild):
    os.unlink(tmp_file)

#--------------------------------
def master_parser(target):
  global host, base_dir, environ, args

  environ = dict( )

  # Parse the .master.env file
  config = configparser.ConfigParser()
  config.optionxform = str    # preserve case
  config.read(base_dir + '/_master/.master.env')

  # Process all of the 'required' key=value pairs.
  process_section('required', 'ERROR', config)

  # Check the PA_VERSION variable versus the version number of this script.
  version_found = False
  required = config.items('required')

  for key, value in required:
    if key == 'PA_VERSION':
      (val, comment) = value.split(' ', 1)
      parts = val.split('.', 2)
      min_version = int(parts[0])*100 + int(parts[1])*10 + int(parts[2])
      parts = VERSION.split('.', 2)
      this_version = int(parts[0])*100 + int(parts[1])*10 + int(parts[2])
      if min_version > this_version:
        red("ERROR: Your '.master.env' file specifies a minimum Port-Ability version of '{0}' but this script is version '{1}'!\n\n".format(val, VERSION))
        sys.exit(20)
      else:
        version_found = True
      break

  if not version_found:
    red("ERROR: Your '.master.env' file does not specify a reqiured 'PA_VERSION'!\n\n")
    sys.exit(30)

  # Make sure the host is in our [servers] list.
  try:
    servers = config.items('servers')
  except:
    red("ERROR: Your '.master.env' file must have a [{0}] section!\n\n".format('servers'))
    sys.exit(100)

  try:
    targets = config.items('targets')
  except:
    red("ERROR: Your '.master.env' file must have a [{0}] section!\n\n".format('targets'))
    sys.exit(101)

  server_found = False

  for key, value in servers:
    environment = value.split(' ')[0]
    if key == host:
      normal("Found '{0}' key in [{1}] with a value of: '{2}'.".format(key, 'servers', environment))
      environ['HOST'] = host
      server_found = True
      break

  if not server_found:
    red("ERROR: Sorry, this host, '{0}' is not in the list of [servers] found in .master.env!\n\n".format(host))
    sys.exit(110)

  target_found = False

  # Check for "all" targets...
  if target == 'traefik' and 'all' in args.targets:
    args.targets = []
    for key, value in targets:
      if not value.startswith('none') and not key == 'traefik':
        args.targets.append(key)

  # Still with us?  OK, check the 'target' and the server's environment (dev, stage or prod).
  green("OK, you are targeting '{0}' in a '{1}' environment on host '{2}'.".format(target, environment, host))
  environ['ENVIRONMENT'] = environment

  for key, value in targets:
    if key == target:
      normal("Found '{0}' key in [{1}] with a value of: '{2}'.".format(key, 'targets', environment))
      target_found = True
      break

  if not target_found:
    red("ERROR: Sorry, your target, '{0}' is not in the list of [targets] found in .master.env!\n\n".format(target))
    sys.exit(111)

  # Process all of the 'common' key=value pairs.
  process_section('common', 'ERROR', config)

  # Process any 'common.environment' key=value pairs.
  dott = "common.{0}".format(environment)
  process_section(dott, 'WARNING', config)

  # Process any 'common.host' key=value pairs.
  dott = "{0}.{1}".format('common', host)
  process_section(dott, 'ATTENTION', config)

  # Process any 'common.environment.host' key=value pairs.
  dott = "{0}.{1}.{2}".format('common', environment, host)
  process_section(dott, 'ATTENTION', config)

  # Process any 'target' key=value pairs.
  process_section(target, 'WARNING', config)

  # Process any 'target.environment' key=value pairs.
  dott = "{0}.{1}".format(target, environment)
  process_section(dott, 'WARNING', config)

  # Finally, Process any 'target.environment.host' key=value pairs.
  dott = "{0}.{1}.{2}".format(target, environment, host)
  process_section(dott, 'ATTENTION', config)

  normal("master_parser( ) is done. Moving on.")
  return environ

#--------------------------------
def process_section(section, severity, config):
  global environ, verbose

  try:
    sect = config.items("{}".format(section))
  except:
    if severity == 'ERROR':
      red("ERROR: Your '.master.env' file must have a [{0}] section!".format(section))
      sys.exit(100)
    elif severity == 'WARNING':
      yellow("WARNING: Your '.master.env' file has no [{0}] section.".format(section))
      return
    else:
      normal("{0}: Your '.master.env' file has no [{1}] section.".format(severity, section))
      return

  for key, value in sect:
    parts = value.split('#', 2)
    val = parts[0].strip( )
    if val.startswith('${HOME}'):
      val = val.replace('${HOME}', os.environ['HOME'])
    environ[key] = val
    if len(parts) > 1:
      normal("  '{0}' is a key in [{2}] with a value of '{1}' and comment '{3}'".format(key, parts[0].strip( ), section, parts[1].strip( )))
    else:
      normal("  '{0}' is a key in [{2}] with a value of '{1}'".format(key, parts[0].strip( ), section))

#--------------------------------
def ensure_network_is_up(environ):
  global client, base_dir

  try:
    networks = client.networks.list(environ['NETWORK_PROXY'])
    if len(networks) > 0:
      green("The '{0}' network already exists.  Moving on.".format(environ['NETWORK_PROXY']))
    else:
      client.networks.create(name=environ['NETWORK_PROXY'])
      green("The '{0}' network has been created.  Moving on.".format(environ['NETWORK_PROXY']))
  except:
    unexpected( )
    raise

#--------------------------------
def ensure_traefik_is_up( ):
  global host, base_dir, client, environ, verbose

  try:
    cont = client.containers.get('traefik')
    if cont.status == 'running':
      green("The 'Traefik' container already exists and is running.  Moving on.")
      return
    else:
      cont.start( )
      green("The existing 'Traefik' container has been re-started.  Moving on.")
      return
  except docker.errors.NotFound:
    yellow("Traefik container does not exist.  Attempting to 'docker run' a new instance.")
  except docker.errors.APIError:
    red("A Docker API error has occured.\nIf the text of the error message includes 'driver failed programming external connectivity on endpoint...',\nplease refer to the Port-Ability/docs/FAQ.md file for guidance.")
    raise
  except:
    unexpected( )
    raise

  # Determine if we have a traefik.toml.ENV.HOST file, or just traefik.toml.ENV to use
  toml_path = "{0}/traefik/traefik.toml.{1}.{2}".format(base_dir, environ['ENVIRONMENT'], host)
  toml_default = "{0}/traefik/traefik.toml.{1}".format(base_dir, environ['ENVIRONMENT'])
  if not os.path.isfile(toml_path):
    normal("There is no '{0}' file for Traefik configuration.  Attempting to use '{1}' instead.".format(toml_path, toml_default))
    toml_path = toml_default
    if not os.path.isfile(toml_path):
      red("There is no suitable .toml file for Traefik configuration.  Traefik failed to start.")
      return

  # Build the Docker command used to launch Traefik.
  cmd = "docker run -d -v /var/run/docker.sock:/var/run/docker.sock \
     -v {1}:/traefik.toml \
     -v {0}/traefik/acme.json:/acme.json \
     -p 80:80 -p 443:443 \
     -l traefik.frontend.rule=Host:{2}.{3} \
     -l traefik.port=8080 \
     --network {5} --name traefik traefik:{4} --docker".format(base_dir,
       toml_path, environ['SUBDOMAIN'], environ['DOMAIN'], environ['TRAEFIK_VERSION'], environ['NETWORK_PROXY'])

  debug("Command to restart Traefik is: \n{0}".format(cmd))

  # Do it.
  try:
    result = os.system(cmd)
  except:
    unexpected( )
    raise

#--------------------------------
def remove_containers(target, target_env):
  global client

  containers = target_env['CONTAINERS'].strip("'").split(' ')

  for container in containers:
    cont_name = "{0}_{1}".format(target, container)

    try:
      cont = client.containers.get(cont_name)
      if cont.status == 'running':
        cont.stop( )
        green("The '{0}' container has been stopped.".format(cont_name))
        cont.remove(v=True)
        green("The '{0}' container and associated non-persistent volumes have been removed.".format(cont_name))
      else:
        yellow("The '{0}' container is not running.  Nothing to stop.".format(cont_name))
        cont.remove(v=True)
        green("The '{0}' container and associated non-persistent volumes have been removed.".format(cont_name))
    except docker.errors.NotFound:
      yellow("Container '{0}' does not exist.  Nothing to stop or remove.".format(cont_name))
    except:
      unexpected()
      raise

#--------------------------------
def restart_containers(target, target_env):
  global base_dir

  # Get the current working directory, and move to the target Stacks directory
  target_env['BASE_PATH'] = base_dir + "/"
  wd = target_env['STACKS'] + "/" + target_env['PROJECT_PATH']
  os.chdir(wd)
  debug("Working directory set to: {0}".format(wd))

  # Write a temporary .env file here from the contents of target_env.
  with open('.env', 'w+') as dotenv:
    for key, value in target_env.items( ):
      dotenv.write("{0}={1}\n".format(key, value))
    dotenv.close( )
  os.chmod('.env', 0o600)

  # If DOCKER_COMPOSE_FILE is defined, copy the specified file to the target directory
  try:
    yaml = target_env['DOCKER_COMPOSE_FILE']
    dc_source = target_env['BASE_PATH'] + "_master/" + yaml
    dc_dest = wd + "/docker-compose.yml"
    green("Copying {0} to {1} per DOCKER_COMPOSE_FILE setting.".format(dc_source, dc_dest))
    shutil.copyfile(dc_source, dc_dest)
  except KeyError:
    pass
  except:
    unexpected()
    raise

  # Use 'docker compose up -d' to build the target stack
  try:
    os.system("docker-compose up -d")
    if environ['ENVIRONMENT'] != 'dev':
      os.unlink('.env')
  except:
    unexpected( )
    if environ['ENVIRONMENT'] != 'dev':
      os.unlink('.env')
    raise

#--------------------------------
def red(msg):
  print(Fore.RED + "\n" + msg + "\n" + Style.RESET_ALL)

#--------------------------------
def blue(msg):
  print(Fore.BLUE + msg + Style.RESET_ALL)

# --------------------------------
def green(msg):
  global verbose
  if verbose > 0:
    print(Fore.GREEN + msg + Style.RESET_ALL)

# --------------------------------
def magenta(msg):
  global verbose
  if verbose > 0:
    print(Fore.MAGENTA + msg + Style.RESET_ALL)

#--------------------------------
def yellow(msg):
  global verbose
  if verbose > 1:
    print(Fore.YELLOW + msg + Style.RESET_ALL)

#--------------------------------
def normal(msg):
  global verbose
  if verbose > 2:
    print(Style.RESET_ALL + msg)

#--------------------------------
def debug(msg):
  global verbose
  if verbose > 2:
    print(Fore.CYAN + "DEBUG: " + msg + Style.RESET_ALL)

#--------------------------------
def unexpected( ):
  red("Oh no...")
  print("Unexpected error: ", sys.exc_info()[0])


#--- main -------------------------------------------

if __name__ == "__main__":

  # Init globals here
  cwd = os.getcwd( )
  environ = dict()
  verbose = 0        # print only blue(), a positive color, and red(), it's negative counterpart
  # default
  host = 'Unknown'
  args = dict()
  target = 'Undefined'
  base_dir = cwd
  do_not_repeat = False

  # Check that we are running this from the Port-Ability working directory
  if not cwd.endswith('/Port-Ability'):
    red("ERROR: Sorry, but {1} cannot be launched from this ({0}) directory. You MUST launch "
        "Port-Ability from the /Port-Ability directory.".format(cwd, identify))
    sys.exit(1)

  # Fetch the Docker client
  try:
    client =  docker.from_env( )
  except:
    unexpected( )
    raise

  # Parse arguments
  parser = argparse.ArgumentParser(prog='port-ability', description='This is Port-Ability!')
  parser.add_argument('action', metavar='action', nargs=1, choices=available_actions,
    help='The action to be performed on the target(s)')
  parser.add_argument('targets', metavar='target', nargs='+',
    help='Target stacks (app and/or sites) to be processed')
  parser.add_argument('-v', '--verbosity', action='count', help='increase output verbosity (default: OFF)')
  parser.add_argument('--version', action='version', version=identify + " " + extra_info)
  parser.add_argument('-p', action='store_true', help="turns on Portainer inclusion")
  parser.add_argument('-i', action='store_true', help="for ISLE...no network, Traefik or Portainer")
  args = parser.parse_args( )

  # Set verbosity
  if args.verbosity is None:
    verbose = 0                 # print blue/red only
  elif args.verbosity > 2:
    verbose = 3                 # print all (blue/red, green/magenta, yellow, black)
  elif args.verbosity > 1:
    verbose = 2                 # print blue/red plus green/magenta and yellow
  else:
    verbose = 1                 # print blue/red plus green/magenta

  # Get the hostname...helps determine our environemnt (dev, stage, or prod)
  host = socket.gethostname( )   # Note this does not work when the application is "Dockerized"
  # host = os.environ['HOSTNAME']  # When Dockerized.  Comment out this line if running via Python venv

  # Initialize colorama
  init( )

  # Provide some feedback to the user
  arg_list = " ".join(sys.argv[1:])
  blue("{0} ({1}) called on {2} with arguments: {3}".format(identify, sys.argv[0], host, arg_list))
  blue("  port_ability.py {0} and {1}".format(extra_info, master_info))

  # Startup and make sure network and Traefik are up and running
  if not args.i:
    environ = master_parser('traefik')
    ensure_network_is_up(environ)
    ensure_traefik_is_up( )
  else:
    args.p = False
    if 'portainer' in args.targets:
      args.targets.remove('portainer')
    environ = master_parser('isle')

  # Ok, now we are ready to take 'action'.
  if args.action[0] not in available_actions:
    red("ERROR: Sorry, the specified action '{0}' is not available.".format(args.action[0]))
    sys.exit(10)

  # If not specified, prepend 'portainer' to the list of targets.
  if args.p and 'portainer' not in args.targets:
     args.targets.insert(0, 'portainer')

  # Loop through the specified targets...
  for target in args.targets:
    target_env = master_parser(target)

    if target_env['BLOCK_THIS_STACK'] in ['1', 'True', 'TRUE', 'true']:
      red("The '{0}' stack is BLOCKED from deployment on host '{1}'.  Nothing to do here.  Moving on.".format(target, host))
      continue
    else:
      green("Launching a '{0}' action for target '{1}'.".format(args.action[0], target))

    if args.action[0] == 'test':
      verbose = max(verbose, 1)     # ok, we really should see something
      do_test(target, target_env)

    if args.action[0] == 'stop':
      do_stop(target, target_env)

    if args.action[0] == 'restart':
      do_restart(target, target_env)

    if args.action[0] == 'fix-permissions':
      do_fix_permissions(target, target_env)

    if args.action[0] == 'backup':
      do_drupal_backup(target, target_env)

    if args.action[0] == 'pull-data':
      do_pull_data(target, target_env)

    if args.action[0] == 'push-code':
      do_push_code(target, target_env)

  # All done.  Set working directory back to original.
  os.chdir(cwd)

  blue("That's all folks!")


#------------------------------------------
# The following code did NOT work properly for launching Traefikself.
  # toml = "{0}/traefik/traefik.toml.{1}".format(base_dir, environ['ENVIRONMENT'])
  # acme = "{0}/traefik/acme.json".format(base_dir)
  # host = "Host:{0}.{1}".format(environ['SUBDOMAIN'], environ['DOMAIN'])
  # vols = {'/var/run/docker.sock': {'bind':'/var/run/docker.sock', 'mode':'rw'}, toml: {'bind':'/traefik.toml', 'mode':'rw'}, acme: {'bind':'/acme.json', 'mode':'rw'}}
  # # labls = {'traefik.frontend.rule':host, 'traefik.port':'8080'}
  # labls = {'traefik.frontend.rule':host}
  # prts = {'8080/tcp':8080, '80/tcp':80}
  # # prts = {'8080/tcp':8080, '80/tcp':80, '443/tcp':443}
  # # prts = {'80/tcp':80, '443/tcp':443}
  #
  # debug("ensure_trakfik_is_up - toml: '{0}'".format(toml))
  # debug("ensure_trakfik_is_up - acme: '{0}'".format(acme))
  # debug("ensure_trakfik_is_up - host: '{0}'".format(host))
  # debug("ensure_trakfik_is_up - vols: '{0}'".format(vols))
  # debug("ensure_trakfik_is_up - labls: '{0}'".format(labls))
  # debug("ensure_trakfik_is_up - prts: '{0}'".format(prts))
  #
  # try:
  #   cont = client.containers.get('traefik')
  #   if cont.status == 'running':
  #     green("The 'Traefik' container already exists and is running.  Moving on.")
  #     return
  #   else:
  #     cont.remove(v=True)
  # except docker.errors.NotFound:
  #   yellow("Traefik container does not exist.  Nothing to stop or remove.")
  # except:
  #   unexpected( )
  #   raise
  #
  # try:
  #   debug("Launching Traefik using .toml file '{0}'.".format(toml))
  #   cont = client.containers.run('traefik:1.6.5-alpine', ' ', name='traefik', detach=True, environment=environ, network='port-ability-proxy', ports=prts, volumes=vols, labels=labls)
  #   status = "{0}".format(cont.status)
  #   debug("Traefik container launched.  Status is: {0}.".format(status))
  #   # if status == 'created':
  #   #   debug("Attempting to start the new container.")
  #   #   cont.start( )
  #   #   debug("Traefik container status is now: {0}.".format(cont.status))
  #   # # msg = cont.logs(tail='all')
  #   # # debug("Container logs... \n{0}".format(msg))
  #   # green("Traefik container successfully started.  Moving on.")
  #   return
