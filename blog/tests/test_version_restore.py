from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from blog.models import Article, ArticleVersion

User = get_user_model()

class VersionRestoreTest(TestCase):
    def setUp(self):
        # 创建测试用户
        self.user1 = User.objects.create_superuser(
            username='testuser1', email='test1@example.com', password='test123456'
        )
        self.user2 = User.objects.create_superuser(
            username='testuser2', email='test2@example.com', password='test123456'
        )
        
        # 创建测试文章
        self.article = Article.objects.create(
            title="初始版本标题",
            body="初始版本正文内容",
            author=self.user1,
            status='p',
            creation_time=timezone.now()
        )

    def test_version_restore_functionality(self):
        """测试版本恢复功能是否正确生成变更记录"""
        # 验证初始版本
        initial_versions = ArticleVersion.objects.filter(article=self.article).count()
        self.assertEqual(initial_versions, 1)
        
        # 修改文章，创建版本2
        self.article.title = "修改后的标题版本2"
        self.article.body = "修改后的正文版本2"
        self.article.save()
        
        version2 = ArticleVersion.objects.filter(article=self.article, version_number=2).first()
        self.assertIsNotNone(version2)
        self.assertEqual(version2.title, "修改后的标题版本2")
        
        # 再次修改文章，创建版本3
        self.article.title = "修改后的标题版本3"
        self.article.body = "修改后的正文版本3"
        self.article.save()
        
        version3 = ArticleVersion.objects.filter(article=self.article, version_number=3).first()
        self.assertIsNotNone(version3)
        self.assertEqual(version3.title, "修改后的标题版本3")
        
        # 模拟视图中的恢复逻辑
        # 先保存恢复前的版本
        ArticleVersion.objects.create(
            article=self.article,
            title=self.article.title,
            body=self.article.body,
            editor=self.user2,
            comment="恢复前的版本"
        )
        
        # 恢复到版本2
        self.article.title = version2.title
        self.article.body = version2.body
        self.article.author = version2.editor
        self.article.save(create_version=True)
        
        # 添加恢复说明
        latest_version = ArticleVersion.objects.filter(article=self.article).order_by('-version_number').first()
        latest_version.comment = f"从版本 {version2.version_number} 恢复"
        latest_version.save()
        
        # 验证版本数量
        all_versions = ArticleVersion.objects.filter(article=self.article).order_by('version_number')
        self.assertEqual(all_versions.count(), 5)  # v1, v2, v3, v4(恢复前), v5(恢复后)
        
        # 检查恢复记录
        restore_versions = ArticleVersion.objects.filter(article=self.article, comment__contains="恢复")
        self.assertEqual(restore_versions.count(), 2)
        
        # 验证恢复结果
        restored_article = Article.objects.get(id=self.article.id)
        self.assertEqual(restored_article.title, version2.title)
        self.assertEqual(restored_article.body, version2.body)
        
        print("✅ 版本恢复功能测试通过")
        print(f"   总版本数: {all_versions.count()}")
        for v in all_versions:
            comment = f" - {v.comment}" if v.comment else ""
            print(f"   v{v.version_number}: {v.title}{comment}")