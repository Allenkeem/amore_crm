import sys
import os
import pytest

# Add backend to sys.path so tests can import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def sample_query():
    return "30대 VIP 고객을 위한 설화수 자음생 크림 겨울 프로모션 문구 작성해줘"
