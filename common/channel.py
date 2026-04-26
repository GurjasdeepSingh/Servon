import datetime
import unicodedata
from collections import defaultdict, Counter


def is_emoji(char: str) -> bool:
    return unicodedata.category(char) in ("So", "Sk")


def is_symbol(char: str) -> bool:
    return not char.isalnum() and char != "-" and not is_emoji(char)


def tokenize(name: str):
    print("tokenizing")
    tokens = []
    buffer = ""

    for ch in name:
        if is_emoji(ch):
            if buffer:
                tokens.append(("text", buffer))
                buffer = ""
            tokens.append(("emoji", ch))

        elif is_symbol(ch):
            if buffer:
                tokens.append(("text", buffer))
                buffer = ""
            tokens.append(("symbol", ch))

        else:
            buffer += ch

    if buffer:
        tokens.append(("text", buffer))

    return tokens


def symbol_positions(name: str):
    return [(i, ch) for i, ch in enumerate(name) if is_symbol(ch)]

def group_channels(channel_names):
    print("grouping channels")
    groups = defaultdict(list)

    for name in channel_names:
        for key in structure_positions_both(name):
            groups[key].append(name)

    if not groups:
        return None, channel_names

    best_key = max(groups, key=lambda k: len(groups[k]))
    return best_key, groups[best_key]
def structure_positions_both(name: str):
    length = len(name)
    positions = []

    for i, ch in enumerate(name):
        if is_symbol(ch) or is_emoji(ch):
            positions.append(("L", ch, i))                 # from left
            positions.append(("R", ch, length - 1 - i))    # from right

    return positions

def has_structure(names):
    for name in names:
        for ch in name:
            if is_symbol(ch) or is_emoji(ch):
                return True
    return False
def detect_components(names):
    has_emoji = False
    has_symbol = False

    for name in names:
        for ch in name:
            if is_emoji(ch):
                has_emoji = True
            elif is_symbol(ch):
                has_symbol = True

    return has_emoji, has_symbol

def derive_pattern(names, allow_emoji, allow_symbol):
    print("deriving patterns")
    token_lists = [tokenize(n) for n in names]

    min_len = min(len(t) for t in token_lists)
    pattern = []

    for i in range(min_len):
        types = [tokens[i][0] for tokens in token_lists]
        most_common = Counter(types).most_common(1)[0][0]

        if most_common == "emoji" and allow_emoji:
            chars = [tokens[i][1] for tokens in token_lists if tokens[i][0] == "emoji"]
            char = Counter(chars).most_common(1)[0][0]
            pattern.append(("emoji", char))

        elif most_common == "symbol" and allow_symbol:
            chars = [tokens[i][1] for tokens in token_lists if tokens[i][0] == "symbol"]
            char = Counter(chars).most_common(1)[0][0]
            pattern.append(("symbol", char))

        else:
            pattern.append(("text", None))

    return pattern

def build_name(pattern, text, emoji):
    print("building name")
    result = []

    for typ, val in pattern:
        if typ == "text":
            result.append(text)
        elif typ == "emoji":
            result.append(emoji)
        elif typ == "symbol":
            result.append(val)

    return "".join(result)


# ---- MAIN FUNCTION ----

def generate_channel_name(channel_names, new_text, new_emoji):
    print("starting")
    _, grouped = group_channels(channel_names)

    if not grouped:
        return None

    allow_emoji, allow_symbol = detect_components(grouped)

    # pure text case
    if not allow_emoji and not allow_symbol:
        return new_text

    pattern = derive_pattern(grouped, allow_emoji, allow_symbol)

    return build_name(pattern, new_text, new_emoji)
if __name__ == '__main__':
    channels = [
        "genera📍•",
        "ahhk📍•",
        "bot-commands📍",
        "random-channel"
    ]
    start_time = datetime.datetime.now()
    print(start_time)
    print()
    print(generate_channel_name(channels, "announcements", "📢"))
    print()
    print("Time taken:", datetime.datetime.now()-start_time)