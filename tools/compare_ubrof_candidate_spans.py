"""跨库启发式候选区间的有界比较；不解释 UBROF 记录语义。"""

def compare_candidate_spans(a, a_start, a_limit, b, b_start, b_limit, cap=65536):
    """返回字节观察及截断原因；候选区间不是已验证的模块边界。"""
    if not isinstance(cap, int) or cap <= 0:
        raise ValueError("cap must be positive")
    if not (0 <= a_start <= a_limit <= len(a)):
        raise ValueError("invalid left span")
    if not (0 <= b_start <= b_limit <= len(b)):
        raise ValueError("invalid right span")
    n = min(a_limit - a_start, b_limit - b_start, cap)
    first = next((i for i in range(n) if a[a_start+i] != b[b_start+i]), None)
    common = n if first is None else first
    span_end = first is None and (a_start+n == a_limit or b_start+n == b_limit)
    cap_hit = first is None and n == cap
    return {
        "compared_bytes": n, "common_bytes": common,
        "first_difference_offset": first, "divergence_observed": first is not None,
        "hit_comparison_cap": cap_hit,
        "hit_candidate_span_end": span_end,
        "left_span_ended": first is None and a_start+n == a_limit,
        "right_span_ended": first is None and b_start+n == b_limit,
        "equality_beyond_window_unknown": first is None and
            a_start+n < a_limit and b_start+n < b_limit,
        "candidate_boundaries_verified": False,
        "record_semantics_verified": False,
        "executable_conversion": False,
    }
