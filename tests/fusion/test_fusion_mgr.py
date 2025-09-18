import pytest

from psengine.fusion.fusion_mgr import FusionDirectory, FusionMgr


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

    def test_list_path(self, fusion_mgr, mocker, make_response):
        filepath = '/home/moise'
        response = {
            'type': 'directory',
            'name': 'moise',
            'path': '/home/moise',
            'files': [
                {
                    'type': 'file',
                    'name': 'vulns.json',
                    'path': '/home/moise/vulns.json',
                    'format': 'json',
                    'hash': '5c8e6a102df38b0e455b9a05353c45c0f6bcb5fb94aca4fea5547efbb60042b9',
                    'created': '2025-03-13T22:38:15.029Z',
                    'size': 26814,
                    'flow': 'snow_vuln_metrics',
                    'owner': '5zQaSyRpA1',
                },
                {
                    'type': 'file',
                    'name': 'vulns.csv',
                    'path': '/home/moise/vulns.csv',
                    'format': 'csv',
                    'hash': 'd31a29fab17fdd5dc784dc2f7d7052ef74e3872d6ea8ac82a1e1d0a842344894',
                    'created': '2025-03-14T09:38:32.165Z',
                    'size': 75722379,
                    'flow': 'snow_vuln_metrics',
                    'owner': '5zQaSyRpA1',
                },
                {
                    'type': 'directory',
                    'name': 'test',
                    'path': '/home/moise/test',
                },
            ],
        }
        mocker.patch.object(fusion_mgr.rf_client, 'request', return_value=make_response(response))
        data = fusion_mgr.list_dir(filepath)
        assert data.path == filepath
        assert data.name == 'moise'
        assert data.type_ == 'directory'
        assert data.files[-1].type_ == 'directory'
        assert data.files[0].type_ == 'file'

        assert isinstance(data, FusionDirectory)
