# Run LogisticsNow AI Console (frontend + backend)
Set-Location $PSScriptRoot
python -m streamlit run app.py --server.port 8501 --server.headless true
