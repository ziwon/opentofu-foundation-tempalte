moved {
  from = aws_vpc.this
  to   = module.stack.aws_vpc.this
}

moved {
  from = aws_subnet.private
  to   = module.stack.aws_subnet.private
}

moved {
  from = aws_default_security_group.this
  to   = module.stack.aws_default_security_group.this
}
