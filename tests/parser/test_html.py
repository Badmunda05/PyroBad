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
from pyrogram import raw
from pyrogram.parser.html import HTML
from pyrogram.types import User


@pytest.mark.parametrize(
    ("expected", "text", "entities"),
    [
        (
            "<b>bold</b>",
            "bold",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BOLD, offset=0, length=4)
            ]),
        ),
        (
            "<i>italic</i>",
            "italic",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.ITALIC, offset=0, length=6)
            ]),
        ),
        (
            "<u>underline</u>",
            "underline",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.UNDERLINE, offset=0, length=9)
            ]),
        ),
        (
            "<s>strike</s>",
            "strike",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.STRIKETHROUGH, offset=0, length=6)
            ]),
        ),
        (
            "<spoiler>spoiler</spoiler>",
            "spoiler",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.SPOILER, offset=0, length=7)
            ]),
        ),
        (
            '<a href="https://pyrogram.org/">URL</a>',
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
            '<a href="tg://user?id=123456">mention</a>',
            "mention",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(
                    type=pyrogram.enums.MessageEntityType.TEXT_MENTION,
                    offset=0,
                    length=7,
                    user=User(id=123456, is_self=False),
                )
            ]),
        ),
        (
            '<tg-time unix="1647531900" format="wDT">22:45 tomorrow</tg-time>',
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
            "<code>code</code>",
            "code",
            pyrogram.types.List([
                pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.CODE, offset=0, length=4)
            ]),
        ),
    ],
)
def test_html_unparse_simple(expected, text, entities):
    assert HTML.unparse(text=text, entities=entities) == expected


def test_html_unparse_pre():
    expected = """<pre language="python">for i in range(10):
    print(i)</pre>"""

    text = """for i in range(10):
    print(i)"""

    entities = pyrogram.types.List([pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.PRE, offset=0,
                                                                 length=32, language='python')])

    assert HTML.unparse(text=text, entities=entities) == expected


def test_html_unparse_blockquote():
    expected = """<blockquote>Quote text</blockquote>
    from pyrogram"""

    text = """Quote text
    from pyrogram"""

    entities = pyrogram.types.List([pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BLOCKQUOTE, offset=0,
                                                                 length=10)])

    assert HTML.unparse(text=text, entities=entities) == expected


def test_html_unparse_mixed():
    expected = "<b>aaaaaaa<i>aaa<u>bbbb</u></i></b><u><i>bbbbbbccc</i></u><u>ccccccc<s>ddd</s></u><s>ddddd<spoiler>dd" \
               "eee</spoiler></s><spoiler>eeeeeeefff</spoiler>ffff<code>fffggggggg</code>ggghhhhhhhhhh"
    text = "aaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeeeffffffffffgggggggggghhhhhhhhhh"
    entities = pyrogram.types.List(
        [pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BOLD, offset=0, length=14),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.ITALIC, offset=7, length=7),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.UNDERLINE, offset=10, length=4),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.UNDERLINE, offset=14, length=9),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.ITALIC, offset=14, length=9),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.UNDERLINE, offset=23, length=10),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.STRIKETHROUGH, offset=30, length=3),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.STRIKETHROUGH, offset=33, length=10),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.SPOILER, offset=38, length=5),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.SPOILER, offset=43, length=10),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.CODE, offset=57, length=10)])

    assert HTML.unparse(text=text, entities=entities) == expected


def test_html_unparse_escaped():
    expected = "<b>&lt;b&gt;bold&lt;/b&gt;</b>"
    text = "<b>bold</b>"
    entities = pyrogram.types.List(
        [pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BOLD, offset=0, length=11)])

    assert HTML.unparse(text=text, entities=entities) == expected


def test_html_unparse_escaped_nested():
    expected = "<b>&lt;b&gt;bold <u>&lt;u&gt;underline&lt;/u&gt;</u> bold&lt;/b&gt;</b>"
    text = "<b>bold <u>underline</u> bold</b>"
    entities = pyrogram.types.List(
        [pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BOLD, offset=0, length=33),
         pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.UNDERLINE, offset=8, length=16)])

    assert HTML.unparse(text=text, entities=entities) == expected


def test_html_unparse_no_entities():
    expected = "text"
    text = "text"
    entities = []

    assert HTML.unparse(text=text, entities=entities) == expected


def test_html_parse_date_time():
    result = asyncio.run(HTML(None).parse('<tg-time unix="1647531900" format="wDT">22:45 tomorrow</tg-time>'))

    assert result["message"] == "22:45 tomorrow"
    assert len(result["entities"]) == 1

    entity = result["entities"][0]
    assert entity.type == pyrogram.enums.MessageEntityType.DATE_TIME
    assert entity.offset == 0
    assert entity.length == 14
    assert entity.unix_time == 1647531900
    assert entity.date_time_format == "wDT"


def test_html_parse_date_time_without_format():
    result = asyncio.run(HTML(None).parse('<tg-time unix="1647531900">22:45 tomorrow</tg-time>'))

    assert result["message"] == "22:45 tomorrow"
    assert len(result["entities"]) == 1

    entity = result["entities"][0]
    assert entity.type == pyrogram.enums.MessageEntityType.DATE_TIME
    assert entity.unix_time == 1647531900
    assert entity.date_time_format is None


