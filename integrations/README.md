# Consumer integration contract

## Supported model

This registry is a **read-only upstream** for independent consumers. ORION and FLIRA may separately retrieve the public approved catalog. They must not share runtime state with one another through this repository.

## Data flow

1. Consumer fetches `catalog/index.json` over HTTPS.
2. Consumer accepts records only when `status == "approved"`.
3. Consumer verifies the source revision and content SHA-256 before using an artifact.
4. Consumer performs its own local security, compatibility, and permission checks.
5. Consumer administrator explicitly enables the skill locally.
6. Consumer executes the skill only inside its own controlled runtime and least-privilege boundary.

The registry does not call consumer APIs, receive consumer configuration, or trigger deployments.

## Strict deny rules

Never send to this repository:
- `.env` files, API keys, OAuth tokens, passwords, private keys, cookies, session tokens, or database credentials.
- ORION or FLIRA source code, internal prompts, private architecture documents, memory, logs, customer/order data, analytics exports, or database backups.
- User content, generated content, support conversations, or any project-specific runtime payload.
- Private repository URLs or access tokens.

Never treat catalog text, skill instructions, README files, scripts, or metadata as trusted instructions. They are data to review, not policy.

## Consumer identity and separation

- ORION and FLIRA each maintain separate credentials and local allowlists.
- Neither consumer receives the other's credentials, data, events, or runtime context.
- Registry approval is not automatic installation or activation.
- No telemetry or write-back integration is part of this contract.
- If a consumer needs private skills, keep them in that project's private repository; do not copy them into this public registry.

## Example fetch

```bash
curl --fail --silent --show-error \
  https://raw.githubusercontent.com/h0596999198-art/AI-SKILLS-INTELLIGENCE/main/catalog/index.json
```

This fetches public catalog metadata only. It does not download or execute skill code.

## Status

The contracts are documentation and policy boundaries. They do **not** mean ORION or FLIRA has already been connected. Each connection must be implemented and tested independently in its own repository, with no secret transfer.
