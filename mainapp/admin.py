from fixmystreet.mainapp.models import UserProfile,EmailRule,Ward,ReportCategory,City, ReportCategoryClass, FaqEntry, Councillor
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

class FaqEntryAdmin(admin.ModelAdmin):
    list_display = ('q', 'order')

admin.site.register(FaqEntry, FaqEntryAdmin)

class CityAdminCouncillorForm(forms.ModelForm):
    class Meta:
        model = Councillor
        exclude = ['city','fax','phone']

class SuperUserCouncillorForm(forms.ModelForm):
    class Meta:
        model = Councillor

class CouncillorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email')

    def queryset(self,request):
        if request.user.is_superuser:
            return( super(CouncillorAdmin,self).queryset(request) )
        profile = request.user.get_profile()
        qs = self.model._default_manager.filter(city=profile.city)
        return(qs)
    
    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            return( SuperUserCouncillorForm )
        else:
            return( CityAdminCouncillorForm )
        
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            profile = request.user.get_profile()
            obj.city = profile.city
        return( super(CouncillorAdmin,self).save_model(request,obj,form,change))
            
    
admin.site.register(Councillor,CouncillorAdmin)


class WardAdmin(admin.ModelAdmin):
    list_display = ('city','number','name',)
    list_display_links = ('name',)
    ordering       = ['city', 'number']
    exclude = ['city','geom']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "councillor":
                profile = request.user.get_profile()
                kwargs["queryset"] = Councillor.objects.filter(city=profile.city)
        return super(WardAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        
    def queryset(self,request):
        if request.user.is_superuser:
            return( super(WardAdmin,self).queryset(request) )
        profile = request.user.get_profile()
        qs = self.model._default_manager.filter(city=profile.city)
        return(qs)
    
    
admin.site.register(Ward,WardAdmin)

class CityAdminRuleForm(forms.ModelForm):
    class Meta:
        model = EmailRule
        exclude = ['city',]
   

class SuperUserRuleForm(forms.ModelForm):
    class Meta:
        model = EmailRule

class EmailRuleAdmin(admin.ModelAdmin):

    change_list_template = 'admin/mainapp/emailrules/change_list.html'


    def queryset(self,request):
        if request.user.is_superuser:
            return( super(EmailRuleAdmin,self).queryset(request) )
        profile = request.user.get_profile()
        qs = self.model._default_manager.filter(city=profile.city)
        return(qs)
    
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            profile = request.user.get_profile()
            obj.city = profile.city
        return( super(EmailRuleAdmin,self).save_model(request,obj,form,change))

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            return( SuperUserRuleForm )
        else:
            return( CityAdminRuleForm )
        
    def changelist_view(self, request, extra_context=None):
        if not request.user.is_superuser:
            profile = request.user.get_profile()
            if extra_context == None:
                extra_context = {}
            extra_context['city'] = profile.city
        return(super(EmailRuleAdmin,self).changelist_view(request,extra_context))


admin.site.register(EmailRule,EmailRuleAdmin)
