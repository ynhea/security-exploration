1. 취약 코드 분석
- routes 폴더 = 웹앱의 URL경로로 들어왔을 때, 실행할 코드(로직)
	-> search가 URL에 존재O & SQL Injection존재하므로, search만 찾으면 됨 		
	(routes폴더에서 취약점이 존재하는 코드를 찾아야 하는 이유임. routes 폴더를 몰라서 삽질함)
	- 취약점 존재 코드파일 : routes/search.ts
	※ 웹앱은 URL을 통해 취약점의 위치에 대한 힌트를 알 수 O ※

2. 원인 파악 및 개념 학습
- let criteria: any = req.query.q === 'undefined' ? '' : req.query.q ?? ''
criteria = (criteria.length <= 200) ? criteria : criteria.substring(0, 200) > Null과 글자수 예외만 잡아냄
	-> 입력값 안의 SQL 특수문자 검사하는 로직X
	-> SQL Injection 원인 = (1차)입력을 직접 이어붙임 Template Literal & (2차)입력값 검증X

3. 수정 코드 작성
★ 이스케이프 처리(예: ' → \')하는 방식은 실제로 시도되었다가 많은 보안 사고를 낸 방법입니다. 우회 방법이 너무 많거든요 (유니코드, 인코딩, DB마다 다른 이스케이프 규칙 등).
- 실무 해결법 : 쿼리의 "구조"(SQL 문법)와 "값"(사용자 입력)을 처음부터 완전히 분리해서 DB에 전달
		    (Prepared Statement) (Parameterized Query)
	sequelize.query(
  	  "SELECT * FROM Products WHERE name LIKE :criteria",
	  { replacements: { criteria: `%${criteria}%` } }
	)
	>> ':criteria'는 값이 들어갈 자리라는 표시 & 실제 입력은 데이터로만 전달됨
- (`SELECT * FROM Products WHERE ((name LIKE :criteria OR description LIKE :criteria) AND deletedAt IS NULL) ORDER BY name`, {replacements: { criteria: `%${criteria}%` }})
	>> 백틱(`)으로 적어야 함!!


4. 테스트(재현 안 됨을 확인)
(1) Docker 컨테이너로 테스트 -> search.js 수정코드 생성
(search.ts이나 Docker이미지는 TS를 JS로 빌드해 둔 결과물만 실행)
(2) cp로 수정코드로 복붙
(3) restart 컨테이너로 재실행 (Node.js는 시작할 때 파일을 한 번에 읽어서 메모리에 올려두고 계속 동작하기 때문)
(4) 컨테이너 파일 cp해서 cat으로 확인
(5) http://localhost:3000/rest/products/search?q=apple
    http://localhost:3000/rest/products/search?q=xyz123%27%20OR%20%271%27%3D%271%27--
    테스트 진행
- 어제 검색창에 "xyz123' OR '1'='1'--" 테스트 진행 -> 검색 결과 없음 -> SQL Injection증명 X
   (Angular 프론트엔드 라우트라서 "xyz123' OR '1'='1'--" 로 상품 목록을 필터링함)
   (Angular는 해시(#)뒤쪽만 보는데 #을 지우니까 빈값으로 처리돼서 "모든 제품"이 뜬 것임)
   (따라서 백엔드API 호출결과를 확인하기 위해 rest/products 주소로 확인해본 결과, "You successfully solved a challenge: Error Handling (Provoke an error that is neither very gracefully nor consistently handled.)" 안내메세지가 뜨며 SQL Injection을 정확히 증명함을 확인할 수 있었음)
  (-- 뒤의 내용이 전부 주석 처리되면서, 쿼리 뒤쪽에 있던 닫는 괄호들과 ORDER BY name까지 통째로 날아가 버림. 따라서 SQL 문법상 괄호가 안 맞아서 "문장이 완성되지 않았다(incomplete input)"는 에러가 나는 거임)
- 수정코드로 테스트를 진행했을 때는 {"status":"success","data":[]}로 사용자의 입력이 SQL 문법으로 해석되지 않고, 값으로만 들어가서 data가 빈 리스트로 나옴을 확인할 수 있었음.
