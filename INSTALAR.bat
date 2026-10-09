@echo off
chcp 65001 >nul
title Central da Consultoria - instalação
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
