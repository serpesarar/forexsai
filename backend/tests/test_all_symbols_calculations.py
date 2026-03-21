"""
Tüm Sembol Hesaplama Kontrol Testleri
NDX.INDX, GDAXI.INDX, XAUUSD, CL.F için pip/TP/SL hesaplamalarını doğrular
"""
import pytest
import sys
sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/backend")

from services.target_config import (
    get_symbol_config,
    calculate_target_prices,
    calculate_stoploss_price,
    pips_from_price_change,
    SYMBOL_CONFIGS,
)


class TestNDXCalculations:
    """NASDAQ-100 (NDX.INDX) hesaplama testleri"""

    def test_config(self):
        config = get_symbol_config("NDX.INDX")
        assert config.pip_value == 1.0
        assert config.is_percentage == False
        assert config.stoploss_pips == 50
        
        targets = [t.pips for t in config.targets]
        assert targets == [15, 25, 35, 50]

    def test_buy_target_prices(self):
        """BUY sinyali için TP fiyatları doğru hesaplanıyor mu?"""
        entry = 25000.0
        targets = calculate_target_prices(entry, "BUY", "NDX.INDX")
        
        # 1 pip = 1 point
        assert targets["TP1"] == 25015.0  # +15 pips
        assert targets["TP2"] == 25025.0  # +25 pips
        assert targets["TP3"] == 25035.0  # +35 pips
        assert targets["TP4"] == 25050.0  # +50 pips

    def test_sell_target_prices(self):
        """SELL sinyali için TP fiyatları doğru hesaplanıyor mu?"""
        entry = 25000.0
        targets = calculate_target_prices(entry, "SELL", "NDX.INDX")
        
        assert targets["TP1"] == 24985.0  # -15 pips
        assert targets["TP2"] == 24975.0  # -25 pips
        assert targets["TP3"] == 24965.0  # -35 pips
        assert targets["TP4"] == 24950.0  # -50 pips

    def test_buy_stoploss(self):
        """BUY sinyali için SL fiyatı doğru hesaplanıyor mu?"""
        entry = 25000.0
        sl = calculate_stoploss_price(entry, "BUY", "NDX.INDX")
        assert sl == 24950.0  # -50 pips

    def test_sell_stoploss(self):
        """SELL sinyali için SL fiyatı doğru hesaplanıyor mu?"""
        entry = 25000.0
        sl = calculate_stoploss_price(entry, "SELL", "NDX.INDX")
        assert sl == 25050.0  # +50 pips

    def test_pips_from_price_change(self):
        """Fiyat değişiminden pip hesaplaması doğru mu?"""
        # 50 point yükseliş = 50 pips
        assert pips_from_price_change(50.0, "NDX.INDX") == 50.0
        # 25 point düşüş = -25 pips
        assert pips_from_price_change(-25.0, "NDX.INDX") == -25.0


class TestGDAXICalculations:
    """DAX (GDAXI.INDX) hesaplama testleri - NDX ile aynı"""

    def test_config(self):
        config = get_symbol_config("GDAXI.INDX")
        assert config.pip_value == 1.0
        assert config.is_percentage == False
        assert config.stoploss_pips == 50

    def test_buy_target_prices(self):
        entry = 18000.0
        targets = calculate_target_prices(entry, "BUY", "GDAXI.INDX")
        
        assert targets["TP1"] == 18015.0
        assert targets["TP2"] == 18025.0
        assert targets["TP3"] == 18035.0
        assert targets["TP4"] == 18050.0

    def test_buy_stoploss(self):
        entry = 18000.0
        sl = calculate_stoploss_price(entry, "BUY", "GDAXI.INDX")
        assert sl == 17950.0


