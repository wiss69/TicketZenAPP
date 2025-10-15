@echo off
REM Build ProofPal.exe avec PyInstaller (onefolder), icône et exclure console
python -m pip install --upgrade pip
pip install -r ..\requirements.txt
python ..\app\assets\icon_png.py
pyinstaller --noconfirm --clean ^
  --name ProofPal ^
  --windowed ^
  --icon ..\app\assets\icon.png ^
  --add-data "..\app\assets;app/assets" ^
  --paths .. ^
  ..\app\main.py
echo.
echo Build termine. Exe dans .\dist\ProofPal\ProofPal.exe
pause
