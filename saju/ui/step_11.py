"""STEP 11 — AI 사주 챗봇 (완성형 · 상담 방 저장소 동기 · STEP12 연동)."""

from __future__ import annotations

import html
import re
import streamlit as st

from saju_app.persistence import storage as saju_storage
from saju_app.ui import analysis_favorite_memo as AFM
from saju_app.ui import components as M
from saju_app.ui import consulting_knowledge as K
from saju_app.ui import webapp_launch as W
from saju_app.ui.chat_messages import (
    dedupe_chat_messages,
    render_conversation_chat_ui,
    tail_matches_assistant,
    tail_matches_user,
)


def _step11_ensure_room_key() -> str:
    rk = str(st.session_state.get("step11_chat_room_key") or "").strip()
    if rk:
        return rk
    if M.step11_admin_preview_mode():
        admin_rk = str(st.session_state.get("admin_selected_room") or "").strip()
        if admin_rk:
            st.session_state.step11_chat_room_key = admin_rk
            return admin_rk
    u_nm = str(st.session_state.get("u_name", "익명") or "익명").strip()
    u_data = st.session_state.get("u_data")
    if isinstance(u_data, (list, tuple)) and len(u_data) >= 3:
        try:
            birth = {
                "year": int(u_data[0]),
                "month": int(u_data[1]),
                "day": int(u_data[2]),
            }
        except (TypeError, ValueError):
            birth = {"year": 1995, "month": 1, "day": 1}
    else:
        birth = {"year": 1995, "month": 1, "day": 1}
    fp = saju_storage.user_profile_fingerprint(display_name=u_nm, birth=birth)
    st.session_state.step11_chat_room_key = f"chat_{fp[:16]}"
    return str(st.session_state.step11_chat_room_key)


def _classify_consultation_type(text: str) -> str:
    """관리자 목록에서 바로 볼 수 있는 상담 카테고리."""
    t = str(text or "")
    if any(k in t for k in ("연애", "결혼", "재회", "속마음", "궁합", "이별", "바람", "외도", "인연", "배우자")):
        return "연애·궁합"
    if any(k in t for k in ("돈", "재물", "금전", "투자", "주식", "사업", "창업", "부동산", "집", "대출")):
        return "재물·사업"
    if any(k in t for k in ("직장", "회사", "이직", "퇴사", "승진", "취업", "진급", "커리어", "상사")):
        return "직장·커리어"
    if any(k in t for k in ("건강", "질병", "수술", "사고", "임신", "출산", "병원", "컨디션")):
        return "건강·임신"
    if any(k in t for k in ("공부", "시험", "합격", "자격증", "성적", "면접")):
        return "공부·시험"
    if any(k in t for k in ("이사", "이동", "이민", "계약", "소송", "법", "관재")):
        return "이동·문서"
    return "일반상담"


def _hydrate_customer_label_from_room(room_key: str) -> dict[str, str]:
    """저장소 라벨에서 고객 표시명·연락처만 세션에 반영(관리자 미리보기)."""
    rk = str(room_key or "").strip()
    out: dict[str, str] = {}
    if not rk:
        return out
    try:
        _, lab = saju_storage.get_shared_chat_room(rk)
    except Exception:
        lab = None
    if not isinstance(lab, dict):
        return out
    nm = str(lab.get("u_name") or "").strip()
    if nm:
        st.session_state.u_name = nm
        out["u_name"] = nm
    contact = str(lab.get("contact") or "").strip()
    if contact:
        st.session_state.contact_value = contact
        out["contact"] = contact
    return out


def _admin_preview_engine_stub() -> dict[str, str]:
    return {
        "day_stem": "—",
        "day_el": "관리자 확인",
        "yongshin": "—",
        "strength": "—",
    }


def _step11_chat_label(u_name: str, consultation_type: str = "미분류") -> dict:
    gapja = st.session_state.get("u_gapja")
    gapja_list = [str(x) for x in gapja] if isinstance(gapja, (list, tuple)) else []
    user_ilju = gapja_list[2] if len(gapja_list) > 2 else ""
    return {
        "u_name": str(u_name or "").strip(),
        "contact": str(st.session_state.get("contact_value") or ""),
        "user_gapja": user_ilju,
        "user_ilju": user_ilju,
        "user_gapja_full": gapja_list,
        "consultation_type": str(consultation_type or "미분류"),
        "ts": M.now_kst().isoformat(timespec="seconds"),
    }


def _is_welcome_seed_message(msg: dict) -> bool:
    """예전 버전에서 DB에 넣어 둔 첫 인사(assistant) — 실제 AI 답변과 구분."""
    if str(msg.get("role") or "") != "assistant":
        return False
    if bool(msg.get("is_manual", False)):
        return False
    body = str(msg.get("msg") or "")
    return "일간의 특성상" in body and "성찰의 시간" in body


def filter_conversation_messages(msgs: list) -> list[dict]:
    """채팅 목록에서 첫 인사 시드만 제외(표시·저장 정리용)."""
    return [
        m
        for m in (msgs or [])
        if isinstance(m, dict) and not _is_welcome_seed_message(m)
    ]




