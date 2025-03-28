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
import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional

from typer import Argument, Option, Typer

from ..constants import TEMPLATES_DIR
from .epilogs import EPILOG_TEMPLATE_MANAGER, EPILOG_TEMPLATE_PROJECT

# This will be the name of the command
CMD_NAME = 'template'

# Main help message for the command
CMD_HELP = 'Generate templates to kickstart development'

# Rich help text for the command
CMD_RICH_HELP = 'Developer Utilities'

# Create a new Typer instance
app = Typer(no_args_is_help=True)


@app.command(help='Template for a new PSEngine powered project', epilog=EPILOG_TEMPLATE_PROJECT)
def project(
    project_name: Annotated[
        str,
        Argument(show_default=False, help='Name of the project to create, for example: siemonster'),
    ],
    path: Optional[str] = Argument(default='.', help='Path where to create the project folder'),
    force: Annotated[
        bool, Option('--force-create', '-f', help='Overwrite the project if it already exists')
    ] = False,
):
    """Template for a new PSEngine powered project."""
    path = Path(f'{path}/{project_name}')
    if path.exists() and not force:
        print('Project already exists. Use -f or --force-create to overwrite')
        sys.exit(1)

    os.system(
        f'cookiecutter {TEMPLATES_DIR}/project -f -o {path} --no-input project_name={project_name}'
    )
    print(f'New project created at {path}/{project_name}')


def is_inside_git_repo() -> bool:
    """Check if we are running inside the psengine-py repository."""
    is_psengine_repo = False
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--is-inside-work-tree'],
            capture_output=True,
            text=True,
            check=True,
        )
        is_psengine_repo = result.stdout.strip() == 'true'

        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True,
        )

        repo_path = result.stdout.strip()
        is_psengine_repo = is_psengine_repo and 'psengine-py' in repo_path.lower()
        return is_psengine_repo
    except subprocess.CalledProcessError:
        return False


@app.command(
    help='Template for a new module for PSEngine (must run within psengine-py repo)',
    epilog=EPILOG_TEMPLATE_MANAGER,
)
def module(
    module_name: Annotated[
        str,
        Argument(show_default=False, help='Name of the module to create, for example: identity'),
    ],
    force: Annotated[
        bool, Option('--force-create', '-f', help='Overwrite the module if it already exists')
    ] = False,
):
    """Template for a new module for PSEngine (must run within psengine-py repo)."""
    if not is_inside_git_repo():
        print('You must be in the psengine-py repository to run this command')
        sys.exit(1)

    required_paths = ['psengine', 'tests', 'examples']
    # Warn users if things already exists and if they want to overwrite?
    paths = [Path(f'{prefix}/{module_name}') for prefix in required_paths]
    if any(path.exists() for path in paths) and not force:
        print(
            'Warning: Some files already exist in psengine/, tests/ or examples/.  Use -f or --force-create to overwrite.'  # noqa: E501
        )
        sys.exit(1)

    current_dir = Path.cwd()
    if [f for f in required_paths if not Path(current_dir / f).exists()]:
        print('Error: you must be in the root of psengine repo.')
        sys.exit(1)

    os.system(
        f'cookiecutter {TEMPLATES_DIR}/module/module -f -o psengine --no-input module_name={module_name}'  # noqa: E501
    )
    print(f'New module created at psengine/{module_name}')
    os.system(
        f'cookiecutter {TEMPLATES_DIR}/module/tests -f -o tests --no-input module_name={module_name}'  # noqa: E501
    )
    print(f'New tests created at tests/{module_name}')
    os.system(
        f'cookiecutter {TEMPLATES_DIR}/module/example_app -f -o examples --no-input module_name={module_name}'  # noqa: E501
    )
    print(f'New example app created at examples/{module_name}')
