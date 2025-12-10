#!/usr/bin/env python3
import os
import sys
# 将当前目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoBlog.settings')

import django
django.setup()

from blog.models import Article, ArticleVersion
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def test_version_restore():
    print("=== 测试版本恢复功能 ===")
    
    # 创建测试用户
    user1 = User.objects.create_superuser(username='testuser1', email='test1@example.com', password='test123456')
    user2 = User.objects.create_superuser(username='testuser2', email='test2@example.com', password='test123456')
    
    # 创建测试文章
    article = Article.objects.create(
        title="初始版本标题",
        body="初始版本正文内容",
        author=user1,
        status='p',
        creation_time=timezone.now()
    )
    
    print(f"\n1. 创建初始文章成功: {article.title}")
    initial_versions = ArticleVersion.objects.filter(article=article).count()
    print(f"   初始版本数量: {initial_versions}")
    
    # 修改文章，创建版本2
    article.title = "修改后的标题版本2"
    article.body = "修改后的正文版本2"
    article.save()
    
    version2 = ArticleVersion.objects.filter(article=article, version_number=2).first()
    print(f"\n2. 创建版本2成功: v{version2.version_number} - {version2.title}")
    
    # 再次修改文章，创建版本3
    article.title = "修改后的标题版本3"
    article.body = "修改后的正文版本3"
    article.save()
    
    version3 = ArticleVersion.objects.filter(article=article, version_number=3).first()
    print(f"\n3. 创建版本3成功: v{version3.version_number} - {version3.title}")
    
    # 测试恢复到版本2
    print(f"\n4. 开始恢复到版本2")
    
    # 模拟视图中的恢复逻辑
    # 先保存恢复前的版本
    ArticleVersion.objects.create(
        article=article,
        title=article.title,
        body=article.body,
        editor=user2,
        comment="恢复前的版本"
    )
    
    # 恢复到版本2
    article.title = version2.title
    article.body = version2.body
    article.author = version2.editor
    article.save(create_version=True)
    
    # 添加恢复说明
    latest_version = ArticleVersion.objects.filter(article=article).order_by('-version_number').first()
    latest_version.comment = f"从版本 {version2.version_number} 恢复"
    latest_version.save()
    
    # 检查所有版本
    all_versions = ArticleVersion.objects.filter(article=article).order_by('version_number')
    print(f"\n5. 恢复完成后所有版本:")
    for v in all_versions:
        comment = f" - {v.comment}" if v.comment else ""
        print(f"   v{v.version_number}: {v.title}{comment} (编辑者: {v.editor.username})")
    
    # 验证恢复结果
    restored_article = Article.objects.get(id=article.id)
    print(f"\n6. 恢复结果验证:")
    print(f"   当前文章标题: {restored_article.title}")
    print(f"   版本2标题: {version2.title}")
    print(f"   标题匹配: {restored_article.title == version2.title}")
    print(f"   当前文章正文: {restored_article.body[:30]}...")
    print(f"   版本2正文: {version2.body[:30]}...")
    print(f"   正文匹配: {restored_article.body == version2.body}")
    
    # 检查恢复记录
    restore_versions = ArticleVersion.objects.filter(article=article, comment__contains="恢复")
    print(f"\n7. 恢复记录数量: {restore_versions.count()}")
    for v in restore_versions:
        print(f"   {v.comment} (v{v.version_number})")
    
    print("\n=== 测试完成 ===")
    return True

if __name__ == "__main__":
    try:
        test_version_restore()
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)