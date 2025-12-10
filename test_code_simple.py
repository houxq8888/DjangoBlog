from blog.models import Article, ArticleVersion, Category
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

print("=== 测试版本恢复功能 ===")

# 创建测试用户
user1, created = User.objects.get_or_create(username='testuser1', defaults={'email': 'test1@example.com', 'is_superuser': True, 'is_staff': True})
if created:
    user1.set_password('test123456')
    user1.save()

# 创建测试分类
category, created = Category.objects.get_or_create(name='测试分类', slug='test-category')

# 删除旧的测试文章
Article.objects.filter(title__contains="初始版本标题").delete()

# 创建测试文章
article = Article.objects.create(
    title="初始版本标题",
    body="初始版本正文内容",
    author=user1,
    category=category,
    status='p',
    creation_time=timezone.now()
)

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

# 查看当前版本
all_versions = ArticleVersion.objects.filter(article=article).order_by('version_number')
print("\n=== 恢复前版本 ===")
for v in all_versions:
    print(f"v{v.version_number}: {v.title}")

# 恢复到版本2
version2 = ArticleVersion.objects.filter(article=article, version_number=2).first()
print(f"\n=== 开始恢复到版本2 ===")

# 保存恢复前版本
ArticleVersion.objects.create(
    article=article,
    title=article.title,
    body=article.body,
    editor=user1,
    comment="恢复前的版本"
)

# 恢复内容
article.title = version2.title
article.body = version2.body
article.save(create_version=True)

# 更新恢复说明
latest_version = ArticleVersion.objects.filter(article=article).order_by('-version_number').first()
latest_version.comment = f"从版本 {version2.version_number} 恢复"
latest_version.save()

# 查看恢复后版本
all_versions = ArticleVersion.objects.filter(article=article).order_by('version_number')
print("\n=== 恢复后所有版本 ===")
for v in all_versions:
    comment = f" ({v.comment})" if v.comment else ""
    print(f"v{v.version_number}: {v.title}{comment}")

# 验证结果
article.refresh_from_db()
print(f"\n=== 恢复结果 ===")
print(f"当前标题: {article.title}")
print(f"版本2标题: {version2.title}")
print(f"恢复成功: {article.title == version2.title}")

print("\n✅ 测试完成！")