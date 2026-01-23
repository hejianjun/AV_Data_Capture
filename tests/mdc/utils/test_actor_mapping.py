from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from mdc.utils.actor_mapping import (
    load_mapping, get_actor_mapping, get_info_mapping,
    process_text_mappings, process_text_mapping, process_special_actor_name
)


class TestActorMapping:
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
        assert mapping['actor1'] == '演员A'
        assert mapping['act1'] == '演员A'
        assert mapping['アクターa'] == '演员A'
        assert mapping['演員a'] == '演员A'
        assert mapping['演员a'] == '演员A'
        assert mapping['アクターb'] == '演员B'
        assert mapping['演員b'] == '演员B'
        assert mapping['演员b'] == '演员B'
    
    @patch('mdc.utils.actor_mapping.load_mapping')
    def test_get_actor_mapping(self, mock_load_mapping):
        """测试获取演员映射"""
        mock_mapping = {'test': '测试'}
        mock_load_mapping.return_value = mock_mapping
        
        # 第一次调用应该加载映射
        mapping1 = get_actor_mapping(1)
        mock_load_mapping.assert_called_once()
        assert mapping1 == mock_mapping
        
        # 第二次调用应该使用缓存
        mapping2 = get_actor_mapping(1)
        assert mapping2 == mock_mapping
        assert mock_load_mapping.call_count == 1  # 确保只调用了一次
    
    @patch('mdc.utils.actor_mapping.load_mapping')
    def test_get_info_mapping(self, mock_load_mapping):
        """测试获取信息映射"""
        mock_mapping = {'tag1': '标签1'}
        mock_load_mapping.return_value = mock_mapping
        
        # 第一次调用应该加载映射
        mapping1 = get_info_mapping(1)
        mock_load_mapping.assert_called_once()
        assert mapping1 == mock_mapping
        
        # 第二次调用应该使用缓存
        mapping2 = get_info_mapping(1)
        assert mapping2 == mock_mapping
        assert mock_load_mapping.call_count == 1  # 确保只调用了一次
    
    def test_process_text_mapping(self):
        """测试文本映射处理"""
        mapping = {
            'test': '测试',
            'delete': '删除'
        }
        
        # 测试正常映射
        result, should_delete = process_text_mapping('test', mapping)
        assert result == '测试'
        assert not should_delete
        
        # 测试删除映射
        result, should_delete = process_text_mapping('delete', mapping)
        assert result is None
        assert should_delete
        
        # 测试不存在的映射
        result, should_delete = process_text_mapping('not_found', mapping)
        assert result == 'not_found'
        assert not should_delete
    
    def test_process_text_mappings(self):
        """测试文本映射批量处理"""
        mapping = {
            'test1': '测试1',
            'test2': '测试2',
            'delete': '删除'
        }
        
        # 测试字符串处理
        result = process_text_mappings('test1', mapping)
        assert result == '测试1'
        
        # 测试列表处理
        result = process_text_mappings(['test1', 'test2', 'delete', 'not_found'], mapping)
        assert result == ['测试1', '测试2', 'not_found']
        
        # 测试其他类型（应原样返回）
        result = process_text_mappings(123, mapping)
        assert result == 123
    
    def test_process_special_actor_name(self):
        """测试特殊演员名称处理"""
        mapping = {
            'actor1': '演员A',
            'actor2': '演员A',
            'alias': '演员A'
        }
        
        # 测试普通名称
        result = process_special_actor_name('actor1', mapping)
        assert result == '演员A'
        
        # 测试带括号的名称（全角）
        result = process_special_actor_name('actor1（别名）', mapping)
        assert result == '演员A(别名)'
        
        # 测试带括号的名称（半角）
        result = process_special_actor_name('actor1(alias)', mapping)
        assert result == '演员A'
        
        # 测试带多个别名的名称
        result = process_special_actor_name('actor1（alias1、alias2）', mapping)
        assert result == '演员A(alias1,alias2)'
        
        # 测试不存在的名称
        result = process_special_actor_name('unknown', mapping)
        assert result == 'unknown'
    
    
    @patch('mdc.utils.actor_mapping.process_movie_dir')
    def test_migrate_files(self, mock_process_movie_dir):
        """测试迁移文件功能"""
        from mdc.utils.actor_mapping import migrate_files
        
        # 创建模拟路径
        mock_src_dir = MagicMock(spec=Path)
        mock_new_actor_dir = "新演员目录"
        mock_reason = "迁移原因"
        
        # 测试迁移文件
        migrate_files(mock_src_dir, mock_new_actor_dir, mock_reason)
        assert mock_src_dir.called
    
    @patch('mdc.utils.actor_mapping.safe_iterdir')
    @patch('mdc.utils.actor_mapping.modify_nfo_content')
    def test_process_movie_dir(self, mock_modify_nfo_content, mock_safe_iterdir):
        """测试处理电影目录功能"""
        from mdc.utils.actor_mapping import process_movie_dir
        
        # 创建模拟路径
        mock_dir = MagicMock(spec=Path)
        mock_nfo_file = MagicMock(spec=Path)
        mock_nfo_file.exists.return_value = True
        mock_nfo_file.suffix.return_value = '.nfo'
        mock_safe_iterdir.return_value = [mock_nfo_file]
        
        # 测试处理电影目录
        process_movie_dir(mock_dir)
        assert mock_safe_iterdir.called
        assert mock_modify_nfo_content.called
    
    def test_is_movie_dir(self):
        """测试电影目录检测功能"""
        from mdc.utils.actor_mapping import is_movie_dir
        
        # 创建模拟路径
        mock_path = MagicMock(spec=Path)
        mock_path.is_dir.return_value = True
        mock_file = MagicMock(spec=Path)
        mock_file.suffix = '.nfo'
        mock_path.glob.return_value = [mock_file]
        
        # 测试目录检测
        result = is_movie_dir(mock_path)
        assert mock_path.is_dir.called
        assert mock_path.glob.called
        assert result
    
    @patch('mdc.utils.actor_mapping.is_movie_dir')
    def test_find_movie_dirs(self, mock_is_movie_dir):
        """测试查找电影目录功能"""
        from mdc.utils.actor_mapping import find_movie_dirs
        
        # 创建模拟路径
        mock_root = MagicMock(spec=Path)
        mock_dir1 = MagicMock(spec=Path)
        mock_dir2 = MagicMock(spec=Path)
        mock_root.iterdir.return_value = [mock_dir1, mock_dir2]
        
        # 设置模拟返回值
        mock_is_movie_dir.side_effect = [True, False]
        
        # 测试查找电影目录
        result = find_movie_dirs(mock_root)
        assert len(result) == 1
        assert result[0] == mock_dir1
    
    def test_safe_iterdir(self):
        """测试安全遍历目录功能"""
        from mdc.utils.actor_mapping import safe_iterdir
        
        # 创建模拟路径
        mock_path = MagicMock(spec=Path)
        mock_file = MagicMock(spec=Path)
        mock_dir = MagicMock(spec=Path)
        mock_path.iterdir.return_value = [mock_file, mock_dir]
        
        # 测试正常情况
        result = safe_iterdir(mock_path)
        assert result == [mock_file, mock_dir]
        
        # 测试异常情况
        mock_path.iterdir.side_effect = PermissionError
        result = safe_iterdir(mock_path)
        assert result == []