def test_html_parse_invalid_date_time():
    result = asyncio.run(HTML(None).parse('<tg-time unix="abc" format="wDT">22:45 tomorrow</tg-time>'))

    assert result["message"] == '<tg-time unix="abc" format="wDT">22:45 tomorrow</tg-time>'
    assert result["entities"] is None


@pytest.mark.parametrize(
    ("text", "message", "entity_type"),
    [
        ("<b>bold</b>", "bold", pyrogram.enums.MessageEntityType.BOLD),
        ("<i>italic</i>", "italic", pyrogram.enums.MessageEntityType.ITALIC),
        ("<u>underline</u>", "underline", pyrogram.enums.MessageEntityType.UNDERLINE),
        ("<s>strike</s>", "strike", pyrogram.enums.MessageEntityType.STRIKETHROUGH),
        ("<spoiler>spoiler</spoiler>", "spoiler", pyrogram.enums.MessageEntityType.SPOILER),
    ],
)
def test_html_parse_basic_tags(text, message, entity_type):
    result = asyncio.run(HTML(None).parse(text))

    assert result["message"] == message
    assert len(result["entities"]) == 1
    assert result["entities"][0].type == entity_type


def test_html_parse_unclosed_tag_becomes_text():
    text = "<b>bold"
    result = asyncio.run(HTML(None).parse(text))

    assert result["message"] == text
    assert result["entities"] is None


def test_html_parse_utf16_date_time_with_emoji_prefix():
    result = asyncio.run(HTML(None).parse('🥲 <tg-time unix="1647531900">22:45 tomorrow</tg-time>'))

    assert result["message"] == "🥲 22:45 tomorrow"
    assert len(result["entities"]) == 1

    entity = result["entities"][0]
    assert entity.type == pyrogram.enums.MessageEntityType.DATE_TIME
    assert entity.offset == 3
    assert entity.length == 14


def test_html_parse_legacy_emoji_tag():
    result = asyncio.run(HTML(None).parse('<emoji id="123">x</emoji>'))

    assert result["message"] == "x"
    assert len(result["entities"]) == 1

    entity = result["entities"][0]
    assert entity.type == pyrogram.enums.MessageEntityType.CUSTOM_EMOJI
    assert entity.offset == 0
    assert entity.length == 1
    assert entity.custom_emoji_id == 123


def test_html_roundtrip_multiple_entity_types():
    text = "bold code URL 22:45 tomorrow"
    entities = pyrogram.types.List([
        pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.BOLD, offset=0, length=4),
        pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.CODE, offset=5, length=4),
        pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.TEXT_LINK,
                                     offset=10, length=3, url="https://pyrogram.org/"),
        pyrogram.types.MessageEntity(type=pyrogram.enums.MessageEntityType.DATE_TIME,
                                     offset=14, length=14, unix_time=1647531900, date_time_format="wDT"),
    ])

    parsed = asyncio.run(HTML(None).parse(HTML.unparse(text, entities)))

    assert parsed["message"] == text
    assert [(entity.type, entity.offset, entity.length) for entity in parsed["entities"]] == [
        (pyrogram.enums.MessageEntityType.BOLD, 0, 4),
        (pyrogram.enums.MessageEntityType.CODE, 5, 4),
        (pyrogram.enums.MessageEntityType.TEXT_LINK, 10, 3),
        (pyrogram.enums.MessageEntityType.DATE_TIME, 14, 14),
    ]
    assert parsed["entities"][2].url == "https://pyrogram.org/"
    assert parsed["entities"][3].unix_time == 1647531900
    assert parsed["entities"][3].date_time_format == "wDT"


class _FakeClient:
    async def resolve_peer(self, user_id: int):
        return raw.types.InputUser(user_id=user_id, access_hash=0)


def test_html_unparse_email():
    text = "test@example.com"
    entities = pyrogram.types.List([
        pyrogram.types.MessageEntity(
            type=pyrogram.enums.MessageEntityType.EMAIL,
            offset=0,
            length=16,
        )
    ])

    assert HTML.unparse(text=text, entities=entities) == '<a href="mailto:test@example.com">test@example.com</a>'


def test_html_parse_mailto():
    result = asyncio.run(HTML(None).parse('<a href="mailto:test@example.com">Email me</a>'))

    assert result["message"] == "Email me"
    assert len(result["entities"]) == 1

    entity = result["entities"][0]
    assert entity.type == pyrogram.enums.MessageEntityType.EMAIL
    assert entity.offset == 0
    assert entity.length == 8


def test_html_parse_mailto_roundtrip():
    text = "test@example.com"
    entities = pyrogram.types.List([
        pyrogram.types.MessageEntity(
            type=pyrogram.enums.MessageEntityType.EMAIL,
            offset=0,
            length=16,
        )
    ])

    html_text = HTML.unparse(text, entities)
    parsed = asyncio.run(HTML(None).parse(html_text))

    assert parsed["message"] == text
    assert len(parsed["entities"]) == 1
    assert parsed["entities"][0].type == pyrogram.enums.MessageEntityType.EMAIL


def test_html_parse_returns_raw_entities_for_client():
    result = asyncio.run(HTML(_FakeClient()).parse('<a href="tg://user?id=123456">mention</a>'))

    assert result["message"] == "mention"
    assert len(result["entities"]) == 1
    assert isinstance(result["entities"][0], raw.types.InputMessageEntityMentionName)
    assert result["entities"][0].offset == 0
    assert result["entities"][0].length == 7
