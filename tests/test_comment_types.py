from lib2to3.pytree import Base
from xml.dom import ValidationErr
from hydrolib.core.io.ini.models import Comment, IntComment
from pydantic import BaseModel, Field, ValidationError


# def test_comment():
#     i = IntComment(1)
#     ii = IntComment(2, comment="test")
#     iii = IntComment(3, comment="test 2")

#     print(i, ii, iii)

#     class Test(BaseModel):
#         a: IntComment

#         class Config:
#             arbitrary_types_allowed = True
#             validate_assignment = True
#             use_enum_values = True

#     # t = Test(a=1)
#     # t = Test(a="1")
#     t = Test(a="1 # comment")
#     print(t)
#     print(t.a)
#     print(t.a.comment)
#     t.a.comment = "Something else"
#     print(t.a.comment)
#     t.a += 1
#     print(type(t.a))
#     print(t.a)

#     0 / 0


def test_error():
    class Test(BaseModel):
        a: float

    try:
        t = Test()
    except ValidationError as e:
        print(e)
        e.errors()
        0 / 0


# def test_second_approach():
#     class Test(BaseModel):
#         a: int = Field(1, description="test")

#     t = Test()
#     tt = Test()
#     print(t.a)
#     print(t.__fields__.get("a").field_info.description)
#     t.__fields__.get("a").field_info.description = "nuh"
#     print(t.__fields__.get("a").field_info.description)
#     print(tt.__fields__.get("a").field_info.description)

#     print(t)
#     print(tt)
#     0 / 0
