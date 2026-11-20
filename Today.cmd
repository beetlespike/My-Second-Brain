@echo off
setlocal
pushd "%~dp0" || exit /b 1
where py >nul 2>nul
if errorlevel 1 (
    python -B .flashcards\review.py today %*
) else (
    py -3 -B .flashcards\review.py today %*
)
set "review_exit=%errorlevel%"
popd
if not "%review_exit%"=="0" if "%~1"=="" pause
exit /b %review_exit%
