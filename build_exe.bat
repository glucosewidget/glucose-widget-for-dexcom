@echo off
rem GlucoseWidgetForDexcom.exe をビルドする（初回のみ。Python が必要）
cd /d "%~dp0"
echo [1/2] 必要なライブラリをインストール中...
py -m pip install -q -r requirements.txt pyinstaller || goto :err
echo [2/2] exe をビルド中...（1～2分かかります）
py -m PyInstaller --noconfirm --clean --onefile --noconsole ^
  --name GlucoseWidgetForDexcom --icon icon.ico --version-file version_info.txt ^
  --hidden-import pystray._win32 --add-data "icon.ico;." ^
  --collect-submodules keyring.backends --copy-metadata keyring ^
  glucose_widget.py || goto :err
copy /y dist\GlucoseWidgetForDexcom.exe . >nul
rmdir /s /q build dist >nul 2>&1
del /q GlucoseWidgetForDexcom.spec >nul 2>&1
echo.
echo 完成: %~dp0GlucoseWidgetForDexcom.exe
echo このexeは単体で動きます。好きな場所に移動してOKです。
pause
exit /b 0
:err
echo.
echo ビルドに失敗しました。上のエラーを確認してください。
pause
exit /b 1
