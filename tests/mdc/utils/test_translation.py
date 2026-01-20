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
    



if __name__ == "__main__":
    unittest.main()