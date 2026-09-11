
# 문제 1

## 참고내용
- 배달 로봇
- 2D 라이다(10Hz)
- RGB 카메라(30fps·1080p)
- IMU(200Hz)
- 바퀴 엔코더(1kHz) 
- 모터 드라이버
- LTE 모듈
  
## 1. 연산 분담 배치표 — 작업 / 위치 / 지연 예산 / 데이터량 / 근거 (6행)
| 작업 | 처리 위치 | 지연 예산 | 데이터량 | 근거 |
|:------|:-----------:|:--------|:------|:-----------:|
|모터 속도 제어|임베디드|1ms|약 8 KB/s|엔코더가 1 kHz로 동작하므로 1회 2바이트 × 4개 데이터로 가정하면 약 8 KB/s이다. 데이터량은 작지만 1 ms 수준의 빠르고 결정적인 제어가 필요하므로 임베디드에서 처리한다.|
|장애물 감지|Edge AI|100 ms 이하|약 14.4 KB/s (LiDAR)|LiDAR가 10 Hz로 동작하고 1회 360개 측정값 × 4 byte로 가정하면 약 14.4 KB/s이다. 10 Hz 센서이므로 최대 약 100 ms 내에 처리해야 하며, 즉각적인 장애물 대응을 위해 Edge에서 처리한다.|
|보행자 인식|Edge AI|약 33 ms|약 186.6 MB/s (RGB 원시 영상)|1920×1080 RGB 영상을 30 fps로 전송하면 1프레임이 약 6.22 MB이고 초당 약 186.6 MB이다. 원시 영상을 LTE로 전송하기에는 데이터량이 매우 크므로 Edge에서 인식한다.|
|지도 기반 경로 계획|클라우드|수백 ms~수초|수십 KB~수 MB 수준| 1~100 ms 단위의 즉각적인 반응이 필수적이지 않으며, 지도 데이터를 이용한 상대적으로 무거운 계산을 클라우드에서 수행할 수 있다.|
|배달 완료 사진 업로드|클라우드|수초~수십초|사진 1장당 수 MB|실시간 제어와 관계없는 작업이며, 촬영한 사진을 압축하여 LTE를 통해 클라우드로 전송할 수 있다.|
|운행 로그 집계|클라우드|수초~분|수 KB~수 MB/min|실시간성이 낮은 작업이므로 운행 데이터를 모아서 클라우드에서 집계할 수 있다. 센서 원시 데이터에 비해 로그 데이터의 크기도 작다.|



## 2. 카메라 원시 영상 전송량
- 1920×1080×3×30= 186,624,000 bytes/s => 186.624 MB/s
- 원시 RGB 영상을 그대로 LTE로 전송하기에는 데이터량이 지나치게 크다. 따라서 카메라 영상은 Edge에서 압축 또는 AI 추론하고, 필요한 결과나 압축 영상을 전송하는 것이 적절하다.

## 3. 인지·판단·제어 계층 매핑과 주기표

```
     인지              판단              제어
┌──────────┐      ┌──────────┐     ┌──────────┐     
│ 장애물 감지 │     │지도 기반 경로 계획 │모터속도 제어│
│ 보행자 인식 │     │          │     │           │
│운행 로그 집계│ ─▶ │          │ ─▶ │           │ 
│          │      │          │     │          │       
└──────────┘      └──────────┘     └──────────┘

배달 완료 사진 업로드 ──────▶ 서버/클라우드
운행 로그 집계       ──────▶ 서버/클라우드

```
 
## 4. Hard / Firm / Soft 분류표 — Hard 항목의 마감 초과 결과
| 작업 | 작업 강도 | Hard 물리 결과 |
|:------|:-----------:|:--------|
|모터 속도 제어|Hard|속도가 제어되지 않을 경우, 충돌사고로 이어질 수 있음|
|장애물 감지|Firm|-|
|보행자 인식|Firm|-|
|지도 기반 경로 계획|Soft|-|
|배달 완료 사진 업로드|Soft|-|
|운행 로그 집계|Soft|-|


## 5. 주기 · 지연 · 지터 구분 — 각 한 문장
- 주기 : 배달 로봇이 일정한 시간 간격으로 센서 데이터를 수집하고 모터를 제어한다.
- 지연 : 장애물을 감지한 후 모터가 정지하기까지 시간이 걸린다.
- 지터 : 배달 주문을 받은 후, 경로를 설정하는 데 걸리는 시간이 매번 달라지는 것이다.

