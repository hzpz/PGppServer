# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: pogoprotos/enums/combat_player_finish_state.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='pogoprotos/enums/combat_player_finish_state.proto',
  package='pogoprotos.enums',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n1pogoprotos/enums/combat_player_finish_state.proto\x12\x10pogoprotos.enums*:\n\x17\x43ombatPlayerFinishState\x12\n\n\x06WINNER\x10\x00\x12\t\n\x05LOSER\x10\x01\x12\x08\n\x04\x44RAW\x10\x02\x62\x06proto3')
)

_COMBATPLAYERFINISHSTATE = _descriptor.EnumDescriptor(
  name='CombatPlayerFinishState',
  full_name='pogoprotos.enums.CombatPlayerFinishState',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='WINNER', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='LOSER', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DRAW', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=71,
  serialized_end=129,
)
_sym_db.RegisterEnumDescriptor(_COMBATPLAYERFINISHSTATE)

CombatPlayerFinishState = enum_type_wrapper.EnumTypeWrapper(_COMBATPLAYERFINISHSTATE)
WINNER = 0
LOSER = 1
DRAW = 2


DESCRIPTOR.enum_types_by_name['CombatPlayerFinishState'] = _COMBATPLAYERFINISHSTATE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)


# @@protoc_insertion_point(module_scope)
