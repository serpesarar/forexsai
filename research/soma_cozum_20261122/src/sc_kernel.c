/* SC pozisyon motoru — 1m BID barlarında tek pozisyon yolu (sc_sim.py'deki Python referansıyla birebir aynı kurallar).
 *
 * Fiyat: barlar BID; ask = bid + s[j]. Alış ask'tan girer, bid'den çıkar; satış bid'den girer, ask'tan çıkar.
 * Bar j sırası: (1) j > i0 ve t[j] >= t_cik → o[j]'de ZAMAN çıkışı; (2) açılış boşluğu stopun/TP'nin ötesindeyse açılışta çık;
 * (3) bar içinde stop dokunduysa stopta çık (aynı barda TP de dokunsa bile — kötümser); değilse TP dokunduysa TP'de çık;
 * (4) çıkılmadıysa MFE/MAE ve iz süren stop / başabaş bu barın uç fiyatıyla güncellenir, j+1'den geçerli olur.
 * Neden: bar içinde tepe mi dip mi önce geldi bilinmez; güncellemeyi bir sonraki bara ertelemek iyimser sıralamayı dışlar.
 * Nedenler: 0 STOP (ilk stop), 1 TP, 2 IZ (taşınmış stop: iz/başabaş), 3 ZAMAN, 4 SON (veri bitti).
 */
#include <math.h>
#include <stdint.h>

void sc_yol(const int64_t *t, const double *o, const double *h, const double *l, const double *c, const double *s,
            int64_t nbar, int64_t npoz,
            const int64_t *i0, const int32_t *yon, const double *sl_d, const double *tp_d,
            const double *iz_akt, const double *iz_d, const double *be_akt, const double *be_off,
            const int64_t *t_cik, double sk,
            int64_t *j_out, double *px_out, double *giris_out, int32_t *neden_out, double *mfe_out, double *mae_out)
{
    for (int64_t k = 0; k < npoz; k++) {
        int64_t i = i0[k];
        int32_t y = yon[k];
        double E = (y > 0) ? o[i] + sk * s[i] : o[i];
        double S = (y > 0) ? E - sl_d[k] : E + sl_d[k];   /* sl_d = INFINITY → stop yok */
        double T = (y > 0) ? E + tp_d[k] : E - tp_d[k];
        int tasindi = 0;
        double mfe = 0.0, mae = 0.0;
        int64_t j;
        int bitti = 0;
        for (j = i; j < nbar; j++) {
            double sj = sk * s[j];
            double ao = (y > 0) ? o[j] : o[j] + sj;          /* çıkış tarafı fiyatları */
            double ah = (y > 0) ? h[j] : h[j] + sj;
            double al = (y > 0) ? l[j] : l[j] + sj;
            if (j > i && t[j] >= t_cik[k]) { px_out[k] = ao; neden_out[k] = 3; bitti = 1; break; }
            if (y > 0) {
                if (ao <= S) { px_out[k] = ao; neden_out[k] = tasindi ? 2 : 0; bitti = 1; break; }
                if (ao >= T) { px_out[k] = ao; neden_out[k] = 1; bitti = 1; break; }
                if (al <= S) { px_out[k] = S; neden_out[k] = tasindi ? 2 : 0; bitti = 1; break; }
                if (ah >= T) { px_out[k] = T; neden_out[k] = 1; bitti = 1; break; }
                double fav = ah - E, adv = E - al;
                if (fav > mfe) mfe = fav;
                if (adv > mae) mae = adv;
                if (fav >= iz_akt[k]) { double ns = ah - iz_d[k]; if (ns > S) { S = ns; tasindi = 1; } }
                if (fav >= be_akt[k]) { double ns = E + be_off[k]; if (ns > S) { S = ns; tasindi = 1; } }
            } else {
                if (ao >= S) { px_out[k] = ao; neden_out[k] = tasindi ? 2 : 0; bitti = 1; break; }
                if (ao <= T) { px_out[k] = ao; neden_out[k] = 1; bitti = 1; break; }
                if (ah >= S) { px_out[k] = S; neden_out[k] = tasindi ? 2 : 0; bitti = 1; break; }
                if (al <= T) { px_out[k] = T; neden_out[k] = 1; bitti = 1; break; }
                double fav = E - al, adv = ah - E;
                if (fav > mfe) mfe = fav;
                if (adv > mae) mae = adv;
                if (fav >= iz_akt[k]) { double ns = al + iz_d[k]; if (ns < S) { S = ns; tasindi = 1; } }
                if (fav >= be_akt[k]) { double ns = E - be_off[k]; if (ns < S) { S = ns; tasindi = 1; } }
            }
        }
        if (!bitti) { j = nbar - 1; px_out[k] = (y > 0) ? c[j] : c[j] + sk * s[j]; neden_out[k] = 4; }
        j_out[k] = j;
        giris_out[k] = E;
        mfe_out[k] = mfe;
        mae_out[k] = mae;
    }
}
