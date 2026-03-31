import traceback
try:
    import app
except Exception as e:
    with open('error_clean.log', 'w', encoding='utf-8') as f:
        f.write(traceback.format_exc())
