"""
Database seeding script for Python Deep Dive quizzes
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.problem import Problem, DifficultyLevel, ProblemCategory
from app.core.database import Base


async def seed_database():
    """Seed database with Python Deep Dive quiz data"""

    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        # Create test users
        users = [
            User(
                email="admin@codepath.com",
                username="admin",
                hashed_password=get_password_hash("Admin123!"),
                full_name="Admin User",
                role=UserRole.ADMIN,
                is_verified=True
            ),
            User(
                email="test@codepath.com",
                username="testuser",
                hashed_password=get_password_hash("Test123!"),
                full_name="Test User",
                role=UserRole.USER,
                is_verified=True
            ),
        ]

        session.add_all(users)
        await session.commit()

        print(f"Created {len(users)} users")

        # Create Python Deep Dive quizzes
        problems = [
            Problem(
                title="GIL이란 무엇인가?",
                slug="what-is-gil",
                description="""## Global Interpreter Lock (GIL)

다음 코드의 실행 결과를 예측하세요.

```python
import threading
import time

counter = 0

def increment():
    global counter
    for _ in range(1000000):
        counter += 1

threads = []
for _ in range(2):
    t = threading.Thread(target=increment)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print(counter)
```

### 질문
1. `counter`의 최종 값은 항상 2000000인가?
2. 그 이유는 무엇인가?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.GIL,
                starter_code='''def solution():
    """
    GIL에 대해 설명하고, 위 코드의 결과를 예측하세요.

    Returns:
        dict: {
            "expected_value": int or str,  # 예상 결과값 (정확한 숫자 또는 "불확정")
            "reason": str,  # 이유 설명
            "is_thread_safe": bool  # counter += 1이 thread-safe한지
        }
    """
    return {
        "expected_value": None,
        "reason": "",
        "is_thread_safe": None
    }
''',
                solution_code='''def solution():
    return {
        "expected_value": "불확정 (<= 2000000)",
        "reason": "GIL이 있어도 counter += 1은 atomic하지 않음. LOAD, ADD, STORE 연산 사이에 context switch가 발생할 수 있어 race condition 발생",
        "is_thread_safe": False
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {
                            "expected_value": "불확정 (<= 2000000)",
                            "is_thread_safe": False
                        },
                        "is_hidden": False
                    }
                ],
                constraints=["GIL의 동작 원리를 이해해야 합니다"],
                hints=["GIL은 bytecode 단위로 lock을 관리합니다", "counter += 1은 여러 bytecode로 분리됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="Shallow Copy vs Deep Copy",
                slug="shallow-vs-deep-copy",
                description="""## 얕은 복사와 깊은 복사

다음 코드의 실행 결과를 예측하세요.

```python
import copy

a = [[1, 2], [3, 4]]
b = a.copy()          # 또는 list(a), a[:]
c = copy.deepcopy(a)

a[0][0] = 999
a.append([5, 6])

print(f"a = {a}")
print(f"b = {b}")
print(f"c = {c}")
```

### 질문
각 변수의 최종 값은?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.COPY,
                starter_code='''def solution():
    """
    얕은 복사와 깊은 복사의 차이를 설명하세요.

    Returns:
        dict: {
            "a": list,  # a의 최종 값
            "b": list,  # b의 최종 값
            "c": list,  # c의 최종 값
            "explanation": str  # 차이점 설명
        }
    """
    return {
        "a": None,
        "b": None,
        "c": None,
        "explanation": ""
    }
