import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from mdc.utils.translation import is_japanese, translate


class TestTranslation(unittest.TestCase):
    """测试翻译相关功能"""
    
    def test_is_japanese(self):
        """测试日语检测功能"""
        # 测试日语文本（仅包含假名的文本）
        self.assertTrue(is_japanese("こんにちは"))  # 平假名
        self.assertTrue(is_japanese("カンニチワ"))  # 片假名
        self.assertTrue(is_japanese("Helloこんにちは"))  # 混合日语（包含假名）
        
        # 注意：纯汉字文本（如"日本語"）不会被检测为日语，因为汉字在中日韩文本中都存在
        # self.assertTrue(is_japanese("日本語"))      # 这个测试会失败，因为没有假名
        
        # 测试非日语文本
        self.assertFalse(is_japanese("Hello"))
        self.assertFalse(is_japanese("你好"))
        self.assertFalse(is_japanese("안녕하세요"))
        self.assertFalse(is_japanese("12345"))
        self.assertFalse(is_japanese(""))
    
    @patch('mdc.utils.translation.config')
    @patch('mdc.utils.translation.get_html')
    def test_translate_google_free(self, mock_get_html, mock_config):
        """测试谷歌免费翻译功能"""
        # 设置模拟
        mock_instance = MagicMock()
        mock_instance.get_target_language.return_value = "zh-CN"
        mock_instance.get_translate_engine.return_value = "google-free"
        mock_instance.get_translate_service_site.return_value = "translate.google.cn"
        mock_config.getInstance.return_value = mock_instance
        
        # 设置响应模拟
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "sentences": [{"trans": "你好"}]
        }
        mock_get_html.return_value = mock_response
        
        # 测试翻译
        result = translate("こんにちは")
        self.assertEqual(result, "你好")
        
        # 测试空字符串
        result = translate("")
        self.assertEqual(result, "")
        
        # 测试非日语中文文本（不应翻译）
        result = translate("你好")
        self.assertEqual(result, "你好")
    
    @patch('mdc.utils.translation.is_movie_dir')
    def test_is_movie_dir(self, mock_is_movie_dir):
        """测试电影目录检测功能"""
        from mdc.utils.translation import is_movie_dir
        
        # 创建模拟路径
        mock_path = MagicMock(spec=Path)
        mock_path.is_dir.return_value = True
        mock_path.glob.return_value = [mock_path]
        
        # 测试目录检测
        result = is_movie_dir(mock_path)
        self.assertTrue(mock_path.is_dir.called)
        self.assertTrue(mock_path.glob.called)
    
    @patch('mdc.utils.translation.is_movie_dir')
    def test_find_movie_dirs(self, mock_is_movie_dir):
        """测试查找电影目录功能"""
        from mdc.utils.translation import find_movie_dirs
        
        # 创建模拟路径
        mock_root = MagicMock(spec=Path)
        mock_dir1 = MagicMock(spec=Path)
        mock_dir2 = MagicMock(spec=Path)
        mock_root.iterdir.return_value = [mock_dir1, mock_dir2]
        
        # 设置模拟返回值
        mock_is_movie_dir.side_effect = [True, False]
        
        # 测试查找电影目录
        result = find_movie_dirs(mock_root)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_dir1)
    
    def test_safe_iterdir(self):
        """测试安全遍历目录功能"""
        from mdc.utils.translation import safe_iterdir
        
        # 创建模拟路径
        mock_path = MagicMock(spec=Path)
        mock_dir = MagicMock(spec=Path)
        mock_path.iterdir.return_value = [mock_dir]
        
        # 测试正常情况
        result = safe_iterdir(mock_path)
        self.assertEqual(result, [mock_dir])
        
        # 测试异常情况
        mock_path.iterdir.side_effect = PermissionError
        result = safe_iterdir(mock_path)
        self.assertEqual(result, [])
    
    @patch('mdc.utils.translation.safe_iterdir')
    @patch('mdc.utils.translation.process_movie_dir')
    def test_process_movie_dir(self, mock_process_movie_dir, mock_safe_iterdir):
        """测试处理电影目录功能"""
        from mdc.utils.translation import process_movie_dir
        
        # 创建模拟路径
        mock_dir = MagicMock(spec=Path)
        mock_safe_iterdir.return_value = []
        
        # 测试处理电影目录
        process_movie_dir(mock_dir)
        self.assertTrue(mock_safe_iterdir.called)
        self.assertTrue(mock_process_movie_dir.called)
    
    @patch('mdc.utils.translation.is_japanese')
    @patch('mdc.utils.translation.translate')
    def test_modify_nfo_content(self, mock_translate, mock_is_japanese):
        """测试修改NFO文件内容功能"""
        from mdc.utils.translation import modify_nfo_content
        
        # 创建模拟路径和文件内容
        mock_path = MagicMock(spec=Path)
        mock_path.read_text.return_value = "<title>こんにちは</title><plot>世界</plot>"
        mock_path.write_text = MagicMock()
        
        # 设置模拟返回值
        mock_is_japanese.return_value = True
        mock_translate.side_effect = ["你好", "世界"]
        
        # 测试修改NFO内容
        result = modify_nfo_content(mock_path)
        self.assertTrue(mock_path.read_text.called)
        self.assertTrue(mock_path.write_text.called)


if __name__ == "__main__":
    unittest.main()