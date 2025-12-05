# Security Incident Summary - Sisters of the Good Samaritan

**Date**: 5 December 2025
**Prepared for**: SGS IT / Management
**Classification**: Confidential

---

## What Happened

On **3 December 2025**, we detected unauthorized access to one email account using stolen credentials. Our investigation revealed this was part of a larger credential-testing attack that began on **13 November 2025**.

**Account Affected**: 1 user (rbrady@goodsams.org.au)
**Accounts Targeted**: 8 users total (only 1 compromised)
**Current Status**: Contained - all attacker access has been blocked

---

## How It Happened

Attackers obtained the user's password (likely from a previous data breach elsewhere) and used automated tools to test it against your Microsoft 365 environment. They exploited a legacy authentication method that **bypasses multi-factor authentication (MFA)**.

The attack came from:
- A US-based cloud server (initial testing)
- Residential internet connections in Brazil, Argentina, and Saudi Arabia (later attempts)

---

## What We Did

| Action | Status |
|--------|--------|
| Reset affected user's password | ✅ Complete |
| Blocked attacker access | ✅ Complete |
| Analyzed 30 days of sign-in logs | ✅ Complete |
| Confirmed no other accounts compromised | ✅ Complete |
| Published detailed incident report | ✅ Complete |

---

## What You Need to Do

### Immediate (This Week)

1. **Block legacy authentication** - We will implement a Conditional Access policy to prevent this attack method. No user impact expected (we confirmed no legitimate legacy auth usage).

2. **Notify affected user** - Inform Robyn Brady that her account was accessed. Recommend she:
   - Change any other accounts using the same password
   - Be alert for phishing emails referencing her account

### Recommended (Next 30 Days)

3. **Review the 8 targeted accounts** for any unusual activity:
   - vgriffith, kduckworth, tibouri, thegoodoil, emurray, jfarrell, msmith, rbrady

4. **Enable additional protections**:
   - Block sign-ins from high-risk countries (if not business-required)
   - Enable Azure AD Identity Protection for risky sign-in detection

---

## Questions?

Contact your Orro service desk or account manager for further information.

---

*This summary is based on our full incident report available on request.*
