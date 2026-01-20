import unittest
from unittest.mock import patch, MagicMock
from mdc.image.imgproc import face_crop_width, face_crop_height, face_center


class TestImgProc(unittest.TestCase):
    """测试图片处理功能"""
    
    @patch('mdc.image.imgproc.config')
    @patch('mdc.image.imgproc.face_center')
    def test_face_crop_width(self, mock_face_center, mock_config):
        """测试人脸宽度裁剪功能"""
        # 设置模拟配置
        mock_instance = MagicMock()
        mock_instance.face_aspect_ratio.return_value = 2  # 宽高比为2:1
        mock_config.getInstance.return_value = mock_instance
        
        # 测试找到人脸的情况
        mock_face_center.return_value = (100, 50)  # (center, top)
        
        # 图片尺寸：300x200
        result = face_crop_width("test.jpg", 300, 200)
        
        # 计算预期结果：cropWidthHalf = 200 / 3 ≈ 66.67，实际使用整数除法得到66
        # 所以裁剪宽度为66 * 2 = 132
        self.assertEqual(result, (100 - 66, 0, 100 + 66, 200))  # (34, 0, 166, 200)
        
        # 测试未找到人脸的情况
        mock_face_center.side_effect = Exception("Face not found")
        
        result = face_crop_width("test.jpg", 300, 200)
        
        # 默认靠右切：width - cropWidthHalf * aspect_ratio = 300 - 66 * 2 = 168
        self.assertEqual(result, (168, 0, 300, 200))
    
    @patch('mdc.image.imgproc.config')
    @patch('mdc.image.imgproc.face_center')
    def test_face_crop_height(self, mock_face_center, mock_config):
        """测试人脸高度裁剪功能"""
        # 设置模拟配置
        mock_instance = MagicMock()
        mock_instance.face_aspect_ratio.return_value = 2/3  # 宽高比为2:3
        mock_config.getInstance.return_value = mock_instance
        
        # 测试找到人脸的情况
        mock_face_center.return_value = (100, 50)  # (center, top)
        
        # 图片尺寸：200x300
        result = face_crop_height("test.jpg", 200, 300)
        
        # 计算预期结果：cropHeight = 200 * 3 / 2 = 300
        # 从顶部开始裁剪，高度为300
        self.assertEqual(result, (0, 50, 200, 50 + 300))  # (0, 50, 200, 350)
        
        # 测试边界情况：裁剪高度超过图片高度
        mock_face_center.return_value = (100, 100)  # (center, top)
        result = face_crop_height("test.jpg", 200, 300)
        
        # 当裁剪底部超过图片高度时，默认从顶部开始裁剪
        self.assertEqual(result, (0, 0, 200, 300))
        
        # 测试未找到人脸的情况
        mock_face_center.side_effect = Exception("Face not found")
        
        result = face_crop_height("test.jpg", 200, 300)
        
        # 默认从顶部向下切割
        self.assertEqual(result, (0, 0, 200, 300))
    
    @patch('mdc.image.imgproc.importlib')
    def test_face_center(self, mock_importlib):
        """测试人脸中心检测功能"""
        # 设置模拟模块
        mock_module = MagicMock()
        mock_module.face_center.return_value = (100, 50)
        mock_importlib.import_module.return_value = mock_module
        
        # 测试正常情况
        result = face_center("test.jpg", "hog")
        self.assertEqual(result, (100, 50))
        
        # 测试模块导入失败的情况
        mock_importlib.import_module.side_effect = Exception("Module not found")
        
        result = face_center("test.jpg", "hog")
        self.assertEqual(result, (0, 0))  # 失败时返回默认值
    
    @patch('mdc.image.imgproc.config')
    @patch('mdc.image.imgproc.os')
    @patch('mdc.image.imgproc.Image')
    @patch('mdc.image.imgproc.cv2')
    @patch('mdc.image.imgproc.face_crop_width')
    @patch('mdc.image.imgproc.face_crop_height')
    def test_cutImage(self, mock_face_crop_height, mock_face_crop_width, mock_cv2, mock_Image, mock_os, mock_config):
        """测试图片裁剪功能"""
        from mdc.image.imgproc import cutImage
        
        # 设置模拟配置
        mock_instance = MagicMock()
        mock_instance.image_naming_with_number.return_value = False
        mock_instance.face_uncensored_only.return_value = False
        mock_instance.face_aways_imagecut.return_value = False
        mock_instance.face_locations_model.return_value = "hog"
        mock_config.getInstance.return_value = mock_instance
        
        # 设置模拟路径
        mock_path = "test.jpg"
        mock_thumb_path = "thumb.jpg"
        mock_poster_path = "poster.jpg"
        
        # 设置模拟返回值
        mock_cv2.imread.return_value = MagicMock()
        mock_cv2.resize.return_value = MagicMock()
        mock_cv2.cvtColor.return_value = MagicMock()
        mock_Image.open.return_value = MagicMock()
        mock_face_crop_width.return_value = (0, 0, 100, 100)
        mock_face_crop_height.return_value = (0, 0, 100, 100)
        
        # 测试正常情况
        result = cutImage(True, mock_path, mock_thumb_path, mock_poster_path)
        self.assertTrue(mock_cv2.imread.called)
        self.assertTrue(mock_cv2.resize.called)
        self.assertTrue(mock_Image.open.called)
        self.assertTrue(mock_face_crop_width.called)
        self.assertTrue(mock_face_crop_height.called)
        
        # 测试跳过人脸检测的情况
        result = cutImage(True, mock_path, mock_thumb_path, mock_poster_path, skip_facerec=True)
        self.assertTrue(mock_cv2.imread.called)


if __name__ == "__main__":
    unittest.main()