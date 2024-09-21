DELIMETERS = {
    "start": "<discharge_summary>",
    "end": "</discharge_summary>",
}


def strip_delimeters(out_str: str) -> str:
    """
    Strip the delimeters from the output string.

    I.e. remove everything before and including &lt;discharge_summary&gt; and
    everything after and including &lt;/discharge_summary&gt;.

    These are specified in the prompt instructions.
    """
    start = out_str.find(DELIMETERS["start"])
    if start != -1:
        # Strip everything before and including <discharge_summary>
        out_str = out_str[(start + len(DELIMETERS["start"])):]

    end = out_str.rfind(DELIMETERS["end"])
    if end != -1:
        # Strip everything after the last occurrence of </discharge_summary>
        out_str = out_str[:end]

    return out_str
