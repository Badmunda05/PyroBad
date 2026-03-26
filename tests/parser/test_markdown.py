#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

import asyncio

import pyrogram
import pytest
from pyrogram import enums
from pyrogram import raw
from pyrogram.parser import Parser
from pyrogram.parser.markdown import Markdown


@pytest.mark.parametrize(
    ("expected", "text", "entities"),
    [
        (
            "**bold**",
            "bold",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BOLD, offset=0, length=4)
            ]),
        ),
        (
            "__italic__",
            "italic",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.ITALIC, offset=0, length=6)
            ]),
        ),
        (
            "--underline--",
            "underline",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.UNDERLINE, offset=0, length=9)
            ]),
        ),
        (
            "~~strike~~",
            "strike",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.STRIKETHROUGH, offset=0, length=6)
            ]),
        ),
        (
            "||spoiler||",
            "spoiler",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.SPOILER, offset=0, length=7)
            ]),
        ),
        (
            "[URL](https://pyrogram.org/)",
            "URL",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(
                    type=pyrogram.enums.MessageEntityType.TEXT_LINK,
                    offset=0,
                    length=3,
                    url="https://pyrogram.org/",
                )
            ]),
        ),
        (
            "![🥲](tg://emoji?id=5195264424893488796) im crying",
            "🥲 im crying",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(
                    type=pyrogram.enums.MessageEntityType.CUSTOM_EMOJI,
                    offset=0,
                    length=2,
                    custom_emoji_id=5195264424893488796,
                )
            ]),
        ),
        (
            "![22:45 tomorrow](tg://time?unix=1647531900&format=wDT)",
            "22:45 tomorrow",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(
                    type=pyrogram.enums.MessageEntityType.DATE_TIME,
                    offset=0,
                    length=14,
                    unix_time=1647531900,
                    date_time_format="wDT",
                )
            ]),
        ),
        (
            "`code`",
            "code",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.CODE, offset=0, length=4)
            ]),
        ),
    ],
)
def test_markdown_unparse_simple(expected, text, entities):
    assert Markdown.unparse(text=text, entities=entities) == expected


def test_markdown_unparse_pre():
    expected = """```python
for i in range(10):
    print(i)
```"""

    text = """for i in range(10):
    print(i)"""

    entities = pyrogram.types.List([pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.PRE, offset=0,
                                                                 length=32, language='python')])

    assert Markdown.unparse(text=text, entities=entities) == expected


def test_markdown_unparse_blockquote():
    expected = """> Hello
> from

> pyrogram!"""

    text = """Hello\nfrom\n\npyrogram!"""

    entities = pyrogram.types.List(
        [pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BLOCKQUOTE, offset=0, length=10),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BLOCKQUOTE, offset=12, length=9)])

    assert Markdown.unparse(text=text, entities=entities) == expected


def test_markdown_unparse_mixed():
    expected = "**aaaaaaa__aaabbb**__~~dddddddd||ddeee~~||||eeeeeeefff||ffff`fffggggggg`ggghhhhhhhhhh"
    text = "aaaaaaaaaabbbddddddddddeeeeeeeeeeffffffffffgggggggggghhhhhhhhhh"
    entities = pyrogram.types.List(
        [pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BOLD, offset=0, length=13),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.ITALIC, offset=7, length=6),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.STRIKETHROUGH, offset=13, length=13),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.SPOILER, offset=21, length=5),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.SPOILER, offset=26, length=10),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.CODE, offset=40, length=10)])

    assert Markdown.unparse(text=text, entities=entities) == expected


def test_markdown_unparse_no_entities():
    expected = "text"
    text = "text"
    entities = []

    assert Markdown.unparse(text=text, entities=entities) == expected

def test_markdown_unparse_html():
    expected = "__This works, it's ok__ <b>This shouldn't</b>"
    text = "This works, it's ok <b>This shouldn't</b>"
    entities = pyrogram.types.List(
        [pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.ITALIC, offset=0, length=19)])

    assert Markdown.unparse(text=text, entities=entities) == expected


