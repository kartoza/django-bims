# Ansible Project Setup

This Readme aims as an explanation of how the project setup works.
When deploying service with complex micro architecture we need some kind
of configuration so the setup works across different machines in their own
development environment. This project setup serve as a configuration file
generator. At the moment we used ansible to do multiple tasks to generate
config files for developer's environment.

## How it works

The setup is a series of Ansible task. It was recommended that you
understand what Ansible is, and how it is used to provision files.
However, to only use this project setup (not to develop), you can just
use existing scripts provided here and or adapt it to your project
configuration.

Each task does idempotent things, which is changing state or generating
necessary files. There are several steps included:

1. Generating docker-compose.override.yml

This docker-compose files is used to override base docker-compose file
of the project. Some project configuration needed explicit specific values,
such as IP Address for testing or domain name. Some things that is
necessary for deployment can also be set, for example default port forward.
Some member of the team might also needs to develop some certain part of
the project, but not the other. This make it possible to toggle or switch
of some part of a complex project.

2. Generating PyCharm configuration

We heavily used Jetbrains IDE to develop our project. In the past, we have
to setup the interpreters and run configuration to truly use the capabilities
of the IDE. It is really painful to set multiple environment variables and
run configuration for a complex project, and it is also troublesome for new
team members to join the development workflow.

This step tries to simplify that problems with that design in mind. The
setup will generate certain PyCharm configuration files in your `.idea`
folders, which is located in the root of your project and used by PyCharm.
This will contain information/configuration:

   a. Project interpreter to use
   b. Source file mappings to remote interpreter (docker container)
   c. Run configurations

Additionally this step will also inject Project interpreter definition
into your local PyCharm installations.

3. Extra file configurations

This step will generate extra file configuration needed by the project.
The detail of this step may vary between project.

## How to use

In order for you to use this setup, first copy file on `development/group_vars/all.sample.yml`
and paste it as `all.yml` file in that same directory. Modify all variables
there according to your installations.

Then, open your project in PyCharm so your `.idea` folder will be generated.

Lastly, run setup script to generate all configuration files.

The explanation of the script can be seen below.

## Setup Scripts

There are basically several steps.

1. Check ansible is working.

You have to install ansible. Run following command in this folder:

```
pip install -r requirements.txt
```

Then, run check script

```
ansible -i development/hosts all -m ping
ansible-playbook -i development/hosts development/site.yml --list-tasks --list-hosts
```

It should print that your local machine is responding ansible and lists
all the task that will run

2. Run setup

To run the ansible tasks itself, do this:

```
ansible-playbook -i development/hosts development/site.yml
```

This will run all the project setup and should return `ok`

3. Write shortcut for developers

This folder only contains basic and generic way of using this setup.
It is more recommended to write these scripts as shortcut. For example,
create a Makefile target to perform this tasks, so it can be executed
from the root of the project.

Assuming that this Ansible Project Setup root folder is always be placed
inside `deployment/ansible` subdirectory, then you can add the following
Makefile targets to your root project Makefile command.

```
# Define environment variable to be used by docker-compose automatically

# Define Project Prefix name
export COMPOSE_PROJECT_NAME=[The Name of The Project]
# Define docker-compose file location to use. We can use multiple docker-compose file for overriding values.
export COMPOSE_FILE=deployment/docker-compose.yml:deployment/docker-compose.override.yml
# Define ansible project setup location
export ANSIBLE_PROJECT_SETUP_DIR=deployment/ansible

# This target checks ansible
ansible-check:
	@echo "Check ansible command"
	@ansible -i ${ANSIBLE_PROJECT_SETUP_DIR}/development/hosts all -m ping
	@ansible-playbook -i ${ANSIBLE_PROJECT_SETUP_DIR}/development/hosts ${ANSIBLE_PROJECT_SETUP_DIR}/development/site.yml --list-tasks --list-hosts $(ANSIBLE_ARGS)

# This target do the actual project setup
setup-ansible:
	@echo "Setup configurations using ansible"
	@ansible-playbook -i ${ANSIBLE_PROJECT_SETUP_DIR}/development/hosts ${ANSIBLE_PROJECT_SETUP_DIR}/development/site.yml $(ANSIBLE_ARGS)
```


Notes for the setup:

   a. You had to specify the location of this Ansible Project Setup.
   b. You had to specify the location of your docker-compose file so you
      can easily use it in docker-compose command as default value
   c. It is possible that PyCharm will ask you to restart after the setup finished.
      Restart accordingly.
   d. Running setup-ansible will destroy all your current Run Configuration,
      because it can't coexists.

If you did step 3, then step 1 and 2 can be executed using make target
that you made.

4. Create the interpreter

You have to actually build the docker container and run it, before it
is actually being used by Project Interpreter. Typically you want to do
something like `make build up web` to build and start the ssh container.


