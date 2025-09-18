from requests import Response
from psengine.fusion.fusion_mgr import FusionMgr
import pytest


class TestFusionMgr:
    @pytest.mark.parametrize(
        'filepath',
        [
            '/home/moise/vulns.json',
            'home/moise/vulns.json',
        ],
    )
    def test_get_file(self, fusion_mgr: FusionMgr, mocker, make_binary_response, filepath):
        mock = make_binary_response(b'abcdef', {})
        mock_response = mocker.patch.object(fusion_mgr.rf_client, 'request', return_value=mock)

        data = fusion_mgr.get_files(filepath)[0]

        assert data.file_path == '/home/moise/vulns.json'
        assert data.file_content == b'abcdef'
        assert data.file_found is True
        assert mock_response.call_args[0] == (
            'get',
            'https://api.recordedfuture.com/fusion/v3/files/%2Fhome%2Fmoise%2Fvulns.json',
        )

    def test_get_files(self, fusion_mgr, mocker, make_binary_response):
        filepaths = ['/home/moise/vulns.json', '/home/moise/vulns.csv']

        mock = make_binary_response(b'abcdef', {})
        mock_response = mocker.patch.object(
            fusion_mgr.rf_client, 'request', side_effect=[mock, mock]
        )
        data = fusion_mgr.get_files(filepaths)
        for i, d in enumerate(data):
            assert d.file_path == filepaths[i]
            assert d.file_content == b'abcdef'
            assert d.file_found is True
            assert mock_response.call_args[0][0] == 'get'
            assert mock_response.call_args[0][1].startswith(
                'https://api.recordedfuture.com/fusion/v3/files/%2Fhome%2Fmoise%2Fvulns'
            )

    def test_get_file_not_found(self, fusion_mgr, mocker):
        filepath = '/home/fake/vulns.json'

        mocker.patch.object(fusion_mgr, '_get_files', return_value=None)
        data = fusion_mgr.get_files(filepath)[0]
        assert len(data.file_content) == 0
        assert data.file_found is False

    def test_list_path(self, fusion_mgr, mocker):
        filepath = '/home/moise'
        mocker.patch.object(fusion_mgr.rf_client, 'request', return_value=mocked_data)
        data = fusion_mgr.list_dir(filepath)
        assert data.path == filepath
        assert data.name == 'moise'
        assert data.type_ == 'directory'
        assert all(d.type_ == 'file' for d in data.files)
        assert all(d.hash is not None for d in data.files)
        assert all(d.flow is not None for d in data.files)
        assert all(d.size is not None for d in data.files)

    # def test_list_dir(self, fusion_mgr, mocker):
    #     filepath = '/home'
    #     mocker.patch.object(fusion_mgr.rf_client, 'request', return_value=mocked_data)
    #     data = fusion_mgr.list_dir(filepath)
    #     assert data.path == filepath
    #     assert data.name == 'home'
    #     assert data.type_ == 'directory'
    #     assert all(d.type_ == 'file' for d in data.files)
    #     assert all(d.hash is not None for d in data.files)
    #     assert all(d.flow is not None for d in data.files)
    #     assert all(d.size is not None for d in data.files)
