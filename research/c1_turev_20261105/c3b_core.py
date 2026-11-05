import numpy as np
def sim(S, E, entry, exit_fn, sp, fin, maxh):
    tr, i, n = [], 0, len(S)
    while i < n:
        if entry[i]:
            j = exit_fn(i); j = min(j, n - 1)
            if j > i:
                tr.append((i, j, (E[j] / (E[i] + sp) - 1) * 1e4 - fin * (j - i))); i = j; continue
        i += 1
    return tr
