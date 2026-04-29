import pytest

from psengine.playbook_alerts import PACategory
from psengine.playbook_alerts.helpers import save_pba_images


def _store_first_image(alert, image_bytes: bytes):
    image_id = alert.image_ids[0]
    alert.store_image(image_id, image_bytes)
    return alert


def test_save_pba_images_supports_geopol(alerts_factory, tmp_path):
    geopol_alert = _store_first_image(
        alerts_factory(PACategory.GEOPOLITICS_FACILITY.value)[0],
        b'geopol-image',
    )

    save_pba_images(geopol_alert, tmp_path)

    saved_images = list(tmp_path.glob('*.png'))
    assert len(saved_images) == 1
    assert saved_images[0].read_bytes() == b'geopol-image'


def test_save_pba_images_supports_image_alert_list(alerts_factory, tmp_path):
    domain_alert = _store_first_image(
        next(alert for alert in alerts_factory(PACategory.DOMAIN_ABUSE.value) if alert.image_ids),
        b'domain-image',
    )
    geopol_alert = _store_first_image(
        alerts_factory(PACategory.GEOPOLITICS_FACILITY.value)[0],
        b'geopol-image',
    )

    save_pba_images([domain_alert, geopol_alert], tmp_path)

    assert {saved_image.read_bytes() for saved_image in tmp_path.glob('*.png')} == {
        b'domain-image',
        b'geopol-image',
    }


def test_save_pba_images_rejects_mixed_unsupported_alert_list(alerts_factory, tmp_path):
    geopol_alert = _store_first_image(
        alerts_factory(PACategory.GEOPOLITICS_FACILITY.value)[0],
        b'geopol-image',
    )
    identity_alert = alerts_factory(PACategory.IDENTITY_NOVEL_EXPOSURES.value)[0]

    with pytest.raises(TypeError, match='Image saving is only supported'):
        save_pba_images([geopol_alert, identity_alert], tmp_path)
