"""Moved-block chains map every legacy address to exactly one current resource."""

import unittest

from tools.addresses import parse_module, verify_continuity


class ContinuityTests(unittest.TestCase):
    def test_deployment_without_legacy_addresses_needs_no_moves(self):
        verify_continuity([], {"module.stack.terraform_data.new"}, [])

    def test_two_legacy_addresses_cannot_reach_one_resource(self):
        moves = [("aws_vpc.this", "module.stack.aws_vpc.this"), ("aws_vpc.old", "aws_vpc.this")]
        with self.assertRaisesRegex(ValueError, r"aws_vpc\.old.*module\.stack\.aws_vpc\.this"):
            verify_continuity(["aws_vpc.this", "aws_vpc.old"], {"module.stack.aws_vpc.this"}, moves)

    def test_cycle_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            verify_continuity(["a.x"], {"a.z"}, [("a.x", "a.y"), ("a.y", "a.x")])

    def test_conflicting_moves_from_one_address_are_rejected(self):
        moves = [("a.x", "module.stack.a.x"), ("a.x", "module.other.a.x")]
        with self.assertRaisesRegex(ValueError, r"a\.x"):
            verify_continuity(["a.x"], {"module.stack.a.x", "module.other.a.x"}, moves)


class ParseModuleTests(unittest.TestCase):
    def test_reads_managed_resources_local_calls_and_moves(self):
        resources, calls, moves = parse_module('''
data "aws_region" "current" {}

resource "terraform_data" "catalog" {
  input = { name = "a" }
  dynamic "tag" {
    for_each = {}
    content {}
  }
}

module "vpc" {
  source = "../vpc"
}

moved {
  from = terraform_data.old
  to   = module.vpc.terraform_data.catalog
}
''')
        self.assertEqual(resources, {"terraform_data.catalog"})
        self.assertEqual(calls, {"vpc": "../vpc"})
        self.assertEqual(moves, [("terraform_data.old", "module.vpc.terraform_data.catalog")])
