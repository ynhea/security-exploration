import argparse
import re
from collections import Counter
from datetime import datetime

# 타임스태프 뽑기
TIMESTAMP_RE = re.compile(r"(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)")

# 신뢰도
RULES = [
    ("information_disclosure", re.compile(r"SQLITE_ERROR|incomplete input|SQL syntax", re.I), 80),
    ("server_error", re.compile(r"\b500\b|Error:", re.I), 40),
    ("sql_metachar", re.compile(r"('|--|/\*|\*/|;|\bUNION\b|\bSELECT\b|\bOR\b\s+1\s*=\s*1)", re.I), 20),
]


def parse_line(line):
    match = TIMESTAMP_RE.search(line)
    ts = match.group("ts") if match else "NO_TIMESTAMP"
    message = line[match.end():].strip() if match else line.strip()
    return ts, message

# 로그 검사
def score_line(line):
    hits = []
    score = 0
    for name, pattern, weight in RULES:
        if pattern.search(line):    # RULES의 패턴이 로그에 있으면
            hits.append(name)
            score += weight         # 점수 더하기
    return score, hits

# 신뢰도 분류
def confidence(score):
    if score >= 80:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    if score > 0:
        return "LOW"
    return "NONE"


def normalize_powershell_noise(lines):
    noise_prefixes = ("At line:", "+ ", "    + CategoryInfo", "    + FullyQualifiedErrorId")
    for line in lines:
        stripped = line.rstrip("\n")
        if not stripped:
            continue
        if stripped.startswith(noise_prefixes):
            continue
        if stripped.startswith("docker : "):
            stripped = stripped.removeprefix("docker : ")
        yield stripped


def main():
    parser = argparse.ArgumentParser(description="Simple SQLi indicator detector for timestamped Docker logs.")
    parser.add_argument("logfile", help="Path to timestamped Docker log file")
    args = parser.parse_args()

    with open(args.logfile, "r", encoding="utf-8", errors="replace") as f:
        lines = list(normalize_powershell_noise(f))

    findings = []
    for line_no, line in enumerate(lines, start=1):
        score, hits = score_line(line)
        if score:
            ts, message = parse_line(line)
            findings.append((ts, line_no, score, confidence(score), hits, message))

    # 개수 -> 규칙 -> 시간 계산 & 정리
    by_confidence = Counter(item[3] for item in findings)
    by_rule = Counter(rule for item in findings for rule in item[4])
    by_minute = Counter(item[0][:16] for item in findings if item[0] != "NO_TIMESTAMP")

    print("SQLi log detection summary")
    print(f"- analyzed_lines: {len(lines)}")
    print(f"- findings: {len(findings)}")
    print(f"- confidence_counts: {dict(by_confidence)}")
    print(f"- rule_counts: {dict(by_rule)}")
    print(f"- timeline_by_minute: {dict(sorted(by_minute.items()))}")
    print()
    print("Findings")
    for ts, line_no, score, conf, hits, message in findings:
        print(f"{ts} line={line_no} confidence={conf} score={score} hits={','.join(hits)}")
        print(f"  {message}")


if __name__ == "__main__":
    main()
