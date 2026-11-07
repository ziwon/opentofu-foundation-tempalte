# OpenTofu foundation template

AWS, Azure, GCP를 위한 인프라 모노레포 템플릿입니다. 각 배포 디렉터리가 독립적인
OpenTofu 실행 루트입니다. 해당 디렉터리에서 `tofu` 명령을 직접 실행합니다.
일반 배포에는 Python, 생성기, 저장소 전용 실행기가 필요하지 않습니다.
지원하는 CLI는 OpenTofu입니다.

[English](README.md) · [구조](docs/architecture.md) · [클라우드 설정](docs/cloud-setup.md) ·
[운영](docs/operations.md) · [마이그레이션](docs/migration.md) · [보안](SECURITY.md)

## 기본 구조

```text
live/dev/aws/network/core/        독립적인 OpenTofu 루트
  backend.tf                     명시적인 상태 저장 위치
  context.tf                     공통 이름과 태그
  main.tf                        module "stack" 호출
  providers.tf                   계정 및 provider 설정
  versions.tf                    OpenTofu 및 provider 버전 요구사항
  .terraform.lock.hcl            선택된 provider 버전과 해시
  variables.tf                   입력 선언
  terraform.tfvars.json          비밀이 아닌 배포별 값
  outputs.tf                     배포 출력
  migrations.tf                  기존 리소스 주소의 이동 선언
stacks/aws/network/core/         루트가 호출하는 용도별 구성
modules/context/                 공통 이름과 태그 규칙
modules/<cloud>/<module>/        재사용할 핵심 구성 요소
```

배포 ID는 `environment/cloud/group/stack`입니다. AWS, Azure, GCP의 네트워크,
스토리지, 상태 저장소 bootstrap과 로컬 catalog를 dev, stage, prod에 제공하므로
총 30개 루트가 있습니다. 각 루트는 기본 workspace를 사용합니다.

저장소는 세 계층으로 나뉩니다. `live/` 루트는 상태, provider, 입력을 소유하고
stack 하나를 `module "stack"`으로 호출합니다. `stacks/<cloud>/<group>/<stack>`의
stack은 한 가지 용도에 맞게 리소스를 구성하며 `modules/`의 핵심 모듈을 호출할 수 있습니다.
핵심 모듈에는 재사용할 구성 요소와 공통 규칙인 `modules/context`가 있습니다.
Stack과 모듈에는 backend나 provider 설정을 넣지 않습니다.

## 클라우드 계정 없이 시작하기

