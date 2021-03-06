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
AWS DocumentDB entrypoint for ECS ComposeX
"""

from troposphere import Ref, GetAtt

from ecs_composex.common.compose_resources import XResource, set_resources
from ecs_composex.common.stacks import ComposeXStack
from ecs_composex.docdb.docdb_params import (
    MOD_KEY,
    RES_KEY,
    DOCDB_NAME,
    DOCDB_PORT,
    DOCDB_SECRET,
    DOCDB_SG,
)
from ecs_composex.vpc.vpc_params import STORAGE_SUBNETS
from ecs_composex.docdb.docdb_template import (
    create_docdb_template,
    init_doc_db_template,
)


class DocDb(XResource):
    """
    Class to manage DocDB
    """

    subnets_param = STORAGE_SUBNETS

    def __init__(self, name, definition, module_name, settings):
        """
        Init method

        :param str name:
        :param dict definition:
        :param ecs_composex.common.settings.ComposeXSettings settings:
        """
        self.db_secret = None
        self.db_sg = None
        self.db_subnets_group = None
        super().__init__(name, definition, module_name, settings)
        self.set_override_subnets()

    def init_outputs(self):
        """
        Method to init the DocDB output attributes
        """
        self.output_properties = {
            DOCDB_NAME: (self.logical_name, self.cfn_resource, Ref, None),
            DOCDB_PORT: (
                f"{self.logical_name}{DOCDB_PORT.return_value}",
                self.cfn_resource,
                GetAtt,
                DOCDB_PORT.return_value,
            ),
            DOCDB_SECRET: (
                self.db_secret.title,
                self.db_secret,
                Ref,
                None,
            ),
            DOCDB_SG: (self.db_sg.title, self.db_sg, GetAtt, DOCDB_SG.return_value),
        }


class XStack(ComposeXStack):
    """
    Class for the Stack of DocDB
    """

    def __init__(self, title, settings, **kwargs):
        set_resources(settings, DocDb, RES_KEY, MOD_KEY)
        new_resources = [
            docdb
            for docdb in settings.compose_content[RES_KEY].values()
            if not docdb.lookup and not docdb.use
        ]
        if new_resources:
            stack_template = init_doc_db_template()
            super().__init__(title, stack_template, **kwargs)
            create_docdb_template(stack_template, new_resources, settings, self)
        else:
            self.is_void = True
        for resource in settings.compose_content[RES_KEY].values():
            resource.stack = self
