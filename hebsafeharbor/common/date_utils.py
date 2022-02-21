import re
from typing import List
from hebsafeharbor.common.date_regex import HEB_FULL_DATE_REGEX, HEB_MONTH_YEAR_REGEX, HEB_DAY_MONTH_REGEX, LATIN_DATE_REGEX
MIN_DATE_LENGTH = 6

class DateMentionComponent:
    """
    This class stores the information on the certain date component - its value (text) and its offset the date mention
    """

    def __init__(self, text: str, start: int, end:int):
        """
        Initialize the DateMentionComponent

        :param text: the value of the date component (its text)
        :param start: the first index of the date component
        :param end: the last index of the date component
        """
        self.text = text
        self.start = start
        self.end = end


class DateMention:
    """
    This class stores the information on the components of a certain date - the date components and the string that
    separates between them. In case that not all the components exist, None will be placed under their member field.
    """

    def __init__(self, day: DateMentionComponent = None, month: DateMentionComponent = None,
                 year: DateMentionComponent = None,
                 text: str = None):
        """
        Initialize the DateMention

        :param day: DateComponent object which represents the day
        :param month: DateComponent object which represents the month
        :param year: DateComponent object which represents the year
        :param text: the original text
        """
        self.day = day
        self.month = month
        self.year = year
        self.text = text

    def reconstruct_date_string(self) -> str:
        """
        Reconstructs the date string based on the stored date components information and the given string prefix

        :return a string of the stored date along with the text that precedes the date
        """
        date_components = [self.day, self.month, self.year]
        date_components = [dt for dt in date_components if (dt is not None) and (dt.text is not None)] #filter empty date components
        sorted_date_components = sorted(date_components, key=lambda date_comp: date_comp.start, reverse=True)
        masked_text = self.text
        #move backwards on the text, replacing the components in reverse order
        for date_comp in sorted_date_components:
            masked_text = masked_text[:date_comp.start] + date_comp.text + masked_text[date_comp.end:]

        return masked_text
 

def set_date_mention_component(matched:re.Match,ind:int) -> DateMentionComponent:
    '''
    Extracts the date and its span from a regular expression and sets a DateMentionComponent 
    instance accordingly.
    :param matched: a re.Match instance containing the groups of a regular expression
    :param ind: the index of the group we would like to retrieve. if ind<1, return an empty instance
    :return: a DateMentionComponent instance
    '''
    date_instance = (
        DateMentionComponent(matched.group(ind),matched.span(ind)[0],matched.span(ind)[1]) if ind>0 else None
    )
    return date_instance

def set_date_mention(matched:re.Match,group_order:List[int]) -> DateMention:
    '''
    Extracts the date and its span from a regular expression and sets a DateMention
    instance accordingly.
    :param matched: a re.Match instance containing the groups of a regular expression
    :param group_order: the order of the group indexes to extract from the matched regular expression
    :return: a list of DateMentionComponent instances
    '''
    day,month,year = [set_date_mention_component(matched,ind) for ind in group_order]
    return DateMention(day=day,month=month, year=year,text=matched.string)




def extract_date_components(text: str) -> DateMention:
    """
    Extracts the different date components out of the give recognized entity text

    :param text: the recognized entity text
    :return: a DateContainer object which contains the extracted date components (text and location) - day, month and
    year - along with the separator.
    """

    # if there are less than 6 characters, it is probably not a date (just a mistake in recognition such as season,
    # scale of pain 3/10, etc.)
    if len(text) < MIN_DATE_LENGTH:
        return DateMention()

    #Hebrew dates
    heb_pattern = HEB_FULL_DATE_REGEX
    matched = re.search(heb_pattern,text)
    if matched:
        return set_date_mention(matched,group_order=[1,2,3])

    heb_pattern = HEB_MONTH_YEAR_REGEX
    matched = re.search(heb_pattern,text)
    if matched:
        return set_date_mention(matched,group_order=[-1,1,2])

    heb_pattern = HEB_DAY_MONTH_REGEX
    matched = re.search(heb_pattern,text)
    if matched:
        return set_date_mention(matched,group_order=[1,2,-1])
        
    #Latin dates
    latin_pattern = LATIN_DATE_REGEX
    matched = re.search(latin_pattern,text)
    if matched:
        return set_date_mention(matched,group_order=[1,2,3]) 
   
    # Numerical dates
    num_pattern = r"(\d+)(?:[/.-])(\d+)(?:(?:[/.-])(\d+))?"
    matched = re.search(num_pattern,text)
    if matched:
        if not matched.group(3): #date with only two components <month>[/.-]<year> or <year>[/.-]<month>
            day = None
            if int(matched.group(1)) > 12:
                year = set_date_mention_component(matched,ind=1)
                month = set_date_mention_component(matched,ind=2)
            else:
                month = set_date_mention_component(matched,ind=1)
                year = set_date_mention_component(matched,ind=2)
            return DateMention(day=day,month=month,text=text)        
        else:
            if int(matched.group(1))>31:        
                year = set_date_mention(matched,ind=1)
                if int(matched.group(2))>12:
                    month = set_date_mention_component(matched,ind=3)
                    day = set_date_mention_component(matched,ind=2)
                else:
                    month = set_date_mention_component(matched,ind=2)
                    day = set_date_mention_component(matched,ind=3)
            else:
                year = set_date_mention_component(matched,ind=3)
                if int(matched.group(2))>12:
                    month = set_date_mention_component(matched,ind=1)
                    day = set_date_mention_component(matched,ind=2)
                else:
                    month = set_date_mention_component(matched,ind=2)
                    day = set_date_mention_component(matched,ind=1)
            return DateMention(day=day,month=month, year=year,text=text)
    return DateMention()