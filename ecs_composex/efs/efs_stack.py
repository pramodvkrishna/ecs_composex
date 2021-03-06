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

"""
Module to handle the creation of the root EFS stack
"""

from troposphere import Ref, GetAtt, Sub, Select
from troposphere.ec2 import SecurityGroup
from troposphere.efs import FileSystem, MountTarget

from ecs_composex.common import build_template
from ecs_composex.common.compose_resources import XResource, set_resources
from ecs_composex.common.stacks import ComposeXStack
from ecs_composex.efs.efs_params import (
    RES_KEY,
    FS_ID,
    FS_ARN,
    FS_PORT,
    MOD_KEY,
    FS_MNT_PT_SG_ID,
)
from ecs_composex.resources_import import import_record_properties
from ecs_composex.vpc.vpc_params import STORAGE_SUBNETS, VPC_ID


def create_efs_stack(settings, new_resources):
    """
    Function to create the root stack and add EFS FS.

    :param ecs_composex.common.settings.ComposeXSettings settings:
    :param list new_resources:
    :return: Root template for EFS
    :rtype: troposphere.Template
    """
    template = build_template("Root for EFS built by ECS Compose-X", [FS_PORT])
    for res in new_resources:
        res_cfn_props = import_record_properties(res.properties, FileSystem)
        res.cfn_resource = FileSystem(res.logical_name, **res_cfn_props)
        res.db_sg = SecurityGroup(
            f"{res.logical_name}SecurityGroup",
            GroupName=Sub(f"{res.logical_name}EfsSg"),
            GroupDescription=Sub(f"SG for EFS {res.cfn_resource.title}"),
            VpcId=Ref(VPC_ID),
        )
        if settings.vpc_imported:
            for count, az in enumerate(
                settings.subnets_mappings[STORAGE_SUBNETS.title]["Azs"]
            ):
                template.add_resource(
                    MountTarget(
                        f"{res.logical_name}MountPoint{az.title().strip().split('-')[-1]}",
                        FileSystemId=Ref(res.cfn_resource),
                        SecurityGroups=[GetAtt(res.db_sg, "GroupId")],
                        SubnetId=Select(count, Ref(STORAGE_SUBNETS)),
                    )
                )
        else:
            for count, az in enumerate(settings.aws_azs):
                template.add_resource(
                    MountTarget(
                        f"{res.logical_name}MountPoint{az['ZoneName'].title().strip().split('-')[-1]}",
                        FileSystemId=Ref(res.cfn_resource),
                        SecurityGroups=[GetAtt(res.db_sg, "GroupId")],
                        SubnetId=Select(count, Ref(STORAGE_SUBNETS)),
                    )
                )
        template.add_resource(res.cfn_resource)
        template.add_resource(res.db_sg)
        res.init_outputs()
        res.generate_outputs()
        template.add_output(res.outputs)
    return template


class Efs(XResource):
    """
    Class to represent a Filesystem
    """

    subnets_param = STORAGE_SUBNETS

    def __init__(self, name, definition, module_name, settings):
        self.db_sg = None
        self.db_secret = None
        self.mnt_targets = []
        self.access_points = []
        self.volume = definition["Volume"]
        super().__init__(name, definition, module_name, settings)
        self.set_override_subnets()

    def init_outputs(self):
        """
        Method to init the DocDB output attributes
        """
        self.output_properties = {
            FS_ID: (self.logical_name, self.cfn_resource, Ref, None),
            FS_ARN: (self.logical_name, self.cfn_resource, GetAtt, FS_ARN.return_value),
            FS_PORT: (f"{self.logical_name}{FS_PORT.title}", FS_PORT, Ref, None),
            FS_MNT_PT_SG_ID: (
                f"{self.logical_name}{FS_MNT_PT_SG_ID.return_value}",
                self.db_sg,
                GetAtt,
                FS_MNT_PT_SG_ID.return_value,
            ),
        }


class XStack(ComposeXStack):
    """
    Class to represent the root for EFS
    """

    def __init__(self, name, settings, **kwargs):
        set_resources(settings, Efs, RES_KEY, MOD_KEY)
        new_resources = [
            fs
            for fs in settings.compose_content[RES_KEY].values()
            if not fs.lookup and not fs.use and fs.properties
        ]
        if new_resources:
            stack_template = create_efs_stack(settings, new_resources)
            super().__init__(name, stack_template, **kwargs)
        else:
            self.is_void = True
        for resource in settings.compose_content[RES_KEY].values():
            resource.stack = self