SAJU_PRO_MASTER_RULES: dict[str, dict[str, object]] = {
    "love_and_marriage": {
        "title": "연애 / 결혼 / 외도 / 이별 / 궁합",
        "keywords": ("연애", "결혼", "궁합", "이별", "외도", "바람", "인연", "남자", "여자", "배우자"),
        "rules": (
            "여성은 관성운(정관·편관), 남성은 재성운(정재·편재)에 인연·결혼운이 강하게 발동합니다.",
            "편관/편재 인연은 초반 끌림이 강하지만 피로·구속감이 생기기 쉽고, 정관/정재 인연은 처음은 심심해도 안정감이 깊어집니다.",
            "대운에서 본인의 일간과 합이 되는 흐름은 천생연분을 만나는 중요한 적기로 봅니다.",
            "생(生)을 받는 쪽은 사랑을 확인받고 주도권을 잡으려 하며, 생하는 쪽은 배려와 헌신이 깊어집니다.",
            "일간 상생 + 일지 합은 몸과 마음이 맞는 최상급 궁합, 일간 극 + 일지 합은 싸우면서도 정으로 묶이는 궁합입니다.",
            "일주와 세운이 형·극·충을 이루거나, 여성은 식상운·남성은 인성/관성운이 강해질 때 이별 압력이 커집니다.",
            "원국 지지의 자·오·묘·유 도화가 많고 암합이 숨어 있으면 외부 인연·외도성 유혹을 경계해야 합니다.",
        ),
    },
    "wealth_and_business": {
        "title": "재물 / 주택 / 사업 / 투자 / 손실",
        "keywords": ("돈", "재물", "금전", "사업", "투자", "주식", "부동산", "주택", "손실", "창업"),
        "rules": (
            "편재운은 횡재·상속·큰돈·투기성 기회가 열리기 쉽고, 정재운은 급여·연금·예적금처럼 안정 자산에 강합니다.",
            "인성운에 대운의 재성·관성이 받쳐 주면 문서·주택 취득이 쉬우며, 식상이 함께 움직이면 고가 부동산까지 노릴 수 있습니다.",
            "식신생재 흐름은 개인 기술 기반 소규모 창업에 맞고, 동업은 금물입니다.",
            "식신·재성·관성운이 고르게 오고 일주가 신강하면 직원을 둔 프랜차이즈형 사업도 가능합니다.",
            "신강 사주는 비겁운에도 경쟁을 버티지만, 신약 사주는 평생 무리한 투자를 피하고 수비적으로 자산을 관리해야 합니다.",
            "겁재운은 손재수와 치료비·사고 지출이 커질 수 있어 현금성 자산을 예금·보험으로 묶어 두는 방어가 필요합니다.",
        ),
    },
    "education_and_exam": {
        "title": "공부 / 시험",
        "keywords": ("공부", "시험", "합격", "성적", "자격증", "수능", "면접"),
        "rules": (
            "인수운은 공부운이지만 원국 인성이 약하거나 지지충이 심하면 산만해져 집중력이 흔들립니다.",
            "인성이 과다하면 나태와 잡생각이 늘 수 있으므로 강도 높은 운동을 병행해야 공부가 살아납니다.",
            "식상이 강하면 재능은 많지만 집중이 분산되므로 행동 교정과 루틴 훈련이 우선입니다.",
            "재성이 강하면 계산·실무는 좋지만 독해·입체 이해가 약해질 수 있어 독서량을 늘려야 합니다.",
            "시험 당일은 일운이 중요합니다. 인수일은 점수 상승, 편관일은 압박·실수, 식상일은 아는 문제 실수에 주의합니다.",
        ),
    },
    "career_and_job": {
        "title": "직장 / 진급 / 이직",
        "keywords": ("직장", "회사", "취업", "진급", "승진", "이직", "퇴사", "스카우트", "공무원"),
        "rules": (
            "지지에 재성·관성·인성이 유기적으로 상생하고 천간에 비겁이 하나쯤 있으면 조직·대기업·공직에 맞습니다.",
            "지지 역마나 지지충이 강하고 천간 비겁이 약하면 구속을 싫어하는 자유 전문직형으로 봅니다.",
            "편관운의 진급은 발탁·파격 승진, 정관운의 진급은 매뉴얼과 순서에 따른 안정 승진입니다.",
            "관성을 극하는 식상운이 강하면 이직 욕구가 커지고, 식상생재가 되면 내 일을 하고 싶은 마음이 강해집니다.",
            "신약 사주에서 세운이 일지를 강하게 충하면 본인 의지와 무관한 강제 이직·부서 변화가 생길 수 있습니다.",
        ),
    },
    "health_and_surgery": {
        "title": "건강 / 수술 / 사고 / 이사",
        "keywords": (
            "건강",
            "수술",
            "사고",
            "질병",
            "이사",
            "교통",
            "관재",
            "삼살",
        ),
        "rules": (
            "신강 사주는 체력이 있어 중장년 이후 질병이 드러나기 쉽고, 신약 사주는 유년·청소년기부터 잔병치레에 예민합니다.",
            "목은 간·담·눈, 화는 심장·혈압·혈관, 토는 위장·소화기, 금은 폐·대장·비염, 수는 신장·방광·귀를 봅니다.",
            "사·묘·절지와 재살이 겹치거나 인·사·신 삼형이 완성될 때는 수술·칼 대는 일을 조심합니다.",
            "인신충은 역마 충돌로 교통사고 주의, 인·사·신 삼형은 사고와 관재구설을 함께 부를 수 있습니다.",
            "일주와 세운 지지가 충하면 이동수가 강해 이사 가능성이 크며, 삼살방은 피하고 재방·식상방·인수방을 길방으로 봅니다.",
        ),
    },
}


