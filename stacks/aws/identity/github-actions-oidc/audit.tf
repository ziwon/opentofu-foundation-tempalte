locals {
  # Permissions from https://docs.prowler.com/user-guide/providers/aws/authentication.
  # The inline additions copy permissions/prowler-additions-policy.json at Prowler
  # 5.48.0 without securityhub:BatchImportFindings, a write that only the
  # --security-hub output uses.
  audit_roles = length(var.audit_subjects) == 0 ? {} : {
    audit = {
      subjects = var.audit_subjects
      managed_policy_arns = [
        "arn:aws:iam::aws:policy/SecurityAudit",
        "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess",
      ]
      # A full scan of every region can outlast the one-hour default.
      max_session_duration = 7200
      inline_policy_json = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Sid      = "AllowMoreReadOnly"
            Effect   = "Allow"
            Resource = "*"
            Action = [
              "account:Get*",
              "amplify:ListApps",
              "amplify:ListBranches",
              "appstream:Describe*",
              "appstream:List*",
              "backup:List*",
              "backup:Get*",
              "bedrock-agentcore:GetAgentRuntime",
              "bedrock-agentcore:GetBrowser",
              "bedrock-agentcore:GetCodeInterpreter",
              "bedrock-agentcore:GetGateway",
              "bedrock-agentcore:GetGatewayTarget",
              "bedrock-agentcore:GetMemory",
              "bedrock-agentcore:GetTokenVault",
              "bedrock-agentcore:ListAgentRuntimes",
              "bedrock-agentcore:ListBrowsers",
              "bedrock-agentcore:ListCodeInterpreters",
              "bedrock-agentcore:ListGatewayTargets",
              "bedrock-agentcore:ListGateways",
              "bedrock-agentcore:ListMemories",
              "bedrock-agentcore:ListTagsForResource",
              "bedrock:List*",
              "bedrock:Get*",
              "cloudtrail:GetInsightSelectors",
              "codeartifact:List*",
              "codebuild:BatchGet*",
              "codebuild:ListReportGroups",
              "cognito-idp:GetUserPoolMfaConfig",
              "datapipeline:DescribePipelines",
              "datapipeline:GetPipelineDefinition",
              "datapipeline:ListPipelines",
              "dlm:Get*",
              "drs:Describe*",
              "ds:Get*",
              "ds:Describe*",
              "ds:List*",
              "dynamodb:GetResourcePolicy",
              "ec2:GetEbsEncryptionByDefault",
              "ec2:GetSnapshotBlockPublicAccessState",
              "ec2:GetInstanceMetadataDefaults",
              "ecr:Describe*",
              "ecr:GetRegistryScanningConfiguration",
              "ecr:BatchGetImage",
              "ecr:GetDownloadUrlForLayer",
              "elasticfilesystem:DescribeBackupPolicy",
              "glue:GetConnections",
              "glue:GetSecurityConfiguration*",
              "glue:SearchTables",
              "glue:GetMLTransforms",
              "inspector2:BatchGetFindingDetails",
              "lambda:GetFunction*",
              "lambda:GetLayerVersion",
              "logs:FilterLogEvents",
              "lightsail:GetRelationalDatabases",
              "macie2:GetMacieSession",
              "macie2:GetAutomatedDiscoveryConfiguration",
              "rolesanywhere:ListProfiles",
              "rolesanywhere:ListTagsForResource",
              "rolesanywhere:ListTrustAnchors",
              "s3:GetAccountPublicAccessBlock",
              "s3:GetObjectAcl",
              "s3:ListBucket",
              "shield:DescribeProtection",
              "shield:GetSubscriptionState",
              "securityhub:GetFindings",
              "servicecatalog:Describe*",
              "servicecatalog:List*",
              "ssm:GetDocument",
              "ssm-incidents:List*",
              "states:ListTagsForResource",
              "support:Describe*",
              "tag:GetTagKeys",
              "wellarchitected:List*",
            ]
          },
          {
            Sid    = "AllowAPIGatewayReadOnly"
            Effect = "Allow"
            Action = ["apigateway:GET"]
            Resource = [
              "arn:*:apigateway:*::/restapis/*",
              "arn:*:apigateway:*::/apis/*",
              "arn:*:apigateway:*::/domainnames",
              "arn:*:apigateway:*::/domainnames/*",
            ]
          },
        ]
      })
    }
  }
}
