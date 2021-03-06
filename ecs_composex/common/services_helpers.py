﻿#  -*- coding: utf-8 -*-
#   ECS ComposeX <https://github.com/lambda-my-aws/ecs_composex>
#   Copyright (C) 2020  John Mille <john@lambda-my-aws.io>
#  #
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#  #
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#  #
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from troposphere import Ref, Sub, GetAtt, ImportValue, FindInMap
from troposphere.ecs import ContainerDefinition
from troposphere.ecs import Environment
from ecs_composex.common import LOG
from ecs_composex.common import keyisset, keypresent


def import_secrets(template, service, container, settings):
    """
    Function to import secrets from composex mapping to AWS Secrets in Secrets Manager

    :param troposphere.Template template:
    :param troposhere.ecs.ContainerDefinition container:
    :param ecs_composex.common.settings.ComposeXSettings settings:
    :return:
    """
    if not service.secrets:
        return
    if not keyisset("secrets", settings.compose_content):
        return
    else:
        settings_secrets = settings.compose_content["secrets"]
    for secret in service.secrets:
        if (
            isinstance(secret, str)
            and secret in settings_secrets
            and keyisset("ComposeSecret", settings_secrets[secret])
        ):
            settings_secrets[secret]["ComposeSecret"].assign_to_task_definition(
                template, container
            )
        elif isinstance(secret, dict) and keyisset("source", secret):
            secret_name = secret["source"]
            if keyisset("ComposeSecret", settings_secrets[secret_name]):
                settings_secrets[secret_name][
                    "ComposeSecret"
                ].assign_to_task_definition(template, container)


def define_string_interpolation(var_value):
    """
    Function to determine whether an env variable string should use Sub.

    :param str var_value: The env var string as defined in compose file
    :return: String as is or Sub for interpolation
    :rtype: str
    """
    if var_value.find(r"${AWS::") >= 0:
        LOG.debug(var_value)
        return Sub(var_value)
    return var_value


def import_env_variables(environment):
    """
    Function to import Docker compose env variables into ECS Env Variables

    :param environment: Environment variables as defined on the ecs_service definition
    :type environment: dict
    :return: list of Environment
    :rtype: list<troposphere.ecs.Environment>
    """
    env_vars = []
    for key in environment:
        if not isinstance(environment[key], str):
            env_vars.append(Environment(Name=key, Value=str(environment[key])))
        else:
            env_vars.append(
                Environment(
                    Name=key, Value=define_string_interpolation(environment[key])
                )
            )
    return env_vars


def extend_container_secrets(container, secret):
    """
    Function to add secrets to a Container definition

    :param container: container definition
    :type container: troposphere.ecs.ContainerDefinition
    :param secret: secret to add
    :type secret: troposphere.ecs.Secret
    """
    if hasattr(container, "Secrets"):
        secrets = getattr(container, "Secrets")
        if secrets:
            uniq = [secret.Name for secret in secrets]
            if secret.Name not in uniq:
                secrets.append(secret)
        else:
            setattr(container, "Secrets", [secret])
    else:
        setattr(container, "Secrets", [secret])


def extend_container_envvars(container, env_vars):
    ignored_containers = ["xray-daemon", "envoy"]
    if (
        isinstance(container, ContainerDefinition)
        and not isinstance(container.Name, (Ref, Sub, GetAtt, ImportValue, FindInMap))
        and container.Name in ignored_containers
    ):
        LOG.debug(f"Ignoring AWS Container {container.Name}")
        return
    environment = (
        getattr(container, "Environment")
        if hasattr(container, "Environment")
        and not isinstance(getattr(container, "Environment"), Ref)
        else []
    )
    if environment:
        existing = [var.Name for var in environment]
        for var in env_vars:
            if var.Name not in existing:
                LOG.debug(f"Adding {var.Name} to {existing}")
                environment.append(var)

    else:
        setattr(container, "Environment", env_vars)
    LOG.debug(f"{container.Name}, {[env.Name for env in environment]}")


def define_ingress_mappings(service_ports):
    """
    Function to create a mapping of sources for a common target
    """
    ingress_mappings = {}
    for port in service_ports:
        if not keyisset("target", port):
            raise KeyError("The ports must always at least define the target.")
        if not keyisset("published", port):
            port["published"] = port["target"]
        if not port["target"] in ingress_mappings.keys():
            ingress_mappings[port["target"]] = [port["published"]]
        elif (
            port["target"] in ingress_mappings.keys()
            and not port["published"] in ingress_mappings[port["target"]]
        ):
            ingress_mappings[port["target"]].append(port["published"])
    return ingress_mappings


def validate_healthcheck(healthcheck, valid_keys, required_keys):
    """
    Healthcheck definition validation

    :param dict healthcheck:
    :param list valid_keys:
    :param list required_keys:
    """
    for key in healthcheck.keys():
        if key not in valid_keys:
            raise AttributeError(f"Key {key} is not valid. Expected", valid_keys)
    if not all(required_keys) not in healthcheck.keys():
        raise AttributeError(
            f"Expected at least {required_keys}. Got", healthcheck.keys()
        )


def set_else_none(key, props, alt_value=None, eval_bool=False):
    """
    Function to serialize if not keyisset () set other value

    :param str key:
    :param dict props:
    :param alt_value:
    :param bool eval_bool: Allows to gets booleans properties
    :return:
    """
    if not eval_bool:
        return alt_value if not keyisset(key, props) else props[key]
    elif eval_bool:
        return alt_value if not keypresent(key, props) else props[key]