SAJU_STORYTELLING_DATABASE: dict[str, dict[str, str]] = {
    "love_and_marriage": {
        "여성_편관운_만남": "현재 들어온 편관운은 불꽃같은 설렘을 주는 시기랍니다. 첫눈에 '내 남자다!' 하고 매료되어 소개를 받거나 만나게 되죠. 하지만 조심하셔야 해요. 이 기운은 시간이 흐를수록 나를 구속하는 느낌이나 스트레스로 변해 상대가 미워질 수 있으니 초기 감정에 너무 휩쓸리지 마세요.",
        "여성_정관운_만남": "지금 들어온 정관운은 첫 만남엔 다소 답답하고 어설퍼 보일 수 있어요. '내 스타일이 아닌가?' 싶겠지만, 이 인연은 함께 시간을 보낼수록 진국이라는 걸 알게 되고 깊은 신뢰와 안정감을 주는 다정한 관계로 발전하게 되니 진득하게 지켜보세요.",
        "남성_편재운_만남": "현재 편재운이 강하게 들어와 눈이 번쩍 뜨일 만큼 압도적인 매력을 가진 여성에게 매료되는 시기입니다. 쟁취하고 싶은 욕구가 강하게 일어나겠지만, 연애가 길어질수록 본인의 정신적·신체적 에너지 소모가 심해져 피로감을 느낄 수 있으니 페이스 조절이 필요합니다.",
        "남성_정재운_만남": "정재운이 들어오면 수수하고 온순한 스타일의 인연이 다가옵니다. 짜릿한 재미는 덜할지 몰라도, 늘 내 편이 되어주는 안도감과 다정함을 주는 편안한 동반자이니 화려함보다는 내실을 보셔야 합니다.",
        "연애_주도권": "명리학에서 연애의 주도권은 '생(生)을 받는 쪽'이 쥐게 된답니다. 사랑을 끊임없이 확인받으려 하죠. 반대로 '생(生)을 하는 쪽'은 상대를 향한 배려와 헌신이 깊어 뒤에서 묵묵히 챙겨주는 역할을 자처하게 됩니다.",
        "일간_합": "두 분은 일간이 합(合)을 이루는 흐름을 타고 있네요. 이 기운이 발동하면 이성적인 판단을 떠나 서로를 향한 마음이 애절하고 간절해집니다. 떨어져 있으면 괜히 마음이 쓰이고 다시 끌리는 천생연분의 신호랍니다.",
        "결혼_대운": "10년 대운에서 일간과 합이 되는 흐름은 인생에서 내 영혼의 짝을 만나 가정을 꾸릴 수 있는 최고의 타이밍으로 봅니다. 이때는 가볍게 스쳐 가는 인연보다 오래 갈 사람을 보는 눈이 중요합니다.",
        "결혼_년운_여성": "올해 세운에서 관성운이 들어오면 여성에게는 공식적인 배우자의 기운이 문을 두드리는 해입니다. 감정만 보는 연애보다 관계를 구체화하고 결혼을 현실로 만드는 쪽에 힘이 실립니다.",
        "결혼_년운_남성": "올해 세운에서 재성운이 들어오는 것은 남성에게 가정을 이루고 안정을 찾으라는 신호입니다. 책임질 사람, 함께 생활을 만들 사람을 만나기 쉬운 결혼의 적기랍니다.",
        "외도_암합_도화": "주의 깊게 보셔야 할 부분이 있습니다. 지지에 숨은 암합이나 자·오·묘·유 도화가 강하게 움직일 때는 마음이 흔들리는 기운이 생깁니다. 이 시기에는 관계 밖의 설렘보다 지금 관계 안의 균열을 먼저 봐야 합니다.",
        "궁합_천생연분": "일간이 서로 상생하면서 일지까지 합을 이루면 몸과 마음, 생활 리듬까지 잘 맞는 최고의 천생연분 궁합으로 봅니다. 서로가 서로의 부족한 부분을 자연스럽게 채워주는 관계죠.",
        "궁합_동반자": "일간은 상생하고 일지는 비화 흐름이면 불타는 자극보다는 친구처럼 대화가 잘 통하고 평생 의지할 수 있는 안정적인 동반자 스타일입니다.",
        "궁합_애틋함": "일간은 비화인데 일지가 합을 이루면 성격이나 가치관은 비슷하면서도 서로를 향한 정과 끌림이 깊습니다. 쉽게 끊어지지 않는 애틋한 관계로 봅니다.",
        "궁합_미운정": "일간이 극을 하는데 일지가 합을 이루면 성격 차이로 투덕거리며 자주 싸우면서도, 뒤돌아서면 마음이 풀리는 미운 정 고운 정의 인연입니다.",
        "이별_운": "일주와 일년운이 형·극·충으로 강하게 부딪히는 해에는 이별수가 따릅니다. 여성은 식상운에 상대의 단점이 크게 보이고, 남성은 인수·관성운에 인연의 끈이 약해지기 쉬우니 말을 세게 꺼내기 전 한 번 더 멈춰야 합니다.",
    },
    "wealth_and_career": {
        "식상생재_재물": "본인의 특별한 기술이나 재능이 곧 돈이 되는 식상생재의 흐름입니다. 가만히 앉아 있기보다는 내 창작물이나 전문성을 세상에 선보일 때 재물이 따라붙습니다.",
        "군겁쟁재_주의": "올해는 비겁운이 강하게 들어오는 흐름입니다. 명리에서는 이를 군겁쟁재라 하여 내 재물을 노리는 무리가 주변에 많아지는 시기로 봅니다. 이 시기에는 지인과의 돈 거래나 동업은 정말 조심하셔야 합니다.",
        "상관견관_퇴사주의": "직장운에서 상관견관의 흐름이 보입니다. 윗사람이나 조직의 틀이 숨 막히게 답답하고, 홧김에 사표를 던지고 싶은 충동이 강하게 올라올 수 있습니다. 지금은 감정으로 결정하지 말고 운이 지나갈 때까지 버티는 지혜가 필요합니다.",
    },
}


def _is_female_gender(gender: str) -> bool:
    return any(token in str(gender or "") for token in ("여", "女", "F", "f"))