# 문제 2
## 1. 고른 접속 대상: localhost / 가상머신 중 ___ — 무비밀번호 접속 로그와 who·echo $SSH_CONNECTION 출력
- 접속 대상                 :localhost
- 접속 로그

```console     
pa3@pa3-Legion-Pro-5-16IAX10:~$ ssh pa3@localhost
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 6.8.0-136-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

Applications를 위한 확장된 보안 유지보수 비활성화됨.

21개의 업데이트가 즉시 적용 가능합니다.
20개의 업데이트는 일반 보안 업데이트입니다.
추가 업데이트를 확인하려면 apt list --upgradable 을 실행하세요.

146 추가 보안 업데이트는 ESM Apps에 적용될 수 있습니다. 
ESM Apps 서비스 at https://ubuntu.com/esm 활성화에 대해 자세히 알아보십시오.

New release '24.04.4 LTS' available.
Run 'do-release-upgrade' to upgrade to it.

Last login: Tue Aug 25 09:52:14 2026 from 127.0.0.1
```
  
- who·echo $SSH_CONNECTION : 127.0.0.1 41520 127.0.0.1 22

## 2. 개인키·공개키 중 서버에 등록하는 것: ___ — 안전한 이유
- 등록 키: 공개키 
- 이유   : 서버에는 공개키만 등록하고 개인키는 사용자 측에 보관한다. 서버는 공개키를 이용해 사용자가 대응하는 개인키를 소유하고 있음을 검증하므로 개인키를 서버에 전달할 필요가 없어 안전하다.


## 3. 원격 단일 명령 실행과 scp 전송 출력
```console
pa3@pa3-Legion-Pro-5-16IAX10:~$ ls
Desktop  Documents  Downloads  Pictures  Practice  Public  ROS2_WS  SpartaPA  cpp  fake_sensors  git  snap  turtlebot3_ws

pa3@pa3-Legion-Pro-5-16IAX10:~$ cd Downloads/

pa3@pa3-Legion-Pro-5-16IAX10:~/Downloads$ ls
Test.py  src  공부자료

pa3@pa3-Legion-Pro-5-16IAX10:~/Downloads$ scp Test.py pa3@localhost:/home/pa3/
Test.py                                                                                       100%   79    92.4KB/s   00:00    

pa3@pa3-Legion-Pro-5-16IAX10:~/Downloads$ cd ..

pa3@pa3-Legion-Pro-5-16IAX10:~$ ls
Desktop  Documents  Downloads  Pictures  Practice  Public  ROS2_WS  SpartaPA  Test.py  cpp  fake_sensors  git  snap  turtlebot3_ws

```

## 4. 두 장치를 구분한 속성: 라이다 ___ / IMU ___
- 라이다: ATTR{loop/backing_file} → lidar.img
- IMU: ATTR{loop/backing_file} → imu.img

## 5. 작성한 udev 규칙 2개 + 규칙 키 설명표
- 작성한 규칙

SUBSYSTEM=="block", KERNEL=="loop*", ATTR{loop/backing_file}=="/home/pa3/fake_sensors/lidar.img", SYMLINK+="robot_lidar", MODE="0666"

SUBSYSTEM=="block", KERNEL=="loop*", ATTR{loop/backing_file}=="/home/pa3/fake_sensors/imu.img", SYMLINK+="robot_imu", MODE="0666"


- 규칙 키 설명표
  

|어트리뷰트|뜻|
|:------|:-----------|
|SUBSYSTEM|장치가 속한 커널 장치 종류(subsystem) 를 지정|
|KERNEL|커널이 장치에 부여한 장치 이름을 지정|
|ATTR{...}|장치의 sysfs attribute 값을 조건으로 사용|
|SYMLINK+=|해당 장치에 추가할 심볼릭 링크 이름|
|MODE|장치 파일의 권한(permission) 을 지정|
|GROUP|장치 파일의 소유 그룹(group) 을 지정|
|==|조건 비교|
|=|값을 설정/대입|
|+=|기존 값에 추가|

