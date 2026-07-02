# Day 4 - SOC Analyst
## 로그 기반 SQL Injection 탐지 및 False Positive 분석

> **Role** : SOC Analyst  
> **Objective** : 애플리케이션 로그를 분석하여 SQL Injection 공격 흔적을 탐지하고, 탐지 규칙의 한계를 이해한다.

---

# 학습 목표

- 로그를 확인하는 방법 익히기
- 정상 요청과 공격 요청의 차이 분석
- 공격 패턴을 기반으로 탐지 근거 도출
- grep을 이용한 간단한 탐지 로직 작성
- False Positive를 직접 만들어보고 탐지 규칙의 한계 이해

---

# 1. 로그 확인 방법

## Docker 로그 확인

```bash
docker logs <컨테이너명>
```

### 확인한 내용

- 기본 Docker 로그는 요청 하나하나를 자세히 기록하지 않는다.
- 애플리케이션 로그 위주로 출력된다.

---

## 브라우저 Network 확인

Chrome DevTools

```
Network
☑ Disable Cache
```

실제 요청(Request)과 응답(Response)을 함께 확인하며 로그와 비교했다.

---

# 2. 정상 요청 vs SQL Injection 요청 비교

## 정상 요청

Response

```json
{
  "status": "...",
  "data": [...]
}
```

- 정상적인 상품 목록 반환
- JSON 구조 유지

---

## SQL Injection 요청

Payload

```text
xyz123' OR '1'='1'--
```

Response

```text
500 Internal Server Error

SQLITE_ERROR: incomplete input
```

### 확인한 점

- HTTP Status Code : **500**
- DB 에러 메시지 노출
- SQLite 사용 사실 노출

→ **Information Disclosure** 발생

---

# 3. 공격 흔적(IOC) 식별

이번 실습에서 사용할 수 있는 탐지 근거를 정리했다.

| 탐지 근거 | 신뢰도 | 이유 |
|-----------|--------|------|
| SQLITE_ERROR 노출 | ⭐⭐⭐⭐⭐ | 실제 DB 오류 발생 |
| HTTP 500 | ⭐⭐⭐ | 서버 오류일 수도 있음 |
| SQL 특수문자(`'`, `OR`, `--`) | ⭐⭐ | 단순 오타 가능성 존재 |

### 결론

```
Information Disclosure
>
HTTP 500
>
SQL 특수문자
```

신뢰도가 높을수록 False Positive가 적다.

---

# 4. grep 기반 탐지

## 기본 탐지

```bash
docker logs <컨테이너명> | grep SQLITE
```

결과

```text
Error: SQLITE_ERROR: incomplete input
```

---

## Timestamp 포함

```bash
docker logs <컨테이너명> -t | grep SQLITE
```

Timestamp가 추가되어

- 공격 발생 시각
- 이벤트 순서

를 확인할 수 있었다.

---

# grep 탐지의 한계

현재 Docker 로그만으로는

- Client IP
- Request URL
- Query Parameter
- User-Agent

를 확인할 수 없었다.

따라서 실제 침해사고 분석에는 부족하다.

---

# 실제 현업에서는 추가로 필요한 로그

| 로그 | 목적 |
|------|------|
| Access Log | 공격 성공 여부 확인 |
| Reverse Proxy Log | 요청 유입 경로 확인 |
| WAF Log | 공격 유형 분석 |
| Browser Network | 실제 요청/응답 검증 |

여러 로그를 교차 분석해야 정확한 사고 분석이 가능하다.

---

# 5. False Positive 분석

grep은 문자열만 검색한다.

따라서

```bash
grep SQLITE
```

만 사용하면

공격이 아닌 정상 로그도 탐지될 수 있다.

---

## 탐지 규칙의 트레이드오프

탐지 강도를 높이면

- False Positive ↓
- 놓치는 공격(False Negative) ↑

탐지 강도를 낮추면

- 더 많은 공격 탐지 가능
- False Positive 증가

즉,

> 탐지 규칙은 정확도와 탐지율 사이의 균형이 중요하다.
