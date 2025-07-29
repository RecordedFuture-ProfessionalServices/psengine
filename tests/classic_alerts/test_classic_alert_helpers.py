import os

import pytest

from psengine.classic_alerts import ClassicAlertMgr
from psengine.classic_alerts.helpers import save_image, save_images
from psengine.errors import WriteFileError
from tests.classic_alerts.conftest import MOCK_DIR

ALERT_IDS = ['w1KF1z', 'whz4Ya', 'w7HgBa']


class Test_ClassicAlertHelpers:
    def test_save_image(self, ca_mgr: ClassicAlertMgr, tmp_path, make_binary_response, mocker):
        mock = make_binary_response(b'abcd', {'Content-Disposition': 'filename=abc.jpg'})
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        raw_image = ca_mgr.fetch_image(id_='img:d4620c6a-c789-48aa-b652-b47e0d06d91a')
        output_dir = tmp_path / 'output' / 'alerts'
        file_path = save_image(
            image_bytes=raw_image,
            file_name='d4620c6a-c789-48aa-b652-b47e0d06d91a',
            output_directory=output_dir.as_posix(),
        )
        assert os.path.exists(file_path)

    def test_save_image_raises_WriteFileError(
        self, ca_mgr: ClassicAlertMgr, make_binary_response, mocker
    ):
        mock = make_binary_response(b'abcd', {'Content-Disposition': 'filename=abc.jpg'})
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        raw_image = ca_mgr.fetch_image(id_='img:d4620c6a-c789-48aa-b652-b47e0d06d91a')
        output_dir = os.path.join('/groot', 'tmp')
        with pytest.raises(WriteFileError):
            save_image(
                image_bytes=raw_image,
                file_name='d4620c6a-c789-48aa-b652-b47e0d06d91a',
                output_directory=output_dir,
            )

    def test_save_images(
        self, ca_mgr: ClassicAlertMgr, tmp_path, make_binary_response, mocker, mock_request
    ):
        mocks = [
            mock_request(MOCK_DIR / 'test_save_images.json'),
            make_binary_response(b'abcd', {'Content-Disposition': 'filename=abc.jpg'}),
            make_binary_response(b'abcde', {'Content-Disposition': 'filename=abc2.jpg'}),
        ]
        mocker.patch.object(ca_mgr.rf_client, 'request', side_effect=mocks)

        alert = ca_mgr.fetch('xOTsae')
        ca_mgr.fetch_all_images(alert)
        results = save_images(alert, output_directory=tmp_path.as_posix())

        for result in results.values():
            assert os.path.exists(result)
