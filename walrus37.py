import codecs
import io
import token as tokens
import tokenize
from functools import partial

tokens.COLONEQUAL = 0xFF
tokens.tok_name[0xFF] = "COLONEQUAL"
tokenize.EXACT_TOKEN_TYPES[":="] = tokens.COLONEQUAL

tokenize.PseudoToken = tokenize.Whitespace + tokenize.group(
    r":=",
    tokenize.PseudoExtras,
    tokenize.Number,
    tokenize.Funny,
    tokenize.ContStr,
    tokenize.Name,
)


def generate_walrused_source(readline):
    source_tokens = list(tokenize.tokenize(readline))
    modified_source_tokens = source_tokens.copy()

    def inc(token, by=1, page=0):
        start = list(token.start)
        end = list(token.end)

        start[page] += by
        end[page] += by

        return token._replace(start=tuple(start), end=tuple(end))

    def line_start_index(tokens, line):
        for token in tokens:
            if token.start[0] == line:
                return tokens.index(token)

    for index, token in enumerate(source_tokens):
        if token.exact_type == tokens.COLONEQUAL:
            name = modified_source_tokens[index - 1]
            __op = modified_source_tokens.pop(index)
            value = modified_source_tokens.pop(index)

            pattern = io.BytesIO(f"{name.string} = {value.string}\n".encode("utf8"))
            assignment_tokens = list(tokenize.tokenize(pattern.readline))[1:-1]

            modified_source_tokens[index] = modified_source_tokens[index]._replace(
                start=name.end
            )

            current_lineno = modified_source_tokens[index].start[0] + 1
            start = line_start_index(modified_source_tokens, current_lineno) + 1
            for _index, _token in enumerate(modified_source_tokens[start:], start):
                modified_source_tokens[_index] = inc(_token)

            for assignment_token in reversed(assignment_tokens):
                assignment_token = inc(assignment_token, current_lineno - 1)
                assignment_token = inc(
                    assignment_token, modified_source_tokens[start - 1].end[1], 1
                )
                modified_source_tokens.insert(start, assignment_token)

    return tokenize.untokenize(modified_source_tokens)


def decode(input, errors="strict", encoding=None):
    if not isinstance(input, bytes):
        input, _ = encoding.encode(input, errors)

    buffer = io.BytesIO(input)
    result = generate_walrused_source(buffer.readline)
    return encoding.decode(result)


class IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def _buffer_decode(self, input, errors, final):  # pragma: no cove
        return decode(input, errors, encoding=self._encoding)


def search(name):
    if "walrus37" in name:
        encoding = name.strip("walrus37").strip("-") or "utf8"
        encoding = codecs.lookup(encoding)
        IncrementalDecoder._encoding = encoding

        walrus_codec = codecs.CodecInfo(
            name="walrus37",
            encode=encoding.encode,
            decode=partial(decode, encoding=encoding),
            incrementalencoder=encoding.incrementalencoder,
            incrementaldecoder=IncrementalDecoder,
            streamreader=encoding.streamreader,
            streamwriter=encoding.streamwriter,
        )
        return walrus_codec
