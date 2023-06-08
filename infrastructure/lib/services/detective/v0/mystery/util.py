import datetime

import tiktoken


def count_tokens(text: str, encoding_name: str) -> int:
    '''Counts the number of tokens in a string.

    Args:
        text `str`: The string to count tokens in.
        encoding_name `str`: The name of the encoding to use.

    Returns:
        The number of tokens in the string.
    '''
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    count = len(tokens)
    return count


def date_day_to_timestamp(date_day: int) -> int:
    '''Converts a date day, i.e. an int of the form YYYYMMDD, to a
    timestamp.

    Args:
        date_day `int`: The date day to convert.

    Returns:
        `int`: The timestamp.
    '''
    year = date_day // 10000
    month = (date_day % 10000) // 100
    day = date_day % 100
    timestamp = datetime.datetime(year, month, day).timestamp()
    return timestamp


def timestamp_to_date_day(timestamp: int) -> int:
    '''Converts a timestamp to a date day.

    Args:
        timestamp `int`: The timestamp to convert.

    Returns:
        `int`: The date day.
    '''
    date = datetime.datetime.fromtimestamp(timestamp)
    date_day = date.year * 10000 + date.month * 100 + date.day
    return date_day


def date_string_to_date_day(date_string: int) -> str:
    '''Converts a date string to a date day.

    Args:
        date_string `str`: The date string to convert; YYYY-MM-DD.

    Returns:
        `int`: The date day.
    '''
    date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
    date_day = date.year * 10000 + date.month * 100 + date.day
    return date_day


def get_today_timestamp() -> int:
    '''Gets the timestamp for today.

    Returns:
        `int`: The timestamp for today.
    '''
    return int(datetime.datetime.today().timestamp())


def get_today_date_day() -> int:
    '''Gets the date day for today.

    Returns:
        `int`: The date day for today.
    '''
    return timestamp_to_date_day(get_today_timestamp())


def get_today_date_string() -> str:
    '''Gets the date string for today.

    Returns:
        `str`: The date string for today.
    '''
    return datetime.datetime.today().strftime('%Y-%m-%d')