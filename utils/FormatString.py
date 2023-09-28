import re
import os
from datetime import datetime, timezone, timedelta
import pytz


class FormatString:

    def is_within_forward_days(self, target_date, days):
        us_eastern = pytz.timezone('America/New_York')
        current_date = datetime.now(us_eastern).date()
        date_threshold = current_date + timedelta(days=days)
        if current_date <= target_date <= date_threshold:
            return True
        else:
            return False

    def is_within_specific_month(self, isoformat, offset_month=0):
        current_date = self.current_est_datetime_obj()
        month = current_date.month + offset_month
        target_month = 12 if month <= 0 else month  # if anyone make offset -1 and current month is 1 then it will move back to previous month which is 12
        pattern = f"{current_date.year}-{str(target_month).zfill(2)}"
        regex = re.compile(pattern)
        if regex.match(isoformat):
            return True
        else:
            return False

    def iso_to_time_obj(self, isoformat):
        new_iso_time = isoformat
        if "Z" in isoformat:
            new_iso_time = isoformat.replace("Z", "+00:00")
        time_obj = datetime.fromisoformat(new_iso_time)
        return time_obj

    def iso_to_readable_date(self, isoformat, format="mm/dd/yyyy"):
        time_obj = self.iso_to_time_obj(isoformat=isoformat)
        formatted_time = self.datetime_obj_to_readable(datetime_obj=time_obj, format=format)
        return formatted_time

    def iso_to_est_readable_date(self, isoformat, format="mm/dd/yyyy"):
        time_obj = self.iso_to_est_time(iso_time=isoformat)
        formatted_time = self.datetime_obj_to_readable(datetime_obj=time_obj, format=format)
        return formatted_time

    def datetime_obj_to_readable(self, datetime_obj, format='m/d/y'):
        if format == "mm/dd/yyyy" or format == "m/d/y" or format == "m/d/Y":
            return datetime_obj.strftime("%m/%d/%Y")
        elif format == "Y-m-d":
            return datetime_obj.strftime("%Y-%m-%d")
        elif format == "Y/m/d":
            return datetime_obj.strftime("%Y/%m/%d")
        elif format == "Y-m":
            return datetime_obj.strftime("%Y-%m")
        else:
            return datetime_obj.strftime("%m/%d/%Y")

    def iso_to_est_time(self, iso_time):
        time_obj = self.iso_to_time_obj(isoformat=iso_time)
        est_timezone = pytz.timezone('America/New_York')
        est_datetime_obj = time_obj.astimezone(est_timezone)
        return est_datetime_obj

    def current_est_isotime(self):
        current_datetime = self.current_est_datetime_obj()
        iso_formatted_datetime = current_datetime.isoformat()
        return iso_formatted_datetime

    def current_est_datetime_obj(self):
        us_eastern = pytz.timezone('America/New_York')
        current_datetime = datetime.now(us_eastern)
        return current_datetime

    def one_format_to_another(self, date, source_format, target_format):
        date_obj = None
        if source_format == "m/d/Y":
            date_obj = datetime.strptime(date, "%m/%d/%Y")
        else:
            date_obj = datetime.strptime(date, "%m/%d/%Y")

        convert_to_iso = date_obj.isoformat()
        readable_time = self.iso_to_readable_date(isoformat=convert_to_iso, format=target_format)
        return readable_time

    def str_to_datetime_obj(self, date_str):
        datetime_obj = datetime.strptime(date_str, '%m/%d/%Y')
        return datetime_obj

    def datetime_offset(self, days):
        current_datetime = self.current_est_datetime_obj()
        offseted = current_datetime + timedelta(days=days)
        return offseted