def _pick_storytelling_advice(
    user_text: str,
    *,
    gender: str,
    daewoon_ten: str,
) -> tuple[str, str] | None:
    """질문에 가장 가까운 스토리텔링 답변 1개만 고릅니다."""
    text = str(user_text or "")
    is_female = _is_female_gender(gender)
    love = SAJU_STORYTELLING_DATABASE["love_and_marriage"]
    wealth = SAJU_STORYTELLING_DATABASE["wealth_and_career"]

    if any(k in text for k in ("외도", "바람", "불륜")):
        return "연애 / 외도", love["외도_암합_도화"]
    if any(k in text for k in ("이별", "헤어", "재회")):
        return "연애 / 이별", love["이별_운"]
    if "궁합" in text:
        if any(k in text for k in ("친구", "편안", "안정")):
            return "궁합", love["궁합_동반자"]
        if any(k in text for k in ("싸", "다툼", "성격차", "미운")):
            return "궁합", love["궁합_미운정"]
        if any(k in text for k in ("애틋", "끌림", "속궁합")):
            return "궁합", love["궁합_애틋함"]
        return "궁합", love["궁합_천생연분"]
    if any(k in text for k in ("결혼", "배우자", "혼인")):
        if "대운" in text:
            return "결혼 시기", love["결혼_대운"]
        return ("결혼 시기", love["결혼_년운_여성" if is_female else "결혼_년운_남성"])
    if any(k in text for k in ("소개", "만남", "남자", "여자", "인연", "연애")):
        if any(k in text for k in ("주도권", "누가", "헌신", "사랑 확인")):
            return "연애 심리", love["연애_주도권"]
        if any(k in text for k in ("합", "끌림", "천생")):
            return "연애 합", love["일간_합"]
        if is_female:
            key = "여성_정관운_만남" if "정관" in str(daewoon_ten) else "여성_편관운_만남"
        else:
            key = "남성_정재운_만남" if "정재" in str(daewoon_ten) else "남성_편재운_만남"
        return "새 인연", love[key]
    if any(k in text for k in ("퇴사", "상사", "윗사람", "직장", "회사")):
        return "직장 / 퇴사", wealth["상관견관_퇴사주의"]
    if any(k in text for k in ("동업", "돈거래", "빌려", "비겁", "겁재", "손실")):
        return "재물 손실", wealth["군겁쟁재_주의"]
    if any(k in text for k in ("돈", "재물", "사업", "창업", "투자", "수익")):
        return "재물 / 사업", wealth["식상생재_재물"]
    if any(
        k in text
        for k in ("부모", "어머니", "아버지", "모시", "요양", "병원", "아픈", "아프", "간병", "입원")
    ):
        return (
            "가족 건강·거처",
            "부모님·가족 건강과 어디로 모실지는 사주로 병명·병원을 단정하지 않습니다. "
            "먼저 주치의·응급 여부를 확인하고, 전문 진료 접근성·간병 동선·수면·식사 환경을 "
            "기준으로 자택 간병·요양·병원 인근 거주를 비교하세요. "
            "무리한 이사보다 의료진 상담 후 가족 돌봄 여력에 맞는 선택이 우선입니다.",
        )
    return None


def _is_family_health_care_question(user_text: str) -> bool:
    """부모·가족 건강·어디로 모실지 등 돌봄·거처 질문."""
    t = str(user_text or "")
    if not any(k in t for k in ("부모", "어머니", "아버지", "모시", "요양", "간병", "돌봄")):
        if not ("아픈" in t or "아프" in t) or "부모" not in t and "어머니" not in t and "아버지" not in t:
            if "어디" not in t and "모시" not in t:
                return False
    return any(
        k in t
        for k in (
            "아픈",
            "아프",
            "병",
            "병원",
            "입원",
            "어디",
            "모시",
            "요양",
            "간병",
            "돌봄",
            "쾌유",
        )
    )


def _final_judgment_line(*, user_text: str, score: int, yongshin: str) -> str:
    """질문 맥락에 맞는 한 줄 정리(대운 점수만으로 '준비·정비' 고정하지 않음)."""
    ut = str(user_text or "")
    ys = html.escape(str(yongshin or "균형"))
    if _is_family_health_care_question(ut):
        return (
            "의료진·응급 여부를 먼저 확인하고, 가족 돌봄 여력에 맞게 "
            "<b>자택 간병 · 요양 · 병원 인근</b>을 비교하세요. "
            "무리한 이사·큰 결정은 컨디션이 안정된 뒤 검토하는 편이 낫습니다."
        )
    if any(k in ut for k in ("돈", "재물", "사업", "투자", "창업")):
        if score >= 70:
            return "수익·계약은 밀어붙일 만하나, 지인 돈거래·충동 지출은 피하세요."
        return "당장 큰 승부보다 현금 흐름·계약 조건을 먼저 정리하는 구간입니다."
    if any(k in ut for k in ("연애", "결혼", "인연", "궁합", "이별")):
        return "감정만으로 단정하기보다 상대의 생활 태도·약속·스트레스 반응을 2~3주 더 지켜보세요."
    if any(k in ut for k in ("직장", "이직", "퇴사", "승진", "취업")):
        return "감정적 퇴사보다 다음 조건·생활비·역할을 먼저 적어 보고 결정하세요."
    if score >= 75:
        return f"기회가 열리는 시기입니다. 다만 용신 <b>{ys}</b>이 살아나는 환경·사람·속도를 맞추면 체감이 좋아집니다."
    if score >= 55:
        return (
            f"속도를 맞추고 방향을 다듬는 시기입니다(체감 {score}점). "
            f"무리한 확장보다 용신 <b>{ys}</b>에 맞는 루틴·환경 정리가 먼저입니다."
        )
    return (
        f"지금은 크게 벌리기보다 기반·컨디션·관계를 다지는 편이 유리합니다(체감 {score}점). "
        f"급한 결정은 줄이고 용신 <b>{ys}</b>을 살리는 생활 리듬부터 잡으세요."
    )


def _matched_master_rule_keys(user_text: str) -> list[str]:
    text = str(user_text or "")
    matched: list[str] = []
    for key, data in SAJU_PRO_MASTER_RULES.items():
        keywords = tuple(data.get("keywords", ())) if isinstance(data, dict) else ()
        if any(str(k) and str(k) in text for k in keywords):
            matched.append(key)
    return matched[:2]


