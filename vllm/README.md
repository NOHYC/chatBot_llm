# vllm

간단한 설명

이 디렉토리는 vLLM 관련 실험과 자료를 모아둔 폴더입니다.

주요 파일
- (colab)Dacon.ipynb: 실험 노트북
- Dockerfile: 컨테이너 빌드용 Dockerfile
- kleague_sharegpt_final.jsonl: 대화 데이터셋 예시 파일

빠른 시작
1. 도커 이미지 빌드

```bash
docker build -t vllm:local vllm
```

2. 컨테이너 실행 (GPU 사용 시 `--gpus all` 추가)

```bash
docker run -it --rm -v $(pwd)/vllm:/workspace/vllm vllm:local /bin/bash
```

실험 환경
- `(colab)Dacon.ipynb`는 Google Colab에서 실행되었습니다.
- 학습은 NVIDIA A100 환경에서 진행되었고, QLoRA로 LLM 모델을 파인튜닝했습니다.

노트
- 노트북은 로컬 또는 적절한 런타임에서 열어 실행하세요.
- 추가 의존성은 Dockerfile 또는 프로젝트 상위의 `requirements.txt`를 참고하세요.

