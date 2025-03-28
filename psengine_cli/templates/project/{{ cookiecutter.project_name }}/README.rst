==================================================
{{ cookiecutter.project_name_title }}
==================================================
**PSEngine** powered integration project.

PSEngine officially supports Python >= 3.9, < 3.14

Repo Structure
-----------------
- deps - Contains the dependencies required for the project, such as the PSEngine SDK.
- config - Contains the configuration
- {{ cookiecutter.lib_folder_name }} - Contains the main code logic
- {{cookiecutter.run_file_name }}.py - The main entry point
- requirements.txt - Contains the dependencies required for the project.
- requirements_dev.txt - Contains the dependencies required for development.
- tests - Contains the tests for the project.


Installation
==================================================
To install {{ cookiecutter.project_name_title }} for development, run the following command:

.. code-block:: bash

   $ pip install -r requirements_dev.txt


Testing & Code Review
==================================================



.. code-block:: bash
  
    $ make test      # Run ruff checks + unittests
    $ make unittests # Run unittests only