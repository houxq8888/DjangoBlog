import difflib
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _

# Register your models here.
from .models import Article, Category, Tag, Links, SideBar, BlogSettings, ArticleVersion


class ArticleForm(forms.ModelForm):
    # body = forms.CharField(widget=AdminPagedownWidget())

    class Meta:
        model = Article
        fields = '__all__'


def makr_article_publish(modeladmin, request, queryset):
    queryset.update(status='p')


def draft_article(modeladmin, request, queryset):
    queryset.update(status='d')


def close_article_commentstatus(modeladmin, request, queryset):
    queryset.update(comment_status='c')


def open_article_commentstatus(modeladmin, request, queryset):
    queryset.update(comment_status='o')


makr_article_publish.short_description = _('Publish selected articles')
draft_article.short_description = _('Draft selected articles')
close_article_commentstatus.short_description = _('Close article comments')
open_article_commentstatus.short_description = _('Open article comments')


class ArticlelAdmin(admin.ModelAdmin):
    list_per_page = 20
    search_fields = ('body', 'title')
    form = ArticleForm
    list_display = (
        'id',
        'title',
        'author',
        'link_to_category',
        'creation_time',
        'views',
        'status',
        'type',
        'article_order',
        'versions_link')
    list_display_links = ('id', 'title')
    list_filter = ('status', 'type', 'category')
    date_hierarchy = 'creation_time'
    filter_horizontal = ('tags',)
    exclude = ('creation_time', 'last_modify_time')
    view_on_site = True
    actions = [
        makr_article_publish,
        draft_article,
        close_article_commentstatus,
        open_article_commentstatus]
    raw_id_fields = ('author', 'category',)

    def link_to_category(self, obj):
        info = (obj.category._meta.app_label, obj.category._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.category.id,))
        return format_html(u'<a href="%s">%s</a>' % (link, obj.category.name))

    link_to_category.short_description = _('category')
    
    def versions_link(self, obj):
        count = obj.versions.count()
        link = reverse('admin:blog_articleversion_changelist') + f'?article__id__exact={obj.id}'
        return format_html(u'<a href="%s">%d versions</a>' % (link, count))
    
    versions_link.short_description = _('Versions')

    def get_form(self, request, obj=None, **kwargs):
        form = super(ArticlelAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['author'].queryset = get_user_model(
        ).objects.filter(is_superuser=True)
        return form

    def save_model(self, request, obj, form, change):
        # 保存request到threading.local，以便模型的save方法可以获取当前用户
        from blog.middleware import local
        local.request = request
        super(ArticlelAdmin, self).save_model(request, obj, form, change)

    def get_view_on_site_url(self, obj=None):
        if obj:
            url = obj.get_full_url()
            return url
        else:
            from djangoblog.utils import get_current_site
            site = get_current_site().domain
            return site


class TagAdmin(admin.ModelAdmin):
    exclude = ('slug', 'last_mod_time', 'creation_time')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category', 'index')
    exclude = ('slug', 'last_mod_time', 'creation_time')


class LinksAdmin(admin.ModelAdmin):
    exclude = ('last_mod_time', 'creation_time')


class SideBarAdmin(admin.ModelAdmin):
    list_display = ('name', 'content', 'is_enable', 'sequence')
    exclude = ('last_mod_time', 'creation_time')


class BlogSettingsAdmin(admin.ModelAdmin):
    pass


def restore_version(modeladmin, request, queryset):
    for version in queryset:
        # 恢复版本内容到原文章
        article = version.article
        article.title = version.title
        article.body = version.body
        # 保存时创建新版本记录
        article.save(create_version=True)
        # 添加恢复版本的注释
        latest_version = article.versions.order_by('-version_number').first()
        if latest_version:
            latest_version.comment = f"Restored from version {version.version_number}"
            latest_version.save()


restore_version.short_description = _('Restore selected version to article')


def compare_versions(modeladmin, request, queryset):
    if len(queryset) != 2:
        modeladmin.message_user(request, _('Please select exactly two versions to compare.'), level='ERROR')
        return
    
    version1, version2 = queryset.order_by('version_number')
    
    # 对比标题
    title_diff = list(difflib.unified_diff(
        version1.title.splitlines(),
        version2.title.splitlines(),
        fromfile=f'Version {version1.version_number}',
        tofile=f'Version {version2.version_number}',
        lineterm=''
    ))
    
    # 对比正文
    body_diff = list(difflib.unified_diff(
        version1.body.splitlines(),
        version2.body.splitlines(),
        fromfile=f'Version {version1.version_number}',
        tofile=f'Version {version2.version_number}',
        lineterm=''
    ))
    
    # 生成HTML格式的差异显示
    diff_html = '<div style="padding: 15px;">'
    
    if title_diff:
        diff_html += '<h3>Title Differences:</h3><pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">'
        for line in title_diff:
            if line.startswith('+'):
                diff_html += f'<span style="color: green;">{line}</span>\n'
            elif line.startswith('-'):
                diff_html += f'<span style="color: red;">{line}</span>\n'
            elif line.startswith('@'):
                diff_html += f'<span style="color: blue; font-weight: bold;">{line}</span>\n'
            else:
                diff_html += f'{line}\n'
        diff_html += '</pre>'
    
    if body_diff:
        diff_html += '<h3>Body Differences:</h3><pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; white-space: pre-wrap;">'
        for line in body_diff:
            if line.startswith('+'):
                diff_html += f'<span style="color: green;">{line}</span>\n'
            elif line.startswith('-'):
                diff_html += f'<span style="color: red;">{line}</span>\n'
            elif line.startswith('@'):
                diff_html += f'<span style="color: blue; font-weight: bold;">{line}</span>\n'
            else:
                diff_html += f'{line}\n'
        diff_html += '</pre>'
    
    if not title_diff and not body_diff:
        diff_html += '<p style="color: #666;">No differences found between the selected versions.</p>'
    
    diff_html += '</div>'
    
    from django.http import HttpResponse
    return HttpResponse(diff_html)


compare_versions.short_description = _('Compare selected versions')




class ArticleVersionAdmin(admin.ModelAdmin):
    list_per_page = 20
    search_fields = ('title', 'body', 'article__title')
    list_display = (
        'id',
        'article_title',
        'version_number',
        'editor',
        'creation_time',
        'restore_link',
        'comment_link'
    )
    list_display_links = ('id', 'version_number')
    list_filter = ('article', 'editor', 'creation_time')
    date_hierarchy = 'creation_time'
    raw_id_fields = ('article', 'editor',)
    readonly_fields = ('version_number', 'creation_time', 'last_modify_time')
    actions = [restore_version, compare_versions]
    
    def restore_link(self, obj):
        from django.urls import reverse
        return f'<a href="{reverse("blog:article_version_restore", args=[obj.pk])}" onclick="return confirm(\'确定要恢复到此版本吗？\')">恢复此版本</a>'
    restore_link.short_description = _('Restore Operation')
    restore_link.allow_tags = True
    
    def article_title(self, obj):
        link = reverse('admin:blog_article_change', args=(obj.article.id,))
        return format_html(u'<a href="%s">%s</a>' % (link, obj.article.title))
    
    article_title.short_description = _('Article Title')
    
    def comment_link(self, obj):
        if obj.comment:
            return mark_safe(f'<span title="{obj.comment}">{obj.comment}</span>')
        return ''
    
    comment_link.short_description = _('Comment')
    
    def has_add_permission(self, request):
        # 禁止手动添加版本，版本只能自动创建
        return False
    
    def has_change_permission(self, request, obj=None):
        # 禁止修改版本历史
        return False


admin.site.register(Article, ArticlelAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Links, LinksAdmin)
admin.site.register(SideBar, SideBarAdmin)
admin.site.register(BlogSettings, BlogSettingsAdmin)
admin.site.register(ArticleVersion, ArticleVersionAdmin)
