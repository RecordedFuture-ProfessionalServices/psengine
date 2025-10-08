import pytest

from psengine.analyst_notes import AnalystNote


def test_common_models_json():
    note = AnalystNote(
        id='12345',
        attributes={'title': 'abc', 'text': 'abc', 'published': '2023-11-03T13:31:56.878Z'},
        source={'id': 'abc', 'name': 'abc', 'type': 'abc'},
        external_id='',
    )
    unset_true = note.json(exclude_unset=True, auto_exclude_unset=False)
    all_print = note.json(exclude_none=False, exclude_unset=False, auto_exclude_unset=False)
    exclude_id = note.json(exclude={'attributes'})

    with pytest.raises(
        ValueError, match='`auto_exclude_unset` is False, `exclude_unset has to be provided`'
    ):
        note.json(auto_exclude_unset=False)

    assert unset_true['external_id'] == ''
    assert unset_true['attributes'].get('context_entities', 'missing') == 'missing'
    assert all_print['attributes'].get('context_entities', 'missing') != 'missing'
    assert exclude_id.get('attributes', 'missing') == 'missing'
