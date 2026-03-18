# FSI Agent Card Validator
# Run with: python validate_fsi_agent_card.py <agent-card.json> [--schema <schema.json>]
# Requires Python 3.8 or later. Compatible with Windows, macOS, and Linux.
"""
FSI Agent Card Validator
========================
Validates an FSI Agent Card JSON document against the FSI Agent Card schema
and enforces the production registration rules defined in the README.

Usage
-----
    python validate_fsi_agent_card.py <agent-card.json> [--schema <schema.json>]

Arguments
---------
    agent-card.json     Path to the agent card to validate.
    --schema            Path to the FSI Agent Card schema. Defaults to
                        fsi-agent-card-schema.json in the same directory
                        as this script.

Exit codes
----------
    0   Validation passed with no errors.
    1   One or more validation errors found.
    2   Usage error or file not found.

Requirements
------------
    Python 3.8 or later (Windows, macOS, Linux).
    pip install jsonschema

    See the README for virtual environment setup instructions.
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# Attempt to import jsonschema; fail clearly if not installed
# ---------------------------------------------------------------------------
try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema is not installed.")
    print("       Run: pip install jsonschema")
    print("       See the README for virtual environment setup instructions.")
    sys.exit(2)


# ---------------------------------------------------------------------------
# Colour output
#
# ANSI colour codes are supported on:
#   - macOS and Linux terminals
#   - Windows 10 version 1511+ with Windows Terminal or VS Code terminal
#   - Any terminal where the NO_COLOR environment variable is not set
#
# Colour is disabled automatically when output is piped or redirected,
# or when the NO_COLOR environment variable is set (https://no-color.org).
# ---------------------------------------------------------------------------
def _supports_colour():
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if sys.platform == "win32":
        # Enable ANSI on Windows by attempting to set the console mode.
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return True


USE_COLOUR = _supports_colour()


def red(text):    return f"\033[31m{text}\033[0m" if USE_COLOUR else text
def yellow(text): return f"\033[33m{text}\033[0m" if USE_COLOUR else text
def green(text):  return f"\033[32m{text}\033[0m" if USE_COLOUR else text
def bold(text):   return f"\033[1m{text}\033[0m"  if USE_COLOUR else text


# ---------------------------------------------------------------------------
# Result collector
# ---------------------------------------------------------------------------
class Results:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, rule, message):
        self.errors.append((rule, message))

    def warn(self, rule, message):
        self.warnings.append((rule, message))

    @property
    def passed(self):
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Production registration rules
# (These mirror the rules in FSI-AGENT-CARD-README.md)
# ---------------------------------------------------------------------------

def _get(card, *path, default=None):
    """Safe nested dict access."""
    node = card
    for key in path:
        if not isinstance(node, dict):
            return default
        node = node.get(key, default)
        if node is default:
            return default
    return node


OVERSIGHT_MODEL_MAP = {
    "A0": "human-executes-all-actions",
    "A1": "human-approves-every-action",
    "A2": "human-reviews-at-checkpoints",
    "A3": "human-reviews-at-milestones",
    "A4": "human-receives-exception-alerts-only",
}

SHARED_INBOX_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)
INDIVIDUAL_PATTERNS = re.compile(
    r"^(firstname|lastname|name|first\.last|f\.last|fname|lname)",
    re.IGNORECASE,
)


def run_registration_rules(card, results):
    """
    Enforce the 15 production registration rules from the README.
    Errors block production registration.
    Warnings are advisory.
    """

    autonomy_level = _get(card, "governance", "autonomyLevel")
    oversight_model = _get(card, "governance", "humanOversightModel")

    # ── Rule 1: humanOversightModel must be consistent with autonomyLevel ──
    if autonomy_level and oversight_model:
        expected = OVERSIGHT_MODEL_MAP.get(autonomy_level)
        if expected and oversight_model != expected:
            results.error(
                "Rule 1",
                f"humanOversightModel '{oversight_model}' is not consistent with "
                f"autonomyLevel '{autonomy_level}'. Expected '{expected}'."
            )

    # ── Rule 2: approvedActionList required for A2+ ────────────────────────
    if autonomy_level in ("A2", "A3", "A4"):
        action_list = _get(card, "governance", "approvedActionList")
        if not action_list:
            results.error(
                "Rule 2",
                f"governance.approvedActionList is required for autonomyLevel "
                f"'{autonomy_level}' and must not be empty."
            )

    # ── Rule 3: approvedAgentRegistry required for A3+ ────────────────────
    if autonomy_level in ("A3", "A4"):
        registry = _get(card, "governance", "approvedAgentRegistry")
        if not registry:
            results.error(
                "Rule 3",
                f"governance.approvedAgentRegistry is required for autonomyLevel "
                f"'{autonomy_level}' and must not be empty."
            )
        else:
            for i, entry in enumerate(registry):
                if not entry.get("approvalReference"):
                    results.error(
                        "Rule 3",
                        f"governance.approvedAgentRegistry[{i}] (agent '{entry.get('name', '?')}') "
                        f"is missing approvalReference."
                    )

    # ── Rule 4: killSwitchEndpoint required for A3+ ────────────────────────
    if autonomy_level in ("A3", "A4"):
        kill_switch = _get(card, "compliance", "incidentResponse", "killSwitchEndpoint")
        if not kill_switch:
            results.error(
                "Rule 4",
                f"compliance.incidentResponse.killSwitchEndpoint is required for "
                f"autonomyLevel '{autonomy_level}'."
            )

    # ── Rule 5: auditTrail.immutable must be true for A1+ ─────────────────
    if autonomy_level in ("A1", "A2", "A3", "A4"):
        immutable = _get(card, "compliance", "auditTrail", "immutable")
        if immutable is not True:
            results.error(
                "Rule 5",
                f"compliance.auditTrail.immutable must be true for autonomyLevel "
                f"'{autonomy_level}'."
            )

    # ── Rule 6: piiHandling required when PII in permittedDataDomains ──────
    permitted_domains = _get(card, "dataHandling", "permittedDataDomains", default=[])
    if "PII" in permitted_domains:
        pii_handling = _get(card, "dataHandling", "piiHandling")
        if not pii_handling:
            results.error(
                "Rule 6",
                "dataHandling.piiHandling is required when 'PII' is listed in "
                "dataHandling.permittedDataDomains."
            )
        else:
            if not pii_handling.get("piiTypesHandled"):
                results.error(
                    "Rule 6",
                    "dataHandling.piiHandling.piiTypesHandled must be populated "
                    "when 'PII' is listed in permittedDataDomains."
                )
            if not pii_handling.get("legalBasis"):
                results.error(
                    "Rule 6",
                    "dataHandling.piiHandling.legalBasis must be populated "
                    "when 'PII' is listed in permittedDataDomains."
                )

    # ── Rule 7: modelInventoryId must be populated ────────────────────────
    model_inventory_id = _get(card, "governance", "modelRisk", "modelInventoryId")
    if not model_inventory_id:
        results.error(
            "Rule 7",
            "governance.modelRisk.modelInventoryId must be populated before "
            "production deployment."
        )

    # ── Rule 8: url must use HTTPS ────────────────────────────────────────
    url = _get(card, "url", default="")
    if url and not url.startswith("https://"):
        results.error(
            "Rule 8",
            f"url must use HTTPS in production. Found: '{url}'"
        )

    # ── Rule 9: securitySchemes must have at least one entry ──────────────
    security_schemes = _get(card, "securitySchemes", default={})
    if not security_schemes:
        results.error(
            "Rule 9",
            "securitySchemes must contain at least one entry. 'none' is not "
            "acceptable for any agent that accesses non-public data."
        )

    # ── Rule 10: teamContact must be a shared address ────────────────────
    team_contact = _get(card, "provider", "teamContact", default="")
    if team_contact and INDIVIDUAL_PATTERNS.match(team_contact.split("@")[0]):
        results.warn(
            "Rule 10",
            f"provider.teamContact '{team_contact}' may be an individual's email. "
            "This field must be a shared team inbox."
        )

    # ── Rules 11–15: dependency checks ───────────────────────────────────
    mcp_servers = _get(card, "dependencies", "mcpServers", default=[])
    agent_skills = _get(card, "dependencies", "agentSkills", default=[])

    # Rule 11: mcpServers[].permittedDataDomains must be subset of agent domains
    for i, server in enumerate(mcp_servers):
        server_domains = set(server.get("permittedDataDomains", []))
        agent_domains = set(permitted_domains)
        excess = server_domains - agent_domains
        if excess:
            results.error(
                "Rule 11",
                f"dependencies.mcpServers[{i}] ('{server.get('name', '?')}') declares "
                f"permittedDataDomains {sorted(excess)} that are not in "
                f"dataHandling.permittedDataDomains."
            )

    # Rule 12: third-party MCP servers require a vendor risk assessment reference
    for i, server in enumerate(mcp_servers):
        if server.get("providerType") == "third-party":
            if not server.get("approvalReference"):
                results.error(
                    "Rule 12",
                    f"dependencies.mcpServers[{i}] ('{server.get('name', '?')}') is "
                    f"third-party and must reference a vendor risk assessment in "
                    f"approvalReference."
                )

    # Rule 13: approvalReference required for all agentSkills
    for i, skill in enumerate(agent_skills):
        if not skill.get("approvalReference"):
            results.error(
                "Rule 13",
                f"dependencies.agentSkills[{i}] ('{skill.get('name', '?')}') is "
                f"missing approvalReference. Required for all skill sources."
            )

    # Rule 14: securityReviewReference required for executable or third-party skills
    for i, skill in enumerate(agent_skills):
        needs_review = (
            skill.get("containsExecutableCode") is True
            or skill.get("source") == "third-party"
        )
        if needs_review and not skill.get("securityReviewReference"):
            results.error(
                "Rule 14",
                f"dependencies.agentSkills[{i}] ('{skill.get('name', '?')}') contains "
                f"executable code or is third-party and must have a "
                f"securityReviewReference."
            )

    # Rule 15: skill versions must be pinned (no floating references)
    FLOATING_VERSION_RE = re.compile(r"^(latest|main|master|\*|^$)", re.IGNORECASE)
    for i, skill in enumerate(agent_skills):
        version = skill.get("version", "")
        if version and FLOATING_VERSION_RE.match(version):
            results.error(
                "Rule 15",
                f"dependencies.agentSkills[{i}] ('{skill.get('name', '?')}') version "
                f"'{version}' is a floating reference. Pin to a specific version "
                f"in production."
            )
        if not version:
            results.warn(
                "Rule 15",
                f"dependencies.agentSkills[{i}] ('{skill.get('name', '?')}') has no "
                f"version declared. Pin to a specific version in production."
            )

    # ── Advisory: validation date freshness ──────────────────────────────
    last_validation = _get(card, "governance", "modelRisk", "lastValidationDate")
    if last_validation:
        try:
            validation_date = date.fromisoformat(last_validation)
            age_days = (date.today() - validation_date).days
            if age_days > 365:
                results.warn(
                    "Advisory",
                    f"governance.modelRisk.lastValidationDate is {age_days} days ago "
                    f"({last_validation}). Consider whether a re-validation is due."
                )
        except ValueError:
            results.warn(
                "Advisory",
                f"governance.modelRisk.lastValidationDate '{last_validation}' is not "
                f"a valid ISO 8601 date."
            )

    # ── Advisory: autonomyLevelJustification should not be a restatement ──
    justification = _get(card, "governance", "autonomyLevelJustification", default="")
    if justification and autonomy_level:
        level_names = {
            "A0": "no agency", "A1": "tool-calling", "A2": "workflow",
            "A3": "goal-directed", "A4": "self-directing"
        }
        name = level_names.get(autonomy_level, "")
        if name and justification.lower().strip().startswith(name):
            results.warn(
                "Advisory",
                "governance.autonomyLevelJustification appears to restate the level "
                "name. It should provide a reasoned argument with specific "
                "implementation constraints."
            )

    # ── Advisory: cardSigning ─────────────────────────────────────────────
    signed = _get(card, "agentSecurity", "cardSigning", "signed")
    jwks_url = _get(card, "agentSecurity", "cardSigning", "jwksUrl")
    if signed is True and not jwks_url:
        results.error(
            "Advisory",
            "agentSecurity.cardSigning.signed is true but jwksUrl is absent. "
            "Callers cannot verify the signature without the JWKS URL."
        )
    if signed is False:
        results.warn(
            "Advisory",
            "agentSecurity.cardSigning.signed is false. Card signing is strongly "
            "recommended for production deployments."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_json(path: Path, label: str) -> dict:
    if not path.exists():
        print(red(f"ERROR: {label} not found: {path}"))
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        print(red(f"ERROR: {label} is not valid JSON: {exc}"))
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(
        description="Validate an FSI Agent Card against the FSI Agent Card schema "
                    "and production registration rules."
    )
    parser.add_argument(
        "card",
        metavar="agent-card.json",
        help="Path to the agent card to validate."
    )
    parser.add_argument(
        "--schema",
        metavar="schema.json",
        default=None,
        help="Path to the FSI Agent Card schema. Defaults to "
             "fsi-agent-card-schema.json in the same directory as this script."
    )
    args = parser.parse_args()

    card_path = Path(args.card)
    schema_path = (
        Path(args.schema)
        if args.schema
        else Path(__file__).parent / "fsi-agent-card-schema.json"
    )

    card = load_json(card_path, "Agent card")
    schema = load_json(schema_path, "Schema")

    results = Results()

    # ── Step 1: JSON Schema validation ────────────────────────────────────
    print(bold(f"\nFSI Agent Card Validator"))
    print(f"  Card:   {card_path}")
    print(f"  Schema: {schema_path}\n")

    print(bold("── Step 1: Schema validation"))
    validator = Draft202012Validator(schema)

    # json_path was added in jsonschema 4.0; fall back gracefully for older
    # installations so the script works regardless of installed version.
    def _sort_key(err):
        try:
            return err.json_path
        except AttributeError:
            return list(err.absolute_path)

    schema_errors = sorted(validator.iter_errors(card), key=_sort_key)

    if schema_errors:
        for err in schema_errors:
            field_path = " -> ".join(str(p) for p in err.absolute_path) or "(root)"
            message = f"{field_path}: {err.message}"
            results.error("Schema", message)
            print(f"  {red('FAIL')} [Schema] {message}")
    else:
        print(green("  PASS Schema validation passed"))

    # ── Step 2: Production registration rules ─────────────────────────────
    print(bold("\n── Step 2: Production registration rules"))
    run_registration_rules(card, results)

    rule_errors   = [(r, m) for r, m in results.errors if r != "Schema"]
    rule_warnings = results.warnings

    if not rule_errors and not rule_warnings:
        print(green("  PASS All registration rules passed"))
    else:
        for rule, message in rule_errors:
            print(f"  FAIL [{rule}] {message}")
        for rule, message in rule_warnings:
            print(f"  WARN [{rule}] {message}")

    # ── Summary ───────────────────────────────────────────────────────────
    print(bold("\n── Summary"))
    total_errors = len(results.errors)
    total_warnings = len(results.warnings)

    if results.passed:
        status = green("PASSED")
        note = f" with {total_warnings} warning(s)" if total_warnings else ""
        print(f"  {status}{note}")
        print("\n  This agent card meets the FSI Agent Card production registration rules.\n")
    else:
        status = red("FAILED")
        print(f"  {status} -- {total_errors} error(s), {total_warnings} warning(s)")
        print("\n  Resolve all errors before registering this agent in production.\n")

    sys.exit(0 if results.passed else 1)


if __name__ == "__main__":
    main()