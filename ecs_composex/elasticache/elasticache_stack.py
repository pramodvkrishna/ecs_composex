﻿#  -*- coding: utf-8 -*-
#   ECS ComposeX <https://github.com/lambda-my-aws/ecs_composex>
#   Copyright (C) 2020-2021  John Mille <john@lambda-my-aws.io>
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

"""
Module to handle the AWS ES Stack and resources creation
"""

import json

from troposphere import Ref, GetAtt, Sub
from troposphere.ssm import Parameter as SSMParameter

from ecs_composex.common.compose_resources import XResource, set_resources
from ecs_composex.common.stacks import ComposeXStack
from ecs_composex.elasticache.elasticache_params import (
    MOD_KEY,
    RES_KEY,
    CLUSTER_NAME,
    CLUSTER_MEMCACHED_ADDRESS,
    CLUSTER_MEMCACHED_PORT,
    CLUSTER_REDIS_PORT,
    CLUSTER_REDIS_ADDRESS,
    REPLICA_READ_ENDPOINT_ADDRESSES,
    REPLICA_READ_ENDPOINT_PORTS,
    REPLICA_PRIMARY_ADDRESS,
    REPLICA_PRIMARY_PORT,
    CLUSTER_SG,
    CLUSTER_CONFIG,
)
from ecs_composex.elasticache.elasticache_template import create_root_template
from ecs_composex.vpc.vpc_params import STORAGE_SUBNETS


