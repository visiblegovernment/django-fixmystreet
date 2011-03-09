from django.utils.translation import ugettext as _

class EmailRuleBehaviour(object):
    def get_email(self,report,email_rule):
        return(None)
    
    def describe(self, email_rule):
        return("")
            
class ToCouncillor(EmailRuleBehaviour):
    def get_email(self, report, email_rule):
        return( report.ward.councillor.email )

    def describe(self, email_rule ):
        return("Send Reports to Councillor's Email Address")

    def report_group(self, email_rule):
        return(_("All reports"))
    
    def value_for_ward(self, email_rule, ward):
        return( ward.councillor.email )

    def value_for_city(self,email_rule):
        return(_("the councillor's email address"))
    
class MatchingCategoryClass(EmailRuleBehaviour):
    def get_email(self,report, email_rule):
        if report.category.category_class == email_rule.category_class:
            return( email_rule.email )
        else:
            return( None )

    def describe(self,email_rule):
        return('Send All Reports Matching Category Type %s To %s' % (email_rule.category_class.name_en, email_rule.email))
    
    def report_group(self, email_rule ):
        return(_("'%s' reports") % ( email_rule.category_class.name ) )
    
    def value_for_ward(self, email_rule, ward):
        return( email_rule.email )
    
    def value_for_city(self,email_rule):
        return(email_rule.email)
    
class NotMatchingCategoryClass(EmailRuleBehaviour):
    def get_email(self,report, email_rule):
        if report.category.category_class != email_rule.category_class:
            return( email_rule.email )
        else:
            return( None )

    def describe(self,email_rule):
        return('Send All Reports Not Matching Category Type %s To %s' % (email_rule.category_class.name_en, email_rule.email))

    def report_group(self, email_rule):
        return(_("non-'%s' reports") % ( email_rule.category_class.name ) )
    
    def value_for_ward(self, email_rule, ward):
        return( email_rule.email )

    def value_for_city(self,email_rule):
        return(email_rule.email)
    
# Creates a human-readable description of a single email rule 
# in the context of a particular ward or city.

class EmailRuleDescriber:

    def __init__(self, desc):
        self.cc = []
        self.to = []            
        self.desc = desc
        
    def __unicode__(self):
        s = _("%s will be ") % (self.desc)
        if len(self.to) != 0:
            s += _("sent to:")
            s += ",".join(self.to)
        
        if len(self.to) != 0 and len(self.cc) != 0:
            s += _(" and ")
            
        if len(self.cc) != 0:
            s += _("cc'd to:")
            s += ",".join(self.cc)
        return( s )

    def add_rule(self, rule, ward ):
        value = rule.value(ward)
        if rule.is_cc:
            self.cc.append(value)
        else:
            self.to.append(value)


# Creates a human-readable description of an email rule set
# for a particular ward or city.

class EmailRulesDesciber:
    
    def __init__(self, rules, city, ward = None):
        self.rule_set = {}
        if city.email:
            city_email = EmailRuleDescriber( _('All reports') )
            city_email.to.append(city.email)
            self.rule_set[city_email.desc] = city_email
            
        for rule in rules:
            label = rule.label()
            if not self.rule_set.has_key( label ):
                self.rule_set[ label ] = EmailRuleDescriber( label )
        
            describer = self.rule_set[ label ]
            describer.add_rule( rule, ward )
            
    def values(self):
        ret = self.rule_set.values()
        ret.reverse()
        return( ret )

        