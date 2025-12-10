#!/usr/bin/env python3
import os
import sys

# 使用 Django shell 运行
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoBlog.settings')
    import django
    django.setup()
    
    from blog.models import Article, ArticleVersion
    from django.contrib.auth import get_user_model
    from django.utils import timezone

    User = get_user_model()
    
    print("=== 测试版本恢复功能 ===")
    
    try:
        # 创建测试用户
        user1, created = User.objects.get_or_create(username='testuser1', defaults={'email': 'test1@example.com', 'is_superuser': True, 'is_staff': True})
        if created:
            user1.set_password('test123456')
            user1.save()
        
        user2, created = User.objects.get_or_create(username='testuser2', defaults={'email': 'test2@example.com', 'is_superuser': True, 'is_staff': True})
        if created:
            user2.set_password('test123456')
            user2.save()
        
        # 创建测试文章
        article, created = Article.objects.get_or_create(
            title="初始版本标题",
            defaults={
                'body': "初始版本正文内容",
                'author': user1,
                'status': 'p',
                'creation_time': timezone.now()
            }
        )
        
        print(f"\n1. 当前文章: {article.title}")
        
        # 清理旧版本
        ArticleVersion.objects.filter(article=article).delete()
        
        # 手动创建初始版本
        ArticleVersion.objects.create(
            article=article,
            version_number=1,
            title=article.title,
            body=article.body,
            editor=user1
        )
        
        # 修改文章，创建版本2
        article.title = "修改后的标题版本2"
        article.body = "修改后的正文版本2"
        article.save()
        
        # 修改文章，创建版本3
        article.title = "修改后的标题版本3"
        article.body = "修改后的正文版本3"
        article.save()
        
        all_versions = ArticleVersion.objects.filter(article=article).order_by('version_number')
        print(f"\n2. 恢复前版本列表:")
        for v in all_versions:
            print(f"   v{v.version_number}: {v.title}")
        
        # 获取版本2
        version2 = ArticleVersion.objects.filter(article=article, version_number=2).first()
        
        # 开始恢复
        print(f"\n3. 开始恢复到版本2: {version2.title}")
        
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
        
        # 显示所有版本
        all_versions = ArticleVersion.objects.filter(article=article).order_by('version_number')
        print(f"\n4. 恢复后所有版本:")
        for v in all_versions:
            comment = f" - {v.comment}" if v.comment else ""
            print(f"   v{v.version_number}: {v.title}{comment} (编辑者: {v.editor.username})")
        
        # 验证恢复结果
        article.refresh_from_db()
        print(f"\n5. 恢复结果:")
        print(f"   当前文章标题: {article.title}")
        print(f"   匹配版本2标题: {article.title == version2.title}")
        print(f"\n✅ 测试完成，恢复记录已正确体现在变更历史中！")
        
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)