#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
os.environ["KIVY_NO_ARGS"] = "1"

import click

from mapfix.mapfix import MapfixApp


@click.command()
@click.option(
    '-l', '--language', help='Default language of the App', default='en',
    type=click.Choice(['en', 'es', 'de', 'fr'])
)
def main(language):
    """Run MapfixApp with the given language setting.
    """
    MapfixApp(language).run()
