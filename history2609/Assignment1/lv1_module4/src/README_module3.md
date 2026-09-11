# 모듈 ③ 파일을 여기에 복사하세요

이 과제는 모듈 ③ 에서 **여러분이 직접 구현한** 네 파일을 그대로 import 합니다.
배포본에는 들어 있지 않으므로, 모듈 ③ 작업 폴더의 `src/` 에서 아래 네 파일을
이 폴더(`lv1_module4/src/`)로 복사해 넣으세요.

```
lv1_module3_student/src/vectors.py           ->  src/vectors.py
lv1_module3_student/src/rotation.py          ->  src/rotation.py
lv1_module3_student/src/transform.py         ->  src/transform.py
lv1_module3_student/src/coordinate_chain.py  ->  src/coordinate_chain.py
```

Windows PowerShell 예시 (경로는 본인 환경에 맞게):

```powershell
Copy-Item ..\lv1_module3_student\src\vectors.py, ..\lv1_module3_student\src\rotation.py, `
          ..\lv1_module3_student\src\transform.py, ..\lv1_module3_student\src\coordinate_chain.py  src\
```

## 이 과제가 사용하는 모듈 ③ API

| 모듈 | 함수 / 클래스 | 용도 |
|---|---|---|
| `rotation.py` | `rot_x`, `rot_y`, `rot_z`, `rodrigues` | 장면 좌표계 정의, 참값 회전 생성 |
| `rotation.py` | `axis_angle_from_matrix`, `quaternion_from_axis_angle` | 각도 오차 계산, 쿼터니언 비교 |
| `transform.py` | `make_T`, `inv_T`, `transform_points` | 동차변환, 점군 벡터화 변환 |
| `coordinate_chain.py` | `CoordinateChain`, `default_chain`, `camera_point_to_base` | base-link-camera 체인 |
| `vectors.py` | (`rotation.py` 가 내부에서 import) | `det`, `normalize`, `skew` |

쿼터니언 순서는 모듈 ③ 과 같은 **(x, y, z, w)** 입니다 (SciPy `Rotation.as_quat()` 와 동일).

복사한 뒤 아래 명령이 오류 없이 돌아가면 준비가 된 것입니다.

```powershell
python -c "from src.coordinate_chain import default_chain; print(default_chain().T('base', 'camera'))"
```

모듈 ③ 의 함수가 아직 `NotImplementedError` 를 내는 상태라면 이 과제의 노트북도 그 지점에서 멈춥니다.
먼저 모듈 ③ 을 완성하세요.
