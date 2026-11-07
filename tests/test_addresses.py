"""Moved-block chains map every legacy address to exactly one current resource."""

from pathlib import Path
import tempfile
import unittest

from tools.addresses import managed_addresses, parse_module, verify_continuity

ROOT_MOVE = '''module "stack" {
  source = "./stack"
}
moved {
  from = terraform_data.x
  to   = module.stack.terraform_data.x
}
'''


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


class MisreadTests(unittest.TestCase):
    """Each case matches real OpenTofu: a destroy plan or an unmodelled construct must not pass."""

    def trace(self, root_text, stack_text, extra=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "stack").mkdir()
            (root / "main.tf").write_text(root_text)
            (root / "stack/main.tf").write_text(stack_text)
            for name, text in (extra or {}).items():
                (root / name).write_text(text)
            verify_continuity(["terraform_data.x"], *managed_addresses(root))

    def test_hidden_or_commented_constructs_do_not_pass(self):
        resource = 'resource "terraform_data" "x" {\n  input = "v"\n}\n'
        cases = {
            "block-commented move": ('module "stack" {\n  source = "./stack"\n}\n/*\n' + ROOT_MOVE.split("}\n", 1)[1] + "*/\n", resource),
            "line-commented move": ('module "stack" {\n  source = "./stack"\n}\n' + "".join("# " + line + "\n" for line in ROOT_MOVE.split("}\n", 1)[1].splitlines()), resource),
            "heredoc hides a move": ('module "stack" {\n  source = "./stack"\n}\nlocals {\n  doc = <<EOT\n' + ROOT_MOVE.split("}\n", 1)[1] + "EOT\n}\n", resource),
            "count after a brace in a string": (ROOT_MOVE, 'resource "terraform_data" "x" {\n  input = "}"\n  count = 1\n}\n'),
            "count after a brace in a comment": (ROOT_MOVE, 'resource "terraform_data" "x" {\n  input = "v" # }\n  count = 0\n}\n'),
            "for_each with an inline map": (ROOT_MOVE, 'resource "terraform_data" "x" {\n  input    = "v"\n  for_each = { a = 1 }\n}\n'),
            "for_each with a multiline map": (ROOT_MOVE, 'resource "terraform_data" "x" {\n  for_each = {\n    a = 1\n  }\n}\n'),
            "for_each on a module": ('module "stack" {\n  source   = "./stack"\n  for_each = { a = 1 }\n}\n' + ROOT_MOVE.split("}\n", 1)[1], resource),
            "lifecycle enabled": (ROOT_MOVE, 'resource "terraform_data" "x" {\n  lifecycle {\n    enabled = false\n  }\n}\n'),
        }
        for case, (root_text, stack_text) in cases.items():
            reason = "Legacy address" if "move" in case.split()[-1] else "Cannot trace"
            with self.subTest(case), self.assertRaisesRegex(ValueError, reason):
                self.trace(root_text, stack_text)

    def test_unread_configuration_files_are_rejected(self):
        resource = 'resource "terraform_data" "x" {}\n'
        for name in ("main.tofu", "extra.tf.json", "extra.tofu.json"):
            with self.subTest(name), self.assertRaisesRegex(ValueError, "Cannot trace"):
                self.trace(ROOT_MOVE, resource, {name: "{}\n"})

    def test_strings_and_comments_do_not_hide_a_real_move(self):
        root_text = ROOT_MOVE.replace("to   = module.stack.terraform_data.x", "to   = module.stack.terraform_data.x # moved in 2026 }")
        stack_text = 'resource "terraform_data" "x" {\n  input = "${jsonencode({ a = "}" })} /* not a comment */"\n}\n'
        self.trace(root_text, stack_text)
