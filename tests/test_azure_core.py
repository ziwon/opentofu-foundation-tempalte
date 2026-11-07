"""Azure state at either earlier address reaches the core module that now owns the resource."""

import json
from pathlib import Path
import unittest

from tools.addresses import managed_addresses

ROOT = Path(__file__).resolve().parents[1]
STORAGE_ACCOUNT = {
    "azurerm_resource_group.this": "module.stack.azurerm_resource_group.this",
    "azurerm_storage_account.this": "module.stack.module.storage_account.azurerm_storage_account.this",
    "azurerm_storage_container.this": "module.stack.module.storage_account.azurerm_storage_container.this",
}
EXPECTED = {
    "bootstrap/state": STORAGE_ACCOUNT,
    "storage/bucket": STORAGE_ACCOUNT,
    "network/core": {
        "azurerm_resource_group.this": "module.stack.azurerm_resource_group.this",
        "azurerm_virtual_network.this": "module.stack.module.network.azurerm_virtual_network.this",
        "azurerm_subnet.private": "module.stack.module.network.azurerm_subnet.private",
        "azurerm_network_security_group.this": "module.stack.module.network.azurerm_network_security_group.this",
        "azurerm_subnet_network_security_group_association.this":
            "module.stack.module.network.azurerm_subnet_network_security_group_association.this",
    },
}


def resolve(address: str, moves: list[tuple[str, str]]) -> str:
    targets = dict(moves)
    while address in targets:
        address = targets[address]
    return address


class AzureCoreModuleAddressTests(unittest.TestCase):
    def test_every_azure_root_moves_legacy_and_native_state_into_core_modules(self):
        legacy = json.loads((ROOT / "tools/legacy-addresses.json").read_text())
        roots = sorted((ROOT / "live").glob("*/azure/*/*/terraform.tfvars.json"))
        self.assertEqual(len(roots), 9)
        for variables in roots:
            environment, _, group, stack = variables.parent.relative_to(ROOT / "live").parts
            expected = EXPECTED[f"{group}/{stack}"]
            self.assertEqual(sorted(legacy[f"azure/{group}/{stack}"]), sorted(expected))
            resources, moves = managed_addresses(variables.parent)
            with self.subTest(root=f"{environment}/azure/{group}/{stack}"):
                self.assertEqual(resources, set(expected.values()))
                for old, new in expected.items():
                    self.assertEqual(resolve(old, moves), new, f"shared-stack state at {old}")
                    self.assertEqual(resolve(f"module.stack.{old}", moves), new, f"native-root state at module.stack.{old}")


if __name__ == "__main__":
    unittest.main()
