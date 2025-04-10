##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

import importlib
import os
from collections import namedtuple
from pathlib import Path
from typing import Annotated, Optional

import typer
import urllib3

from psengine._version import __version__

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

Command = namedtuple('Command', ['cmd', 'name', 'cmd_help', 'cmd_rich_help'])

PKG_NAME = __name__.split('.')[0]
CMD_FOLDER = (Path(__file__).parent / 'commands').resolve()

BRANDING = 'By Cyber Security Engineering at Recorded Future'
APP_DESCRIPTION = f"""A Recorded Future based CLI application for
rapid integration development with PSEngine. \n\n{BRANDING}"""


def get_commands() -> list[Command]:
    """Dynamically load all the available commands and subcommands."""
    commands = []
    for filename in os.listdir(CMD_FOLDER):
        if filename.endswith('.py') and filename.startswith('cmd_'):
            module_name = filename[:-3]
            module = importlib.import_module(f'.commands.{module_name}', package=PKG_NAME)
            commands.append(
                Command(
                    module.app,
                    module.CMD_NAME,
                    module.CMD_HELP + f'\n\n{BRANDING}\n\n',
                    module.CMD_RICH_HELP,
                )
            )

    return commands


app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode='markdown',
    context_settings={'help_option_names': ['-h', '--help']},
    help=APP_DESCRIPTION,
)

for command in get_commands():
    app.add_typer(
        command.cmd, name=command.name, help=command.cmd_help, rich_help_panel=command.cmd_rich_help
    )


def version_callback(value: bool):
    """Version callback."""
    if value:
        print(f'PSEngine version: {__version__} | {BRANDING}')
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,  # noqa: ARG001
    version: Annotated[  # noqa: ARG001
        Optional[bool],
        typer.Option('--version', callback=version_callback, is_eager=True),
    ] = None,
):
    """Main entry point."""


app()
