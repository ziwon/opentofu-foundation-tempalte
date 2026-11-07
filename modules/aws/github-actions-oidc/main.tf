locals {
  issuer   = "token.actions.githubusercontent.com"
  audience = "sts.amazonaws.com"
  provider_arn = (var.create_oidc_provider
    ? one(aws_iam_openid_connect_provider.github[*].arn)
    : one(data.aws_iam_openid_connect_provider.github[*].arn)
  )
  trust = {
    Effect    = "Allow"
    Principal = { Federated = local.provider_arn }
    Action    = "sts:AssumeRoleWithWebIdentity"
  }
}

resource "aws_iam_openid_connect_provider" "github" {
  count          = var.create_oidc_provider ? 1 : 0
  url            = "https://${local.issuer}"
  client_id_list = [local.audience]
}

data "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 0 : 1
  url   = "https://${local.issuer}"
}

resource "aws_iam_role" "this" {
  for_each             = var.roles
  name                 = each.value.name
  max_session_duration = each.value.max_session_duration
  permissions_boundary = each.value.permissions_boundary
  # IAM ANDs condition operators within a statement, so prefix patterns get
  # their own statement to widen the exact subjects instead of narrowing them.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      length(each.value.subjects) == 0 ? [] : [merge(local.trust, {
        Condition = { StringEquals = { "${local.issuer}:aud" = local.audience, "${local.issuer}:sub" = each.value.subjects } }
      })],
      length(each.value.subject_patterns) == 0 ? [] : [merge(local.trust, {
        Condition = { StringEquals = { "${local.issuer}:aud" = local.audience }, StringLike = { "${local.issuer}:sub" = each.value.subject_patterns } }
      })],
    )
  })
}

resource "aws_iam_role_policy_attachment" "this" {
  for_each = { for pair in flatten([
    for key, role in var.roles : [for arn in role.managed_policy_arns : { key = "${key} ${arn}", role = key, arn = arn }]
  ]) : pair.key => pair }
  role       = aws_iam_role.this[each.value.role].name
  policy_arn = each.value.arn
}

resource "aws_iam_role_policy" "this" {
  for_each = { for key, role in var.roles : key => role if role.inline_policy_json != null }
  name     = "inline"
  role     = aws_iam_role.this[each.key].name
  policy   = each.value.inline_policy_json
}
