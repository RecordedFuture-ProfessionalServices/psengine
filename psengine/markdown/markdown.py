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

import html
from typing import Union

import markdown_strings
from markdown_strings import header
from pydantic import validate_call

from .models import Section

TITLE_HEADER_LEVEL = 2

###############################################################################
# Helpers
###############################################################################


def divider() -> str:
    """Return divider."""
    return '\n---\n'


def table_from_rows(table_list) -> str:
    r"""Return a formatted table, using each list as the list. The specifics are
    the same as those for the table function.

    >>> table_from_rows([["1","2","3"],["4","5","6"],["7","8","9"]])
    '| 1 | 2 | 3 |\\n| --- | --- | --- |\\n| 4 | 5 | 6 |\\n| 7 | 8 | 9 |'
    """
    longest_list = max(table_list, key=len)
    number_of_columns = len(longest_list)
    columns = [
        [
            str(row[column]).replace('|', ' ').replace('\n', ' ') if column < len(row) else ''
            for row in table_list
        ]
        for column in range(number_of_columns)
    ]
    return markdown_strings.table(columns)


def clean_text(text: str) -> str:
    """Cleanup legacy alerts data from markdown and html text special chars."""
    text = (
        text.replace('\n', '')
        .replace('#', '\\#')
        .replace('_', '\\_')
        .replace('-', '\\-')
        .replace('*', '•')
        .replace('\u2028', ' ')
    )
    return html.escape(text)


def escape_pipe_characters(text: str) -> str:
    """Escape pipe characters in text."""
    return text.replace('|', '\\|')


def html_textarea(text: str) -> str:
    """Wrap text in a markdown code block."""
    return f'<textarea readonly="true">{text}</textarea>'


class MarkdownMaker:
    """Class to manage markdown inputs and formatting of markdown output."""

    def __init__(
        self,
        addendum: str = '',
        character_limit: int = None,
        defang_iocs: bool = False,
        iocs_to_defang: list = None,
    ):
        self.title = None
        self.sections = []
        self.addendum = addendum
        if character_limit is not None and character_limit < len(addendum):
            raise ValueError(f'Character limit must be at least {len(addendum)}')
        self.character_limit = character_limit
        self.defang_iocs = defang_iocs
        if self.defang_iocs and iocs_to_defang is None:
            raise ValueError('If `defang_iocs` is True, you need to supply `iocs_to_defang`.')
        self.iocs_to_defang = iocs_to_defang

    @validate_call
    def add_title(self, title: str) -> None:
        """Add title to the markdown."""
        self.title = title

    def validate_section(self, title: str, content: Union[list[dict], list[str]]) -> Section:
        """Recursive function to validate a section and its content.

        Args:
            title (str): Section title
            content (Union[list[dict], list[str]]): Section content

        Raises:
            ValueError: Raised if the section content is empty.

        Returns:
            Section: Returns a validated section object.
        """
        if len(content) == 0:
            raise ValueError('Section content cannot be empty.')
        if isinstance(content[0], str):
            return Section(title=title, content=content)
        if isinstance(content[0], dict):
            return Section(
                title=title, content=[self.validate_section(**section) for section in content]
            )

    @validate_call
    def add_section(self, title: str, content: Union[list[dict], list[str]]) -> None:
        """Add a section to the markdown."""
        self.sections.append(self.validate_section(title, content))

    def format_section(self, section: Section, header_level: int) -> str:
        """Recursive function to format a section and its content."""
        md_str = header(section.title, header_level) + '\n\n'
        if isinstance(section.content[0], str):
            md_str += '\n'.join(section.content)
        else:
            for sub_section in section.content:
                md_str += self.format_section(sub_section, header_level + 1)

        md_str += '\n\n'

        return md_str

    def format_defang_iocs(self, entities: set, md_str: str) -> str:
        """Replace `.` with `[.]` for every IOC found."""
        for entity in entities:
            defanged = entity.replace('.', '[.]')
            md_str = md_str.replace(entity, defanged)

        return md_str

    def format_output(self) -> str:
        """Format the markdown output.

        Call this method after adding a title and any sections.
        """
        md_str = ''
        if self.title is not None:
            md_str += header(self.title, TITLE_HEADER_LEVEL) + '\n\n'

        for section in self.sections:
            md_str += self.format_section(section, TITLE_HEADER_LEVEL + 1)

        if self.defang_iocs:
            md_str = self.format_defang_iocs(self.iocs_to_defang, md_str)

        if self.character_limit is not None and len(md_str) > self.character_limit:
            md_str = md_str[: self.character_limit - len(self.addendum)] + self.addendum

        return md_str
