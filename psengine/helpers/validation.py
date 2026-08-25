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

import logging
from collections.abc import Iterable
from typing import Annotated, Any, TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError
from typing_extensions import Doc

LOG = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


def validate_list(
    model_cls: Annotated[type[T], Doc('Pydantic model each item should validate against.')],
    items: Annotated[
        Iterable[Any], Doc('Raw items to validate, typically dicts from an API response.')
    ],
    id_path: Annotated[
        str | None,
        Doc(
            'Dotted path into each raw item used to build a friendly identifier for log lines '
            "and exception notes, e.g. `'entity.name'`. If unresolvable for a given item, only "
            'the index is reported.'
        ),
    ] = None,
    log: Annotated[
        logging.Logger | None,
        Doc("Logger for the warnings. Defaults to this module's logger."),
    ] = None,
) -> Annotated[list[T], Doc('The list of validated `model_cls` instances.')]:
    """Validate a list of dicts against `model_cls`.

    Uses pydantic's `TypeAdapter` so a single validation pass collects all per-item errors with an
    index in their `loc`.

    Before re-raising, each failing item is (a) logged individually as a warning and (b) attached
    to the exception via `add_note`, so the entity identifier shows up in the traceback too.

    If `id_path` is provided, a human-readable identifier is extracted from the raw dict
    (e.g. `entity.name`); otherwise only the index is reported.

    Raises:
        pydantic.ValidationError: If any item fails validation. Unchanged
            from `[model_cls.model_validate(x) for x in items]`.
    """
    if not isinstance(items, list):
        items = list(items)
    try:
        return TypeAdapter(list[model_cls]).validate_python(items)
    except ValidationError as e:
        for msg in _format_failures(e, items, id_path, model_cls):
            (log or LOG).warning(msg)
            e.add_note(msg)
        raise


def _format_failures(
    exc: ValidationError,
    items: list[Any],
    id_path: str | None,
    model_cls: type[BaseModel],
) -> list[str]:
    """Build one message per failing item, keyed by index and optional id."""
    seen: set[int] = set()
    messages: list[str] = []
    for err in exc.errors():
        loc = err.get('loc') or ()
        if not loc or not isinstance(loc[0], int):
            continue
        idx = loc[0]
        if idx in seen:
            continue
        seen.add(idx)

        raw = items[idx] if 0 <= idx < len(items) else None
        identifier = _resolve_id_path(raw, id_path) if id_path else None
        id_hint = f' ({id_path}={identifier})' if identifier is not None else ''
        field_path = '.'.join(str(p) for p in loc[1:]) or '<root>'
        messages.append(
            f'{model_cls.__name__} validation failed at index {idx}{id_hint}: '
            f"field '{field_path}' {err.get('msg', '')}"
        )
    return messages


def _resolve_id_path(item: Any, id_path: str) -> Any:
    """Walk `id_path` (dot-separated) into `item`. Returns None on miss."""
    value: Any = item
    for part in id_path.split('.'):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
        if value is None:
            return None
    return value