class TestXAUUSDCalculations:
    """XAUUSD (Altın) hesaplama testleri"""

    def test_config(self):
        config = get_symbol_config("XAUUSD")
        assert config.pip_value == 1.0  # 1 pip = $1.00
        assert config.is_percentage == False
        assert config.stoploss_pips == 15  # $8

    def test_buy_target_prices(self):
        """BUY sinyali için TP fiyatları doğru hesaplanıyor mu?"""
        entry = 2900.00
        targets = calculate_target_prices(entry, "BUY", "XAUUSD")
        
        # 1 pip = $1.00
        assert targets["TP1"] == 2908.00  # +4 pips = +$4
        assert targets["TP2"] == 2915.00  # +7 pips = +$7
        assert targets["TP3"] == 2925.00  # +10 pips = +$10
        assert targets["TP4"] == 2940.00  # +17 pips = +$17

    def test_sell_target_prices(self):
        """SELL sinyali için TP fiyatları doğru hesaplanıyor mu?"""
        entry = 2900.00
        targets = calculate_target_prices(entry, "SELL", "XAUUSD")
        
        assert targets["TP1"] == 2892.00  # -4 pips = -$4
        assert targets["TP2"] == 2885.00  # -7 pips = -$7
        assert targets["TP3"] == 2875.00  # -10 pips = -$10
        assert targets["TP4"] == 2860.00  # -17 pips = -$17

    def test_buy_stoploss(self):
        """BUY sinyali için SL fiyatı doğru hesaplanıyor mu?"""
        entry = 2900.00
        sl = calculate_stoploss_price(entry, "BUY", "XAUUSD")
        assert sl == 2885.00  # -8 pips = -$8

    def test_sell_stoploss(self):
        """SELL sinyali için SL fiyatı doğru hesaplanıyor mu?"""
        entry = 2900.00
        sl = calculate_stoploss_price(entry, "SELL", "XAUUSD")
        assert sl == 2915.00  # +8 pips = +$8

    def test_pips_from_price_change(self):
        """Fiyat değişiminden pip hesaplaması doğru mu?"""
        # $5 yükseliş = 5 pips
        assert pips_from_price_change(5.0, "XAUUSD") == 5.0
        # $0.50 yükseliş = 0.5 pips
        assert pips_from_price_change(0.5, "XAUUSD") == 0.5
        # $10 düşüş = -10 pips
        assert pips_from_price_change(-10.0, "XAUUSD") == -10.0


class TestCLFCalculations:
    """US Oil (CL.F) hesaplama testleri - Percentage-based"""

    def test_config(self):
        config = get_symbol_config("USOIL.FOREX")
        assert config.pip_value == 1.0  # placeholder
        assert config.is_percentage == True  # Önemli: percentage-based!
        assert config.stoploss_pips == 0.05  # 0.05%

    def test_buy_target_prices(self):
        """BUY sinyali için TP fiyatları doğru hesaplanıyor mu?"""
        entry = 70.00  # $70 varil
        targets = calculate_target_prices(entry, "BUY", "USOIL.FOREX")
        
        # Percentage-based: distance = entry * (pct / 100)
        # TP1: 0.02% of $70 = $0.014
        assert abs(targets["TP1"] - 70.014) < 0.001
        # TP2: 0.04% of $70 = $0.028
        assert abs(targets["TP2"] - 70.028) < 0.001
        # TP4: 0.10% of $70 = $0.07
        assert abs(targets["TP4"] - 70.07) < 0.001

    def test_sell_target_prices(self):
        """SELL sinyali için TP fiyatları doğru hesaplanıyor mu?"""
        entry = 70.00
        targets = calculate_target_prices(entry, "SELL", "USOIL.FOREX")
        
        assert abs(targets["TP1"] - 69.986) < 0.001  # -0.02%
        assert abs(targets["TP4"] - 69.93) < 0.001   # -0.10%

    def test_buy_stoploss(self):
        """BUY sinyali için SL fiyatı doğru hesaplanıyor mu?"""
        entry = 70.00
        sl = calculate_stoploss_price(entry, "BUY", "USOIL.FOREX")
        # 0.05% of $70 = $0.035
        assert abs(sl - 69.965) < 0.001

    def test_pips_from_price_change(self):
        """Percentage-based semboller için pip = price change (raw)"""
        # Percentage-based sembollerde pip = fiyat değişimi (ham değer)
        assert pips_from_price_change(0.5, "USOIL.FOREX") == 0.5
        assert pips_from_price_change(-0.25, "USOIL.FOREX") == -0.25


class TestEdgeCases:
    """Sınır durumları ve hata kontrolleri"""

    def test_unknown_symbol_uses_default(self):
        """Bilinmeyen sembol için default config kullanılıyor mu?"""
        config = get_symbol_config("UNKNOWN")
        assert config.pip_value == 1.0
        assert config.stoploss_pips == 50
        assert config.is_percentage == False

    def test_hold_direction_no_change(self):
        """HOLD yönü için fiyat değişimi olmamalı"""
        entry = 100.0
        targets = calculate_target_prices(entry, "HOLD", "NDX.INDX")
        assert targets["TP1"] == entry
        assert targets["TP2"] == entry

    def test_zero_price_change(self):
        """Sıfır fiyat değişimi"""
        assert pips_from_price_change(0.0, "XAUUSD") == 0.0
        assert pips_from_price_change(0.0, "NDX.INDX") == 0.0

    def test_negative_prices(self):
        """Negatif fiyat değişimleri"""
        assert pips_from_price_change(-5.0, "XAUUSD") == -5.0
        assert pips_from_price_change(-10.0, "NDX.INDX") == -10.0

    def test_small_price_movements_xauusd(self):
        """XAUUSD için küçük fiyat hareketleri (0.1 pip)"""
        # XAUUSD'te 0.1$ hareket = 0.1 pip
        assert pips_from_price_change(0.1, "XAUUSD") == 0.1
        assert pips_from_price_change(0.01, "XAUUSD") == 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
