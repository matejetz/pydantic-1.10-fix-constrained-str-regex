"""
Test pydantic's compliance with mypy.

Do a little skipping about with types to demonstrate its usage.
"""
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path, PurePath
from typing import Any, Dict, ForwardRef, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from typing_extensions import Annotated, TypedDict

from pydantic import (
    UUID1,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    DirectoryPath,
    Extra,
    FilePath,
    FutureDate,
    ImportString,
    Json,
    NaiveDatetime,
    NegativeFloat,
    NegativeInt,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PastDate,
    PositiveFloat,
    PositiveInt,
    StrictBool,
    StrictBytes,
    StrictFloat,
    StrictInt,
    StrictStr,
    UrlConstraints,
    root_validator,
    validate_arguments,
    validator,
)
from pydantic.fields import Field, PrivateAttr
from pydantic.networks import AnyUrl


class Flags(BaseModel):
    strict_bool: StrictBool = False

    def __str__(self) -> str:
        return f'flag={self.strict_bool}'


class Model(BaseModel):
    age: int
    first_name: str = 'John'
    last_name: Optional[str] = None
    signup_ts: Optional[datetime] = None
    list_of_ints: List[int]

    @validator('age')
    def check_age(cls, value: int) -> int:
        assert value < 100, 'too old'
        return value

    @root_validator
    def root_check(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        return values

    @root_validator(mode='before', allow_reuse=False)
    def pre_root_check(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        return values


def dog_years(age: int) -> int:
    return age * 7


def day_of_week(dt: datetime) -> int:
    return dt.date().isoweekday()


m = Model(age=21, list_of_ints=[1, '2', b'3'])

assert m.age == 21, m.age
m.age = 42
assert m.age == 42, m.age
assert m.first_name == 'John', m.first_name
assert m.last_name is None, m.last_name
assert m.list_of_ints == [1, 2, 3], m.list_of_ints

dog_age = dog_years(m.age)
assert dog_age == 294, dog_age


m = Model(age=2, first_name=b'Woof', last_name=b'Woof', signup_ts='2017-06-07 00:00', list_of_ints=[1, '2', b'3'])

assert m.first_name == 'Woof', m.first_name
assert m.last_name == 'Woof', m.last_name
assert m.signup_ts == datetime(2017, 6, 7), m.signup_ts
assert day_of_week(m.signup_ts) == 3


data = {'age': 10, 'first_name': 'Alena', 'last_name': 'Sousova', 'list_of_ints': [410]}
m_from_obj = Model.model_validate(data)

assert isinstance(m_from_obj, Model)
assert m_from_obj.age == 10
assert m_from_obj.first_name == data['first_name']
assert m_from_obj.last_name == data['last_name']
assert m_from_obj.list_of_ints == data['list_of_ints']

m_copy = m_from_obj.copy()

assert isinstance(m_copy, Model)
assert m_copy.age == m_from_obj.age
assert m_copy.first_name == m_from_obj.first_name
assert m_copy.last_name == m_from_obj.last_name
assert m_copy.list_of_ints == m_from_obj.list_of_ints


T = TypeVar('T')


class WrapperModel(BaseModel, Generic[T]):
    payload: T


int_instance = WrapperModel[int](payload=1)
int_instance.payload += 1
assert int_instance.payload == 2

str_instance = WrapperModel[str](payload='a')
str_instance.payload += 'a'
assert str_instance.payload == 'aa'

model_instance = WrapperModel[Model](payload=m)
model_instance.payload.list_of_ints.append(4)
assert model_instance.payload.list_of_ints == [1, 2, 3, 4]


class WithField(BaseModel):
    age: int
    first_name: str = Field('John', max_length=42)


# simple decorator
@validate_arguments
def foo(a: int, *, c: str = 'x') -> str:
    return c * a


foo(1, c='thing')
foo(1)


# nested decorator should not produce an error
@validate_arguments(config={'arbitrary_types_allowed': True})
def bar(a: int, *, c: str = 'x') -> str:
    return c * a


bar(1, c='thing')
bar(1)


class Foo(BaseModel):
    a: int


FooRef = ForwardRef('Foo')


class MyConf(BaseModel):
    str_pyobject: ImportString[Type[date]] = Field('datetime.date')
    callable_pyobject: ImportString[Type[date]] = Field(date)


conf = MyConf()
var1: date = conf.str_pyobject(2020, 12, 20)
var2: date = conf.callable_pyobject(2111, 1, 1)


class MyPrivateAttr(BaseModel):
    _private_field: str = PrivateAttr()


class PydanticTypes(BaseModel):
    # Boolean
    my_strict_bool: StrictBool = True
    # Integer
    my_positive_int: PositiveInt = 1
    my_negative_int: NegativeInt = -1
    my_non_positive_int: NonPositiveInt = -1
    my_non_negative_int: NonNegativeInt = 1
    my_strict_int: StrictInt = 1
    # Float
    my_positive_float: PositiveFloat = 1.1
    my_negative_float: NegativeFloat = -1.1
    my_non_positive_float: NonPositiveFloat = -1.1
    my_non_negative_float: NonNegativeFloat = 1.1
    my_strict_float: StrictFloat = 1.1
    # Bytes
    my_strict_bytes: StrictBytes = b'pika'
    # String
    my_strict_str: StrictStr = 'pika'
    # ImportString
    import_string_str: ImportString[Any] = 'datetime.date'
    import_string_callable: ImportString[Any] = date
    # UUID
    my_uuid1: UUID1 = UUID('a8098c1a-f86e-11da-bd1a-00112444be1e')
    my_uuid1_str: UUID1 = 'a8098c1a-f86e-11da-bd1a-00112444be1e'  # type: ignore
    # Path
    my_file_path: FilePath = Path(__file__)
    my_file_path_str: FilePath = __file__  # type: ignore
    my_dir_path: DirectoryPath = Path('.')
    my_dir_path_str: DirectoryPath = '.'  # type: ignore
    # Json
    my_json: Json[Dict[str, str]] = '{"hello": "world"}'  # type: ignore
    my_json_list: Json[List[str]] = '["hello", "world"]'  # type: ignore
    # Date
    my_past_date: PastDate = date.today() - timedelta(1)
    my_future_date: FutureDate = date.today() + timedelta(1)
    # Datetime
    my_aware_datetime: AwareDatetime = datetime.now(tz=timezone.utc)
    my_naive_datetime: NaiveDatetime = datetime.now()

    class Config:
        validate_all = True


validated = PydanticTypes()
validated.import_string_str(2021, 1, 1)
validated.import_string_callable(2021, 1, 1)
validated.my_uuid1.hex
validated.my_uuid1_str.hex
validated.my_file_path.absolute()
validated.my_file_path_str.absolute()
validated.my_dir_path.absolute()
validated.my_dir_path_str.absolute()
validated.my_json['hello'].capitalize()
validated.my_json_list[0].capitalize()


class UrlModel(BaseModel):
    x: Annotated[AnyUrl, UrlConstraints(allowed_schemes=['http'])] = Field(None)
    y: Annotated[AnyUrl, UrlConstraints(allowed_schemes=['http'])] = Field(None)
    z: Annotated[AnyUrl, UrlConstraints(allowed_schemes=['s3', 's3n', 's3a'])] = Field(None)


url_model = UrlModel(x='http://example.com')
assert url_model.x.host == 'example.com'


class SomeDict(TypedDict):
    val: int
    name: str


obj: SomeDict = {
    'val': 12,
    'name': 'John',
}


config = ConfigDict(title='Record', extra=Extra.ignore, str_max_length=1234)


class CustomPath(PurePath):
    def __init__(self, *args: str):
        self.path = os.path.join(*args)

    def __fspath__(self) -> str:
        return f'a/custom/{self.path}'


# TODO:
# DynamicModel = create_model('DynamicModel')
