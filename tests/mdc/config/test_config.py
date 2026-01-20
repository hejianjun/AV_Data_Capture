import unittest
from mdc.config.config import Config, getInstance


class TestConfig(unittest.TestCase):
    """测试Config类的功能"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.config = Config()
    
    def test_singleton_instance(self):
        """测试单例模式是否正常工作"""
        instance1 = getInstance()
        instance2 = getInstance()
        self.assertEqual(instance1, instance2)
    
    def test_config_methods(self):
        """测试Config类的主要方法"""
        mfilter = {"conf", "proxy", "_exit", "_default_config", "ini_path", "set_override"}
        
        # 测试所有公共方法是否可调用
        for _m in [m for m in dir(self.config) if not m.startswith("__") and m not in mfilter]:
            method = getattr(self.config, _m)
            if callable(method):
                # 确保方法可以被调用
                try:
                    method()
                except Exception as e:
                    self.fail(f"Config.{_m}() 调用失败: {e}")
    
    def test_proxy_methods(self):
        """测试Proxy类的主要方法"""
        pfilter = {"proxies", "SUPPORT_PROXY_TYPE"}
        
        # 测试所有公共属性和方法是否可访问
        for _p in [
            p for p in dir(getInstance().proxy())
            if not p.startswith("__") and p not in pfilter
        ]:
            attr = getattr(getInstance().proxy(), _p)
            # 无论属性是方法还是普通属性，都应该可以访问
            _ = attr
    
    def test_override_config(self):
        """测试配置覆盖功能"""
        # 创建一个新的Config实例
        conf2 = Config()
        # 应用配置覆盖，使用正确的语法
        conf2.set_override("face:aspect_ratio=2;face:aways_imagecut=0;priority:website=javdb")
        
        # 验证覆盖是否生效
        self.assertEqual(conf2.face_aspect_ratio(), 2)
        self.assertEqual(conf2.face_aways_imagecut(), False)
        self.assertEqual(conf2.sources(), "javdb")
    
    def test_new_instance(self):
        """测试创建新实例的功能"""
        # 创建新实例应该与单例不同
        conf2 = Config()
        instance = getInstance()
        self.assertNotEqual(instance, conf2)


if __name__ == "__main__":
    unittest.main()