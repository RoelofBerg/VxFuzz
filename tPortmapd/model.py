#! /usr/bin/env python
# coding: utf-8
#
# Author: Yannick Formaggio
from kitty.model import *

rpc_header = Container(
    name="RPC_HEADER",
    fields=[
        Dword(1, name="xid"),
        Dword(0, name="message_type"),
        Dword(2, name="rpc_version"),
        Dword(100000, name="programme"),
        Dword(2, name="program_version"),
        Dword(0, name="procedure_number"),
        Dword(0, name="credential_flavor"),
        Dword(0, name="credential_length"),
        Dword(0, name="verifier_flavor"),
        Dword(0, name="verifier_length"),
    ]
)

portmap_proc_null = Template(
    name="PMAPPROC_NULL",
    fields=[
        SizeInBytes(sized_field=rpc_header, length=32, name="fragment_header"),
        Container(
            name="Packet",
            fields=[
                rpc_header
            ]
        ),
    ]
)