def _master_guidance_html(user_text: str, *, strength: str, yongshin: str) -> str:
    """질문과 맞는 경우에만 짧게 1~2줄. 가족 건강·돌봄 질문에는 목록 통째로 붙이지 않음."""
    if _is_family_health_care_question(user_text):
        return ""
    keys = [k for k in _matched_master_rule_keys(user_text) if k in SAJU_PRO_MASTER_RULES]
    if not keys:
        return ""
    blocks: list[str] = []
    for key in keys[:1]:
        data = SAJU_PRO_MASTER_RULES[key]
        title = html.escape(str(data.get("title", key)))
        rules = tuple(data.get("rules", ()))[:2]
        lis = "".join(f"<li>{html.escape(str(rule))}</li>" for rule in rules)
        blocks.append(f"<b>📚 참고 지침 · {title}</b><ul>{lis}</ul>")
    strength_line = (
        "신강 구조이므로 기회가 올 때 밀고 나가는 힘을 쓰되, 과욕은 경계하세요."
        if "신강" in str(strength)
        else "신약 구조이므로 큰 승부보다 환경·사람·타이밍을 빌리는 전략이 우선입니다."
    )
    return (
        "<br><br>"
        + "".join(blocks)
        + f"<br>🔑 <b>적용 원칙:</b> {html.escape(str(strength_line))} "
        + f"용신 <b>{html.escape(str(yongshin))}</b> 기운을 생활·선택·타이밍의 기준으로 잡으세요."
    )


def _storytelling_guidance_html(
    user_text: str,
    *,
    gender: str,
    daewoon_ten: str,
    strength: str,
    yongshin: str,
) -> str:
    picked = _pick_storytelling_advice(
        user_text,
        gender=gender,
        daewoon_ten=daewoon_ten,
    )
    if not picked:
        return ""
    title, advice = picked
    strength_line = (
        "신강한 분은 이 흐름이 왔을 때 직접 선택하고 밀어붙이는 힘이 살아납니다."
        if "신강" in str(strength)
        else "신약한 분은 혼자 힘으로 밀어붙이기보다 사람·환경·타이밍을 빌려야 운이 편하게 열립니다."
    )
    return (
        "<br><br>"
        f"<b>📚 사주까기 족집게 상담 · {html.escape(str(title))}</b><br>"
        f"{html.escape(str(advice))}<br><br>"
        f"🔑 <b>적용 포인트:</b> {html.escape(str(strength_line))} "
        f"지금은 용신 <b>{html.escape(str(yongshin))}</b> 기운을 기준으로 선택하셔야 합니다."
    )


def _pull_step11_chat_from_storage(room_key: str) -> None:
    """저장소(SAJU 공유 방)의 최신 채팅을 세션·화면에 반영합니다. 관리자 답변 수신용."""
    rk = str(room_key or "").strip()
    if not rk:
        return
    try:
        M.sync_shared_chat_room_into_session(rk)
    except Exception:
        pass


def _clear_step11_chat_history(room_key: str, label: dict | None = None) -> None:
    """세션·저장소의 이전 상담 메시지를 비웁니다."""
    rk = str(room_key or "").strip()
    if not rk:
        return
    try:
        saju_storage.clear_shared_chat_room(rk)
    except Exception:
        pass
    st.session_state.shared_chat = []
    if isinstance(label, dict):
        M._persist_shared_chat_bus(rk, [], label)


def _clear_step11_chat_on_new_browser_session(room_key: str, label: dict) -> None:
    """브라우저 새로고침·탭 재진입 시(세션 키 초기화) 상담 기록 삭제."""
    if st.session_state.get("step11_chat_session_armed"):
        return
    _clear_step11_chat_history(room_key, label)
    st.session_state.step11_chat_session_armed = True


def _delete_current_user_data(room_key: str, u_name: str) -> None:
    """사용자 요청 시 현재 상담 방·세션 아카이브·프로필 키를 가능한 범위에서 삭제."""
    _clear_step11_chat_history(room_key, None)
    try:
        saju_storage.archive_delete_session(M.ensure_session_id())
    except Exception:
        pass
    u_data = st.session_state.get("u_data")
    if isinstance(u_data, (list, tuple)) and len(u_data) >= 3:
        try:
            birth = {
                "year": int(u_data[0]),
                "month": int(u_data[1]),
                "day": int(u_data[2]),
                "time_str": str(u_data[3]) if len(u_data) > 3 else "",
                "lunar": bool(u_data[4]) if len(u_data) > 4 else False,
                "leap_month": bool(u_data[5]) if len(u_data) > 5 else False,
            }
            fp = saju_storage.user_profile_fingerprint(display_name=str(u_name or ""), birth=birth)
            saju_storage.delete_user_profile(fp)
        except Exception:
            pass


def _strip_legacy_welcome_from_room(room_key: str) -> None:
    """DB에 남아 있는 예전 첫 인사 메시지를 한 번 제거합니다."""
    rk = str(room_key or "").strip()
    if not rk:
        return
    try:
        raw, lab = saju_storage.get_shared_chat_room(rk)
    except Exception:
        return
    msgs = list(raw or [])
    kept = filter_conversation_messages(msgs)
    if len(kept) == len(msgs):
        return
    M._persist_shared_chat_bus(rk, kept, lab)