## 6. 순서를 바꿔 재연결한 뒤 ls -l /dev/robot_* 결과
```console
pa3@pa3-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo udevadm control --reload-rules

pa3@pa3-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo losetup -f --show imu.img

sudo losetup -f --show lidar.img /dev/loop19 /dev/loop20one-any.whl (348 kB)
Installing collected packages: pure-eval, ptyprocess, websocket-client, webencodings, webcolors, wcwidth, urllib3, uri-template, tzdata, typing-extensions, traitlets, tornado, tomli, soupsieve, six, send2trash, rpds-py, rfc3986-validator, pyzmq, pyyaml, python-json-logger, pyparsing, pygments, pycparser, psutil, prometheus-client, pluggy, platformdirs, pillow, pexpect, parso, pandocfilters, packaging, overrides, numpy, nest-asyncio2, MarkupSafe, lark, kiwisolver, jupyterlab-pygments, jsonpointer, json5, iniconfig, idna, h11, fqdn, fonttools, fastjsonschema, executing, defusedxml, decorator, debugpy, cycler, comm, charset_normalizer, certifi, babel, attrs, asttokens, tinycss2, terminado, stack_data, scipy, rfc3987-syntax, rfc3339-validator, requests, referencing, python-dateutil, prompt_toolkit, mistune, matplotlib-inline, jupyter-core, jinja2, jedi, httpcore, exceptiongroup, contourpy, cffi, bleach, beautifulsoup4, async-lru, pytest, matplotlib, jupyter-server-terminals, jupyter-client, jupyter-builder, jsonschema-specifications, ipython, arrow, argon2-cffi-bindings, anyio, jsonschema, isoduration, ipykernel, httpx, argon2-cffi, nbformat, nbclient, jupyter-events, nbconvert, jupyter-server, notebook-shim, jupyterlab-server, jupyter-lsp, jupyterlab
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
generate-parameter-library-py 0.7.5 requires typeguard, which is not installed.
Successfully installed MarkupSafe-3.0.3 anyio-4.14.2 argon2-cffi-25.1.0 argon2-cffi-bindings-26.1.0 arrow-1.4.0 asttokens-3.0.2 async-lru-2.3.0 attrs-26.1.0 babel-2.18.0 beautifulsoup4-4.15.0 bleach-6.4.0 certifi-2026.7.22 cffi-2.1.1 charset_normalizer-3.5.1 comm-0.2.3 contourpy-1.3.2 cycler-0.12.1 debugpy-1.8.21 decorator-5.3.1 defusedxml-0.7.1 exceptiongroup-1.3.1 executing-2.2.1 fastjsonschema-2.22.2 fonttools-4.63.0 fqdn-1.5.1 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.19 iniconfig-2.3.0 ipykernel-7.3.0 ipython-8.39.0 isoduration-20.11.0 jedi-0.20.0 jinja2-3.1.6 json5-0.15.0 jsonpointer-3.1.1 jsonschema-4.26.0 jsonschema-specifications-2025.9.1 jupyter-builder-1.2.2 jupyter-client-8.9.1 jupyter-core-5.9.1 jupyter-events-0.12.1 jupyter-lsp-2.3.1 jupyter-server-2.20.0 jupyter-serve
```console
pa3@pa3-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo udevadm trigger --action=add

pa3@pa3-Legion-Pro-5-16IAX10:~/fake_sensors$ ls -l /dev/robot_*
lrwxrwxrwx 1 root root 6  8월 25 17:51 /dev/robot_imu -> loop19
lrwxrwxrwx 1 root root 6  8월 25 17:51 /dev/robot_lidar -> loop20

pa3@pa3-Legion-Pro-5-16IAX10:~/fake_sensors$ 
sudo losetup -d /dev/loop19
sudo losetup -d /dev/loop20

pa3@pa3-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo losetup -f --show lidar.img
sudo losetup -f --show imu.img
/dev/loop19
/dev/loop20

pa3@pa3-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo udevadm trigger --action=add

