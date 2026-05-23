"""Root launcher for Streamlit.

Run with ``streamlit run app.py``.
앱 본체는 ``saju_app.app:main`` → ``saju_app.ui.steps.router`` 로 위임됩니다.
"""

from saju_app.app import main

main()
