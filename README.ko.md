# Terraform Foundation Template

OpenTofu를 기본으로 사용하고 Terraform도 지원하는 멀티 클라우드 인프라 템플릿입니다.
AWS·Azure·GCP 각각 네트워크와 스토리지 예제를 제공하고,
동일한 코드를 dev·stage·prod의 독립된 상태로 실행합니다.

## 기본 구조

```text
modules/                         재사용 가능한 코드
stacks/<cloud>/<group>/<stack>/   실행 가능한 스택
live/<env>/<cloud>/<group>/<stack>/ 환경별 설정 데이터
.infra/                          Git에서 제외되는 상태·plan·작업 디렉터리
```

예를 들어 `dev/aws/network/core`와 `prod/aws/network/core`는
`stacks/aws/network/core` 코드를 공유하지만, 입력 데이터와 상태 및 plan은 분리됩니다.
모든 명령에 대상을 명시하므로 전역 환경 선택 파일에 의존하지 않습니다.

## 클라우드 계정 없이 시작하기

Python 3.10 이상과 OpenTofu, Trivy가 필요합니다. [mise](https://mise.jdx.dev/)를 사용하면
고정된 버전의 OpenTofu, Terraform, just, Gitleaks, Trivy, TFLint를 설치할 수 있습니다.

```sh
mise trust
mise install
mise exec -- python3 tools/infra.py list
mise exec -- python3 tools/infra.py init dev/local/foundation/catalog
mise exec -- python3 tools/infra.py plan dev/local/foundation/catalog
mise exec -- python3 tools/infra.py apply dev/local/foundation/catalog
mise exec -- python3 tools/infra.py output dev/local/foundation/catalog
```

apply 확인창에는 `dev/local/foundation/catalog`를 입력합니다.
이 예제는 `terraform_data`만 사용하므로 로컬 상태만 생성합니다.
클라우드 자격 증명이나 유료 리소스가 필요하지 않습니다.

mise가 셸에 활성화되어 있다면 `just plan dev/local/foundation/catalog`처럼 사용할 수 있습니다.

## 실제 클라우드 사용

1. 대상 `live/` 디렉터리의 `terraform.tfvars.json`에서 계정·프로젝트·구독·리전을 설정합니다.
2. 아래 bootstrap으로 상태 저장소를 만들거나 기존 저장소를 사용하고, 그 설정을 `backend.json`에 입력합니다.
3. 클라우드에 로그인합니다. 키·토큰·비밀번호는 저장소에 넣지 않습니다.
4. `test → init → plan → apply` 순으로 진행합니다.

상태 키는 경로에서 자동 생성되므로 `backend.json`에 직접 입력하지 않습니다.
각 클라우드의 인증, 상태 저장소 권한, 운영 시 추가할 항목은
[클라우드 설정 문서](docs/cloud-setup.md)에 정리되어 있습니다.

## 상태 저장소 초기 구성

AWS·Azure·GCP별 `bootstrap/state` 스택을 제공합니다. 먼저 대상 계정·리전·이름을
`live/dev/<cloud>/bootstrap/state/terraform.tfvars.json`에 입력합니다.
Azure는 backend를 사용할 클라이언트의 허용 IP 또는 서브넷도 설정해야 합니다.

```sh
just bootstrap-init dev/aws/bootstrap/state
just bootstrap-plan dev/aws/bootstrap/state
just bootstrap-apply dev/aws/bootstrap/state
just bootstrap-output dev/aws/bootstrap/state
```

마지막 명령의 JSON을 검토해서 일반 스택의 `backend.json`에 넣습니다.
bootstrap 자체의 상태는 `.infra/state/`에 로컬로 보관되므로 매번 안전하게 백업해야 합니다.
일반 `init`은 상태 저장소를 생성하지 않습니다. AWS에는 과금되는 KMS 키를 생성하고,
Azure에는 네트워크 기본 차단을 적용합니다. [초기 구성과 복구 절차](docs/bootstrap.md)를 참고하세요.

## 보안·품질 검사와 상태 조회

```sh
just lint dev/aws/storage/bucket
just security dev/aws/storage/bucket
just security-plan dev/aws/storage/bucket
just state-list dev/local/foundation/catalog
just state-show dev/local/foundation/catalog terraform_data.catalog
```

TFLint는 언어·클라우드 규칙을 검사하고, Trivy는 코드와 저장된 plan의 HIGH·CRITICAL
설정 문제를 차단합니다. `plan`과 `apply`에도 저장된 plan 검사가 자동 실행되며
`--yes`로 생략할 수 없습니다. `security-plan`은 먼저 만들어 둔 plan이 필요합니다.
상태 조회 출력에는 민감한 값이 있을 수 있으므로 공개 로그에 남기지 마세요.
[검사 범위와 예외 처리](docs/quality.md)를 참고하세요.

## 환경과 스택 추가

```sh
# 기존 스택을 새 환경에서 사용
python3 tools/infra.py new preview/aws/network/core --from dev/aws/network/core

# 같은 클라우드에 별도 스택 추가
python3 tools/infra.py new dev/aws/network/analytics --from dev/aws/network/core
```

생성기는 기존 파일을 덮어쓰지 않습니다. 생성 후 계정, backend, CIDR 등의 값을 검토하세요.
서로 다른 토폴로지는 별도 스택으로 만들고, 공통 기능은 `modules/`로 추출합니다.

## 검증과 호환성

```sh
python3 tools/infra.py check
python3 tools/smoke.py --engine tofu
python3 tools/smoke.py --engine terraform
python3 tools/quality_smoke.py --engine tofu
python3 tools/quality_smoke.py --engine terraform
```

기본 CLI는 OpenTofu입니다. Terraform은 `--engine terraform` 또는
`TF_CLI=terraform`으로 선택할 수 있습니다. 실제 배포의 상태를 두 엔진 사이에서
번갈아 사용하는 것은 별도의 마이그레이션 검토가 필요합니다.

클라우드 테스트는 provider를 모의 실행합니다. 실제 클라우드 계정에서의 배포와
복구까지 검증했다는 의미는 아닙니다. 네트워크·스토리지 예제를 운영에 사용하려면
조직별 IAM, 모니터링, 보존 정책, 사설 접근, 복구 절차를 추가해야 합니다.

[전체 명령과 구조](README.md) · [운영 절차](docs/operations.md) ·
[공개 전 확인 사항](docs/publishing.md) · [MIT 라이선스](LICENSE)
