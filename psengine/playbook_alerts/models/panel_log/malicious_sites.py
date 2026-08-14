##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

from datetime import datetime

from ....common_models import RFBaseModel
from .common import (
    ChangeType,
    ReregistrationRecord,
    WhoisContactRecord,
    WhoisRecord,
    _DnsChangeShape,
    _MaliciousDnsChangeShape,
    _MaliciousUrlChangeShape,
    _UrlImageChange,
)


class ThreatBehavior(RFBaseModel):
    threat_types: list[str] | None = []


class PhishingMaliciousBehaviorChange(ChangeType):
    domain: str | None = None
    added: ThreatBehavior | None = None
    removed: ThreatBehavior | None = None


class AttackerAddedChange(ChangeType):
    attacker: str | None = None
    cause: str | None = None
    manual_addition_user_id: str | None = None
    manual_addition_user_name: str | None = None
    typosquat_targets: list[str] | None = []
    similar_domains_keywords: list[str] | None = []


class ForSaleChange(_UrlImageChange):
    pass


class ParkedChange(_UrlImageChange):
    pass


class LogoHashChange(ChangeType):
    url: str | None = None
    scan: str | None = None
    hashes: list[str] | None = []
    brands: list[str] | None = []


class PhishingVerdictChange(ChangeType):
    domain: str | None = None
    url: str | None = None
    risk_rule: str | None = None
    ttps: list[str] | None = []
    brands: list[str] | None = []


class SuggestedTakedownChange(ChangeType):
    has_phishing_verdict: bool | None = None
    has_high_interest_logo: bool | None = None
    has_login_form: bool | None = None
    screenshot: str | None = None


class MaliciousSitesLogotypeRegion(RFBaseModel):
    min_x: int | None = None
    min_y: int | None = None
    max_x: int | None = None
    max_y: int | None = None


class MaliciousSitesLogotype(RFBaseModel):
    logotype_id: str | None = None
    screenshot_id: str | None = None
    url: str | None = None
    screenshot_width: int | None = None
    screenshot_height: int | None = None
    region: MaliciousSitesLogotypeRegion | None = None
    is_high_interest: bool | None = None


class MaliciousSitesAttackerAddedChange(AttackerAddedChange):
    logotypes: list[MaliciousSitesLogotype] | None = []


class MaliciousSitesDnsChange(_DnsChangeShape):
    """`malicious_sites_dns_change` — same shape as `DomainAbuseDnsChange`, distinct type."""


class MaliciousSitesMaliciousDnsChange(_MaliciousDnsChangeShape):
    """`malicious_sites_malicious_dns_change` — same shape as DA's, distinct type."""


class MaliciousSitesMaliciousUrlChange(_MaliciousUrlChangeShape):
    """`malicious_sites_malicious_url_change` — same shape as DA's, distinct type."""


class MaliciousSitesWhoisRecord(WhoisRecord):
    updated: datetime | None = None
    expires: datetime | None = None


class MaliciousSitesWhoisChange(ChangeType):
    domain: str | None = None
    old_record: MaliciousSitesWhoisRecord | None = None
    new_record: MaliciousSitesWhoisRecord | None = None
    removed_contacts: list[WhoisContactRecord] | None = []
    added_contacts: list[WhoisContactRecord] | None = []


class MaliciousSitesReregistrationChange(ChangeType):
    domain: str | None = None
    removed: ReregistrationRecord | None = None
    added: ReregistrationRecord | None = None


class MaliciousSitesLogoChange(ChangeType):
    domain: str | None = None
    removed: list[MaliciousSitesLogotype] | None = []
    added: list[MaliciousSitesLogotype] | None = []


class MaliciousSitesScreenshotMentionChange(ChangeType):
    url: str | None = None
    scan: str | None = None
    screenshot: str | None = None
    mentions: list[str] | None = []
    texts: list[str] | None = []
