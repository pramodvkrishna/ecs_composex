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
Module for DNS parameters
"""

from os import path
from ecs_composex.common.cfn_params import Parameter

MOD_KEY = path.basename(path.dirname(path.abspath(__file__)))
RES_KEY = f"x-{path.basename(path.dirname(path.abspath(__file__)))}"


ZONES_PATTERN = r"^none$|^ns-[a-z0-9]{6,24}$|^Z[0-9A-Z]+$"

PUBLIC_DNS_ZONE_NAME_T = "PublicDnsZoneName"
PUBLIC_DNS_ZONE_NAME = Parameter(
    PUBLIC_DNS_ZONE_NAME_T, Type="String", Default="none.existant"
)

PUBLIC_DNS_ZONE_ID_T = "PublicDnsZoneId"
PUBLIC_DNS_ZONE_ID = Parameter(
    PUBLIC_DNS_ZONE_ID_T,
    Type="String",
    Default="none",
    AllowedPattern=ZONES_PATTERN,
)

PRIVATE_DNS_ZONE_NAME_T = "PrivateDnsZoneName"
PRIVATE_DNS_ZONE_NAME = Parameter(
    PRIVATE_DNS_ZONE_NAME_T, Type="String", Default="cluster.internal"
)

PRIVATE_DNS_ZONE_ID_T = "PrivateDnsZoneId"
PRIVATE_DNS_ZONE_ID = Parameter(
    PRIVATE_DNS_ZONE_ID_T,
    Type="String",
    Default="none",
    AllowedPattern=ZONES_PATTERN,
)

PRIVATE_NAMESPACE_ID_T = "PrivateNamespaceId"
PRIVATE_NAMESPACE_ID = Parameter(
    PRIVATE_NAMESPACE_ID_T, Type="String", Default="none", AllowedPattern=ZONES_PATTERN
)
