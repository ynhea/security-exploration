1. 로그 확인 방법 파악
- docker logs 컨테이너명
- 기존 로그레벨 = 요청 하나하나를 찍지X
- 브라우저 개발자도구 Network + Disable Cache
D
2. 정상 요청 vs SQLi 요청 로그 비교
(정상 요청 시 Response구조를 알고 기준점으로 삼아야, 이상한 응답을 알아챌 수 있다)
- 정상 요청 시 Response : JSON형태의 상품목록 (status, data..)
- 이상한 요청 시 Response(SQL Injection) : 500 Error: SQLITE_ERROR: incomplete input
	 						(추가 위험(Information Disclosure) = SQL이름 노출)

3. 공격 흔적 패턴 수동 식별 및 정리
- 공격을 잡아낼 수 있는 근거 = SQL 특수문자 & 상태코드 500 & Information Disclosure
- 신뢰도 : Information Disclosure > 상태코드 500(서버 버그일 수도 있음) > 특수문자 (오타 가능성)
  (False Positive 적을 수록, 신뢰도 ↑)

4. grep/Python 기반 간단 탐지로직 작성
- grep 단어 파일 : 파일 안의 특정 단어가 포함된 줄만 찾아서 보여주는 명령어
- 명령어 = docker logs romantic_aryabhata | grep SQLITE(신뢰도가 높은 패턴)
- 결과	 = Error: SQLITE_ERROR: incomplete input
      		0 [main] us 0 init_cheap: VirtualAlloc pointer is null, Win32 error 487
- 문제점 = TimeStamp & 반복횟수(공격강도) 존재X -> 타임라인 재구성 X
- 해결 = docker logs romantic_aryabhata -t | grep SQLITE (TimeStamp 옵션 추가)
※ 한계 ※
- 요청 URL, IP, User-Agent, 파라미터가 남지 않는다.
- 정확한 분석을 위해서는 access log(공격 시 서버 행동 파악), reverse proxy(외부 요청 라우팅 경로 확인) log, WAF(웹방화벽) log, 브라우저 Network 기록(실제 패킷)이 추가로 필요하다.
(WAF로 공격 성격을 보고, Proxy로 유입 경로를 찾고, Access log로 성공 여부를 확인한 뒤, Network 기록으로 실제 유출된 내용을 교차 검증)

5. False Positive 케이스 직접 만들어보고 구분 연습
- False Positive경우 = grep은 문자열만 보고 판단 → 공격의도X 정상검색도 걸릴 수 있음 
- 탐지 규칙의 모순 = 탐지강도(키워드 구체화 등...)와 False Positive는 반비례한다
			   (EX) docker logs romantic_aryabhata | grep SQLITE_ERROR: incomplete input
