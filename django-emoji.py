#coding=utf-8

from django import template
from re import compile
from emoji_list import emojis

register = template.Library()
emoji_finder = compile(u'(:[^:]+:)')

@register.filter(name='emoji')
def emoji_praser(value):
    for emoji in set(emoji_finder.findall(value)):
        if emoji in emojis:
            value = value.replace(emoji,u'<img src="%s" height="22" width="22"> />' % emojis[emoji])
    return value