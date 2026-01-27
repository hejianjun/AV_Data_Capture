# If you can't run this script, please execute the following command in PowerShell.
# Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

$CLOUDSCRAPER_PATH = $( python -c 'import cloudscraper as _; print(_.__path__[0])' | select -Last 1 )
$OPENCC_PATH = $( python -c 'import opencc as _; print(_.__path__[0])' | select -Last 1 )
$FACE_RECOGNITION_MODELS = $( python -c 'import face_recognition_models as _; print(_.__path__[0])' | select -Last 1 )

$Env:PYTHONPATH=$pwd.path
$PYTHONPATH=$pwd.path

mkdir build
mkdir __pycache__


pyinstaller --collect-submodules "mdc.image.imgproc" `
    --collect-data "face_recognition_models" `
    --collect-data "cloudscraper" `
    --collect-data "opencc" `
    --add-data "mdc/image/Img;Img" `
    --add-data "config.ini;." `
    --onefile Movie_Data_Capture.py

rmdir -Recurse -Force build
rmdir -Recurse -Force __pycache__
Remove-Item -Force Movie_Data_Capture.spec

echo "[Make]Finish"
pause