ls -l /dev/robot_*
lrwxrwxrwx 1 root root 6  8월 25 17:52 /dev/robot_imu -> loop20
lrwxrwxrwx 1 root root 6  8월 25 17:52 /dev/robot_lidar -> loop19
```

## 7. 실제 USB 센서용 규칙 초안과 구분 근거
- LiDAR
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="robot_lidar", MODE="0666"

- IMU
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6015", SYMLINK+="robot_imu", MODE="0666"

- 구분 근거
idVendor가 동일하여, 같은 객체로 인식할 수 있으므로, idProduct를 추가적으로 등록하여 구분할 수 있도록 설정한다.


# 문제 3
## 1. 저장소 URL: ___ / PR URL: ___
- 저장소 URL: https://github.com/developlcy-oss/PA_Assingment1
- PR URL    : https://github.com/developlcy-oss/PA_Assingment1/pulls

## 2. PR 리뷰 코멘트와 반영 커밋 (캡처 또는 링크)

## 3. 충돌이 난 파일과 줄: ___ — 충돌 표식의 뜻과 해결 방법

```console
<<<<<<< feature/compute-layout
- feature/compute-layout 브랜치에서 작업한 내용이 표시 됨
=======
-  main 브랜츠에서 작업한 내용이 표시됨
>>>>>>> main 

- 해결 방법 : main 브런치와 내가 작업한 feature/compute-layout 브랜치의 내용을 확인하고, 살릴 내용과 삭제할 내용을 남긴후
 >>>>>>> main 태그, ======= 태그, <<<<<<< feature/compute-layout 태그를 삭제한다. (브런치 태그 및 ======= 내용 구분자 태그 삭제하기)
```

## 4. merge 방식 이력 그래프 / rebase 방식 이력 그래프 (두 출력 비교)

- 충돌 해결후 merge

```console
pa3@pa3-Legion-Pro-5-16IAX10:~/git/Assignment1$ git log --oneline --graph
*   30a1ace (HEAD -> main) merge: resolve README conflict
|\  
| * 2df8acf (branch-b) test: branch-b conflict
* | 2a0b6d1 (branch-a) test: branch-a conflict
|/  
*   79aaf14 (origin/main) Merge pull request #3 from developlcy-oss/feature/compute-layout
|\  
| * a00f5e2 (origin/feature/compute-layout, feature/compute-layout) Fix formatting in README for delivery robot section
| * d629674 Fix formatting in README for delivery robot section
* |   baf6a30 Merge pull request #2 from developlcy-oss/feature/udev-rules
|\ \  
| * | d63934b (origin/feature/udev-rules) Fix formatting in README for delivery robot section2
* | |   655756b Merge pull request #1 from developlcy-oss/feature/compute-layout
|\ \ \  
| |/ /  
|/| /   
| |/    
| * 0b71f63 fix: report.md 파일 문구 수정
| * f6c6ff0 feat: 99-robot-sensor.rules 첨부
| * 054a1b4 (feature/udev-rules) feat : 연산 분담 설계 문서 작성
|/  
* 42e992e feat: 로봇 스펙 업데이트
* 09d3926 first commit
```

- Rebase 후 커밋

```console
pa3@pa3-Legion-Pro-5-16IAX10:~/git/Assignment1$ git log --oneline --graph
* 875c6b7 (HEAD -> branch-rebase, main) test: new main change
*   30a1ace merge: resolve README conflict
|\  
| * 2df8acf (branch-b) test: branch-b conflict
* | 2a0b6d1 (branch-a) test: branch-a conflict
|/  
*   79aaf14 (origin/main) Merge pull request #3 from developlcy-oss/feature/compute-layout
|\  
| * a00f5e2 (origin/feature/compute-layout, feature/compute-layout) Fix formatting in README for delivery robot section
| * d629674 Fix formatting in README for delivery robot section
* |   baf6a30 Merge pull request #2 from developlcy-oss/feature/udev-rules
|\ \  
| * | d63934b (origin/feature/udev-rules) Fix formatting in README for delivery robot section2
* | |   655756b Merge pull request #1 from developlcy-oss/feature/compute-layout
|\ \ \  
| |/ /  
|/| /   
| |/    
| * 0b71f63 fix: report.md 파일 문구 수정
| * f6c6ff0 feat: 99-robot-sensor.rules 첨부
| * 054a1b4 (feature/udev-rules) feat : 연산 분담 설계 문서 작성
|/  
* 42e992e feat: 로봇 스펙 업데이트
* 09d3926 first commit
```



## 5. 언제 merge 를, 언제 rebase 를 쓸지 — 3줄 이내

rebase는 개인 브랜치를 최신 상태로 정리할 때, merge는 여러 사람이 공유하는 작업을 합칠 때 사용한다.