def test_markdown_parse_date_time():
    result = asyncio.run(Markdown(None).parse('![22:45 tomorrow](tg://time?unix=1647531900&format=wDT)'))

    assert result["message"] == "22:45 tomorrow"
    assert len(result["entities"]) == 1

    entity = result["entities"][0]
    assert entity.type == pyrogram.enums.MessageEntityType.DATE_TIME
    assert entity.offset == 0
    assert entity.length == 14
    assert entity.unix_time == 1647531900
    assert entity.date_time_format == "wDT"


def test_markdown_parse_date_time_without_format():
    result = asyncio.run(Markdown(None).parse('![22:45 tomorrow](tg://time?unix=1647531900)'))

    assert result["message"] == "22:45 tomorrow"
    assert len(result["entities"]) == 1

    entity = result["entities"][0]
    assert entity.type == pyrogram.enums.MessageEntityType.DATE_TIME
    assert entity.unix_time == 1647531900
    assert entity.date_time_format is None


def test_markdown_parse_invalid_date_time():
    text = '![22:45 tomorrow](tg://time?unix=abc&format=wDT)'
    result = asyncio.run(Markdown(None).parse(text))

    assert result["message"] == text
    assert result["entities"] is None


def test_markdown_parse_tg_user_link_as_text_mention():
    result = asyncio.run(Markdown(None).parse("[Alice](tg://user?id=123456)"))

    assert result["message"] == "Alice"
    assert len(result["entities"]) == 1

    entity = result["entities"][0]
    assert entity.type == pyrogram.enums.MessageEntityType.TEXT_MENTION
    assert entity.offset == 0
    assert entity.length == 5
    assert entity.user.id == 123456


def test_markdown_parse_tg_user_link_exports_raw_mention_for_client():
    result = asyncio.run(Markdown(_FakeClient()).parse("[Alice](tg://user?id=123456)"))

    assert result["message"] == "Alice"
    assert len(result["entities"]) == 1
    assert isinstance(result["entities"][0], raw.types.InputMessageEntityMentionName)
    assert result["entities"][0].offset == 0
    assert result["entities"][0].length == 5


def test_markdown_parse_expandable_blockquote():
    result = asyncio.run(Markdown(None).parse("**> a\n> b||"))

    assert result["message"] == "a\nb"
    assert len(result["entities"]) == 1

    entity = result["entities"][0]
    assert entity.type == pyrogram.enums.MessageEntityType.BLOCKQUOTE
    assert entity.offset == 0
    assert entity.length == 3
    assert entity.expandable is True


def test_default_parse_combined_date_time_and_markdown():
    text = '**<tg-time unix="1647531900" format="wDT">22:45 tomorrow</tg-time>**'
    result = asyncio.run(Parser(None).parse(text, enums.ParseMode.DEFAULT))

    assert result["message"] == "22:45 tomorrow"
    assert len(result["entities"]) == 2

    bold, date_time = result["entities"]
    assert bold.type == pyrogram.enums.MessageEntityType.BOLD
    assert bold.offset == 0
    assert bold.length == 14

    assert date_time.type == pyrogram.enums.MessageEntityType.DATE_TIME
    assert date_time.offset == 0
    assert date_time.length == 14
    assert date_time.unix_time == 1647531900
    assert date_time.date_time_format == "wDT"


@pytest.mark.parametrize(
    ("text", "message", "entity_type"),
    [
        ("**bold**", "bold", pyrogram.enums.MessageEntityType.BOLD),
        ("__italic__", "italic", pyrogram.enums.MessageEntityType.ITALIC),
        ("--underline--", "underline", pyrogram.enums.MessageEntityType.UNDERLINE),
        ("~~strike~~", "strike", pyrogram.enums.MessageEntityType.STRIKETHROUGH),
        ("||spoiler||", "spoiler", pyrogram.enums.MessageEntityType.SPOILER),
    ],
)
def test_markdown_parse_basic_entities(text, message, entity_type):
    result = asyncio.run(Markdown(None).parse(text))

    assert result["message"] == message
    assert len(result["entities"]) == 1
    assert result["entities"][0].type == entity_type


def test_markdown_parse_invalid_emoji_target_stays_plain_text():
    text = "![smile](https://example.com)"
    result = asyncio.run(Markdown(None).parse(text))

    assert result["message"] == text
    assert result["entities"] is None


