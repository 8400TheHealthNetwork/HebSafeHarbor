# Hebrew Dates
heb_months_re = '|'.join(["אלול","אב","תמוז","סיון","סיוון","אייר","ניסן","אדר","שבט","טבת","כסלו","כיסלו","חשוון","תשרי"])
heb_days_re = '|'.join(["[א-ל]׳","""י״(?:[א-ד]|[ז-ט])""","""ט״(?:ו|ז)""","""כ״[א-ט]""","""ל״א"""])
heb_year_re = r"ה?ת[א-ת][א-ת]?״[א-ת]"
HEB_FULL_DATE_REGEX =  rf"\b(?:ב|ל|מ|מה|ה)?(?P<day>{heb_days_re})\s+(?:ב|ל|בחודש|לחודש)?(?:-|\s)?(?P<month>{heb_months_re})(?:\s+|,\s+)(?P<year>{heb_year_re})\b"
HEB_MONTH_YEAR_REGEX =  rf"\b(?:ב|ל|בחודש|לחודש)?(?:-|\s)?(?P<month>{heb_months_re})(?:\s+|,\s+)(?P<year>{heb_year_re})\b"
HEB_DAY_MONTH_REGEX =  rf"\b(?:ב|ל|מ|מה|ה)?(?P<day>{heb_days_re})\s+(?:ב|ל|בחודש|לחודש)?(?:-|\s)?(?P<month>{heb_months_re})\b"

# Latin Dates
latin_months_re =    '|'.join(["ינואר","פברואר","מרץ","אפריל","מאי","יוני","יולי","אוגוסט","ספטמבר","אוקטובר","נובמבר","דצמבר"])
num_days_re = r"[1-9]|0[1-9]|[1-2][0-9]|3[0-1]"
LATIN_DATE_REGEX =  rf"\b(?:ב|ל|מ|מה|ה)?(?P<day>{num_days_re})?(?:\s+)?(?:ב|ל|בחודש|לחודש)?(?:-|\s)?(?P<month>{latin_months_re})(?:\s|,\s)?(?P<year>\d\d|\d\d\d\d)?\b"

# Dates in English
en_abbrv_months_list = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec',]
en_full_months_list = ['january','february','march','april','may','june','july','august','september','octber','november','december']
en_month_re = '|'.join(en_abbrv_months_list+en_full_months_list)
EN_DATE_REGEX = rf"\b(?P<month>{en_month_re})(?:\s|,\s)(?P<day>{num_days_re})(?:\s|,\s)(?P<year>\d\d|\d\d\d\d)\b"

# Dates with no punctuations (ddmmyyyy,mmddyyyy...)
EN_DMY_REGEX = r"\b(?:ה|ב|מ|מה)?(?:-|:)?(?P<day>[0-2][1-9]|[3[0-1]])(?P<month>1[1-2]|0[1-9])(?P<year>\d{4}|\d{2})\b"
EN_MDY_REGEX = r"\b(?:ה|ב|מ|מה)?(?:-|:)?(?P<month>0[1-9]|1[0-2])(?P<day>0[1-9]|[1-2][0-9]|3[0-1])(?P<year>\d{4}|\d{2})\b"
EN_YMD_REGEX = r"\b(?:ה|ב|מ|מה)?(?:-|:)?(?P<year>\d{4}|\d{2})(?P<month>0[1-9]|[1-2][0-9]|3[0-1])(?P<day>0[1-9]|1[0-2])\b"

