import re
from typing import List,Tuple,Optional,Union
from hebsafeharbor.common.date_regex import (HEB_FULL_DATE_REGEX,
                                             HEB_MONTH_YEAR_REGEX,
                                             HEB_DAY_MONTH_REGEX,
                                             LATIN_DATE_REGEX,
                                             EN_DMY_REGEX,
                                             EN_MDY_REGEX,
                                             EN_YMD_REGEX,
                                             EN_DATE_REGEX)

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
 

def set_date_mention_component(matched:re.Match,ind:Union[int,str]) -> Optional[DateMentionComponent]:
    '''
    Extracts the date and its span from a regular expression and sets a DateMentionComponent 
    instance accordingly.
    :param matched: a re.Match instance containing the groups of a regular expression
    :param ind: the index (or group name) of the group we would like to retrieve. if ind<1 (or group name not in the matched groups), return None
    :return: a DateMentionComponent instance
    '''
    if type(ind) == int:
        date_instance = DateMentionComponent(matched.group(ind),matched.span(ind)[0],matched.span(ind)[1]) if ind>0 else None
        
    else:
        date_instance = DateMentionComponent(matched.group(ind),matched.span(ind)[0],matched.span(ind)[1]) if ind in matched.groupdict() else None
        
    return date_instance

def set_date_mention_from_pattern_group_names(matched:re.Match) -> DateMention:
    '''
    Extracts the date and its span from a regular expression by group names and sets a DateMention
    instance accordingly.
    :param matched: a re.Match instance containing the groups of a regular expression
    :return: a list of DateMentionComponent instances
    '''
    day,month,year = [set_date_mention_component(matched,ind) for ind in ['day','month','year'] ]
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

    # check if it's a numerical date (dd.mm.yyyy, mm-dd-yy etc.)
    num_date = extract_numerical_date_components(text)
    if num_date:
        return num_date

    # Go over the different date patterns and search for a match
    pattern_list = [HEB_FULL_DATE_REGEX,HEB_MONTH_YEAR_REGEX,HEB_DAY_MONTH_REGEX,
                    LATIN_DATE_REGEX,
                    EN_DMY_REGEX,EN_MDY_REGEX,EN_YMD_REGEX,
                    EN_DATE_REGEX]

    matched = find_pattern(text,pattern_list)
    if matched:
        return set_date_mention_from_pattern_group_names(matched)
    
    return DateMention()

def find_pattern(text:str,patterns:List[str])-> Optional[re.Match]:
    '''Receives text and a list of patterns and returns the matching pattern. 
    If none of the patterns match, return None
    :param text: the original text
    :param patterns: a list of patterns
    :return a matching pattern or None if none of the patterns matched the given text
    '''
    for pattern in patterns:
        matched = re.search(pattern,text,re.IGNORECASE)
        if matched:
            return matched
    return None

def extract_numerical_date_components(text:str) -> Optional[DateMention]:
    '''
        Checks if the given text matches a numerical date pattern (dd.mm.yy, mm-dd-yyyy etc.) 
       :param text: the original text
       :return if a pattern was found, returns DateMention, otherwise returns None
    '''
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
                year = set_date_mention_component(matched,ind=1)
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
        return None
    
