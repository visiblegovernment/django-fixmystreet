
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
    

class MatchingCategoryClass(EmailRuleBehaviour):
    def get_email(self,report, email_rule):
        if report.category.category_class == email_rule.category_class:
            return( email_rule.email )
        else:
            return( None )

    def describe(self,email_rule):
        return('Send All Reports Matching Category Type %s To %s' % (email_rule.category_class.name_en, email_rule.email))
    
class NotMatchingCategoryClass(EmailRuleBehaviour):
    def get_email(self,report, email_rule):
        if report.category.category_class != email_rule.category_class:
            return( email_rule.email )
        else:
            return( None )

    def describe(self,email_rule):
        return('Send All Reports Not Matching Category Type %s To %s' % (email_rule.category_class.name_en, email_rule.email))