def _family_health_care_reply_html(
    user_text: str,
    *,
    yongshin: str,
    gender: str,
    daewoon_ten: str,
    strength: str,
    phase: str,
    score: int,
) -> str:
    """부모·가족 건강·거처 질문 전용 — 수술·교통사고 등 무관 지침 목록 제외."""
    ut = str(user_text or "")
    ys = html.escape(str(yongshin or "균형"))
    q_line = html.escape(ut[:120] + ("…" if len(ut) > 120 else ""))
    picked = _pick_storytelling_advice(ut, gender=gender, daewoon_ten=daewoon_ten)
    if picked:
        _title, advice = picked
        body = (
            f"<b>📚 사주까기 상담 · {html.escape(str(_title))}</b><br>"
            f"{html.escape(str(advice))}"
        )
    else:
        body = (
            "사주로 병명·병원·수술 시기를 단정하지 않습니다. "
            "먼저 주치의·응급 여부를 확인하고, <b>진료 접근성 · 간병 동선 · 수면·식사 환경</b>을 "
            "기준으로 <b>자택 간병 · 요양시설 · 병원 인근 거주</b>를 비교하세요."
        )
    final_line = _final_judgment_line(user_text=ut, score=score, yongshin=yongshin)
    ph = html.escape(phase)
    return (
        f"💬 <b>질문:</b> {q_line}<br><br>"
        f"{body}<br><br>"
        f"🎯 <b>정리:</b> {final_line}<br><br>"
        f"<i>📊 참고: 지금 대운 흐름은 {ph} (체감 {score}점)입니다. "
        f"급한 이사·큰 환경 변화는 의료·돌봄이 안정된 뒤 검토하세요. "
        f"용신 <b>{ys}</b>이 편한 조용한 환경·동선을 우선하세요.</i><br>"
        f"<i>※ 건강·치료 판단은 반드시 의료진 상담이 우선입니다.</i>"
    )


def generate_saju_reply_master_html(
    user_text: str,
    *,
    engine: dict,
    day_stem: str,
    day_el: str,
    yongshin: str,
    strength: str,
    gender: str = "남자",
) -> str:
    """챗봇에 주입한 마스터 지침·스토리텔링 DB 기반 HTML 답변."""
    try:
        gt = engine.get("get_timing_flow")
        timing = (
            gt()
            if callable(gt)
            else {"phase": "안정기", "score": 70, "daewoon_index": 0}
        )
        if not isinstance(timing, dict):
            timing = {"phase": "준비기", "score": 60, "daewoon_index": 0}
    except Exception:
        timing = {"phase": "준비기", "score": 60, "daewoon_index": 0}

    phase = str(timing.get("phase", "보통"))
    score = int(timing.get("score", 50))
    daewoon_index = int(timing.get("daewoon_index", 0))
    daewoon_ten = ["인성", "비견", "식상", "재성", "관성"][daewoon_index % 5]
    ut = str(user_text or "")

    if _is_family_health_care_question(ut):
        return _family_health_care_reply_html(
            ut,
            yongshin=yongshin,
            gender=gender,
            daewoon_ten=daewoon_ten,
            strength=strength,
            phase=phase,
            score=score,
        )

    ds = html.escape(str(day_stem))
    de = html.escape(str(day_el))
    ys = html.escape(str(yongshin))
    base = f"✨ <b>{ds}({de})</b> 일간의 특성상 "
    base += (
        "주도성과 추진력이 강한 구조입니다."
        if strength == "신강"
        else "흐름을 활용하는 전략형 구조입니다."
    )

    if any(k in ut for k in ("돈", "재물", "사업", "투자", "금전")):
        core = "💰 재물 흐름이 작동하는 구간입니다. 수익 구조 확보가 핵심입니다."
        add = f"👉 용신 <b>{ys}</b> 시기에 수익 극대화됩니다."
    elif any(k in ut for k in ("직장", "승진", "이직", "시험")):
        core = "💼 직장·승진·합격 흐름이 작동합니다."
        add = f"👉 <b>{ys}</b> 기운에서 기회가 열립니다."
    elif any(k in ut for k in ("연애", "결혼", "인연")):
        core = "❤️ 인연 흐름이 들어오는 구간입니다."
        add = f"👉 <b>{ys}</b> 시기에 관계 진전됩니다."
    else:
        core = "📖 내면 성장과 준비 흐름입니다."
        add = f"👉 <b>{ys}</b> 활용이 핵심입니다."

    final_judgment = _final_judgment_line(
        user_text=ut, score=score, yongshin=yongshin
    )
    storytelling_guidance = _storytelling_guidance_html(
        ut,
        gender=gender,
        daewoon_ten=daewoon_ten,
        strength=strength,
        yongshin=yongshin,
    )
    master_guidance = _master_guidance_html(
        ut,
        strength=strength,
        yongshin=yongshin,
    )
    ph = html.escape(phase)
    q_line = html.escape(ut[:100] + ("…" if len(ut) > 100 else ""))
    return (
        f"{K.chatbot_persona_intro_html()}<br><br>"
        f"💬 <b>질문:</b> {q_line}<br><br>"
        f"{base}<br><br>📊 <b>현재 흐름:</b> {ph} (체감도 {score}점)<br><br>"
        f"{core}<br><br>{add}<br><br>🧭 <b>대운 흐름:</b> {daewoon_ten}<br>"
        f"🎯 <b>정리:</b> {final_judgment}"
        f"{storytelling_guidance}{master_guidance}"
    )


def generate_saju_reply(
    user_text: str,
    *,
    engine: dict,
    day_stem: str,
    day_el: str,
    yongshin: str,
    strength: str,
    gender: str = "남자",
) -> str:
    """OpenAI(선택) → 없으면 주입한 마스터 지침·스토리텔링 답변."""
    from saju_app.ui.step11_chat_ai import try_openai_chat_reply

    ai = try_openai_chat_reply(
        user_text=user_text,
        engine=engine,
        day_stem=day_stem,
        day_el=day_el,
        yongshin=yongshin,
        strength=strength,
        gender=gender,
    )
    if ai:
        return ai
    from saju_app.ui.step11_chat_ai import generate_chat_reply_html

    return generate_chat_reply_html(
        user_text=user_text,
        engine=engine,
        day_stem=day_stem,
        day_el=day_el,
        yongshin=yongshin,
        strength=strength,
        gender=gender,
    )


