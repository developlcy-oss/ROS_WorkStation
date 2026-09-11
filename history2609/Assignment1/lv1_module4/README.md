# Lv.1 모듈 ④ 과제 — 픽앤플레이스 로봇의 자세 추정과 궤적 생성 (학생 배포본)

과제 지시문 `과제4_픽앤플레이스_자세추정.md` 를 푸는 **작업 폴더**입니다.
모듈 ①②③ 에서 만든 도구를 하나로 묶어, **점군에서 물체 자세를 추정하고 그곳까지의 궤적을
생성해 애니메이션으로 시연**하는 end-to-end 파이프라인을 완성합니다.

> **환경 규격**: Python 3.10 이상 · **표준 venv 가상환경** (Anaconda 사용 안 함) · JupyterLab 4.0 이상 · ipykernel
> **난수 시드**: 모든 난수는 `np.random.default_rng(42)` 로 고정합니다. 시드가 다르면 오차 수치가 채점 기준과 달라집니다.
> **제출**: 본인 GitHub 저장소의 `lv1_module4/` 폴더 (zip 아님 — 7절 참고).

---

## 0. 무엇이 제공되고 무엇을 채우는가

| 구분 | 제공 (그대로 사용) | 직접 작성 (TODO) |
|---|---|---|
| 노트북 | 문제 설명, **모든 `# --- 검증 ---` 셀**, **모든 3D 그림·그래프·애니메이션 셀**, pytest 실행 셀, 답안 템플릿 | `TODO` 코드 셀 (검증 셀이 참조하는 **변수 이름 그대로** 만들기), 마크다운의 `___` 빈칸 |
| `src/` | `plot3d.py` (3D 헬퍼, 애니메이션), `pose_estimation.rotation_angle_deg` | `pose_pipeline.py`, `quaternion.py`, `trajectory.py`, `pose_estimation.py` 의 함수 본문 |
| `src/` (모듈 ③) | — | **모듈 ③ 에서 만든 `vectors.py`, `rotation.py`, `transform.py`, `coordinate_chain.py` 를 복사해 넣기** (`src/README_module3.md`) |
| `tests/` | `conftest.py` | `test_pose_pipeline.py`, `test_quaternion.py`, `test_trajectory.py` 의 테스트 본문 |
| 기타 | `requirements.txt`, `presentation_template.md` | `presentation.md` (템플릿 복사 후 작성), `demo.gif` (문제 6 셀이 생성) |

검증 셀은 수정하지 마세요. 검증 셀의 `[PASS]`/`[FAIL]` 이 채점의 1차 근거입니다.

---

## 1. 사전 확인 — Python 이 있는가

```powershell
python --version
```

