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
