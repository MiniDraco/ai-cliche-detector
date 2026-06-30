@echo off
REM Local perplexity backend for the AI detector suite (runs on your 3060).
REM Uses the ComfyUI embedded python (already has CUDA torch + transformers) -- no installs.
set PPL_MODEL=gpt2
set PPL_PORT=8770
"D:\AI\ComfyUI_windows_portable\python_embeded\python.exe" "%~dp0perplexity_server.py"
pause
