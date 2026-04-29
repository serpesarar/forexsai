//+------------------------------------------------------------------+
//|  ExportHistoryToCSV.mq5                                          |
//|  XAUUSD + DXY/US10Y/VIX historical bar export for ML retraining  |
//+------------------------------------------------------------------+
//
//  KULLANIM (Windows MT5):
//   1) Bu dosyayı MetaEditor ile aç → F7 (Compile).
//   2) MT5'te bir grafik aç (sembol önemsiz). Navigator → Scripts → ExportHistoryToCSV → çift tıkla.
//   3) Açılan dialog'da YearsBack ve sembolleri ayarla (default 5 yıl).
//   4) CSV'ler şuraya yazılır:
//        <MT5 Data Folder>\MQL5\Files\xauusd_export\
//      File → "Open Data Folder" ile bul, sonra Mac'e zip'le aktar.
//
//  ÇIKTI: bir CSV per (symbol, timeframe). Format:
//        timestamp,open,high,low,close,tick_volume,real_volume,spread
//  timestamp = UTC ISO8601 (broker server time, GMT'e dönüştürülmüş)
//
//  NOT:
//   - Sembol adı brokerine göre değişebilir (USDX, DX-Y.NYB, .DXY, USDOLLAR vb).
//     Yoksa Inputs'ta bırak, script "MarketWatch'ta bulunamadı" diye atlar.
//   - VIX ve US10Y çoğu broker'da yok; sorun değil — sadece XAUUSD bile yeterli başlangıç.
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input int    YearsBack       = 5;
input string XAUUSD_Symbol   = "XAUUSD";
input string DXY_Symbol      = "USDX";        // alternatif: "DX-Y.NYB", ".DXY", "USDOLLAR"
input string US10Y_Symbol    = "US10YT";      // alternatif: "US10Y", "USTNOTE"
input string VIX_Symbol      = "VIX";         // alternatif: "VIXX", "VOLATILITY"
input string OutDir          = "xauusd_export";

string  g_symbols[4];
ENUM_TIMEFRAMES g_xau_tfs[6] = {PERIOD_M5, PERIOD_M15, PERIOD_M30, PERIOD_H1, PERIOD_H4, PERIOD_D1};
ENUM_TIMEFRAMES g_macro_tfs[2] = {PERIOD_H1, PERIOD_D1};

//+------------------------------------------------------------------+
string TfName(ENUM_TIMEFRAMES tf)
  {
   switch(tf)
     {
      case PERIOD_M5:  return "M5";
      case PERIOD_M15: return "M15";
      case PERIOD_M30: return "M30";
      case PERIOD_H1:  return "H1";
      case PERIOD_H4:  return "H4";
      case PERIOD_D1:  return "D1";
     }
   return EnumToString(tf);
  }

//+------------------------------------------------------------------+
string IsoUTC(datetime t)
  {
   MqlDateTime st;
   TimeToStruct(t, st);
   return StringFormat("%04d-%02d-%02dT%02d:%02d:%02dZ",
                       st.year, st.mon, st.day, st.hour, st.min, st.sec);
  }

//+------------------------------------------------------------------+
bool EnsureSymbol(string sym)
  {
   if(sym == "" ) return false;
   if(!SymbolSelect(sym, true))
     {
      PrintFormat("WARN: cannot select symbol %s — atlanıyor", sym);
      return false;
     }
   return true;
  }

//+------------------------------------------------------------------+
int ExportOne(string sym, ENUM_TIMEFRAMES tf, datetime from)
  {
   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   int copied = CopyRates(sym, tf, from, TimeCurrent(), rates);
   if(copied <= 0)
     {
      PrintFormat("  %s/%s : CopyRates=%d  err=%d", sym, TfName(tf), copied, GetLastError());
      return 0;
     }
   string fname = StringFormat("%s/%s_%s.csv", OutDir, sym, TfName(tf));
   int h = FileOpen(fname, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(h == INVALID_HANDLE)
     {
      // FILE_COMMON yoksa lokal MQL5\Files'a yaz
      h = FileOpen(fname, FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
     }
   if(h == INVALID_HANDLE)
     {
      PrintFormat("  %s/%s : FileOpen failed err=%d", sym, TfName(tf), GetLastError());
      return 0;
     }
   FileWrite(h, "timestamp", "open", "high", "low", "close", "tick_volume", "real_volume", "spread");
   for(int i = 0; i < copied; i++)
     {
      FileWrite(h,
                IsoUTC(rates[i].time),
                DoubleToString(rates[i].open,  _Digits),
                DoubleToString(rates[i].high,  _Digits),
                DoubleToString(rates[i].low,   _Digits),
                DoubleToString(rates[i].close, _Digits),
                (long)rates[i].tick_volume,
                (long)rates[i].real_volume,
                (int)rates[i].spread);
     }
   FileClose(h);
   PrintFormat("  %s/%s : %d bars → %s", sym, TfName(tf), copied, fname);
   return copied;
  }

//+------------------------------------------------------------------+
void OnStart()
  {
   datetime from = TimeCurrent() - (datetime)(YearsBack * 365 * 24 * 60 * 60);
   PrintFormat("Export starts: from=%s now=%s outdir=%s",
               TimeToString(from, TIME_DATE|TIME_SECONDS),
               TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
               OutDir);

   // XAUUSD — full TF set
   if(EnsureSymbol(XAUUSD_Symbol))
     {
      Print("--- XAUUSD ---");
      for(int i = 0; i < ArraySize(g_xau_tfs); i++)
         ExportOne(XAUUSD_Symbol, g_xau_tfs[i], from);
     }

   // Macro symbols — H1 + D1 only
   string macros[3];
   macros[0] = DXY_Symbol;
   macros[1] = US10Y_Symbol;
   macros[2] = VIX_Symbol;
   for(int s = 0; s < 3; s++)
     {
      if(!EnsureSymbol(macros[s])) continue;
      PrintFormat("--- %s ---", macros[s]);
      for(int i = 0; i < ArraySize(g_macro_tfs); i++)
         ExportOne(macros[s], g_macro_tfs[i], from);
     }

   Print("DONE. Open Data Folder → MQL5/Files/", OutDir);
  }
//+------------------------------------------------------------------+
