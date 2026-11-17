// fb_resolve.c — braket çözücü (FB, PROTOCOL.md §1). Fiyatlar BID; ask = bid + spr.
// Uzun: giriş ask(o[start]); SL/TP bid yolunda. Kısa: giriş bid(o[start]); SL/TP ask yolunda.
// Aynı barda SL ve TP → SL (E58). Açılış boşluğu SL ötesindeyse açılıştan dolar.
// Zaman çıkışı: end barının açılışı (uzun bid, kısa ask). end >= n → son kapanış.
#include <stdint.h>

void resolve(int64_t n, const double *o, const double *h, const double *l, const double *c,
             const double *spr, int64_t m, const int32_t *side, const int64_t *start,
             const int64_t *end, const double *sl, const double *tp,
             double *out_entry, double *out_exit, int64_t *out_idx, int32_t *out_reason) {
  for (int64_t k = 0; k < m; k++) {
    int64_t s = start[k], e = end[k];
    if (s >= n) { out_reason[k] = -1; out_entry[k] = 0; out_exit[k] = 0; out_idx[k] = n - 1; continue; }
    double S = sl[k], T = tp[k];
    int lg = side[k] > 0;
    double entry = lg ? o[s] + spr[s] : o[s];
    out_entry[k] = entry;
    int done = 0;
    int64_t lim = e < n ? e : n;
    for (int64_t i = s; i < lim; i++) {
      if (lg) {
        if (i > s && o[i] <= S) { out_exit[k] = o[i]; out_idx[k] = i; out_reason[k] = 0; done = 1; break; }
        if (i > s && o[i] >= T) { out_exit[k] = o[i]; out_idx[k] = i; out_reason[k] = 1; done = 1; break; }
        if (l[i] <= S) { out_exit[k] = S; out_idx[k] = i; out_reason[k] = 0; done = 1; break; }
        if (h[i] >= T) { out_exit[k] = T; out_idx[k] = i; out_reason[k] = 1; done = 1; break; }
      } else {
        double ao = o[i] + spr[i];
        if (i > s && ao >= S) { out_exit[k] = ao; out_idx[k] = i; out_reason[k] = 0; done = 1; break; }
        if (i > s && ao <= T) { out_exit[k] = ao; out_idx[k] = i; out_reason[k] = 1; done = 1; break; }
        if (h[i] + spr[i] >= S) { out_exit[k] = S; out_idx[k] = i; out_reason[k] = 0; done = 1; break; }
        if (l[i] + spr[i] <= T) { out_exit[k] = T; out_idx[k] = i; out_reason[k] = 1; done = 1; break; }
      }
    }
    if (!done) {
      if (e < n) { out_exit[k] = lg ? o[e] : o[e] + spr[e]; out_idx[k] = e; }
      else { out_exit[k] = lg ? c[n - 1] : c[n - 1] + spr[n - 1]; out_idx[k] = n - 1; }
      out_reason[k] = 2;
    }
  }
}

// Tek pozisyon: giriş sırasına göre açgözlü; önceki işlemin çıkış indeksinden önce girenler atlanır.
void single_pos(int64_t m, const int64_t *start, const int64_t *exit_idx, int32_t *keep) {
  int64_t busy = -1;
  for (int64_t k = 0; k < m; k++) {
    if (start[k] > busy) { keep[k] = 1; busy = exit_idx[k]; } else keep[k] = 0;
  }
}