def _step11_chat_empty_html(day_stem: str, day_el: str, yongshin: str) -> str:
    """대화가 없을 때 채팅창 — 안내 문구 없이 빈 영역."""
    _ = day_stem, day_el, yongshin
    return ""


def _render_step11_chat_messages() -> None:
    """저장소 기준으로 상담 내용을 그립니다."""
    rk = str(st.session_state.get("step11_chat_room_key") or "").strip()
    if not rk:
        st.info("상담 방 키가 없습니다. 페이지를 한 번 새로고침해 주세요.")
        return
    _pull_step11_chat_from_storage(rk)
    try:
        msgs, _lab = saju_storage.get_shared_chat_room(rk)
    except Exception:
        msgs = []
    conv = dedupe_chat_messages(filter_conversation_messages(list(msgs or [])))
    intro = st.session_state.get("step11_intro") or {}
    ds = str(intro.get("day_stem") or "알 수 없음")
    de = str(intro.get("day_el") or "운세")
    ys = str(intro.get("yongshin") or "균형")
    try:
        chat_box = st.container(border=True, key="step11_hanji_chat")
    except TypeError:
        chat_box = st.container(border=True)
    with chat_box:
        if conv:
            render_conversation_chat_ui(conv, customer_label="고객")
        else:
            _ = ds, de, ys
            st.caption("고민을 입력하면 대화가 여기에 표시됩니다.")

    # 관리자 미리보기 화면에서는 Streamlit 프론트의 간헐적 removeChild 에러 박스를 노출하지 않습니다.
    # (대화 확인만 필요한 화면이며, 오류 박스가 있으면 사용자가 앱이 깨졌다고 오해합니다.)
    if M.step11_admin_preview_mode():
        st.markdown(
            """
<style>
/* Streamlit 예외/스택트레이스 UI 숨김(관리자 STEP11 미리보기 전용) */
div[data-testid="stException"], div[data-testid="stAlert"] pre, div[data-testid="stAlert"] code {
  display: none !important;
  height: 0 !important;
  overflow: hidden !important;
}
</style>
""",
            unsafe_allow_html=True,
        )


