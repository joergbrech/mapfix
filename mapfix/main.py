#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
os.environ["KIVY_NO_ARGS"] = "1"

import click

from mapfix.mapfix import MapFixApp


@click.command()
def main():
    """Run MapfixApp .
    """
    MapFixApp().run()
