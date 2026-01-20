import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from mdc.utils.actor_mapping import (
    load_mapping, get_actor_mapping, get_info_mapping,
    process_text_mappings, process_text_mapping, process_special_actor_name
)


class TestActorMapping(unittest.TestCase):
    """测试演员映射功能"""
    
    @patch('mdc.utils.actor_mapping.etree')
    @patch('mdc.utils.actor_mapping.Path')
    def test_load_mapping(self, mock_path, mock_etree):
        """测试映射加载功能"""
        # 设置模拟路径
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance
        
        # 设置模拟XML解析
        mock_item1 = MagicMock()
        mock_item1.get.side_effect = lambda x: {
            'zh_cn': '演员A',
            'keyword': 'actor1,act1',
            'jp': 'アクターA',
            'zh_tw': '演員A'
        }[x]
        
        mock_item2 = MagicMock()
        mock_item2.get.side_effect = lambda x: {
            'zh_cn': '演员B',
            'keyword': None,
            'jp': 'アクターB',
            'zh_tw': '演員B'
        }[x]
        
        mock_root = MagicMock()
        mock_root.xpath.return_value = [mock_item1, mock_item2]
        mock_etree.parse.return_value = mock_root
        
        # 测试加载中文映射
        mapping = load_mapping(1, "test_mapping.xml")
        
        # 验证映射是否正确建立
        self.assertEqual(mapping['actor1'], '演员A')
        self.assertEqual(mapping['act1'], '演员A')
        self.assertEqual(mapping['アクターa'], '演员A')
        self.assertEqual(mapping['演員a'], '演员A')
        self.assertEqual(mapping['演员a'], '演员A')
        self.assertEqual(mapping['アクターb'], '演员B')
        self.assertEqual(mapping['演員b'], '演员B')
        self.assertEqual(mapping['演员b'], '演员B')
    
    @patch('mdc.utils.actor_mapping.load_mapping')
    def test_get_actor_mapping(self, mock_load_mapping):
        """测试获取演员映射"""
        mock_mapping = {'test': '测试'}
        mock_load_mapping.return_value = mock_mapping
        
        # 第一次调用应该加载映射
        mapping1 = get_actor_mapping(1)
        mock_load_mapping.assert_called_once()
        self.assertEqual(mapping1, mock_mapping)
        
        # 第二次调用应该使用缓存
        mapping2 = get_actor_mapping(1)
        self.assertEqual(mapping2, mock_mapping)
        self.assertEqual(mock_load_mapping.call_count, 1)  # 确保只调用了一次
    
    @patch('mdc.utils.actor_mapping.load_mapping')
    def test_get_info_mapping(self, mock_load_mapping):
        """测试获取信息映射"""
        mock_mapping = {'tag1': '标签1'}
        mock_load_mapping.return_value = mock_mapping
        
        # 第一次调用应该加载映射
        mapping1 = get_info_mapping(1)
        mock_load_mapping.assert_called_once()
        self.assertEqual(mapping1, mock_mapping)
        
        # 第二次调用应该使用缓存
        mapping2 = get_info_mapping(1)
        self.assertEqual(mapping2, mock_mapping)
        self.assertEqual(mock_load_mapping.call_count, 1)  # 确保只调用了一次
    
    def test_process_text_mapping(self):
        """测试文本映射处理"""
        mapping = {
            'test': '测试',
            'delete': '删除'
        }
        
        # 测试正常映射
        result, should_delete = process_text_mapping('test', mapping)
        self.assertEqual(result, '测试')
        self.assertFalse(should_delete)
        
        # 测试删除映射
        result, should_delete = process_text_mapping('delete', mapping)
        self.assertIsNone(result)
        self.assertTrue(should_delete)
        
        # 测试不存在的映射
        result, should_delete = process_text_mapping('not_found', mapping)
        self.assertEqual(result, 'not_found')
        self.assertFalse(should_delete)
    
    def test_process_text_mappings(self):
        """测试文本映射批量处理"""
        mapping = {
            'test1': '测试1',
            'test2': '测试2',
            'delete': '删除'
        }
        
        # 测试字符串处理
        result = process_text_mappings('test1', mapping)
        self.assertEqual(result, '测试1')
        
        # 测试列表处理
        result = process_text_mappings(['test1', 'test2', 'delete', 'not_found'], mapping)
        self.assertEqual(result, ['测试1', '测试2', 'not_found'])
        
        # 测试其他类型（应原样返回）
        result = process_text_mappings(123, mapping)
        self.assertEqual(result, 123)
    
    def test_process_special_actor_name(self):
        """测试特殊演员名称处理"""
        mapping = {
            'actor1': '演员A',
            'actor2': '演员B',
            'alias': '别名演员'
        }
        
        # 测试普通名称
        result = process_special_actor_name('actor1', mapping)
        self.assertEqual(result, '演员A')
        
        # 测试带括号的名称（全角）
        result = process_special_actor_name('actor1（别名）', mapping)
        self.assertEqual(result, '演员A（别名）')
        
        # 测试带括号的名称（半角）
        result = process_special_actor_name('actor1(alias)', mapping)
        self.assertEqual(result, '演员A(alias)')
        
        # 测试带多个别名的名称
        result = process_special_actor_name('actor1（alias1、alias2）', mapping)
        self.assertEqual(result, '演员A（alias1、alias2）')
        
        # 测试不存在的名称
        result = process_special_actor_name('unknown', mapping)
        self.assertEqual(result, 'unknown')


if __name__ == "__main__":
    unittest.main()