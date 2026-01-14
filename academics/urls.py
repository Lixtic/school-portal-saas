from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('activities/manage/', views.manage_activities, name='manage_activities'),
    path('classes/manage/', views.manage_classes, name='manage_classes'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('gallery/upload/', views.upload_gallery_image, name='upload_gallery_image'),
    path('resources/manage/', views.manage_resources, name='manage_resources'),
    path('resources/delete/<int:resource_id>/', views.delete_resource, name='delete_resource'),
    path('settings/', views.school_settings_view, name='school_settings'),
    path('timetable/', views.timetable_view, name='timetable'),
    path('timetable/edit/<int:class_id>/', views.edit_timetable, name='edit_timetable'),
    path('global-search/', views.global_search, name='global_search'),
]
