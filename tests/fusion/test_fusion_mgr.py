from pathlib import Path
from types import SimpleNamespace

import pytest

from psengine.fusion.errors import (
    FusionPostFileError,
)
from psengine.fusion.fusion_mgr import DirectoryListOut, FusionMgr


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

        mocker.patch.object(fusion_mgr, '_get_file', return_value=None)
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

        assert isinstance(data, DirectoryListOut)

    def test_post_file_success(self, tmp_path, fusion_mgr: FusionMgr, mocker):
        local_file = tmp_path / 'vulns.json'
        local_file.write_bytes(b'abcdef')

        api_response = {
            'type': 'file',
            'name': 'vulns.json',
            'path': '/home/moise/vulns.json',
            'format': 'json',
            'size': 6,
        }
        mock_request = mocker.patch.object(
            fusion_mgr.rf_client, 'request', return_value=api_response
        )

        out = fusion_mgr.post_file(local_file, '/home/moise/vulns.json')

        assert out.path == '/home/moise/vulns.json'
        assert out.name == 'vulns.json'
        assert out.type_ == 'file'
        assert mock_request.call_args[0][0] == 'post'
        assert mock_request.call_args[0][1].endswith('%2Fhome%2Fmoise%2Fvulns.json')

    def test_post_file_not_exists_raises(self, tmp_path, fusion_mgr: FusionMgr):
        missing = tmp_path / 'does_not_exist.json'
        with pytest.raises(FusionPostFileError):
            fusion_mgr.post_file(missing, '/home/moise/does_not_exist.json')

    def test_post_file_permission_denied(self, tmp_path: Path, fusion_mgr: FusionMgr):
        local_file = tmp_path / 'noread.json'
        local_file.touch(222)
        local_file.write_bytes(b'abdjlks')

        with pytest.raises(FusionPostFileError, match=r'.*\[Errno 13\] Permission denied.*'):
            fusion_mgr.post_file(local_file, '/home/moise/noread.json')

    def test_delete_files_single(self, fusion_mgr: FusionMgr, mocker):
        mocker.patch.object(fusion_mgr, '_delete_file', side_effect=[object(), None])

        single = fusion_mgr.delete_files('home/moise/vulns.json')[0]
        assert single.file_path == '/home/moise/vulns.json'
        assert single.file_deleted is True

    def test_delete_files_multiple(self, fusion_mgr: FusionMgr, mocker):
        mocker.patch.object(fusion_mgr, '_delete_file', side_effect=[object(), None])

        results = fusion_mgr.delete_files(['/home/moise/one.csv', '/home/moise/two.csv'])
        assert [r.file_deleted for r in results] == [True, False]
        assert results[0].file_path == '/home/moise/one.csv'
        assert results[1].file_path == '/home/moise/two.csv'

    def test_head_files_found_and_not_found(self, fusion_mgr: FusionMgr, mocker):
        head_ok = SimpleNamespace(
            headers={
                'content-disposition': 'attachment; filename="vulns.json"',
                'Content-Length': 6,
                'content-type': 'application/json',
                'etag': 'abvef',
                'last-modified': 'Fri, 14 Mar 2025 10:00:00 GMT',
            }
        )
        mocker.patch.object(fusion_mgr, '_head_file', side_effect=[head_ok, None])

        outs = fusion_mgr.head_files(['/home/moise/vulns.json', '/home/moise/missing.json'])

        assert outs[0].file_path == '/home/moise/vulns.json'
        assert outs[0].file_found is True
        assert outs[0].content_length == 6
        assert outs[0].content_type == 'application/json'
        assert outs[0].content_disposition.startswith('attachment')

        assert outs[1].file_path == '/home/moise/missing.json'
        assert outs[1].file_found is False
        assert outs[1].content_length is None
        assert outs[1].content_type is None

    def test_get_files_mixed_found_and_missing(self, fusion_mgr: FusionMgr, mocker):
        get_ok = SimpleNamespace(content=b'abcdef')
        mocker.patch.object(fusion_mgr, '_get_file', side_effect=[get_ok, None])

        files = ['/home/moise/vulns.json', '/home/moise/missing.json']
        outs = fusion_mgr.get_files(files)

        assert outs[0].file_path == files[0]
        assert outs[0].file_content == b'abcdef'
        assert outs[0].file_found is True

        assert outs[1].file_path == files[1]
        assert outs[1].file_content == b''
        assert outs[1].file_found is False
