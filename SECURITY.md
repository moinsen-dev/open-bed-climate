# Security and safety reports

Open Bed Climate controls heaters and coolers next to a sleeping person. We treat two kinds of issue as security issues:

- **Safety:** anything that could let the system overheat, overcool, leak, or keep running after a fault (for example a way
  around a safety limit in the firmware, a wiring instruction that is unsafe, or a part in the catalog that is not
  rated for its role).
- **Software security:** anything that lets someone on the network change what the bed does without the owner's consent.

**How to report:** email business@moinsen.dev with the subject "Open Bed Climate security". Please do not open a public
issue for something that could hurt people before it is fixed. We aim to answer within 7 days.

For general safety questions that are not urgent, use the
[safety concern issue template](.github/ISSUE_TEMPLATE/safety-concern.yml).

Supported versions: this project is in the design phase; only the `main` branch is maintained.
