# FSI Agent Card Validator
# Run with: python validate_fsi_agent_card.py <agent-card.json> [--schema <schema.json>] [--verbose]
# Requires Python 3.8 or later. Compatible with Windows, macOS, and Linux.
"""
FSI Agent Card Validator
========================
Validates an FSI Agent Card JSON document against the FSI Agent Card schema
and enforces the production registration rules defined in the README.

Usage
-----
    python validate_fsi_agent_card.py <agent-card.json> [options]

Options
-------
    --schema <path>   Path to the FSI Agent Card schema. Defaults to
                      fsi-agent-card-schema.json in the same directory
                      as this script.
    --verbose         Show each rule check in detail: what field was read,
                      what value was found, and whether the rule passed,
                      failed, was skipped, or produced a warning.

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
def cyan(text):   return f"\033[36m{text}\033[0m" if USE_COLOUR else text
def dim(text):    return f"\033[2m{text}\033[0m"   if USE_COLOUR else text
def bold(text):   return f"\033[1m{text}\033[0m"   if USE_COLOUR else text


# ---------------------------------------------------------------------------
# Result collector
# ---------------------------------------------------------------------------
class Results:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passes = []
        self.skips = []

    def error(self, rule, message):
        self.errors.append((rule, message))

    def warn(self, rule, message):
        self.warnings.append((rule, message))

    def record_pass(self, rule, message):
        self.passes.append((rule, message))

    def record_skip(self, rule, message):
        self.skips.append((rule, message))

    @property
    def ok(self):
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Safe nested field access
# ---------------------------------------------------------------------------
def _get(card, *path, default=None):
    """Return the value at the nested path, or default if any step is missing."""
    node = card
    for key in path:
        if not isinstance(node, dict):
            return default
        node = node.get(key, default)
        if node is default:
            return default
    return node


def _fmt(value):
    """Format a value for verbose display. Truncates long strings and lists."""
    if value is None:
        return dim("(not set)")
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        if len(value) > 3:
            preview = ", ".join(str(v) for v in value[:3])
            return f"[{preview}, ... +{len(value) - 3} more]"
        return str(value)
    if isinstance(value, str) and len(value) > 80:
        return f'"{value[:77]}..."'
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)


# ---------------------------------------------------------------------------
# Oversight model mapping (mirrors README validation rule 1)
# ---------------------------------------------------------------------------
OVERSIGHT_MODEL_MAP = {
    "A0": "human-executes-all-actions",
    "A1": "human-approves-every-action",
    "A2": "human-reviews-at-checkpoints",
    "A3": "human-reviews-at-milestones",
    "A4": "human-receives-exception-alerts-only",
}

# Floating version references not acceptable in production (Rule 15)
FLOATING_VERSION_RE = re.compile(r"^(latest|main|master|\*)$", re.IGNORECASE)

# Approved security scheme types per OpenAPI 3.0 / A2A spec (Rule 9)
APPROVED_SCHEME_TYPES = {"apiKey", "http", "oauth2", "openIdConnect", "mutualTLS"}

# Heuristic pattern for individual-looking email local parts (Rule 10)
# Note: this only catches a small set of obviously personal patterns.
# A shared inbox with an unusual naming convention will not be detected.
INDIVIDUAL_EMAIL_RE = re.compile(
    r"^(firstname|lastname|name|first\.last|f\.last|fname|lname)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Production registration rules
# ---------------------------------------------------------------------------
def run_registration_rules(card, results, verbose=False):
    """
    Enforce the 15 production registration rules from the README,
    plus advisory checks. Populates results in-place.
    When verbose=True, prints each check as it runs.
    """

    def vprint(status, rule, message, detail=None):
        """Print a single verbose check line."""
        if not verbose:
            return
        colour_fn = {
            "PASS": green,
            "SKIP": dim,
            "FAIL": red,
            "WARN": yellow,
            "INFO": cyan,
        }.get(status, lambda x: x)
        line = f"  {colour_fn(status)} [{rule}] {message}"
        if detail:
            line += f"  {dim('--')} {dim(detail)}"
        print(line)

    autonomy_level = _get(card, "governance", "autonomyLevel")
    oversight_model = _get(card, "governance", "humanOversightModel")

    # ── Rule 1: humanOversightModel must be consistent with autonomyLevel ──
    if autonomy_level and oversight_model:
        expected = OVERSIGHT_MODEL_MAP.get(autonomy_level)
        if expected and oversight_model != expected:
            results.error(
                "Rule 1",
                f"humanOversightModel '{oversight_model}' is inconsistent with "
                f"autonomyLevel '{autonomy_level}'. Expected '{expected}'."
            )
            vprint("FAIL", "Rule 1", "Oversight model mismatch",
                   f"autonomyLevel={_fmt(autonomy_level)}, "
                   f"humanOversightModel={_fmt(oversight_model)}, "
                   f"expected={_fmt(expected)}")
        else:
            results.record_pass("Rule 1", "humanOversightModel is consistent with autonomyLevel")
            vprint("PASS", "Rule 1", "Oversight model is consistent with autonomy level",
                   f"autonomyLevel={_fmt(autonomy_level)}, "
                   f"humanOversightModel={_fmt(oversight_model)}")
    else:
        results.record_skip("Rule 1", "autonomyLevel or humanOversightModel absent")
        vprint("SKIP", "Rule 1",
               "autonomyLevel or humanOversightModel absent — covered by schema validation",
               f"autonomyLevel={_fmt(autonomy_level)}, "
               f"humanOversightModel={_fmt(oversight_model)}")

    # ── Rule 2: approvedActionList required for A2+ ────────────────────────
    if autonomy_level in ("A2", "A3", "A4"):
        action_list = _get(card, "governance", "approvedActionList")
        if not action_list:
            results.error(
                "Rule 2",
                f"governance.approvedActionList is required for autonomyLevel "
                f"'{autonomy_level}' and must not be empty."
            )
            vprint("FAIL", "Rule 2",
                   "approvedActionList is required for A2+ but is absent or empty",
                   f"autonomyLevel={_fmt(autonomy_level)}, value={_fmt(action_list)}")
        else:
            results.record_pass("Rule 2", f"approvedActionList present with {len(action_list)} action(s)")
            vprint("PASS", "Rule 2", "approvedActionList is present",
                   f"autonomyLevel={_fmt(autonomy_level)}, {len(action_list)} action(s) listed")
    else:
        results.record_skip("Rule 2", f"Not required for autonomyLevel {autonomy_level}")
        vprint("SKIP", "Rule 2",
               f"approvedActionList not required for autonomyLevel {_fmt(autonomy_level)}")

    # ── Rule 3: approvedAgentRegistry required for A3+ ────────────────────
    if autonomy_level in ("A3", "A4"):
        registry = _get(card, "governance", "approvedAgentRegistry")
        if not registry:
            results.error(
                "Rule 3",
                f"governance.approvedAgentRegistry is required for autonomyLevel "
                f"'{autonomy_level}' and must not be empty."
            )
            vprint("FAIL", "Rule 3",
                   "approvedAgentRegistry required for A3+ but is absent or empty",
                   f"autonomyLevel={_fmt(autonomy_level)}")
        else:
            missing = [
                entry.get("name", f"entry[{i}]")
                for i, entry in enumerate(registry)
                if not entry.get("approvalReference")
            ]
            if missing:
                for name in missing:
                    results.error(
                        "Rule 3",
                        f"governance.approvedAgentRegistry entry '{name}' "
                        f"is missing approvalReference."
                    )
                vprint("FAIL", "Rule 3",
                       "approvedAgentRegistry entries missing approvalReference",
                       f"entries: {missing}")
            else:
                results.record_pass("Rule 3", f"approvedAgentRegistry present, all {len(registry)} entry/entries have approvalReference")
                vprint("PASS", "Rule 3",
                       "approvedAgentRegistry present, all entries have approvalReference",
                       f"{len(registry)} entry/entries")
    else:
        results.record_skip("Rule 3", f"Not required for autonomyLevel {autonomy_level}")
        vprint("SKIP", "Rule 3",
               f"approvedAgentRegistry not required for autonomyLevel {_fmt(autonomy_level)}")

    # ── Rule 4: killSwitchEndpoint required for A3+ ────────────────────────
    kill_switch = _get(card, "compliance", "incidentResponse", "killSwitchEndpoint")
    if autonomy_level in ("A3", "A4"):
        if not kill_switch:
            results.error(
                "Rule 4",
                f"compliance.incidentResponse.killSwitchEndpoint is required for "
                f"autonomyLevel '{autonomy_level}'."
            )
            vprint("FAIL", "Rule 4",
                   "killSwitchEndpoint required for A3+ but is absent or null",
                   f"autonomyLevel={_fmt(autonomy_level)}, value={_fmt(kill_switch)}")
        else:
            results.record_pass("Rule 4", "killSwitchEndpoint is present")
            vprint("PASS", "Rule 4", "killSwitchEndpoint is present",
                   f"value={_fmt(kill_switch)}")
    else:
        results.record_skip("Rule 4", f"Not required for autonomyLevel {autonomy_level}")
        vprint("SKIP", "Rule 4",
               f"killSwitchEndpoint not required for autonomyLevel {_fmt(autonomy_level)}",
               f"value={_fmt(kill_switch)} (null is correct for sub-A3 agents)")

    # ── Rule 5: auditTrail.immutable must be true for A1+ ─────────────────
    if autonomy_level in ("A1", "A2", "A3", "A4"):
        immutable = _get(card, "compliance", "auditTrail", "immutable")
        if immutable is not True:
            results.error(
                "Rule 5",
                f"compliance.auditTrail.immutable must be true for autonomyLevel "
                f"'{autonomy_level}'. Found: {_fmt(immutable)}"
            )
            vprint("FAIL", "Rule 5",
                   "auditTrail.immutable must be true for A1+",
                   f"autonomyLevel={_fmt(autonomy_level)}, value={_fmt(immutable)}")
        else:
            results.record_pass("Rule 5", "auditTrail.immutable is true")
            vprint("PASS", "Rule 5", "auditTrail.immutable is true",
                   f"autonomyLevel={_fmt(autonomy_level)}")
    else:
        results.record_skip("Rule 5", f"Not enforced for autonomyLevel {autonomy_level}")
        vprint("SKIP", "Rule 5",
               f"auditTrail.immutable not enforced for autonomyLevel {_fmt(autonomy_level)}")

    # ── Rule 6: piiHandling required when PII in permittedDataDomains ──────
    permitted_domains = _get(card, "dataHandling", "permittedDataDomains", default=[])
    if "PII" in permitted_domains:
        pii_handling = _get(card, "dataHandling", "piiHandling")
        rule6_errors = []
        if not pii_handling:
            rule6_errors.append("piiHandling block is absent")
        else:
            if not pii_handling.get("piiTypesHandled"):
                rule6_errors.append("piiHandling.piiTypesHandled is absent or empty")
            if not pii_handling.get("legalBasis"):
                rule6_errors.append("piiHandling.legalBasis is absent")
        if rule6_errors:
            for msg in rule6_errors:
                results.error("Rule 6", f"PII is in permittedDataDomains but {msg}.")
            vprint("FAIL", "Rule 6",
                   "PII declared but piiHandling is incomplete",
                   f"issues: {rule6_errors}")
        else:
            results.record_pass("Rule 6", "piiHandling block is complete")
            vprint("PASS", "Rule 6", "piiHandling block is complete",
                   f"piiTypesHandled={_fmt(pii_handling.get('piiTypesHandled'))}, "
                   f"legalBasis={_fmt(pii_handling.get('legalBasis'))}")
    else:
        results.record_skip("Rule 6", "PII not in permittedDataDomains")
        vprint("SKIP", "Rule 6",
               "PII is not in permittedDataDomains — piiHandling not required",
               f"permittedDataDomains={_fmt(permitted_domains)}")

    # ── Rule 7: modelInventoryId must be populated ────────────────────────
    model_inventory_id = _get(card, "governance", "modelRisk", "modelInventoryId")
    if not model_inventory_id:
        results.error(
            "Rule 7",
            "governance.modelRisk.modelInventoryId must be populated before "
            "production deployment."
        )
        vprint("FAIL", "Rule 7",
               "modelInventoryId is absent or empty",
               f"value={_fmt(model_inventory_id)}")
    else:
        results.record_pass("Rule 7", "modelInventoryId is populated")
        vprint("PASS", "Rule 7", "modelInventoryId is populated",
               f"value={_fmt(model_inventory_id)}")

    # ── Rule 8: url must use HTTPS ────────────────────────────────────────
    url = _get(card, "url", default="")
    if url and not url.startswith("https://"):
        results.error("Rule 8", f"url must use HTTPS in production. Found: '{url}'")
        vprint("FAIL", "Rule 8", "url does not use HTTPS", f"value={_fmt(url)}")
    elif url:
        results.record_pass("Rule 8", "url uses HTTPS")
        vprint("PASS", "Rule 8", "url uses HTTPS", f"value={_fmt(url)}")
    else:
        results.record_skip("Rule 8", "url absent — covered by schema validation")
        vprint("SKIP", "Rule 8", "url is absent — covered by schema validation")

    # ── Rule 9: securitySchemes must have at least one valid entry ────────
    security_schemes = _get(card, "securitySchemes", default={})
    if not security_schemes:
        results.error("Rule 9", "securitySchemes must contain at least one entry.")
        vprint("FAIL", "Rule 9", "securitySchemes is absent or empty")
    else:
        invalid_schemes = [
            (name, scheme.get("type"))
            for name, scheme in security_schemes.items()
            if scheme.get("type") not in APPROVED_SCHEME_TYPES
        ]
        if invalid_schemes:
            for name, stype in invalid_schemes:
                results.error(
                    "Rule 9",
                    f"securitySchemes['{name}'] uses type '{stype}' which is not in "
                    f"the approved set: {sorted(APPROVED_SCHEME_TYPES)}."
                )
            vprint("FAIL", "Rule 9",
                   "securitySchemes contains scheme(s) with unapproved type",
                   f"invalid: {invalid_schemes}")
        else:
            results.record_pass("Rule 9", f"securitySchemes has {len(security_schemes)} valid scheme(s)")
            scheme_summary = {k: v.get("type") for k, v in security_schemes.items()}
            vprint("PASS", "Rule 9",
                   f"securitySchemes is present with valid scheme types",
                   f"schemes={scheme_summary}")

    # ── Rule 10: teamContact must be a shared address (heuristic) ─────────
    team_contact = _get(card, "provider", "teamContact", default="")
    if team_contact:
        local_part = team_contact.split("@")[0] if "@" in team_contact else team_contact
        if INDIVIDUAL_EMAIL_RE.match(local_part):
            results.warn(
                "Rule 10",
                f"provider.teamContact '{team_contact}' may be an individual's email "
                "(heuristic check). This field must be a shared team inbox."
            )
            vprint("WARN", "Rule 10",
                   "teamContact matched a personal-email pattern (heuristic check)",
                   f"value={_fmt(team_contact)}")
        else:
            results.record_pass("Rule 10", "teamContact passed heuristic check")
            vprint("PASS", "Rule 10",
                   "teamContact passed heuristic shared-inbox check",
                   f"value={_fmt(team_contact)} "
                   f"(note: only common individual patterns are detected)")
    else:
        results.record_skip("Rule 10", "teamContact absent — covered by schema validation")
        vprint("SKIP", "Rule 10", "teamContact absent — covered by schema validation")

    # ── Rules 11–12: MCP server checks ───────────────────────────────────
    mcp_servers = _get(card, "dependencies", "mcpServers", default=[])

    if not mcp_servers:
        results.record_skip("Rule 11", "No mcpServers declared")
        results.record_skip("Rule 12", "No mcpServers declared")
        vprint("SKIP", "Rule 11", "No mcpServers declared — rules 11-12 not applicable")
        vprint("SKIP", "Rule 12", "No mcpServers declared — rules 11-12 not applicable")
    else:
        # Rule 11: permittedDataDomains must be a subset of agent-level domains
        rule11_ok = True
        for i, server in enumerate(mcp_servers):
            server_domains = set(server.get("permittedDataDomains", []))
            agent_domains = set(permitted_domains)
            excess = server_domains - agent_domains
            name = server.get("name", f"server[{i}]")
            if excess:
                rule11_ok = False
                results.error(
                    "Rule 11",
                    f"dependencies.mcpServers[{i}] ('{name}') declares "
                    f"permittedDataDomains {sorted(excess)} that are not in "
                    f"dataHandling.permittedDataDomains."
                )
                vprint("FAIL", "Rule 11",
                       f"MCP server '{name}' has excess data domains",
                       f"server={sorted(server_domains)}, "
                       f"agent={sorted(agent_domains)}, "
                       f"excess={sorted(excess)}")
            else:
                vprint("PASS", "Rule 11",
                       f"MCP server '{name}' data domains are a valid subset",
                       f"server domains={sorted(server_domains)}")
        if rule11_ok:
            results.record_pass("Rule 11", "All MCP server domains are subsets of agent domains")

        # Rule 12: third-party servers need VRA reference
        # Advisory: internal servers should also have an approvalReference
        rule12_ok = True
        for i, server in enumerate(mcp_servers):
            name = server.get("name", f"server[{i}]")
            provider_type = server.get("providerType", "unknown")
            approval_ref = server.get("approvalReference", "")
            if provider_type == "third-party" and not approval_ref:
                rule12_ok = False
                results.error(
                    "Rule 12",
                    f"dependencies.mcpServers[{i}] ('{name}') is third-party and "
                    f"must reference a vendor risk assessment in approvalReference."
                )
                vprint("FAIL", "Rule 12",
                       f"Third-party MCP server '{name}' missing VRA reference",
                       f"providerType={_fmt(provider_type)}, "
                       f"approvalReference={_fmt(approval_ref)}")
            elif provider_type == "third-party":
                vprint("PASS", "Rule 12",
                       f"Third-party MCP server '{name}' has approvalReference",
                       f"approvalReference={_fmt(approval_ref)}")
            elif provider_type == "internal" and not approval_ref:
                results.warn(
                    "Rule 12",
                    f"dependencies.mcpServers[{i}] ('{name}') is internal but has no "
                    f"approvalReference. A change ticket or architecture review reference "
                    f"is recommended."
                )
                vprint("WARN", "Rule 12",
                       f"Internal MCP server '{name}' has no approvalReference",
                       "A change ticket or architecture review reference is recommended.")
            else:
                vprint("PASS", "Rule 12",
                       f"Internal MCP server '{name}' has approvalReference",
                       f"approvalReference={_fmt(approval_ref)}")
        if rule12_ok:
            results.record_pass("Rule 12", "All third-party MCP servers have a VRA reference")

    # ── Rules 13–15: Agent Skills checks ─────────────────────────────────
    agent_skills = _get(card, "dependencies", "agentSkills", default=[])

    if not agent_skills:
        results.record_skip("Rule 13", "No agentSkills declared")
        results.record_skip("Rule 14", "No agentSkills declared")
        results.record_skip("Rule 15", "No agentSkills declared")
        vprint("SKIP", "Rule 13", "No agentSkills declared — rules 13-15 not applicable")
        vprint("SKIP", "Rule 14", "No agentSkills declared — rules 13-15 not applicable")
        vprint("SKIP", "Rule 15", "No agentSkills declared — rules 13-15 not applicable")
    else:
        # Rule 13: approvalReference required for all skills
        rule13_ok = True
        for i, skill in enumerate(agent_skills):
            name = skill.get("name", f"skill[{i}]")
            if not skill.get("approvalReference"):
                rule13_ok = False
                results.error(
                    "Rule 13",
                    f"dependencies.agentSkills[{i}] ('{name}') is missing "
                    f"approvalReference. Required for all skill sources."
                )
                vprint("FAIL", "Rule 13",
                       f"Skill '{name}' missing approvalReference",
                       f"source={_fmt(skill.get('source'))}")
            else:
                vprint("PASS", "Rule 13",
                       f"Skill '{name}' has approvalReference",
                       f"approvalReference={_fmt(skill.get('approvalReference'))}")
        if rule13_ok:
            results.record_pass("Rule 13", "All agent skills have approvalReference")

        # Rule 14: securityReviewReference required for executable or third-party skills
        rule14_ok = True
        for i, skill in enumerate(agent_skills):
            name = skill.get("name", f"skill[{i}]")
            is_executable = skill.get("containsExecutableCode") is True
            is_third_party = skill.get("source") == "third-party"
            needs_review = is_executable or is_third_party
            if needs_review and not skill.get("securityReviewReference"):
                rule14_ok = False
                reasons = []
                if is_executable:
                    reasons.append("containsExecutableCode=true")
                if is_third_party:
                    reasons.append("source=third-party")
                results.error(
                    "Rule 14",
                    f"dependencies.agentSkills[{i}] ('{name}') "
                    f"({', '.join(reasons)}) must have a securityReviewReference."
                )
                vprint("FAIL", "Rule 14",
                       f"Skill '{name}' requires security review but reference is absent",
                       f"reason: {', '.join(reasons)}")
            elif needs_review:
                vprint("PASS", "Rule 14",
                       f"Skill '{name}' has securityReviewReference",
                       f"securityReviewReference={_fmt(skill.get('securityReviewReference'))}")
            else:
                vprint("SKIP", "Rule 14",
                       f"Skill '{name}' does not require security review",
                       f"containsExecutableCode={_fmt(skill.get('containsExecutableCode'))}, "
                       f"source={_fmt(skill.get('source'))}")
        if rule14_ok:
            results.record_pass("Rule 14", "All skills requiring security review have securityReviewReference")

        # Rule 15: skill versions must be pinned — no floating references
        rule15_ok = True
        for i, skill in enumerate(agent_skills):
            name = skill.get("name", f"skill[{i}]")
            version = skill.get("version") or ""
            if not version:
                rule15_ok = False
                results.warn(
                    "Rule 15",
                    f"dependencies.agentSkills[{i}] ('{name}') has no version "
                    f"declared. Pin to a specific version in production."
                )
                vprint("WARN", "Rule 15",
                       f"Skill '{name}' has no version declared")
            elif FLOATING_VERSION_RE.match(version):
                rule15_ok = False
                results.error(
                    "Rule 15",
                    f"dependencies.agentSkills[{i}] ('{name}') version '{version}' "
                    f"is a floating reference. Pin to a specific version in production."
                )
                vprint("FAIL", "Rule 15",
                       f"Skill '{name}' version is a floating reference",
                       f"version={_fmt(version)}")
            else:
                vprint("PASS", "Rule 15",
                       f"Skill '{name}' version is pinned",
                       f"version={_fmt(version)}")
        if rule15_ok:
            results.record_pass("Rule 15", "All skill versions are pinned")

    # ── Advisory: auditTrail.enabled should be true for all production ────
    audit_enabled = _get(card, "compliance", "auditTrail", "enabled")
    if audit_enabled is not True:
        results.error(
            "Advisory",
            f"compliance.auditTrail.enabled must be true for all production "
            f"deployments. Found: {_fmt(audit_enabled)}"
        )
        vprint("FAIL", "Advisory",
               "auditTrail.enabled must be true for production deployments",
               f"value={_fmt(audit_enabled)}")
    else:
        results.record_pass("Advisory", "auditTrail.enabled is true")
        vprint("PASS", "Advisory", "auditTrail.enabled is true")

    # ── Advisory: promptInjectionControls.reference when controls are active
    controls_in_place = _get(
        card, "agentSecurity", "promptInjectionControls", "controlsInPlace"
    )
    pi_reference = _get(
        card, "agentSecurity", "promptInjectionControls", "reference"
    )
    if controls_in_place is True and not pi_reference:
        results.warn(
            "Advisory",
            "agentSecurity.promptInjectionControls.controlsInPlace is true but "
            "no reference is provided. Populate with the control specification "
            "or test evidence."
        )
        vprint("WARN", "Advisory",
               "promptInjectionControls.reference should be populated when "
               "controlsInPlace is true",
               f"controlsInPlace={_fmt(controls_in_place)}, "
               f"reference={_fmt(pi_reference)}")
    elif controls_in_place is True:
        results.record_pass("Advisory", "promptInjectionControls.reference is present")
        vprint("PASS", "Advisory",
               "promptInjectionControls.reference is present",
               f"reference={_fmt(pi_reference)}")
    else:
        results.record_skip("Advisory", "controlsInPlace is not true")
        vprint("INFO", "Advisory",
               "promptInjectionControls.controlsInPlace is not true — reference check skipped",
               f"value={_fmt(controls_in_place)}")

    # ── Advisory: card signing ────────────────────────────────────────────
    signed = _get(card, "agentSecurity", "cardSigning", "signed")
    jwks_url = _get(card, "agentSecurity", "cardSigning", "jwksUrl")
    if signed is True and not jwks_url:
        results.error(
            "Signing",
            "agentSecurity.cardSigning.signed is true but jwksUrl is absent. "
            "Callers cannot verify the card signature without the JWKS URL."
        )
        vprint("FAIL", "Signing",
               "cardSigning.signed is true but jwksUrl is absent",
               f"signed={_fmt(signed)}, jwksUrl={_fmt(jwks_url)}")
    elif signed is True:
        results.record_pass("Signing", "cardSigning is true and jwksUrl is present")
        vprint("PASS", "Signing",
               "cardSigning.signed is true and jwksUrl is present",
               f"jwksUrl={_fmt(jwks_url)}")
    elif signed is False:
        results.warn(
            "Signing",
            "agentSecurity.cardSigning.signed is false. Card signing is strongly "
            "recommended for production deployments."
        )
        vprint("WARN", "Signing",
               "Card signing is disabled — strongly recommended for production",
               f"signed={_fmt(signed)}")
    else:
        results.record_skip("Signing", "cardSigning.signed absent — covered by schema")
        vprint("SKIP", "Signing",
               "cardSigning.signed is absent — covered by schema validation")

    # ── Advisory: model validation date freshness ─────────────────────────
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
                vprint("WARN", "Advisory",
                       f"Model validation is {age_days} days ago — over 12 months",
                       f"lastValidationDate={_fmt(last_validation)}")
            else:
                results.record_pass(
                    "Advisory",
                    f"Model validation date is {age_days} days ago — within 12 months"
                )
                vprint("PASS", "Advisory",
                       "Model validation date is within 12 months",
                       f"lastValidationDate={_fmt(last_validation)}, "
                       f"age={age_days} days")
        except ValueError:
            results.warn(
                "Advisory",
                f"governance.modelRisk.lastValidationDate '{last_validation}' is not "
                f"a valid ISO 8601 date."
            )
            vprint("WARN", "Advisory",
                   "lastValidationDate is not a valid ISO 8601 date",
                   f"value={_fmt(last_validation)}")
    else:
        results.record_skip("Advisory", "lastValidationDate not set")
        vprint("INFO", "Advisory",
               "lastValidationDate not set — freshness check skipped")


# ---------------------------------------------------------------------------
# File loading
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
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
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show each rule check in detail: what field was read, what value "
             "was found, and whether the check passed, failed, was skipped, "
             "or produced a warning."
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

    print(bold("\nFSI Agent Card Validator"))
    print(f"  Card:   {card_path}")
    print(f"  Schema: {schema_path}")
    if args.verbose:
        print(f"  Mode:   verbose\n")
    else:
        print(f"  Mode:   standard  (use --verbose to see every individual check)\n")

    # ── Step 1: JSON Schema validation ────────────────────────────────────
    print(bold("── Step 1: Schema validation"))

    def _sort_key(err):
        # json_path was added in jsonschema 4.0; fall back for older versions
        try:
            return err.json_path
        except AttributeError:
            return list(err.absolute_path)

    validator = Draft202012Validator(schema)
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
    print(bold("\n── Step 2: Production registration rules and advisories"))
    run_registration_rules(card, results, verbose=args.verbose)

    # In standard mode, print failures and warnings after the function returns.
    # In verbose mode, each check was already printed inline.
    if not args.verbose:
        rule_errors   = [(r, m) for r, m in results.errors if r != "Schema"]
        rule_warnings = results.warnings
        if not rule_errors and not rule_warnings:
            print(green("  PASS All checks passed"))
        else:
            for rule, message in rule_errors:
                print(f"  {red('FAIL')} [{rule}] {message}")
            for rule, message in rule_warnings:
                print(f"  {yellow('WARN')} [{rule}] {message}")

    # ── Summary ───────────────────────────────────────────────────────────
    print(bold("\n── Summary"))
    total_errors   = len(results.errors)
    total_warnings = len(results.warnings)

    if args.verbose:
        print(f"  Checks passed:   {green(str(len(results.passes)))}")
        print(f"  Checks skipped:  {dim(str(len(results.skips)))}")
        print(f"  Warnings:        {yellow(str(total_warnings)) if total_warnings else str(total_warnings)}")
        print(f"  Errors:          {red(str(total_errors)) if total_errors else str(total_errors)}")

    if results.ok:
        note = f" with {total_warnings} warning(s)" if total_warnings else ""
        print(f"\n  {green('PASSED')}{note}")
        print("  This agent card meets the FSI Agent Card production registration rules.\n")
    else:
        print(f"\n  {red('FAILED')} -- {total_errors} error(s), {total_warnings} warning(s)")
        print("  Resolve all errors before registering this agent in production.\n")

    sys.exit(0 if results.ok else 1)


if __name__ == "__main__":
    main()