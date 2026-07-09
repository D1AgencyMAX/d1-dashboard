# Independent Post-Incident Technical Resilience & Architecture Review

**Prepared for:** Telstra Group Limited — Network, Product & Technology
**Prepared by:** Digital One Agency Pty Ltd / CISO Advisory Australia
**Contact:** Ken Armitt — ken@digitaloneagency.com.au
**Date:** July 2026
**Classification:** Commercial in Confidence

---

## 1. Context

On Wednesday 8 July 2026, a software defect in time-keeping servers at Telstra data
centres in Sydney and Melbourne disrupted time synchronisation across the national
network from approximately 4:30am to 4:00pm AEST. The incident:

- Disrupted mobile services for millions of customers nationwide
- Blocked or dropped hundreds of Triple Zero calls, triggering 333 welfare checks
- Suspended Victoria's entire V/Line regional network and delayed NSW regional and
  intercity rail; national freight was halted as a safety precaution
- Disrupted payments (Tyro — ~80,000 merchants), taxi payment systems and EV charging
- Was followed by a **secondary fault** overnight on 8–9 July affecting Triple Zero
  connectivity and voicemail routing — after the initial fix was declared

An internal review is inevitable, and regulator scrutiny (ACMA, the Triple Zero
custodian framework, and likely a Bell-style independent inquiry as followed the
Optus November 2023 outage) is highly probable. What the Board will need — and what
regulators and government will expect — is an **independent** technical assessment
that is not authored by the teams whose architecture and change processes are under
examination, and not by an incumbent consultancy with existing delivery interests
inside Telstra.

## 2. What we are proposing

A confidential, independent, engineer-led **post-incident technical resilience and
architecture review**, reporting to the Group Executive Network, Product & Technology
with a board-level summary deliverable.

This is explicitly **not** a penetration test and not a generic security audit. It is
an architecture, resilience and operational-governance review with six workstreams:

### Workstream 1 — Timing & synchronisation architecture
The root-cause domain of this incident. Review of the network time distribution
design: NTP/PTP hierarchy, grandmaster placement, GNSS dependence and holdover
strategy, failure domains of time-keeping infrastructure, blast-radius of a
time-server fault, and monitoring/alerting on time drift. Assessment of whether a
single software defect in this layer should ever have been able to propagate
nationally.

### Workstream 2 — Architectural single points of failure
Systematic failure-domain analysis across core network, signalling, and shared
platform services. Identification of components where redundancy exists on paper but
shares a common failure mode (same software version, same defect, same config push,
same physical or logical dependency).

### Workstream 3 — Redundancy & failover validation
Validation of failover assumptions against tested reality: when were failover paths
last exercised under production-like conditions? The 8–9 July secondary fault —
occurring after the primary fix — indicates recovery and failback procedures
themselves carry unmodelled risk. We review recovery-path engineering, failback
sequencing, and the testing regime for both.

### Workstream 4 — Change management & software assurance
How did the defect reach production time-keeping infrastructure? Review of release
engineering for critical infrastructure components: staged rollout and canarying
practice, pre-production representativeness, rollback capability and decision
authority, and emergency-change governance during incident response.

### Workstream 5 — Triple Zero resilience
Emergency-call handling under degraded network conditions: camp-on behaviour to
other carriers, eCall/emergency-bearer prioritisation, the voicemail-diversion
failure mode observed on 8–9 July, and alignment with ACMA emergency-call
determinations and the Triple Zero custodian framework.

### Workstream 6 — Operational resilience & governance
Incident command effectiveness, detection-to-declaration timeline, internal and
public communications cadence, welfare-check process, and the governance loop from
incident learnings to funded remediation. Board-level reporting on residual risk.

## 3. Deliverables

1. **Rapid Diagnostic Report** (end of Phase 0) — preliminary findings, immediate
   risk items, and a validated scope for the full review.
2. **Technical Findings Report** — detailed, evidence-based findings per workstream
   with severity ratings and engineering-level remediation recommendations.
3. **Board Report** — a concise, plain-English assessment of systemic resilience
   risk, remediation priorities, investment implications, and defensibility of the
   remediation program to regulators and government.
4. **Remediation Roadmap** — sequenced, costed-at-order-of-magnitude program of work.
5. (Phase 2) **Independent Remediation Assurance** — quarterly validation that
   remediation is real, tested and effective, with standing board reporting.

## 4. Engagement structure & investment

| Phase | Scope | Duration | Investment (AUD, ex GST) |
|---|---|---|---|
| **Phase 0 — Rapid Independent Diagnostic** | Timing architecture + change management fast-pass; incident timeline reconstruction; scope validation for Phase 1 | 3 weeks | $285,000 fixed |
| **Phase 1 — Full Resilience & Architecture Review** | All six workstreams; technical findings, board report, remediation roadmap | 10–12 weeks | $1.9M – $2.6M (scope-dependent, fixed after Phase 0) |
| **Phase 2 — Independent Remediation Assurance** | Quarterly independent validation and board reporting over the remediation program | 12 months | $150,000 per quarter |

Phase 0 is deliberately structured as a low-friction entry point: fixed fee, three
weeks, immediately useful output, and it de-risks the Phase 1 scope for both parties.
Telstra is under no obligation to proceed beyond Phase 0.

## 5. Why Digital One Agency / CISO Advisory

- **Independence.** We are not embedded in Telstra delivery today. Our findings are
  not shaped by protecting an existing multi-year engagement, and we can say things
  an incumbent cannot.
- **Engineer-led.** This review is performed by practitioners in distributed-systems
  architecture, network engineering and security governance — not a leveraged
  pyramid of analysts.
- **Specialist framing.** Our practice focus is technical due diligence and
  resilience/architecture review of critical systems (CISO Advisory's TECHDD
  practice), which is precisely the discipline this incident calls for.
- **Confidentiality and speed.** Small senior team, direct executive reporting line,
  NDA from first conversation, Phase 0 findings inside three weeks.

## 6. Working arrangements

- Executive sponsor: Group Executive, Network, Product & Technology
- Access required: architecture documentation, incident timeline/PIR materials,
  change records for the affected systems, and interview access to engineering and
  operations leads. Read-only; no production access required.
- All work performed under NDA; report ownership rests with Telstra.
- Available to commence within 10 business days of engagement.

---

*Digital One Agency Pty Ltd — Sydney | Melbourne | Brisbane | Gold Coast*
*CISO Advisory Australia — cisoadvisory.com.au*
