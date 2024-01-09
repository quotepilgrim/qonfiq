#!/bin/env python

import re


def parse(
    config,
    source="file",
    default_section="DEFAULT",
    delimiters="=",
    subsection_delimiter=".",
    comment_prefixes=("#", ";"),
    inline_comment_prefixes=("",),
    brackets=(r"\[", r"\]"),
    process_keys=lambda s: s,
    process_values=lambda s: s,
    process_headers=lambda s: s,
):
    result = {default_section: {}}
    header = default_section
    levels = {header: 1}
    assignment_split_pattern = re.compile(r"(?<!\\)" f'(?:{"|".join(delimiters)})')
    header_pattern = re.compile(f"^[{brackets[0]}].+?[{brackets[1]}]$")

    def process_multiline(indict, key, value):
        indict[key][value] = process_values(indict[key][value].strip())

    if source == "file":
        with open(config) as f:
            data = [line for line in f]
    elif source == "string":
        data = [line for line in config.splitlines()]
    else:
        raise ValueError(
            f'Invalid argument passed to source. \
            Accepted values are "file" or "string"; received: {repr(source)})'
        )
    #
    # indent = 0
    prev_indent = 0
    prev_header, prev_key, prev_value = "", "", ""
    multiline = False

    for line in data:
        if re.search(header_pattern, line.strip()):
            line = line.replace(" ", "")
            header_level = 0
            for c in line:
                if c not in brackets[0]:
                    break
                header_level += 1

            header = line[1:-1].strip("".join(brackets))
            header = process_headers(header)
            for key in list(reversed(levels)):
                if levels[key] < header_level:
                    header = f"{subsection_delimiter}".join(
                        [key, header.replace(f"{key + subsection_delimiter}", "")]
                    )
                    break
            levels[header] = header_level
            result[header] = {}

        else:
            for prefix in comment_prefixes:
                if prefix and line.strip().startswith(prefix):
                    line = ""

            for prefix in inline_comment_prefixes:
                if prefix and prefix in line:
                    line = line.split(prefix)[0]
                    break

            key, *value = re.split(assignment_split_pattern, line, maxsplit=1)
            key = key.strip()

            if value:
                value = value[0].strip()
            else:
                value = None

            if key:
                key = key
                indent = 0
                while line[indent].isspace():
                    indent += 1

            if indent > prev_indent and header == prev_header and not value:
                if not multiline:
                    multiline = True
                    result[header][prev_key] = prev_value
                result[header][prev_key] += f"\n{key}"
                continue
            elif multiline:
                multiline = False
                process_multiline(result, prev_header, prev_key)

            if key:
                prev_key = key
                prev_value = value or ""
                key = process_keys(key)
                if value:
                    value = process_values(value)
                result[header][key] = value

            prev_indent = indent
            prev_header = header

    if multiline:
        process_multiline(result, prev_header, prev_key)

    return result