class CacheCluster(XResource):
    """
    Class to represent an AWS Elastic CacheCluster
    """

    subnets_param = STORAGE_SUBNETS

    def __init__(self, name, definition, module_name, settings):
        self.db_sg = None
        self.parameter_group = None
        self.db_secret = None
        self.db_subnet_group = None
        self.engine = None
        self.port_attr = None
        self.config_parameter = None
        super().__init__(name, definition, module_name, settings)
        self.set_override_subnets()

    def init_memcached_outputs(self):
        """
        Method to init the DocDB output attributes
        """
        self.output_properties = {
            CLUSTER_NAME: (self.logical_name, self.cfn_resource, Ref, None),
            CLUSTER_MEMCACHED_PORT: (
                f"{self.logical_name}{CLUSTER_MEMCACHED_PORT.return_value}",
                self.cfn_resource,
                GetAtt,
                CLUSTER_MEMCACHED_PORT.return_value,
            ),
            CLUSTER_MEMCACHED_ADDRESS: (
                f"{self.logical_name}{CLUSTER_MEMCACHED_ADDRESS.return_value}",
                self.cfn_resource,
                GetAtt,
                CLUSTER_MEMCACHED_ADDRESS.return_value,
            ),
            CLUSTER_SG: (self.db_sg.title, self.db_sg, GetAtt, CLUSTER_SG.return_value),
        }

    def add_memcahed_config(self, template):
        self.port_attr = CLUSTER_MEMCACHED_PORT
        if not self.lookup:
            self.config_parameter = SSMParameter(
                f"{self.logical_name}Config",
                template=template,
                Type="String",
                Value=Sub(
                    json.dumps(
                        {
                            "endpoint": f"${{{self.logical_name}.{CLUSTER_MEMCACHED_ADDRESS.return_value}}}",
                            "port": f"${{{self.logical_name}.{CLUSTER_MEMCACHED_PORT.return_value}}}",
                        }
                    ),
                ),
            )
            self.output_properties[CLUSTER_CONFIG] = (
                self.config_parameter.title,
                self.config_parameter,
                Ref,
                None,
            )

    def init_redis_replica_outputs(self):
        self.output_properties = {
            CLUSTER_NAME: (self.logical_name, self.cfn_resource, Ref, None),
            REPLICA_PRIMARY_PORT: (
                f"{self.logical_name}{REPLICA_PRIMARY_PORT.title}",
                self.cfn_resource,
                GetAtt,
                REPLICA_PRIMARY_PORT.return_value,
            ),
            REPLICA_PRIMARY_ADDRESS: (
                f"{self.logical_name}{REPLICA_PRIMARY_ADDRESS.title}",
                self.cfn_resource,
                GetAtt,
                REPLICA_PRIMARY_ADDRESS.return_value,
            ),
            REPLICA_READ_ENDPOINT_ADDRESSES: (
                f"{self.logical_name}{REPLICA_READ_ENDPOINT_ADDRESSES.title}",
                self.cfn_resource,
                GetAtt,
                REPLICA_READ_ENDPOINT_ADDRESSES.return_value,
            ),
            REPLICA_READ_ENDPOINT_PORTS: (
                f"{self.logical_name}{REPLICA_READ_ENDPOINT_PORTS.title}",
                self.cfn_resource,
                GetAtt,
                REPLICA_READ_ENDPOINT_PORTS.return_value,
            ),
            CLUSTER_SG: (self.db_sg.title, self.db_sg, GetAtt, CLUSTER_SG.return_value),
        }
        self.port_attr = REPLICA_PRIMARY_PORT

    def add_redis_replica_config(self, template):
        if not self.lookup:
            self.config_parameter = SSMParameter(
                f"{self.logical_name}Config",
                template=template,
                Type="String",
                Value=Sub(
                    json.dumps(
                        {
                            "endpoint": f"${{{self.logical_name}.{REPLICA_PRIMARY_ADDRESS.return_value}}}",
                            "port": f"${{{self.logical_name}.{REPLICA_PRIMARY_PORT.return_value}}}",
                            "readendpoints": f"{{{self.logical_name}{REPLICA_READ_ENDPOINT_ADDRESSES.return_value}}}",
                            "readports": f"{{{self.logical_name}{REPLICA_READ_ENDPOINT_PORTS.return_value}}}",
                            "url": f"redis://${{{self.logical_name}.{REPLICA_PRIMARY_ADDRESS.return_value}}}:"
                            f"${{{self.logical_name}.{REPLICA_PRIMARY_PORT.return_value}}}",
                        }
                    ),
                ),
            )
            self.output_properties[CLUSTER_CONFIG] = (
                self.config_parameter.title,
                self.config_parameter,
                Ref,
                None,
            )

    def init_redis_outputs(self):
        self.output_properties = {
            CLUSTER_NAME: (self.logical_name, self.cfn_resource, Ref, None),
            CLUSTER_REDIS_PORT: (
                f"{self.logical_name}{CLUSTER_REDIS_PORT.return_value}",
                self.cfn_resource,
                GetAtt,
                CLUSTER_REDIS_PORT.return_value,
            ),
            CLUSTER_REDIS_ADDRESS: (
                f"{self.logical_name}{CLUSTER_REDIS_ADDRESS.title}",
                self.cfn_resource,
                GetAtt,
                CLUSTER_REDIS_ADDRESS.return_value,
            ),
            CLUSTER_SG: (self.db_sg.title, self.db_sg, GetAtt, CLUSTER_SG.return_value),
        }
        self.port_attr = CLUSTER_REDIS_PORT

    def add_redis_config(self, template):
        if not self.lookup:
            self.config_parameter = SSMParameter(
                f"{self.logical_name}Config",
                template=template,
                Type="String",
                Value=Sub(
                    json.dumps(
                        {
                            "endpoint": f"${{{self.logical_name}.{CLUSTER_REDIS_ADDRESS.return_value}}}",
                            "port": f"${{{self.logical_name}.{CLUSTER_REDIS_PORT.return_value}}}",
                            "url": f"redis://${{{self.logical_name}.{CLUSTER_REDIS_ADDRESS.return_value}}}:"
                            f"${{{self.logical_name}.{CLUSTER_REDIS_PORT.return_value}}}",
                        }
                    ),
                ),
            )
            self.output_properties[CLUSTER_CONFIG] = (
                self.config_parameter.title,
                self.config_parameter,
                Ref,
                None,
            )


class XStack(ComposeXStack):
    """
    Method to manage the elastic cache resources and root stack
    """

    def __init__(self, title, settings, **kwargs):
        set_resources(settings, CacheCluster, RES_KEY, MOD_KEY)
        new_resources = [
            cache
            for cache in settings.compose_content[RES_KEY].values()
            if not cache.lookup and not cache.use
        ]
        if new_resources:
            stack_template = create_root_template(new_resources)
            super().__init__(title, stack_template, **kwargs)
        else:
            self.is_void = True
        for resource in settings.compose_content[RES_KEY].values():
            resource.stack = self
