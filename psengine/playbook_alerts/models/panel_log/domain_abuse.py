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

from ....common_models import IdOptionalNameType, RFBaseModel
from .common import (
    ChangeType,
    ReregistrationRecord,
    WhoisContactRecord,
    WhoisRecord,
    _DnsChangeShape,
    _MaliciousDnsChangeShape,
    _MaliciousUrlChangeShape,
)


class DomainAbuseDnsChange(_DnsChangeShape):
    pass


class DomainAbuseWhoisChange(ChangeType):
    domain: str
    old_record: WhoisRecord | None = None
    new_record: WhoisRecord | None = None
    removed_contacts: list[WhoisContactRecord]
    added_contacts: list[WhoisContactRecord]


class LogotypeInScreenshot(RFBaseModel):
    logotype_id: str | None = None
    screenshot_id: str | None = None
    url: str


class DomainAbuseLogoTypeChange(ChangeType):
    domain: str
    removed: list[LogotypeInScreenshot] | None = []
    added: list[LogotypeInScreenshot] | None = []


class DomainAbuseMaliciousDnsChange(_MaliciousDnsChangeShape):
    pass


class DomainAbuseReregistrationRecordChange(ChangeType):
    domain: str
    removed: ReregistrationRecord | None = None
    added: ReregistrationRecord | None = None


class DomainAbuseMaliciousUrlChange(_MaliciousUrlChangeShape):
    pass


class MentionedEntity(RFBaseModel):
    entity: IdOptionalNameType
    reference: str | None = None
    fragment: str | None = None


class ScreenshotMention(RFBaseModel):
    url: str
    screenshot_id: str
    document: str
    analyzed: datetime
    mentioned_entities: list[MentionedEntity]


class DomainAbuseScreenshotMentions(ChangeType):
    domain: str
    added: list[ScreenshotMention]
