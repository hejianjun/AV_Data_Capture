import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from mdc.download.subtitles import download_subtitles, open_download


class TestSubtitles(unittest.TestCase):
    """测试字幕下载功能"""
    
    @patch('mdc.download.subtitles.config')
    @patch('mdc.download.subtitles.requests.get')
    @patch('mdc.download.subtitles.html.fromstring')
    @patch('mdc.download.subtitles.open_download')
    def test_download_subtitles_success(
        self, mock_open_download, mock_fromstring, mock_get, mock_config
    ):
        """测试字幕下载成功的情况"""
        # 设置模拟配置
        mock_proxy = MagicMock()
        mock_proxy.enable = False
        
        mock_instance = MagicMock()
        mock_instance.proxy.return_value = mock_proxy
        mock_config.getInstance.return_value = mock_instance
        
        # 设置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<html></html>'
        mock_get.return_value = mock_response
        
        # 设置模拟HTML解析
        mock_tree = MagicMock()
        mock_tree.xpath.return_value = ['/subtitle/123']
        mock_fromstring.return_value = mock_tree
        
        # 设置模拟下载成功
        mock_open_download.return_value = True
        
        # 测试下载功能
        result = download_subtitles(
            "./test.mp4", "./", False, "SSNI-813", 1, "", "", ""
        )
        
        # 验证结果
        self.assertTrue(result)
        mock_get.assert_called_once()
        mock_fromstring.assert_called_once()
        mock_open_download.assert_called_once()
    
    @patch('mdc.download.subtitles.config')
    @patch('mdc.download.subtitles.requests.get')
    def test_download_subtitles_failure(self, mock_get, mock_config):
        """测试字幕下载失败的情况"""
        # 设置模拟配置
        mock_proxy = MagicMock()
        mock_proxy.enable = False
        
        mock_instance = MagicMock()
        mock_instance.proxy.return_value = mock_proxy
        mock_config.getInstance.return_value = mock_instance
        
        # 设置模拟响应 - 请求失败
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # 测试下载功能
        result = download_subtitles(
            "./test.mp4", "./", False, "SSNI-813", 1, "", "", ""
        )
        
        # 验证结果
        self.assertFalse(result)
    
    @patch('mdc.download.subtitles.config')
    @patch('mdc.download.subtitles.requests.get')
    @patch('mdc.download.subtitles.html.fromstring')
    @patch('builtins.open', new_callable=mock_open)
    def test_open_download_success(
        self, mock_file, mock_fromstring, mock_get, mock_config
    ):
        """测试打开下载链接并保存文件"""
        # 设置模拟配置
        mock_proxy = MagicMock()
        mock_proxy.enable = False
        
        mock_instance = MagicMock()
        mock_instance.proxy.return_value = mock_proxy
        mock_config.getInstance.return_value = mock_instance
        
        # 设置模拟字幕页面响应
        mock_subtitle_page_response = MagicMock()
        mock_subtitle_page_response.status_code = 200
        mock_subtitle_page_response.content = b'<html></html>'
        
        # 设置模拟字幕下载响应
        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b'Subtitle content'
        
        # 设置模拟响应序列
        mock_get.side_effect = [mock_subtitle_page_response, mock_download_response]
        
        # 设置模拟HTML解析
        mock_tree = MagicMock()
        mock_tree.xpath.return_value = ['/download/123.srt']
        mock_fromstring.return_value = mock_tree
        
        # 测试打开下载链接
        result = open_download(
            "/subtitle/123", "./", "SSNI-813", "", "", ""
        )
        
        # 验证结果
        self.assertTrue(result)
        mock_get.assert_called()
        self.assertEqual(mock_get.call_count, 2)
        mock_file.assert_called_once_with("./SSNI-813.srt", "wb")
    
    @patch('mdc.download.subtitles.config')
    @patch('mdc.download.subtitles.requests.get')
    def test_open_download_failure(self, mock_get, mock_config):
        """测试打开下载链接失败的情况"""
        # 设置模拟配置
        mock_proxy = MagicMock()
        mock_proxy.enable = False
        
        mock_instance = MagicMock()
        mock_instance.proxy.return_value = mock_proxy
        mock_config.getInstance.return_value = mock_instance
        
        # 设置模拟响应 - 请求失败
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # 测试打开下载链接
        result = open_download(
            "/subtitle/123", "./", "SSNI-813", "", "", ""
        )
        
        # 验证结果
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()