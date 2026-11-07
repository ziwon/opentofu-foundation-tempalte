moved {
  from = aws_vpc.this
  to   = module.vpc.aws_vpc.this
}

moved {
  from = aws_subnet.private
  to   = module.vpc.aws_subnet.private
}

moved {
  from = aws_default_security_group.this
  to   = module.vpc.aws_default_security_group.this
}