def render() -> None:
    admin_view = M.step11_admin_preview_mode()
    _chat_rk = _step11_ensure_room_key()

    if admin_view:
        if not _chat_rk:
            st.header("💬 관리자 · 고객 채팅 확인")
            st.info(
                "STEP12 **실시간 고객 채팅 모니터링**에서 상담 방을 선택한 뒤 "
                "「STEP11로 이 방 열기」를 누르세요."
            )
            if st.button("← 관리자(STEP12)로", use_container_width=True, key="step11_admin_back_no_room"):
                M.navigate_to_step(12)
            return
        _hydrate_customer_label_from_room(_chat_rk)
        engine = _admin_preview_engine_stub()
    else:
        engine = M._require_saju_engine_or_build()

    u_name = str(st.session_state.get("u_name", "사주까기님") or "사주까기님")
    day_stem = str(engine.get("day_stem", "알 수 없음"))
    day_el = str(engine.get("day_el", "운세"))
    yongshin = str(engine.get("yongshin", "균형"))
    strength = str(engine.get("strength", "보통"))
    u_gender = str(st.session_state.get("u_gender", "남자") or "남자")

    _chat_label = _step11_chat_label(u_name)

    if "shared_chat" not in st.session_state:
        st.session_state.shared_chat = []
    # STEP11은 관리자/일반 모두 동일한 "AI 사주 챗봇" UI로 렌더한다.
    # (이전엔 관리자 인증 시 '관리자·고객 채팅 확인' 전용 블록만 보이고 입력창이 사라졌으나,
    #  사용자 요청으로 입력창이 있는 정상 챗봇으로 통일. 관리자 모니터링은 STEP12에서 수행.)
    st.header("💬 AI 사주 챗봇 · 사주까기")
    st.warning(
        "AI 상담은 운세·성향 참고용입니다. 건강, 임신, 질병, 수술, 법률, 투자 등 중요한 결정은 "
        "반드시 해당 분야 전문가와 상담하세요."
    )
    with st.container(key="step11_memo_download_panel"):
        st.markdown("#### 📝 분석 메모 · 상담")
        try:
            _memo_cols = st.columns([1, 1], gap="small")
        except TypeError:
            _memo_cols = st.columns([1, 1])
        with _memo_cols[0]:
            AFM.render_all_memos_download_button(key="step11_all_memos_download")
        with _memo_cols[1]:
            if st.button(
                "🔄 채팅 가져오기",
                key="step11_pull_shared_chat",
                use_container_width=True,
                help="관리자 답변·저장소 내용을 다시 불러옵니다. 기록을 지우지 않습니다.",
            ):
                _pull_step11_chat_from_storage(_chat_rk)
                M.prepare_step_change_ui(dest=int(st.session_state.get("step", 11)))
                # 버튼 콜백 경고/포커스 꼬임 방지를 위해 rerun 대신 상태만 반영합니다.

    st.session_state["step11_intro"] = {
        "day_stem": day_stem,
        "day_el": day_el,
        "yongshin": yongshin,
    }
    if not admin_view:
        _clear_step11_chat_on_new_browser_session(_chat_rk, _chat_label)
        _strip_legacy_welcome_from_room(_chat_rk)
        M.sync_shared_chat_room_into_session(_chat_rk)
    else:
        _strip_legacy_welcome_from_room(_chat_rk)
        _pull_step11_chat_from_storage(_chat_rk)

    if not admin_view:
        with st.expander("개인정보·상담 기록 관리", expanded=False):
            st.caption(
                "현재 상담 방의 질문·답변 기록과 현재 세션 아카이브, 현재 입력 정보로 생성된 프로필 저장값을 삭제할 수 있습니다."
            )
            confirm_delete = st.checkbox(
                "내 상담 기록과 저장 정보를 삭제하는 데 동의합니다.",
                key="step11_delete_my_data_ack",
            )
            if st.button(
                "내 상담 기록 삭제",
                type="primary",
                use_container_width=True,
                disabled=not confirm_delete,
                key="step11_delete_my_data_btn",
            ):
                _delete_current_user_data(_chat_rk, u_name)
                st.session_state.shared_chat = []
                st.success("현재 상담 기록 삭제 요청을 처리했습니다.")

    st.markdown("### 💬 실시간 고객 채팅")
    _render_step11_chat_messages()

    err = st.session_state.pop("_shared_chat_persist_error", None)
    if err:
        st.warning(
            "채팅 저장에 실패했습니다. 저장소(DB/Redis) 경로·권한·네트워크를 확인해 주세요. "
            f"({html.escape(str(err)[:400])})"
        )

    st.markdown("#### 고민 입력")
    user_input = st.chat_input(
        "고민을 입력하세요...",
        key="step11_chat_text_input",
    )

    public_settings = W.public_webapp_settings()
    kakao_url = str(public_settings.get("kakao_url") or "").strip()
    phone = str(public_settings.get("phone") or "").strip() or "준비중"
    tel_digits = re.sub(r"\D", "", phone)
    tel_href = f"tel:{tel_digits}" if tel_digits else ""

    with st.container(key="step11_consult_strip"):
        st.caption("상담 연결")
        try:
            c_kakao, c_phone, c_qr = st.columns(3, gap="small")
        except TypeError:
            c_kakao, c_phone, c_qr = st.columns(3)
        with c_kakao:
            if kakao_url:
                st.link_button(
                    "💬\n오픈채팅",
                    kakao_url,
                    use_container_width=True,
                    key="step11_kakao_link",
                )
            else:
                st.button(
                    "💬\n오픈채팅",
                    use_container_width=True,
                    disabled=True,
                    key="step11_kakao_disabled",
                )
        with c_phone:
            if tel_href:
                st.link_button(
                    "📞\n전화상담",
                    tel_href,
                    use_container_width=True,
                    type="primary",
                    key="step11_phone_link",
                    help=phone,
                )
            else:
                st.button(
                    "📞\n전화상담",
                    use_container_width=True,
                    disabled=True,
                    key="step11_phone_disabled",
                    help=phone,
                )
        with c_qr:
            if st.button(
                "🖼️\nQR문의",
                key="step11_show_qr_btn",
                use_container_width=True,
            ):
                st.session_state.step11_show_qr = not bool(
                    st.session_state.get("step11_show_qr", False)
                )

    with st.container(key="step11_qr_panel"):
        if st.session_state.get("step11_show_qr") and M.QR_DATA:
            st.markdown(
                f"""
<div style="text-align:center;margin:0.75rem 0 1rem 0;">
  <img src="data:image/jpeg;base64,{M.QR_DATA}" alt="QR 문의 코드"
       style="max-width:220px;width:70%;border-radius:16px;
              border:1px solid rgba(212,175,55,0.38);
              box-shadow:0 8px 24px rgba(0,0,0,0.16);" />
  <div style="margin-top:0.45rem;color:#6b5a2a;font-weight:700;">QR코드를 스캔해 문의하세요.</div>
</div>
""",
                unsafe_allow_html=True,
            )
        elif st.session_state.get("step11_show_qr"):
            st.markdown(
                '<p style="margin:0.75rem 0 1rem;color:#6b7280;">'
                "QR 이미지를 찾지 못했습니다. 프로젝트 루트의 <b>qr.jpg</b> 파일을 확인해 주세요."
                "</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="step11-qr-placeholder" aria-hidden="true" style="height:0;overflow:hidden;"></div>',
                unsafe_allow_html=True,
            )

    M.render_step11_inline_step_nav()

    if user_input and str(user_input).strip():
        ui = str(user_input).strip()
        try:
            raw_msgs, lab = saju_storage.get_shared_chat_room(_chat_rk)
        except Exception:
            raw_msgs, lab = [], None
        msgs = dedupe_chat_messages(list(raw_msgs or []))
        lab_out = dict(lab) if isinstance(lab, dict) else {}
        inferred_type = _classify_consultation_type(ui)
        lab_out.update(_step11_chat_label(u_name, inferred_type))
        lab_out["ts"] = M.now_kst().isoformat(timespec="seconds")
        if not tail_matches_user(msgs, ui):
            msgs.append({"role": "user", "msg": ui, "is_manual": False})
            st.session_state.shared_chat = list(msgs)
            M._persist_shared_chat_bus(_chat_rk, msgs, lab_out)
            try:
                saju_storage.archive_append_record(
                    {
                        "session_id": M.ensure_session_id(),
                        "ts": M.now_kst().isoformat(timespec="seconds"),
                        "role": "user",
                        "content": ui,
                        "u_name": u_name,
                    }
                )
            except Exception:
                pass
        with st.spinner("맞춤 답변을 작성하고 저장하는 중…"):
            reply = generate_saju_reply(
                ui,
                engine=engine,
                day_stem=day_stem,
                day_el=day_el,
                yongshin=yongshin,
                strength=strength,
                gender=u_gender,
            )
            try:
                raw2, _ = saju_storage.get_shared_chat_room(_chat_rk)
            except Exception:
                raw2 = []
            msgs2 = dedupe_chat_messages(list(raw2 or []))
            if not tail_matches_assistant(msgs2, reply):
                msgs2.append({"role": "assistant", "msg": reply, "is_manual": False})
                st.session_state.shared_chat = list(msgs2)
                lab_out["ts"] = M.now_kst().isoformat(timespec="seconds")
                M._persist_shared_chat_bus(_chat_rk, msgs2, lab_out)
        return
