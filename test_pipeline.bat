@echo off
REM StockMount XML Pipeline Test Script
REM Test için kullanım örnekleri

echo ========================================
echo StockMount XML Pipeline Test
echo ========================================
echo.

REM 1. Tedarikçi yapısını keşfet
echo [1] eBijuteri yapısını keşfet:
echo python discover_supplier.py ^<EBİJUTERİ_LINKİ^> --supplier ebi
echo.

echo [2] TeknoTok yapısını keşfet:
echo python discover_supplier.py ^<TEKNATOK_LINKİ^> --supplier tkt
echo.

REM 2. Küçük test (ilk 5 ürün)
echo [3] Küçük test (ilk 5 ürün):
echo python update_xml.py --out output.xml --limit 5
echo.

REM 3. Tek tedarikçi test
echo [4] Sadece eBijuteri test:
echo python update_xml.py --out output.xml --only ebi --limit 10
echo.

echo [5] Sadece TeknoTok test:
echo python update_xml.py --out output.xml --only tkt --limit 10
echo.

REM 4. Validasyon
echo [6] Çıktıyı doğrula:
echo python validate_output.py output.xml
echo.

pause
