from fixmystreet.mainapp.models import UserProfile,EmailRule,Ward,ReportCategory,City, ReportCategoryClass, FaqEntry, Councillor,ReportCategorySet
from django.contrib import admin
from contrib.transmeta import canonical_fieldname
from django import forms

admin.site.register(City)
admin.site.register(UserProfile)

class ReportCategoryClassAdmin(admin.ModelAdmin):
    list_display = ('name',)
    
admin.site.register(ReportCategoryClass,ReportCategoryClassAdmin)

class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'hint')

admin.site.register(ReportCategory, ReportCategoryAdmin)

class ReportCategorySetAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(ReportCategorySet, ReportCategorySetAdmin)

class FaqEntryAdmin(admin.ModelAdmin):
    list_display = ('q', 'order')

admin.site.register(FaqEntry, FaqEntryAdmin)
    
class CouncillorAdmin(admin.ModelAdmin):
    ''' only show councillors from cities this user has access to '''
    list_display = ('last_name', 'first_name', 'email')
    
    def queryset(self,request):
        if request.user.is_superuser:
            return( super(CouncillorAdmin,self).queryset(request) )
        profile = request.user.get_profile()        
        qs = self.model._default_manager.filter(city__in=profile.cities.all())
        return(qs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "city":
                profile = request.user.get_profile()
                kwargs["queryset"] = profile.cities.all()
        return super(CouncillorAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    
            
admin.site.register(Councillor,CouncillorAdmin)


class WardAdmin(admin.ModelAdmin):
    ''' only show wards from cities this user has access to '''

    list_display = ('city','number','name',)
    list_display_links = ('name',)
    ordering       = ['city', 'number']
    exclude = ['geom']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            profile = request.user.get_profile()
            if db_field.name == "councillor":
                kwargs["queryset"] = Councillor.objects.filter(city__in=profile.cities.all())
            if db_field.name == "city":
                kwargs["queryset"] = profile.cities.all()
        return super(WardAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        
    def queryset(self,request):
        if request.user.is_superuser:
            return( super(WardAdmin,self).queryset(request) )
        profile = request.user.get_profile()
        qs = self.model._default_manager.filter(city__in=profile.cities.all())
        return(qs)
    
admin.site.register(Ward,WardAdmin)

class EmailRuleAdmin(admin.ModelAdmin):
    ''' only show email rules from cities this user has access to '''

    change_list_template = 'admin/mainapp/emailrules/change_list.html'

    def queryset(self,request):
        if request.user.is_superuser:
            return( super(EmailRuleAdmin,self).queryset(request) )
        profile = request.user.get_profile()
        qs = self.model._default_manager.filter(city__in=profile.cities.all())
        return(qs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "city":
                profile = request.user.get_profile()
                kwargs["queryset"] = profile.cities.all()
        return super(EmailRuleAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    

admin.site.register(EmailRule,EmailRuleAdmin)
