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


def esc_format(text, esc):
    """Return text with markdown formatting characters escaped."""
    if esc:
        return str(text).replace('_', r'\_').replace('*', r'\*').replace('`', r'\`')
    return text


def header(header_text, header_level, style='atx', esc=True):
    """Return a header of the specified level and style."""
    if not isinstance(header_level, int):
        raise TypeError('header_level must be int')
    if not isinstance(header_text, str):
        raise TypeError('header_text must be str')
    if style == 'atx':
        if not 1 <= header_level <= 6:
            raise ValueError(f'Invalid level {header_level} for atx')
        return f'{"#" * header_level} {esc_format(header_text, esc)}'
    if style == 'setext':
        if not 0 < header_level < 3:
            raise ValueError(f'Invalid level {header_level} for setext')
        header_character = '=' if header_level == 1 else '-'
        header_string = (header_character * 3) + header_character * (len(header_text) - 3)
        return f'{esc_format(header_text, esc)}\n{header_string}'
    raise ValueError(f"Invalid style {style} (choose 'atx' or 'setext')")


def italics(text, esc=True):
    """Return italics formatted text."""
    return f'_{esc_format(text, esc)}_'


def bold(text, esc=True):
    """Return bold formatted text."""
    return f'**{esc_format(text, esc)}**'


def inline_code(text):
    """Return formatted inline code."""
    return f'`{str(text)}`'


def code_block(text, language=''):
    """Return a code block, fenced if a language is specified."""
    if language:
        return f'```{language}\n{text}\n```'
    return '\n'.join([f'    {item}' for item in text.split('\n')])


def link(text, link_url, esc=True):
    """Return an inline link."""
    return f'[{esc_format(text, esc)}]({link_url})'


def image(alt_text, link_url, title='', esc=True):
    """Return an inline image."""
    image_string = f'![{esc_format(alt_text, esc)}]({link_url})'
    if title:
        image_string += f' "{esc_format(title, esc)}"'
    return image_string


def unordered_list(text_list, esc=True):
    """Return an unordered list from a list."""
    return '\n'.join([f'-   {esc_format(item, esc)}' for item in text_list])


def ordered_list(text_list, esc=True):
    """Return an ordered list from a list."""
    ordered_list = []
    for number, item in enumerate(text_list):
        ordered_list.append(
            f'{(f"{esc_format(number + 1, esc)}.").ljust(3)} {esc_format(item, esc)}'
        )
    return '\n'.join(ordered_list)


def blockquote(text, esc=True):
    """Return a blockquote."""
    return '\n'.join([f'> {esc_format(item, esc)}' for item in text.split('\n')])


def horizontal_rule(length=79, style='_'):
    """Return a horizontal rule of the specified length and style."""
    if style not in ('_', '*'):
        raise ValueError("Invalid style (choose '_' or '*')")
    if length < 3:
        raise ValueError('Length must be >= 3')
    return style * length


def strikethrough(text, esc=True):
    """Return text with strike-through formatting."""
    return f'~{esc_format(text, esc)}~'


def task_list(task_list, esc=True):
    """Return a task list from a 2-dimensional list of (text, completed) pairs."""
    tasks = []
    for item, completed in task_list:
        tasks.append(f'- [{"X" if completed else " "}] {esc_format(item, esc)}')
    return '\n'.join(tasks)


def table_row(text_list, pad=None, esc=True):
    """Return a single table row, optionally padded."""
    if pad is None:
        pad = [0] * len(text_list)
    row = '|'
    for column_number in range(len(text_list)):
        padding = pad[column_number] + 1
        row += (' ' + esc_format(text_list[column_number], esc)).ljust(padding) + ' |'
    return row


def table_delimiter_row(number_of_columns, column_lengths=None):
    """Return a delimiter row for use in a table."""
    if column_lengths is None:
        column_lengths = [0] * number_of_columns
    if number_of_columns != len(column_lengths):
        raise ValueError('number_of_columns must be the number of columns in column_lengths')
    delimiter_row = [
        '---' + '-' * (column_lengths[column_number] - 3)
        for column_number in range(number_of_columns)
    ]
    return table_row(delimiter_row)


def table(table_list):
    """Return a formatted table generated from a 2-dimensional list of columns."""
    number_of_columns = len(table_list)
    number_of_rows_in_column = [len(column) for column in table_list]
    string_list = [[str(cell) for cell in column] for column in table_list]
    column_lengths = [len(max(column, key=len)) for column in string_list]
    table = []

    row_list = [column[0] for column in string_list]
    table.append(table_row(row_list, pad=column_lengths))

    table.append(table_delimiter_row(len(column_lengths), column_lengths=column_lengths))

    for row in range(1, max(number_of_rows_in_column)):
        row_list = []
        for column_number in range(number_of_columns):
            if number_of_rows_in_column[column_number] > row:
                row_list.append(string_list[column_number][row])
            else:
                row_list.append('')
        table.append(table_row(row_list, pad=column_lengths))
    return '\n'.join(table)