def test_markdown_parse_utf16_date_time_with_emoji_prefix():
    result = asyncio.run(Markdown(None).parse("🥲 ![22:45 tomorrow](tg://time?unix=1647531900)"))

    assert result["message"] == "🥲 22:45 tomorrow"
    assert len(result["entities"]) == 1

    entity = result["entities"][0]
    assert entity.type == pyrogram.enums.MessageEntityType.DATE_TIME
    assert entity.offset == 3
    assert entity.length == 14


def test_markdown_roundtrip_multiple_entity_types():
    text = "bold strike URL 22:45 tomorrow"
    entities = pyrogram.types.List([
        pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BOLD, offset=0, length=4),
        pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.STRIKETHROUGH, offset=5, length=6),
        pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.TEXT_LINK,
                                     offset=12, length=3, url="https://pyrogram.org/"),
        pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.DATE_TIME,
                                     offset=16, length=14, unix_time=1647531900, date_time_format="t"),
    ])

    parsed = asyncio.run(Markdown(None).parse(Markdown.unparse(text, entities)))

    assert parsed["message"] == text
    assert [(entity.type, entity.offset, entity.length) for entity in parsed["entities"]] == [
        (pyrogram.enums.MessageEntityType.BOLD, 0, 4),
        (pyrogram.enums.MessageEntityType.STRIKETHROUGH, 5, 6),
        (pyrogram.enums.MessageEntityType.TEXT_LINK, 12, 3),
        (pyrogram.enums.MessageEntityType.DATE_TIME, 16, 14),
    ]
    assert parsed["entities"][2].url == "https://pyrogram.org/"
    assert parsed["entities"][3].unix_time == 1647531900
    assert parsed["entities"][3].date_time_format == "t"


def test_markdown_roundtrip_underline():
    text = "underline"
    entities = pyrogram.types.List([
        pyrogram.types.MessageEntity(type=enums.MessageEntityType.UNDERLINE, offset=0, length=9)
    ])

    markdown = Markdown.unparse(text, entities)
    parsed = asyncio.run(Markdown(None).parse(markdown))

    assert markdown == "--underline--"
    assert parsed["message"] == text
    assert len(parsed["entities"]) == 1
    assert parsed["entities"][0].type == enums.MessageEntityType.UNDERLINE


def test_markdown_unparse_text_mention():
    text = "Alice"
    entities = pyrogram.types.List([
        pyrogram.types.MessageEntity(
            type=enums.MessageEntityType.TEXT_MENTION,
            offset=0,
            length=5,
            user=pyrogram.types.User(id=123456, is_self=False)
        )
    ])

    assert Markdown.unparse(text, entities) == "[Alice](tg://user?id=123456)"


def test_markdown_unparse_expandable_blockquote():
    text = "a\nb"
    entities = pyrogram.types.List([
        pyrogram.types.MessageEntity(
            type=enums.MessageEntityType.BLOCKQUOTE,
            offset=0,
            length=3,
            expandable=True
        )
    ])

    assert Markdown.unparse(text, entities) == "**> a\n> b||"


def test_default_parse_combined_html_and_markdown_offsets():
    text = '<b>bold</b> __italic__ <tg-time unix="1647531900" format="r">soon</tg-time>'
    result = asyncio.run(Parser(None).parse(text, enums.ParseMode.DEFAULT))

    assert result["message"] == "bold italic soon"
    assert [(entity.type, entity.offset, entity.length) for entity in result["entities"]] == [
        (pyrogram.enums.MessageEntityType.BOLD, 0, 4),
        (pyrogram.enums.MessageEntityType.ITALIC, 5, 6),
        (pyrogram.enums.MessageEntityType.DATE_TIME, 12, 4),
    ]
    assert result["entities"][2].unix_time == 1647531900
    assert result["entities"][2].date_time_format == "r"


def test_markdown_unparse_email():
    text = "test@example.com"
    entities = pyrogram.types.List([
        pyrogram.types.MessageEntity(
            type=pyrogram.enums.MessageEntityType.EMAIL,
            offset=0,
            length=16,
        )
    ])

    assert Markdown.unparse(text, entities) == "[test@example.com](mailto:test@example.com)"


class _FakeClient:
    async def resolve_peer(self, user_id: int):
        return raw.types.InputUser(user_id=user_id, access_hash=0)