OpenTofu 1.12.5를 설치합니다. [mise](https://mise.jdx.dev/)를 사용한다면
[mise.toml](mise.toml)의 고정된 개발 도구 버전을 검토한 후 설치할 수 있습니다.
아래 로컬 실행에는 Python이나 보안 검사 도구가 필요하지 않습니다.

```sh
cd live/dev/local/foundation/catalog
tofu init -lockfile=readonly
tofu plan -out=plan.tfplan
tofu apply plan.tfplan
tofu output
tofu state list
```

내장 `terraform_data` 리소스만 사용하므로 클라우드 리소스는 생성하지 않습니다.
출력 이름은 `starter-catalog-dev`입니다. 상태는 저장소 기준
`.infra/state/dev/local/foundation/catalog/terraform.tfstate`에 저장됩니다.
저장된 plan을 apply하면 별도의 확인 질문이 나오지 않습니다. 먼저 plan을 검토하세요.

로컬 catalog를 제거할 때도 삭제 plan을 검토한 후 적용합니다.

```sh
tofu plan -destroy -out=destroy.tfplan
tofu apply destroy.tfplan
```

저장소 루트에서는 `just init dev/local/foundation/catalog`,
`just plan dev/local/foundation/catalog`, `just apply dev/local/foundation/catalog`를
선택적으로 사용할 수 있습니다. 이 명령은 native OpenTofu 명령의 별칭입니다.
전체 목록은 `just --list`로 확인합니다.

## 실제 클라우드 배포 준비

1. `live/<environment>/<cloud>/<group>/<stack>` 루트를 선택합니다.
2. `terraform.tfvars.json`에 실제 계정, 구독, 프로젝트, 리전, 이름을 설정합니다.
3. [bootstrap](docs/bootstrap.md)으로 상태 저장소를 만들거나 기존 저장소를 사용합니다.
4. `backend.tf`의 저장소 예제 값을 바꿉니다. 기존 배포의 key나 prefix는 유지합니다.
5. 클라우드의 기본 인증 방식을 사용합니다. 키, 토큰, 비밀번호는 Git에 넣지 않습니다.
6. 검사를 실행하고 backend를 초기화한 뒤 저장된 plan을 검토합니다. 승인된 절차로 적용합니다.

```sh
tofu -chdir=live/dev/aws/network/core init -lockfile=readonly
tofu -chdir=live/dev/aws/network/core plan -out=plan.tfplan
tofu -chdir=live/dev/aws/network/core apply plan.tfplan
```

AWS는 VPC, 비공개 subnet, 기본 차단 security group과 암호화된 S3 예제를 제공합니다.
Azure는 VNet, subnet, network security group과 identity 기반 Blob storage를 제공합니다.
GCP는 custom VPC, subnet, ingress firewall과 비공개 GCS bucket을 제공합니다.
클라우드별 인증과 권한은 [클라우드 설정](docs/cloud-setup.md)을 참고하세요.

이 예제에는 컴퓨팅 workload, NAT gateway, 공인 IP가 없습니다. 저장 데이터,
요청, KMS key, 버전, 로그에는 비용이 발생할 수 있습니다. 운영 환경에 적용하기 전에
조직의 IAM, 모니터링, 보존, 사설 연결, 복구 요구사항을 검토해야 합니다.

## 상태 저장소 bootstrap

각 클라우드의 `live/<environment>/<cloud>/bootstrap/state`도 일반 native 루트입니다.
대상 계정과 이름을 설정하고, Azure는 접근을 허용할 IP나 subnet도 설정합니다.

```sh
tofu -chdir=live/dev/aws/bootstrap/state init -lockfile=readonly
tofu -chdir=live/dev/aws/bootstrap/state plan -out=bootstrap.tfplan
tofu -chdir=live/dev/aws/bootstrap/state apply bootstrap.tfplan
tofu -chdir=live/dev/aws/bootstrap/state output -json backend_config
```

plan을 검토하고 필요한 검사와 승인을 받은 후 apply하세요. 마지막 출력의 속성을
workload의 `backend.tf`에 옮기고, 해당 workload의 명시적인 key나 prefix는 유지합니다.
일반 `init`은 저장소를 생성하지 않습니다. Bootstrap에는 삭제 보호가 있으며 Atlantis
대상에서 제외됩니다. 상태는 `.infra/state/<deployment>/terraform.tfstate`에 저장되므로
적용 후 독립적인 암호화 저장소에 백업하세요. [초기 구성과 복구](docs/bootstrap.md)를 참고하세요.

## 이름과 태그

각 루트의 `context.tf`가 `modules/context`를 호출합니다.
`module.context.id`는 `<namespace>-<name>-<environment>` 형식입니다.
`module.context.tags`는 공통 태그와 입력의 추가 태그를 합칩니다.
`project`, `environment`, `managed_by`는 예약된 키이므로 덮어쓸 수 없습니다.

루트는 `id`와 `tags`가 있는 `context` 객체를 `module.stack`에 전달합니다.
Stack은 `var.context.id`, `var.context.tags`를 사용합니다.
Provider 설정은 루트에 두고, 클라우드별 이름 변환은 리소스를 소유한 핵심 모듈에 둡니다.
[이름과 태그](docs/context.md), [배포 추가](docs/adding-stacks.md)를 참고하세요.

## 기존 상태 마이그레이션

로컬 및 bootstrap 상태 경로, S3와 Azure의 key, GCS의 prefix는 유지됩니다.
기존 checkout을 업데이트하면서 `.infra/`를 삭제하면 안 됩니다.

리소스는 `aws_vpc.this`에서 `module.stack.aws_vpc.this`와 같은 주소로 이동합니다.
각 루트의 `migrations.tf`에 있는 `moved` 선언이 이 변경을 연결합니다.
선언을 유지하고, 상태를 백업한 후 기존 상태에 대한 새 plan을 검토하세요.
주소 이동만 있는 경우 리소스 생성, 수정, 교체, 삭제가 없어야 합니다.
기존 plan은 재사용하지 않습니다. 자세한 절차는 [마이그레이션](docs/migration.md)에 있습니다.

## 검사와 배포 정책

Python 3.10 이상은 저장소 검사, 보고서 처리, 테스트용 개발 의존성입니다.
일반 `tofu` 실행에는 필요하지 않습니다.

```sh
python3 tools/check.py
python3 tools/smoke.py
python3 tools/quality_smoke.py
gitleaks dir . --redact --no-banner
```

CI는 OpenTofu만 사용합니다. 형식, 구조, provider 검증, lint, 소스 보안 검사,
mock plan, 로컬 수명주기를 검사합니다. 실제 scanner가 안전한 입력은 허용하고
위험하거나 인식하지 못한 입력은 거부하는지도 확인합니다. 클라우드 테스트는 plan만
만들며 실제 적용과 삭제는 임시 로컬 `terraform_data`에 한정합니다.

Native 로컬 명령에는 이전 실행기의 소스 fingerprint, plan receipt, 정확한 배포 이름
확인, 자동 보안 검사, plan 정리가 없습니다. 저장된 plan의 apply에는 확인 질문도 없습니다.
이는 명시적인 정책 변경입니다. 필수 보안 검사와 승인은 신뢰할 수 있는 배포 자동화에서
강제해야 합니다. [보안 정책](SECURITY.md)과 [품질 검사](docs/quality.md)를 참고하세요.

선택형 [Atlantis 연동](docs/atlantis.md)은 built-in `init`, `plan`, `apply`와
명시적인 소스 및 저장된 `PLANFILE` 검사를 사용합니다. 승인은 서버 소유 설정에 두며
fork PR, 자동 merge, bootstrap 프로젝트는 비활성화합니다. 일반 로컬 CLI에는 Atlantis가
필요하지 않습니다.

State, plan, 출력에는 민감한 값이 포함될 수 있습니다. Git이나 공개 로그에 남기지 마세요.
[검증 범위](docs/verification.md) · [공개 전 확인](docs/publishing.md) · [MIT 라이선스](LICENSE)