''',
                solution_code='''def solution():
    return {
        "a": [[999, 2], [3, 4], [5, 6]],
        "b": [[999, 2], [3, 4]],  # 내부 리스트는 같은 참조, append는 영향 없음
        "c": [[1, 2], [3, 4]],    # 완전히 독립적인 복사본
        "explanation": "shallow copy는 최상위 객체만 복사하고 내부 객체는 참조를 공유. deep copy는 모든 중첩 객체를 재귀적으로 복사"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {
                            "a": [[999, 2], [3, 4], [5, 6]],
                            "b": [[999, 2], [3, 4]],
                            "c": [[1, 2], [3, 4]]
                        },
                        "is_hidden": False
                    }
                ],
                constraints=["copy 모듈의 동작을 이해해야 합니다"],
                hints=["shallow copy는 1단계만 복사합니다", "내부 리스트는 같은 객체를 참조합니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="tuple이 list보다 빠른 이유",
                slug="tuple-vs-list-performance",
                description="""## tuple vs list 성능 차이

다음 중 더 빠른 것은 무엇이고, 그 이유는?

```python
import timeit

# Case 1: list 생성
timeit.timeit('[1, 2, 3, 4, 5]', number=1000000)

# Case 2: tuple 생성
timeit.timeit('(1, 2, 3, 4, 5)', number=1000000)
```

### 질문
1. 어떤 것이 더 빠른가?
2. 그 이유는 무엇인가?
3. 메모리 사용량은 어떻게 다른가?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.DATA_STRUCTURE,
                starter_code='''def solution():
    """
    tuple과 list의 성능 차이를 설명하세요.

    Returns:
        dict: {
            "faster": str,  # "tuple" 또는 "list"
            "reasons": list[str],  # 이유들
            "memory_difference": str  # 메모리 차이 설명
        }
    """
    return {
        "faster": None,
        "reasons": [],
        "memory_difference": ""
    }
''',
                solution_code='''def solution():
    return {
        "faster": "tuple",
        "reasons": [
            "tuple은 immutable이므로 컴파일러가 상수로 최적화할 수 있음 (constant folding)",
            "tuple은 구조가 단순하고 고정 크기라 생성 오버헤드가 상대적으로 작음",
            "list는 가변 컨테이너로 추가 메타데이터와 resize 전략이 필요"
        ],
        "memory_difference": "tuple은 고정 크기만 할당. list는 가변 컨테이너라 추가 메타데이터/여유 공간이 필요할 수 있음"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"faster": "tuple"},
                        "is_hidden": False
                    }
                ],
                constraints=["CPython 내부 구현을 이해하면 도움됩니다"],
                hints=["immutable 객체는 최적화가 가능합니다", "dis 모듈로 bytecode를 확인해보세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="Python 메모리 관리",
                slug="python-memory-management",
                description="""## Reference Counting과 Garbage Collection

다음 코드에서 객체가 즉시 해제되지 않는 이유는?

```python
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

# 순환 참조 생성
a = Node(1)
b = Node(2)
a.next = b
b.next = a  # 순환 참조!

# 참조 제거
del a
del b

# 이 시점에서 Node 객체들은 메모리에서 해제되었을까?
```

### 질문
1. del 후에 객체들이 즉시 해제되는가?
2. Python은 이 문제를 어떻게 해결하는가?""",
                difficulty=DifficultyLevel.HARD,
                category=ProblemCategory.MEMORY,
                starter_code='''def solution():
    """
    Python의 메모리 관리 방식을 설명하세요.

    Returns:
        dict: {
            "immediately_freed": bool,  # del 후 즉시 해제되는지
            "reason": str,  # 이유
            "solution": str,  # Python의 해결 방법
            "gc_trigger": str  # GC가 실행되는 조건
        }
    """
    return {
        "immediately_freed": None,
        "reason": "",
        "solution": "",
        "gc_trigger": ""
    }
''',
                solution_code='''def solution():
    return {
        "immediately_freed": False,
        "reason": "순환 참조로 인해 reference count가 0이 되지 않음. a와 b가 서로를 참조하고 있어 각각 ref count가 1로 유지됨",
        "solution": "Python의 Garbage Collector가 순환 참조를 탐지하여 해제. gc 모듈의 세대별 가비지 컬렉션(generational GC) 사용",
        "gc_trigger": "세대별 threshold 초과 시 또는 gc.collect() 명시적 호출 시"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"immediately_freed": False},
                        "is_hidden": False
                    }
                ],
                constraints=["Reference counting과 GC의 차이를 이해해야 합니다"],
                hints=["Reference counting만으로는 순환 참조를 해결할 수 없습니다", "gc 모듈을 살펴보세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="Generator vs List Comprehension",
                slug="generator-vs-list-comprehension",
                description="""## Generator의 메모리 효율성

다음 두 코드의 메모리 사용량 차이는?

```python
import sys

# List comprehension
nums_list = [x * 2 for x in range(1000000)]
print(sys.getsizeof(nums_list))

# Generator expression
nums_gen = (x * 2 for x in range(1000000))
print(sys.getsizeof(nums_gen))
```

### 질문
1. 각각의 메모리 사용량은 대략 얼마인가?
2. Generator는 어떻게 메모리를 절약하는가?
3. Generator의 단점은 무엇인가?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.GENERATOR,
                starter_code='''def solution():
    """
    Generator와 List의 차이를 설명하세요.

    Returns:
        dict: {
            "list_memory": str,  # list의 대략적인 메모리 (예: "8MB")
            "generator_memory": str,  # generator의 대략적인 메모리
            "how_generator_saves": str,  # 절약 방법
            "generator_drawbacks": list[str]  # 단점들
        }
    """
    return {
        "list_memory": None,
        "generator_memory": None,
        "how_generator_saves": "",
        "generator_drawbacks": []
    }
''',
                solution_code='''def solution():
    return {
        "list_memory": "getsizeof 기준 수 MB 수준 (컨테이너 자체 크기만 측정)",
        "generator_memory": "약 120바이트 (generator 객체 자체만)",
        "how_generator_saves": "Lazy evaluation - 값을 미리 생성하지 않고 요청 시점에 하나씩 생성. 전체 데이터를 메모리에 올리지 않음",
        "generator_drawbacks": [
            "한 번만 순회 가능 (재사용 불가)",
            "인덱싱 불가 (random access 불가)",
            "len() 사용 불가",
            "전체 데이터가 필요한 연산 불가 (sorted, reversed 등)"
        ]
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"generator_memory": "약 120바이트 (고정)"},
                        "is_hidden": False
                    }
                ],
                constraints=["Lazy evaluation 개념을 이해해야 합니다"],
                hints=["Generator는 iterator protocol을 구현합니다", "yield 키워드의 동작을 생각해보세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="Decorator 동작 원리",
                slug="decorator-how-it-works",
                description="""## Decorator의 내부 동작

다음 코드의 출력 순서를 예측하세요.

```python
def decorator_a(func):
    print("A: decorator_a 생성")
    def wrapper(*args, **kwargs):
        print("A: wrapper 시작")
        result = func(*args, **kwargs)
        print("A: wrapper 끝")
        return result
    return wrapper

def decorator_b(func):
    print("B: decorator_b 생성")
    def wrapper(*args, **kwargs):
        print("B: wrapper 시작")
        result = func(*args, **kwargs)
        print("B: wrapper 끝")
        return result
    return wrapper

@decorator_a
@decorator_b
def greet(name):
    print(f"Hello, {name}!")

print("--- 함수 정의 완료 ---")
greet("Python")
```

### 질문
출력 순서는?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.DECORATOR,
                starter_code='''def solution():
    """
    Decorator의 실행 순서를 설명하세요.

    Returns:
        dict: {
            "output_order": list[str],  # 출력 순서
            "decoration_order": str,  # 데코레이터 적용 순서 설명
            "execution_order": str  # 실행 순서 설명
        }
    """
    return {
        "output_order": [],
        "decoration_order": "",
        "execution_order": ""
    }
''',
                solution_code='''def solution():
    return {
        "output_order": [
            "B: decorator_b 생성",
            "A: decorator_a 생성",
            "--- 함수 정의 완료 ---",
            "A: wrapper 시작",
            "B: wrapper 시작",
            "Hello, Python!",
            "B: wrapper 끝",
            "A: wrapper 끝"
        ],
        "decoration_order": "아래에서 위로 적용 (B -> A). @decorator_a(@decorator_b(greet))와 동일",
        "execution_order": "위에서 아래로 실행 (A의 wrapper -> B의 wrapper -> 원본 함수)"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {
                            "decoration_order": "아래에서 위로 적용 (B -> A). @decorator_a(@decorator_b(greet))와 동일"
                        },
                        "is_hidden": False
                    }
                ],
                constraints=["Decorator가 함수를 감싸는 방식을 이해해야 합니다"],
                hints=["@decorator는 syntactic sugar입니다", "func = decorator(func)와 동일합니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="LEGB 스코프 규칙",
                slug="legb-scope-rules",
                description="""## LEGB 스코프 규칙

다음 코드의 출력 결과를 예측하세요.

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        return x
    return inner()

print(outer())
print(x)
```

### 질문
1. 출력되는 두 값은 무엇인가?
2. Python의 스코프 검색 순서는?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.CLOSURE,
                starter_code='''def solution():
    """
    LEGB 스코프 규칙을 설명하세요.

    Returns:
        dict: {
            "inner_x": str,
            "global_x": str,
            "rule": str
        }
    """
    return {
        "inner_x": "",
        "global_x": "",
        "rule": ""
    }
''',
                solution_code='''def solution():
    return {
        "inner_x": "local",
        "global_x": "global",
        "rule": "LEGB (Local -> Enclosing -> Global -> Builtins)"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"rule": "LEGB (Local -> Enclosing -> Global -> Builtins)"},
                        "is_hidden": False
                    }
                ],
                constraints=["LEGB 검색 순서를 이해해야 합니다"],
                hints=["중첩 함수에서 Local과 Enclosing을 구분하세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="Late Binding과 lambda",
                slug="late-binding-lambda",
                description="""## Late Binding

다음 코드의 출력 결과를 예측하세요.

```python
funcs = []
for i in range(3):
    funcs.append(lambda: i)

print([f() for f in funcs])
```

### 질문
1. 출력 결과는 무엇인가?
2. 의도대로 0,1,2를 출력하려면 어떻게 수정해야 하는가?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.CLOSURE,
                starter_code='''def solution():
    """
    Late binding 문제와 해결 방법을 설명하세요.

    Returns:
        dict: {
            "result": list[int],
            "fix": str
        }
    """
    return {
        "result": [],
        "fix": ""
    }
''',
                solution_code='''def solution():
    return {
        "result": [2, 2, 2],
        "fix": "lambda i=i: i"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"result": [2, 2, 2]},
                        "is_hidden": False
                    }
                ],
                constraints=["클로저의 변수 바인딩 시점을 이해해야 합니다"],
                hints=["lambda가 실행될 때 i가 평가됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="Mutable Default Argument",
                slug="mutable-default-argument",
                description="""## 기본 인자의 함정

다음 코드의 출력 결과를 예측하세요.

```python
def append_to(value, lst=[]):
    lst.append(value)
    return lst

print(append_to(1))
print(append_to(2))
```

### 질문
1. 두 번째 출력은 무엇인가?
2. 왜 이런 결과가 발생하는가?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.COPY,
                starter_code='''def solution():
    """
    Mutable default argument 문제를 설명하세요.

    Returns:
        dict: {
            "first": list[int],
            "second": list[int],
            "issue": str
        }
    """
    return {
        "first": [],
        "second": [],
        "issue": ""
    }
''',
                solution_code='''def solution():
    return {
        "first": [1],
        "second": [1, 2],
        "issue": "기본 인자는 함수 정의 시 한 번만 생성되어 공유됨"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"second": [1, 2]},
                        "is_hidden": False
                    }
                ],
                constraints=["기본 인자의 평가 시점을 이해해야 합니다"],
                hints=["함수 정의 시점에 객체가 생성됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="is vs ==",
                slug="is-vs-equals",
                description="""## is와 ==의 차이

다음 코드의 결과는?

```python
a = 256
b = 256
c = 257
d = 257

print(a is b)
print(c is d)
```

### 질문
1. 각각 True/False 여부는?
2. 왜 이런 차이가 발생할 수 있는가?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.CPYTHON,
                starter_code='''def solution():
    """
    is와 ==의 차이를 설명하세요.

    Returns:
        dict: {
            "is_256": bool,
            "is_257": bool,
            "note": str
        }
    """
    return {
        "is_256": None,
        "is_257": None,
        "note": ""
    }
''',
                solution_code='''def solution():
    return {
        "is_256": True,
        "is_257": False,
        "note": "CPython은 작은 정수를 캐싱하지만, 구현/버전/상수 병합 여부에 따라 is 결과가 달라질 수 있음. is는 identity 비교로만 사용해야 함"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"is_256": True},
                        "is_hidden": False
                    }
                ],
                constraints=["is는 identity 비교, ==는 value 비교입니다"],
                hints=["작은 정수 캐싱을 떠올리세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="dict 순서 보장",
                slug="dict-insertion-order",
                description="""## dict의 순서 보장

다음 코드의 출력 결과는?

```python
d = {}
d["b"] = 2
d["a"] = 1
print(list(d.keys()))
```

### 질문
Python 3.7+에서 dict의 순서가 보장되는 이유는?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.DATA_STRUCTURE,
                starter_code='''def solution():
    """
    dict의 순서 보장을 설명하세요.

    Returns:
        dict: {
            "keys": list[str],
            "reason": str
        }
    """
    return {
        "keys": [],
        "reason": ""
    }
''',
                solution_code='''def solution():
    return {
        "keys": ["b", "a"],
        "reason": "CPython의 dict는 삽입 순서를 유지하도록 구현되었으며, 3.7+에서 언어 사양으로 보장"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"keys": ["b", "a"]},
                        "is_hidden": False
                    }
                ],
                constraints=["Python 3.7+ 기준입니다"],
                hints=["dict 구현이 바뀌었습니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="set vs list membership",
                slug="set-vs-list-membership",
                description="""## membership 테스트

다음 두 연산의 평균 시간 복잡도는?

```python
item in my_list
item in my_set
```

### 질문
1. list의 평균 시간 복잡도는?
2. set의 평균 시간 복잡도는?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.DATA_STRUCTURE,
                starter_code='''def solution():
    """
    list와 set의 membership 성능을 설명하세요.

    Returns:
        dict: {
            "list": str,
            "set": str
        }
    """
    return {
        "list": "",
        "set": ""
    }
''',
                solution_code='''def solution():
    return {
        "list": "O(n)",
        "set": "O(1) average"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"set": "O(1) average"},
                        "is_hidden": False
                    }
                ],
                constraints=["최악의 경우를 언급해도 됩니다"],
                hints=["set은 해시 기반입니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="리스트 곱셈의 함정",
                slug="list-multiply-shared-reference",
                description="""## 리스트 곱셈과 참조 공유

다음 코드의 출력 결과는?

```python
matrix = [[0] * 3] * 3
matrix[0][0] = 1
print(matrix)
```

### 질문
왜 이런 결과가 나오는가?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.COPY,
                starter_code='''def solution():
    """
    리스트 곱셈의 참조 공유 문제를 설명하세요.

    Returns:
        dict: {
            "row0": list[int],
            "row1": list[int],
            "reason": str
        }
    """
    return {
        "row0": [],
        "row1": [],
        "reason": ""
    }
''',
                solution_code='''def solution():
    return {
        "row0": [1, 0, 0],
        "row1": [1, 0, 0],
        "reason": "같은 내부 리스트 객체가 3번 참조됨"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"row1": [1, 0, 0]},
                        "is_hidden": False
                    }
                ],
                constraints=["얕은 복사를 이해해야 합니다"],
                hints=["id()로 내부 리스트를 확인해보세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="dataclass와 mutable 기본값",
                slug="dataclass-mutable-default",
                description="""## dataclass 기본값 문제

다음 dataclass의 문제점과 해결책을 설명하세요.

```python
from dataclasses import dataclass

@dataclass
class Bag:
    items: list = []
```

### 질문
1. 어떤 문제가 생기는가?
2. 어떻게 수정해야 하는가?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.OOP,
                starter_code='''def solution():
    """
    dataclass mutable default 문제를 설명하세요.

    Returns:
        dict: {
            "problem": str,
            "fix": str
        }
    """
    return {
        "problem": "",
        "fix": ""
    }
''',
                solution_code='''def solution():
    return {
        "problem": "인스턴스 간 리스트가 공유됨",
        "fix": "field(default_factory=list)"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"fix": "field(default_factory=list)"},
                        "is_hidden": False
                    }
                ],
                constraints=["dataclasses의 기본값 규칙을 이해해야 합니다"],
                hints=["default_factory를 사용하세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="__slots__의 효과",
                slug="slots-memory-benefit",
                description="""## __slots__란?

다음 코드의 결과를 예측하세요.

```python
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
print(hasattr(p, "__dict__"))
```

### 질문
1. 출력 결과는?
2. __slots__의 장점은?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.OOP,
                starter_code='''def solution():
    """
    __slots__의 효과를 설명하세요.

    Returns:
        dict: {
            "has_dict": bool,
            "benefit": str
        }
    """
    return {
        "has_dict": None,
        "benefit": ""
    }
''',
                solution_code='''def solution():
    return {
        "has_dict": False,
        "benefit": "인스턴스 메모리 사용량 감소 및 속성 접근 최적화"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"has_dict": False},
                        "is_hidden": False
                    }
                ],
                constraints=["__slots__는 동적 속성 추가를 제한합니다"],
                hints=["__dict__가 생성되는지 확인하세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="메타클래스 __new__ vs __init__",
                slug="metaclass-new-vs-init",
                description="""## 메타클래스 호출 순서

다음 중 어떤 메서드가 먼저 호출되는가?

```python
class Meta(type):
    def __new__(mcls, name, bases, namespace):
        return super().__new__(mcls, name, bases, namespace)

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
```

### 질문
메타클래스에서 __new__와 __init__의 호출 순서는?""",
                difficulty=DifficultyLevel.HARD,
                category=ProblemCategory.OOP,
                starter_code='''def solution():
    """
    메타클래스 호출 순서를 설명하세요.

    Returns:
        dict: {
            "order": list[str]
        }
    """
    return {
        "order": []
    }
''',
                solution_code='''def solution():
    return {
        "order": ["__new__", "__init__"]
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"order": ["__new__", "__init__"]},
                        "is_hidden": False
                    }
                ],
                constraints=["클래스 생성 과정을 이해해야 합니다"],
                hints=["객체 생성 -> 초기화 순서와 같습니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="asyncio 작업 순서",
                slug="asyncio-task-order",
                description="""## asyncio 실행 순서

다음 코드의 출력 순서를 예측하세요.

```python
import asyncio

async def main():
    task = asyncio.create_task(asyncio.sleep(0.1))
    print("A")
    await task
    print("B")

asyncio.run(main())
```

### 질문
출력 순서는?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.CONCURRENCY,
                starter_code='''def solution():
    """
    asyncio 작업 순서를 설명하세요.

    Returns:
        dict: {
            "order": list[str]
        }
    """
    return {
        "order": []
    }
''',
                solution_code='''def solution():
    return {
        "order": ["A", "B"]
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"order": ["A", "B"]},
                        "is_hidden": False
                    }
                ],
                constraints=["create_task는 즉시 실행을 보장하지 않습니다"],
                hints=["print는 await보다 먼저 실행됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="I/O 작업과 GIL",
                slug="gil-io-release",
                description="""## GIL과 I/O

### 질문
1. Python은 대부분의 표준 I/O 작업 중 GIL을 해제하는가?
2. CPU-bound 작업에서 스레드 병렬화가 제한되는 이유는?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.GIL,
                starter_code='''def solution():
    """
    GIL과 I/O의 관계를 설명하세요.

    Returns:
        dict: {
            "gil_released_on_io": bool,
            "cpu_bound_parallel": bool
        }
    """
    return {
        "gil_released_on_io": None,
        "cpu_bound_parallel": None
    }
''',
                solution_code='''def solution():
    return {
        "gil_released_on_io": True,
        "cpu_bound_parallel": False
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"gil_released_on_io": True},
                        "is_hidden": False
                    }
                ],
                constraints=["GIL의 역할을 이해해야 합니다", "모든 I/O가 GIL을 해제하는 것은 아닙니다"],
                hints=["I/O 대기 중에는 다른 스레드가 실행될 수 있습니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="Context Manager 순서",
                slug="context-manager-order",
                description="""## with 문의 호출 순서

다음 코드의 출력 순서를 예측하세요.

```python
class CM:
    def __init__(self, name):
        self.name = name
    def __enter__(self):
        print(f"enter {self.name}")
        return self
    def __exit__(self, exc_type, exc, tb):
        print(f"exit {self.name}")

with CM("A") as a, CM("B") as b:
    pass
```

### 질문
출력 순서는?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.OOP,
                starter_code='''def solution():
    """
    context manager의 실행 순서를 설명하세요.

    Returns:
        dict: {
            "order": list[str]
        }
    """
    return {
        "order": []
    }
''',
                solution_code='''def solution():
    return {
        "order": ["enter A", "enter B", "exit B", "exit A"]
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"order": ["enter A", "enter B", "exit B", "exit A"]},
                        "is_hidden": False
                    }
                ],
                constraints=["with의 중첩을 이해해야 합니다"],
                hints=["stack처럼 후입선출로 종료됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="Iterator Protocol",
                slug="iterator-protocol",
                description="""## Iterator의 핵심 메서드

### 질문
1. Iterator가 되기 위한 필수 메서드는 무엇인가?
2. 반복이 끝났음을 어떻게 알리는가?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.GENERATOR,
                starter_code='''def solution():
    """
    Iterator protocol을 설명하세요.

    Returns:
        dict: {
            "requires": str,
            "stop": str
        }
    """
    return {
        "requires": "",
        "stop": ""
    }
''',
                solution_code='''def solution():
    return {
        "requires": "__iter__ and __next__",
        "stop": "StopIteration"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"stop": "StopIteration"},
                        "is_hidden": False
                    }
                ],
                constraints=["Iterator와 Iterable을 구분하세요"],
                hints=["for 문이 호출하는 메서드를 떠올리세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="Generator send 동작",
                slug="generator-send",
                description="""## generator.send()

다음 코드의 결과는?

```python
def gen():
    x = yield "ready"
    return x

g = gen()
a = next(g)
try:
    g.send(10)
except StopIteration as e:
    result = e.value
```

### 질문
1. a의 값은?
2. result의 값은?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.GENERATOR,
                starter_code='''def solution():
    """
    generator.send 동작을 설명하세요.

    Returns:
        dict: {
            "first": str,
            "return": int
        }
    """
    return {
        "first": "",
        "return": 0
    }
''',
                solution_code='''def solution():
    return {
        "first": "ready",
        "return": 10
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"return": 10},
                        "is_hidden": False
                    }
                ],
                constraints=["yield 표현식의 값을 이해해야 합니다"],
                hints=["send는 yield 위치로 값을 전달합니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="yield from 동작",
                slug="yield-from-basic",
                description="""## yield from

다음 코드의 출력 결과는?

```python
def outer():
    yield from [1, 2]
    yield 3

print(list(outer()))
```

### 질문
출력 결과는 무엇인가?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.GENERATOR,
                starter_code='''def solution():
    """
    yield from의 동작을 설명하세요.

    Returns:
        dict: {
            "result": list[int]
        }
    """
    return {
        "result": []
    }
''',
                solution_code='''def solution():
    return {
        "result": [1, 2, 3]
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"result": [1, 2, 3]},
                        "is_hidden": False
                    }
                ],
                constraints=["yield from은 하위 iterator에 위임합니다"],
                hints=["리스트의 요소가 그대로 전달됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="functools.wraps의 역할",
                slug="functools-wraps",
                description="""## 데코레이터와 메타데이터

### 질문
1. @functools.wraps 없이 데코레이터를 쓰면 함수 이름은 무엇이 되는가?
2. wraps를 사용하면 어떤 문제가 해결되는가?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.DECORATOR,
                starter_code='''def solution():
    """
    functools.wraps의 효과를 설명하세요.

    Returns:
        dict: {
            "without": str,
            "with": str
        }
    """
    return {
        "without": "",
        "with": ""
    }
''',
                solution_code='''def solution():
    return {
        "without": "wrapper",
        "with": "원본 함수의 __name__"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"without": "wrapper"},
                        "is_hidden": False
                    }
                ],
                constraints=["__name__과 __doc__ 보존을 이해해야 합니다"],
                hints=["wraps는 원본 함수의 메타데이터를 복사합니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="lru_cache의 효과",
                slug="lru-cache-effect",
                description="""## lru_cache

다음 상황에서 함수 본문이 실제로 실행되는 횟수는?

```python
from functools import lru_cache

@lru_cache
def f(x):
    return x * 2

f(1)
f(1)
```

### 질문
실제 함수 실행 횟수는?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.CPYTHON,
                starter_code='''def solution():
    """
    lru_cache의 효과를 설명하세요.

    Returns:
        dict: {
            "executions": int
        }
    """
    return {
        "executions": 0
    }
''',
                solution_code='''def solution():
    return {
        "executions": 1
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"executions": 1},
                        "is_hidden": False
                    }
                ],
                constraints=["캐시가 적중하면 함수가 재실행되지 않습니다"],
                hints=["동일 인자는 캐시됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="작은 정수 캐싱 범위",
                slug="small-int-cache-range",
                description="""## Integer Caching

### 질문
CPython에서 기본적으로 캐싱되는 정수 범위는? (구현/버전에 따라 달라질 수 있음)""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.CPYTHON,
                starter_code='''def solution():
    """
    작은 정수 캐싱 범위를 설명하세요.

    Returns:
        dict: {
            "range": str
        }
    """
    return {
        "range": ""
    }
''',
                solution_code='''def solution():
    return {
        "range": "-5..256"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"range": "-5..256"},
                        "is_hidden": False
                    }
                ],
                constraints=["CPython 기준입니다", "구현/버전에 따라 범위가 달라질 수 있습니다"],
                hints=["작은 정수는 재사용됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="문자열 interning",
                slug="string-interning",
                description="""## String Interning

다음 코드의 결과는?

```python
import sys
a = sys.intern("hello")
b = sys.intern("hello")
print(a is b)
```

### 질문
출력 결과는 무엇이고, 이유는?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.CPYTHON,
                starter_code='''def solution():
    """
    문자열 interning을 설명하세요.

    Returns:
        dict: {
            "interned_is_same": bool,
            "reason": str
        }
    """
    return {
        "interned_is_same": None,
        "reason": ""
    }
''',
                solution_code='''def solution():
    return {
        "interned_is_same": True,
        "reason": "sys.intern은 동일 문자열을 하나의 객체로 재사용"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"interned_is_same": True},
                        "is_hidden": False
                    }
                ],
                constraints=["intern은 메모리 최적화를 위한 기능입니다"],
                hints=["is는 동일 객체 여부를 확인합니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="해시 랜덤화",
                slug="hash-randomization",
                description="""## Hash Randomization

### 질문
1. 같은 문자열의 hash 값은 같은 프로세스 안에서 항상 동일한가?
2. 다른 프로세스 실행 간에도 동일한가?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.CPYTHON,
                starter_code='''def solution():
    """
    Python 해시 랜덤화를 설명하세요.

    Returns:
        dict: {
            "stable_within_process": bool,
            "stable_across_runs": bool
        }
    """
    return {
        "stable_within_process": None,
        "stable_across_runs": None
    }
''',
                solution_code='''def solution():
    return {
        "stable_within_process": True,
        "stable_across_runs": False
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"stable_across_runs": False},
                        "is_hidden": False
                    }
                ],
                constraints=["PYTHONHASHSEED에 따라 달라질 수 있습니다"],
                hints=["보안상의 이유로 랜덤화됩니다", "PYTHONHASHSEED=0이면 프로세스 간에도 동일해질 수 있습니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="dict 리사이즈 임계치",
                slug="dict-resize-threshold",
                description="""## dict 리사이즈

### 질문
CPython의 dict는 어느 정도 채워졌을 때 리사이즈되는가?""",
                difficulty=DifficultyLevel.HARD,
                category=ProblemCategory.DATA_STRUCTURE,
                starter_code='''def solution():
    """
    dict 리사이즈 임계치를 설명하세요.

    Returns:
        dict: {
            "resize_threshold": str
        }
    """
    return {
        "resize_threshold": ""
    }
''',
                solution_code='''def solution():
    return {
        "resize_threshold": "~2/3"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"resize_threshold": "~2/3"},
                        "is_hidden": False
                    }
                ],
                constraints=["CPython 구현 기준입니다"],
                hints=["해시 충돌을 줄이기 위해 여유를 둡니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="list over-allocation",
                slug="list-over-allocation",
                description="""## list append의 암묵적 최적화

### 질문
1. list는 왜 over-allocation을 하는가?
2. append의 평균 시간 복잡도는?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.DATA_STRUCTURE,
                starter_code='''def solution():
    """
    list의 over-allocation을 설명하세요.

    Returns:
        dict: {
            "strategy": str,
            "amortized": str
        }
    """
    return {
        "strategy": "",
        "amortized": ""
    }
''',
                solution_code='''def solution():
    return {
        "strategy": "over-allocation",
        "amortized": "O(1)"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"amortized": "O(1)"},
                        "is_hidden": False
                    }
                ],
                constraints=["append는 평균적으로 O(1)입니다"],
                hints=["resize 비용을 분산시킵니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="CPU-bound 병렬 처리",
                slug="cpu-bound-parallelism",
                description="""## CPU-bound 처리 전략

### 질문
CPU-bound 작업을 병렬로 처리할 때 가장 적합한 방법은?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.CONCURRENCY,
                starter_code='''def solution():
    """
    CPU-bound 작업 처리 방식을 설명하세요.

    Returns:
        dict: {
            "best": str,
            "reason": str
        }
    """
    return {
        "best": "",
        "reason": ""
    }
''',
                solution_code='''def solution():
    return {
        "best": "multiprocessing",
        "reason": "GIL로 인해 스레드 병렬 실행이 제한됨"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"best": "multiprocessing"},
                        "is_hidden": False
                    }
                ],
                constraints=["CPU-bound vs I/O-bound를 구분하세요"],
                hints=["프로세스는 GIL을 공유하지 않습니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="multiprocessing과 pickling",
                slug="multiprocessing-pickling",
                description="""## multiprocessing 제약 (spawn 기준)

### 질문
Process로 전달되는 함수는 어떤 조건을 만족해야 하는가?""",
                difficulty=DifficultyLevel.MEDIUM,
                category=ProblemCategory.CONCURRENCY,
                starter_code='''def solution():
    """
    multiprocessing에서의 pickling 제약을 설명하세요.

    Returns:
        dict: {
            "must_be_picklable": bool,
            "nested_function": bool
        }
    """
    return {
        "must_be_picklable": None,
        "nested_function": None
    }
''',
                solution_code='''def solution():
    return {
        "must_be_picklable": True,
        "nested_function": False
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"nested_function": False},
                        "is_hidden": False
                    }
                ],
                constraints=["spawn 방식에서는 pickling이 필수입니다"],
                hints=["최상위 함수가 안전합니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="global vs nonlocal",
                slug="global-vs-nonlocal",
                description="""## 스코프 수정 키워드

다음 코드에서 outer의 반환값은?

```python
def outer():
    x = 1
    def inner():
        nonlocal x
        x = 2
    inner()
    return x
```

### 질문
1. 반환값은?
2. nonlocal의 역할은?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.CLOSURE,
                starter_code='''def solution():
    """
    global과 nonlocal의 차이를 설명하세요.

    Returns:
        dict: {
            "outer_x": int,
            "keyword": str
        }
    """
    return {
        "outer_x": 0,
        "keyword": ""
    }
''',
                solution_code='''def solution():
    return {
        "outer_x": 2,
        "keyword": "nonlocal"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"outer_x": 2},
                        "is_hidden": False
                    }
                ],
                constraints=["nonlocal은 가장 가까운 enclosing 스코프를 수정합니다"],
                hints=["global과의 차이를 떠올리세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="Descriptor Protocol",
                slug="descriptor-protocol",
                description="""## Descriptor 동작

다음 코드의 출력 결과는?

```python
class D:
    def __get__(self, obj, objtype=None):
        return 42

class C:
    x = D()

c = C()
print(c.x)
```

### 질문
출력 결과와 이유는?""",
                difficulty=DifficultyLevel.HARD,
                category=ProblemCategory.OOP,
                starter_code='''def solution():
    """
    descriptor protocol을 설명하세요.

    Returns:
        dict: {
            "value": int,
            "protocol": str
        }
    """
    return {
        "value": 0,
        "protocol": ""
    }
''',
                solution_code='''def solution():
    return {
        "value": 42,
        "protocol": "__get__"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"value": 42},
                        "is_hidden": False
                    }
                ],
                constraints=["descriptor는 attribute 접근을 가로챕니다"],
                hints=["__get__이 호출됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="클래스 vs 인스턴스 속성",
                slug="class-vs-instance-attribute",
                description="""## 속성 해석 순서

다음 코드의 결과는?

```python
class C:
    x = 1

c = C()
c.x = 2

print(C.x)
print(c.x)
```

### 질문
두 출력값은 무엇인가?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.OOP,
                starter_code='''def solution():
    """
    클래스/인스턴스 속성 차이를 설명하세요.

    Returns:
        dict: {
            "class_x": int,
            "instance_x": int
        }
    """
    return {
        "class_x": 0,
        "instance_x": 0
    }
''',
                solution_code='''def solution():
    return {
        "class_x": 1,
        "instance_x": 2
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"class_x": 1},
                        "is_hidden": False
                    }
                ],
                constraints=["인스턴스 속성은 클래스 속성을 가립니다"],
                hints=["attribute lookup 순서를 떠올리세요"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="MRO (C3 Linearization)",
                slug="mro-c3-linearization",
                description="""## MRO 순서

다음 클래스의 MRO 순서는?

```python
class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass
```

### 질문
D.mro()의 순서는?""",
                difficulty=DifficultyLevel.HARD,
                category=ProblemCategory.OOP,
                starter_code='''def solution():
    """
    MRO 순서를 설명하세요.

    Returns:
        dict: {
            "order": list[str]
        }
    """
    return {
        "order": []
    }
''',
                solution_code='''def solution():
    return {
        "order": ["D", "B", "C", "A", "object"]
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"order": ["D", "B", "C", "A", "object"]},
                        "is_hidden": False
                    }
                ],
                constraints=["C3 linearization을 이해해야 합니다"],
                hints=["왼쪽부터 병합됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
            Problem(
                title="classmethod vs staticmethod",
                slug="classmethod-vs-staticmethod",
                description="""## 메서드 타입

### 질문
1. classmethod는 어떤 인자를 암묵적으로 받는가?
2. staticmethod는 암묵적 인자가 있는가?""",
                difficulty=DifficultyLevel.EASY,
                category=ProblemCategory.OOP,
                starter_code='''def solution():
    """
    classmethod와 staticmethod 차이를 설명하세요.

    Returns:
        dict: {
            "classmethod_arg": str,
            "staticmethod_arg": str
        }
    """
    return {
        "classmethod_arg": "",
        "staticmethod_arg": ""
    }
''',
                solution_code='''def solution():
    return {
        "classmethod_arg": "cls",
        "staticmethod_arg": "none"
    }
''',
                test_cases=[
                    {
                        "input": {},
                        "expected_output": {"classmethod_arg": "cls"},
                        "is_hidden": False
                    }
                ],
                constraints=["인스턴스 메서드와 구분하세요"],
                hints=["classmethod는 클래스에 바인딩됩니다"],
                time_complexity="N/A",
                space_complexity="N/A"
            ),
        ]

        session.add_all(problems)
        await session.commit()

        print(f"Created {len(problems)} Python Deep Dive quizzes")
        print("\nDatabase seeded successfully!")
        print("\nTest Credentials:")
        print("- Admin: admin@codepath.com / Admin123!")
        print("- User: test@codepath.com / Test123!")

    await engine.dispose()


if __name__ == "__main__":
    print("Seeding database with Python Deep Dive quizzes...")
    asyncio.run(seed_database())
