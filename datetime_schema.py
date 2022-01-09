import arrow


def date_time_to_string(pg_date_time_object):
    """Convert a postgres datetime object to a string"""
    return arrow.get(pg_date_time_object).format()


def string_to_date_time(_string):
    """Convert a string to a postgres datetime object"""
    return arrow.get(_string).timestamp()


def trans_dates_to_string(trans):
    """Schema Modifier for Transcript Date Times"""
    trans["updated_at"] = date_time_to_string(trans["updated_at"])
    trans["created_at"] = date_time_to_string(trans["created_at"])
    return trans
