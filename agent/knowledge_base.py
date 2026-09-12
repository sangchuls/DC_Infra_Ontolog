# agent/knowledge_base.py
# 프로젝트 온톨로지 파일 기반 지식베이스.
#
# 배포 참고: 예전에는 이 리포 밖(D:\DATA\앱개발\...)의 절대경로를 직접 참조했는데,
# Render 등 원격 서버에는 그 경로가 존재하지 않으므로 리포 안의 data/knowledge_base/ 로
# 파일을 복사해 자기완결적으로 만들었다. 프로젝트 폴더 하나 = data/knowledge_base/<이름>/
# (ontology.json 필수, description.md 선택) 구조이며, 폴더를 스캔해서 자동으로 목록을 만든다 —
# 새 프로젝트를 추가하려면 이 규칙대로 폴더만 놓으면 된다 (코드 수정 불필요).
#
# KNOWLEDGE_BASE_DIR 환경변수로 다른 위치(예: 로컬 개발 중 D:\DATA\앱개발\... 원본)를
# 가리키도록 재정의할 수 있다.

import json
import os

DATA_DIR = os.environ.get(
    "KNOWLEDGE_BASE_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge_base"),
)


def list_projects() -> list:
    """등록된 프로젝트 온톨로지 목록을 반환한다. 각 항목은 이름과 보유 파일 종류를 담는다."""
    out = []
    if not os.path.isdir(DATA_DIR):
        return out
    for name in sorted(os.listdir(DATA_DIR)):
        proj_dir = os.path.join(DATA_DIR, name)
        if not os.path.isdir(proj_dir):
            continue
        has_ontology = os.path.isfile(os.path.join(proj_dir, "ontology.json"))
        has_desc = os.path.isfile(os.path.join(proj_dir, "description.md"))
        out.append({"name": name, "has_ontology_json": has_ontology, "has_description_md": has_desc})
    return out


def load_project(name: str) -> dict:
    """지정한 프로젝트의 온톨로지(JSON)와 설명(MD)을 읽어 반환한다.

    name: list_projects로 확인한 프로젝트명 (= data/knowledge_base/ 밑의 폴더명)
    """
    proj_dir = os.path.join(DATA_DIR, name)
    if not os.path.isdir(proj_dir):
        return {"error": f"등록되지 않은 프로젝트: {name}. list_projects로 확인하세요."}

    result = {"name": name}

    ontology_path = os.path.join(proj_dir, "ontology.json")
    if os.path.isfile(ontology_path):
        with open(ontology_path, "r", encoding="utf-8") as f:
            try:
                result["ontology"] = json.load(f)
            except json.JSONDecodeError as e:
                result["ontology_error"] = str(e)
    else:
        result["ontology"] = None

    desc_path = os.path.join(proj_dir, "description.md")
    if os.path.isfile(desc_path):
        with open(desc_path, "r", encoding="utf-8") as f:
            result["description_md"] = f.read()
    else:
        result["description_md"] = None

    return result
