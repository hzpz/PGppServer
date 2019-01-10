# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: pogoprotos/map/pokemon/map_pokemon.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from pogoprotos.data import pokemon_display_pb2 as pogoprotos_dot_data_dot_pokemon__display__pb2
from pogoprotos.enums import pokemon_id_pb2 as pogoprotos_dot_enums_dot_pokemon__id__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='pogoprotos/map/pokemon/map_pokemon.proto',
  package='pogoprotos.map.pokemon',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n(pogoprotos/map/pokemon/map_pokemon.proto\x12\x16pogoprotos.map.pokemon\x1a%pogoprotos/data/pokemon_display.proto\x1a!pogoprotos/enums/pokemon_id.proto\"\xeb\x01\n\nMapPokemon\x12\x16\n\x0espawn_point_id\x18\x01 \x01(\t\x12\x14\n\x0c\x65ncounter_id\x18\x02 \x01(\x06\x12\x34\n\x0fpokedex_type_id\x18\x03 \x01(\x0e\x32\x1b.pogoprotos.enums.PokemonId\x12\x1a\n\x12\x65xpiration_time_ms\x18\x04 \x01(\x03\x12\x10\n\x08latitude\x18\x05 \x01(\x01\x12\x11\n\tlongitude\x18\x06 \x01(\x01\x12\x38\n\x0fpokemon_display\x18\x07 \x01(\x0b\x32\x1f.pogoprotos.data.PokemonDisplayb\x06proto3')
  ,
  dependencies=[pogoprotos_dot_data_dot_pokemon__display__pb2.DESCRIPTOR,pogoprotos_dot_enums_dot_pokemon__id__pb2.DESCRIPTOR,])




_MAPPOKEMON = _descriptor.Descriptor(
  name='MapPokemon',
  full_name='pogoprotos.map.pokemon.MapPokemon',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='spawn_point_id', full_name='pogoprotos.map.pokemon.MapPokemon.spawn_point_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='encounter_id', full_name='pogoprotos.map.pokemon.MapPokemon.encounter_id', index=1,
      number=2, type=6, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='pokedex_type_id', full_name='pogoprotos.map.pokemon.MapPokemon.pokedex_type_id', index=2,
      number=3, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='expiration_time_ms', full_name='pogoprotos.map.pokemon.MapPokemon.expiration_time_ms', index=3,
      number=4, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='latitude', full_name='pogoprotos.map.pokemon.MapPokemon.latitude', index=4,
      number=5, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='longitude', full_name='pogoprotos.map.pokemon.MapPokemon.longitude', index=5,
      number=6, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='pokemon_display', full_name='pogoprotos.map.pokemon.MapPokemon.pokemon_display', index=6,
      number=7, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=143,
  serialized_end=378,
)

_MAPPOKEMON.fields_by_name['pokedex_type_id'].enum_type = pogoprotos_dot_enums_dot_pokemon__id__pb2._POKEMONID
_MAPPOKEMON.fields_by_name['pokemon_display'].message_type = pogoprotos_dot_data_dot_pokemon__display__pb2._POKEMONDISPLAY
DESCRIPTOR.message_types_by_name['MapPokemon'] = _MAPPOKEMON
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

MapPokemon = _reflection.GeneratedProtocolMessageType('MapPokemon', (_message.Message,), dict(
  DESCRIPTOR = _MAPPOKEMON,
  __module__ = 'pogoprotos.map.pokemon.map_pokemon_pb2'
  # @@protoc_insertion_point(class_scope:pogoprotos.map.pokemon.MapPokemon)
  ))
_sym_db.RegisterMessage(MapPokemon)


# @@protoc_insertion_point(module_scope)