`Python 3.10.x` 이상이 나오면 됩니다. 안 나오거나 버전이 낮으면
[python.org/downloads](https://www.python.org/downloads/) 에서 설치하세요 (**"Add python.exe to PATH"** 체크).

> **Anaconda 를 쓰지 않는 이유** — 이 과정은 이후 ROS 2 와 붙습니다. conda 환경은 시스템 Python 과
> 라이브러리 경로가 섞여 ROS 2 패키지 빌드에서 충돌이 잦습니다. 표준 `venv` 는 폴더 하나(`.venv/`)만 만듭니다.

---

## 2. venv 가상환경 만들기와 커널 등록

이 README 가 있는 폴더에서:

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ipykernel install --user --name pose_lab --display-name "Python (pose_lab)"
```

`Activate.ps1` 이 정책 때문에 막히면: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` 후 재시도.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ipykernel install --user --name pose_lab --display-name "Python (pose_lab)"
```

### 확인

```powershell
python -c "import sys; print(sys.executable)"
jupyter kernelspec list
```

첫 줄은 이 폴더의 `.venv` 안을 가리켜야 하고, 둘째 줄 목록에 `pose_lab` 이 보여야 합니다.
**문제 1 의 첫 셀이 `sys.executable` 을 출력해 `.venv` 가 포함되어 있는지 검증합니다.**

| 패키지 | 용도 |
|---|---|
| `numpy`, `scipy` | 배열 연산 · `CubicSpline` · SLERP/쿼터니언 비교 대상 (`scipy.spatial.transform`) |
| `matplotlib` | 3D 좌표계, 궤적, 오차 그래프, 애니메이션 (`FuncAnimation`) |
| `pillow` | `demo.gif` 저장 (`writer="pillow"`) |
| `pytest` | 문제 2·3·4 의 테스트 |
| `jupyterlab`, `ipykernel` | 노트북 환경과 커널 등록 |

---

## 3. 모듈 ③ 파일 복사 (필수)

이 과제는 모듈 ③ 에서 **여러분이 구현한** 네 파일을 그대로 import 합니다. 배포본에는 들어 있지 않습니다.

```
lv1_module3_student/src/vectors.py, rotation.py, transform.py, coordinate_chain.py  ->  src/
```

자세한 방법과 확인 명령은 `src/README_module3.md` 를 보세요. 모듈 ③ 이 `NotImplementedError` 상태라면
이 과제도 그 지점에서 멈춥니다.

---

## 4. JupyterLab 실행과 커널 선택

```powershell
jupyter lab
```

`notebooks/01_pipeline.ipynb` 부터 순서대로 진행합니다. 노트북 오른쪽 위 커널 이름이
**Python (pose_lab)** 인지 확인하세요 (다르면 클릭해 바꿉니다).

---

## 5. 어떻게 진행하나

노트북은 문항마다 **(1) 설명 마크다운 → (2) TODO 코드 셀 → (3) 그림 셀(제공) → (4) `# --- 검증 ---` 셀(제공)** 순서입니다.

1. 설명 마크다운을 읽고 `___` 빈칸이 무엇을 요구하는지 파악합니다.
2. `src/*.py` 의 해당 함수를 docstring 계약대로 구현하고 `raise NotImplementedError(...)` 줄을 지웁니다.
3. TODO 셀에서 **주석에 적힌 변수 이름 그대로** 결과를 만듭니다. 그림 셀과 검증 셀이 그 이름을 참조합니다.
4. 그림 셀과 검증 셀을 실행합니다. 검증 셀은 `[PASS]`/`[FAIL]` 을 찍고 마지막에 `전체 통과: True` 가 나와야 합니다.
5. 마지막 답안 템플릿 셀의 `___` 를 계산한 값과 설명으로 채웁니다.

`src/` 를 고친 뒤에는 커널을 재시작하거나 첫 셀 위에 `%load_ext autoreload` / `%autoreload 2` 를 넣어 두세요.

### 노트북별 내용

| 노트북 | 문제 | 구현하는 모듈 |
|---|---|---|
| `01_pipeline.ipynb` | 1 환경·좌표계 모델링, 2 `PosePipeline` | `src/pose_pipeline.py`, `tests/test_pose_pipeline.py` |
| `02_interpolation.ipynb` | 3 쿼터니언·SLERP, 4 궤적 보간 | `src/quaternion.py`, `src/trajectory.py`, `tests/test_quaternion.py`, `tests/test_trajectory.py` |
| `03_pose_estimation.ipynb` | 5 PCA·Kabsch·최소제곱, 6 애니메이션·발표 | `src/pose_estimation.py`, `demo.gif`, `presentation.md` |

### 공통 규칙

- 난수는 전부 `np.random.default_rng(42)`. 문제 5 의 점군 생성 코드는 노트북에 있는 그대로 씁니다
  (`n_points = 240`, 표준편차 0.35 / 0.10 / 0.05).
- 쿼터니언 순서는 **(x, y, z, w)** (모듈 ③·SciPy 와 동일).
- SciPy 의 `Rotation`/`Slerp` 는 **비교 대상**으로만 씁니다. `CubicSpline` 은 `cubic_spline_interp` 안에서 써도 됩니다.
- 비교는 `np.allclose` / `np.isclose` 기본 허용오차를 씁니다.
- 점군 변환은 반복문 없이 `transform_points` 로 한 번에.

### pytest

```powershell
pytest -v
```

노트북의 pytest 실행 셀(2-3, 3-6, 4-6)이 같은 명령을 돌려 통과 출력을 노트북에 남깁니다. 실패 0 이어야 합니다.

---

## 6. 폴더 구조

```
lv1_module4/
├── README.md                 # 이 문서
├── requirements.txt          # 문제 1 의 pip freeze 셀이 덮어씀
├── presentation_template.md  # -> presentation.md 로 복사해 작성
├── presentation.md           # (작성) 발표 자료 — 5개 절 필수
├── demo.gif                  # (생성) 문제 6 애니메이션
├── notebooks/
│   ├── 01_pipeline.ipynb         문제 1·2
│   ├── 02_interpolation.ipynb    문제 3·4
│   └── 03_pose_estimation.ipynb  문제 5·6
├── src/
│   ├── __init__.py
│   ├── README_module3.md         모듈 ③ 파일 복사 안내
│   ├── vectors.py                (모듈 ③ 에서 복사)
│   ├── rotation.py               (모듈 ③ 에서 복사)
│   ├── transform.py              (모듈 ③ 에서 복사)
│   ├── coordinate_chain.py       (모듈 ③ 에서 복사)
│   ├── pose_pipeline.py          문제 2 — PosePipeline (TODO)
│   ├── quaternion.py             문제 3 — 행렬<->쿼터니언, SLERP (TODO)
│   ├── trajectory.py             문제 4 — 선형/스플라인/5차 다항식 (TODO)
│   ├── pose_estimation.py        문제 5 — PCA·Kabsch·평면 피팅 (TODO)
│   └── plot3d.py                 3D 그림·애니메이션 헬퍼 (제공)
└── tests/
    ├── conftest.py               (수정 불필요)
    ├── test_pose_pipeline.py     문제 2 (TODO, 2개 이상)
    ├── test_quaternion.py        문제 3 (TODO)
    └── test_trajectory.py        문제 4 (TODO)
```

함수 이름·반환 형식은 **바꾸지 마세요.** 검증 셀과 테스트가 그 계약을 기준으로 돕니다.

---

## 7. 제출 — GitHub 저장소 `lv1_module4/`

압축 파일이 아니라 **본인 GitHub 저장소**에 이 폴더 전체를 `lv1_module4/` 로 올립니다.

### 제출 전 필수 확인

1. 세 노트북 모두 **Kernel → Restart Kernel and Run All Cells...** 로 처음부터 끝까지 오류 없이 통과하고,
   **그래프와 출력이 남은 상태로 저장**합니다. 셀을 위아래로 오가며 실행한 노트북은 채점자 환경에서 재현되지 않습니다.
2. `pytest -v` 실패 0.
3. `01_pipeline.ipynb` 의 `pip freeze` 셀로 `requirements.txt` 최신화.
4. `demo.gif`, `presentation.md` (다섯 절, `___` 없음) 가 있는지 확인.

### 올릴 것 / 올리지 말 것

- 올림: `notebooks/` (출력 포함), `src/` (모듈 ③ 복사본 포함), `tests/`, `requirements.txt`, `demo.gif`, `presentation.md`, `README.md`
- 올리지 않음: `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ipynb_checkpoints/`

```powershell
# 예시 (저장소 루트에서)
git add lv1_module4
git commit -m "lv1_module4: 픽앤플레이스 자세 추정 과제 제출"
git push
```

`.gitignore` 에 아래를 넣어 두면 실수로 올리는 일을 막을 수 있습니다.

```
.venv/
__pycache__/
.pytest_cache/
.ipynb_checkpoints/
```

---

## 8. 자주 걸리는 문제

| 증상 | 원인과 해결 |
|---|---|
| `ModuleNotFoundError: No module named 'src.rotation'` (또는 `vectors`, `transform`, `coordinate_chain`) | 모듈 ③ 파일을 아직 복사하지 않았습니다. 3절. |
| `NotImplementedError` | 아직 구현하지 않은 함수입니다. 해당 `src/*.py` 를 채우고 커널을 재시작하세요. |
| `NameError: name 'P_base' is not defined` (검증 셀) | TODO 셀에서 주석에 적힌 변수 이름을 그대로 만들지 않았습니다. |
| 1-1 검증 `.venv 가 포함` FAIL | 커널이 가상환경이 아닙니다. 커널을 **Python (pose_lab)** 으로 바꾸세요. |
| `ModuleNotFoundError: No module named 'src'` | 노트북을 `notebooks/` 안에서 열면 cwd 가 달라집니다. 첫 셀의 `sys.path.insert` 가 처리하므로 **첫 셀부터** 실행하세요. |
| 함수를 고쳤는데 결과가 그대로 | 커널이 예전 모듈을 캐시하고 있습니다. 커널 재시작 또는 `%autoreload 2`. |
| `anim.save` 에서 `MovieWriter pillow unavailable` | `pip install pillow`. |
| 애니메이션이 노트북에 안 보임 | `HTML(anim.to_jshtml())` 이 셀의 **마지막 줄**이어야 합니다 (제공 셀 그대로 두세요). |
| 그래프의 한글이 네모(□)로 보임 | 첫 셀이 `Malgun Gothic` 등을 자동으로 잡습니다. 없으면 `plt.rcParams["font.family"]` 를 설치된 한글 폰트로. |
| `ImportError: DLL load failed ... 애플리케이션 제어 정책` | 사내 PC 의 WDAC/AppLocker. 해당 패키지를 한 단계 낮은 버전으로 (`scipy==1.15.3`, `pyzmq==26.2.0`). |
| 채점 기준과 수치가 다름 | 시드를 확인하세요. **`np.random.default_rng(42)`** 이고, 셀 실행 순서가 섞이면 난수 순서도 달라집니다. Restart & Run All. |
