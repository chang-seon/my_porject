"""
features/ 모듈간 직접 import 금지 검사기.
features/X 가 features/Y 를 직접 import 하면 오류로 간주한다.
모든 모듈간 호출은 반드시 core/router.py 를 거쳐야 한다 (CLAUDE.md 규칙).
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
FEATURES_DIR = ROOT / "job_agent" / "features"


def get_feature_modules() -> list[str]:
    return [d.name for d in FEATURES_DIR.iterdir() if d.is_dir() and not d.name.startswith("_")]


def check_file(filepath: Path, feature_modules: list[str]) -> list[str]:
    violations = []
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except Exception as e:
        return [f"파싱 오류: {filepath} — {e}"]

    # 현재 파일이 속한 features 모듈 이름
    parts = filepath.parts
    try:
        features_idx = parts.index("features")
        current_module = parts[features_idx + 1] if features_idx + 1 < len(parts) else None
    except ValueError:
        current_module = None

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module:
                module_str = node.module
            elif isinstance(node, ast.Import):
                module_str = ".".join(alias.name for alias in node.names)
            else:
                continue

            # job_agent.features.X 패턴 검사
            for feat in feature_modules:
                if feat == current_module:
                    continue
                banned_patterns = [
                    f"job_agent.features.{feat}",
                    f"features.{feat}",
                ]
                for pattern in banned_patterns:
                    if module_str.startswith(pattern):
                        violations.append(
                            f"{filepath.relative_to(ROOT)}:{node.lineno} — "
                            f"직접 import 금지: '{module_str}' "
                            f"(core/router.call() 사용할 것)"
                        )
    return violations


def main() -> int:
    feature_modules = get_feature_modules()
    all_py_files = list((ROOT / "job_agent").rglob("*.py"))
    # core/, shared/ 파일은 검사에서 제외 (router.py는 의도적으로 import함)
    target_files = [
        f for f in all_py_files
        if "features" in f.parts and "__pycache__" not in f.parts
    ]

    all_violations: list[str] = []
    for filepath in sorted(target_files):
        violations = check_file(filepath, feature_modules)
        all_violations.extend(violations)

    if all_violations:
        print("❌ features/ 직접 import 위반 발견:")
        for v in all_violations:
            print(f"  {v}")
        return 1

    print(f"✅ lint_imports 통과 — {len(target_files)}개 파일 검사, 위반 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
