from mdc.utils.number_parser import get_number, get_number_by_dict, is_uncensored, G_TAKE_NUM_RULES


class TestNumberParser:
    """测试番号解析功能"""
    
    def test_get_number(self):
        """测试番号提取功能"""
        test_cases = [
            # (输入文件名, 预期输出)
            ("MEYD-594-C.mp4", "MEYD-594"),
            ("SSIS-001_C.mp4", "SSIS-001"),
            ("SSIS100-C.mp4", "SSIS100"),
            ("ssni984.mp4", "SSNI984"),
            ("SDDE-625_uncensored_C.mp4", "SDDE-625"),
            ("Tokyo Hot n9001 FHD.mp4", "N9001"),
            ("caribean-020317_001.nfo", "20317-001"),
            ("ADV-R0624-CD3.wmv", "ADV-R0624"),
            ("XXX-AV   22061-CD5.iso", "XXX-AV-22061"),
            ("rctd-460ch.mp4", "RCTD-460"),
            ("MD-123.ts", "MD-123"),
        ]
        
        for input_file, expected in test_cases:
            result = get_number(False, input_file)
            assert result == expected, f"测试失败: 输入={input_file}, 预期={expected}, 实际={result}"
    
    def test_get_number_special_cases(self):
        """测试特殊情况的番号提取"""
        # 测试空字符串
        result = get_number(False, "")
        assert result is None
        
        # 测试没有扩展名的文件名
        result = get_number(False, "SSNI-829")
        assert result == "SSNI-829"
        
        # 测试带路径的文件名
        result = get_number(False, "/path/to/SSNI-829.mp4")
        assert result == "SSNI-829"
        
        # 测试Windows路径
        result = get_number(False, "C:\path\to\SSNI-829.mp4")
        assert result == "SSNI-829"
    
    def test_get_number_by_dict(self):
        """测试按数据源规则提取番号"""
        test_cases = [
            ("Tokyo Hot n9001 FHD.mp4", "n9001"),
            ("TokyoHot-n1287-HD SP2006 .mp4", "n1287"),
            ("caribean-020317_001.nfo", "020317-001"),
            ("1pon-010121_001.mp4", "010121_001"),
            ("10mu-230101_01.mp4", "230101_01"),
            ("x-art.23.01.01.mp4", "x-art.23.01.01"),
            ("heyzo-1234.mp4", "HEYZO-1234"),
        ]
        
        for input_file, expected in test_cases:
            result = get_number_by_dict(input_file)
            assert result == expected, f"测试失败: 输入={input_file}, 预期={expected}, 实际={result}"
    
    def test_is_uncensored(self):
        """测试判断是否为无码功能"""
        uncensored_cases = [
            "1234-567",
            "123456_789",
            "CZ1234",
            "GEDO1234",
            "K1234",
            "N1234",
            "RED-1234",
            "SE1234",
            "HEYZO-1234",
            "XXX-AV-1234",
            "heydouga-1234-567",
            "x-art.23.01.01",
        ]
        
        for number in uncensored_cases:
            assert is_uncensored(number), f"{number} 应被识别为无码"
        
        # 测试有码情况
        censored_cases = [
            "SSNI-829",
            "MEYD-594",
            "SDDE-625",
        ]
        
        for number in censored_cases:
            assert not is_uncensored(number), f"{number} 应被识别为有码"
    
    def test_take_number_rules(self):
        """测试提取番号的规则集"""
        assert "tokyo.*hot" in G_TAKE_NUM_RULES
        assert "carib" in G_TAKE_NUM_RULES
        assert "1pon|mura|paco" in G_TAKE_NUM_RULES
        assert "10mu" in G_TAKE_NUM_RULES
        assert "x-art" in G_TAKE_NUM_RULES
        assert "xxx-av" in G_TAKE_NUM_RULES
        assert "heydouga" in G_TAKE_NUM_RULES
        assert "heyzo" in G_TAKE_NUM_RULES